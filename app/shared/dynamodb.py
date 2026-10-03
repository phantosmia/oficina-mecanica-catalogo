"""Acesso à tabela DynamoDB do Catálogo (ADR-0009, em oficina-mecanica-fiap).

*Single-table design*: serviços, peças, itens de unicidade de SKU e outbox
de eventos vivem na mesma tabela, diferenciados pelo prefixo da chave:

| Item               | pk                    | gsi1pk     | gsi1sk                         |
|--------------------|-----------------------|------------|--------------------------------|
| Serviço            | `SERVICE#<id>`        | `SERVICE`  | `<nome>#<id>` (lista por nome) |
| Peça               | `PART#<id>`           | `PART`     | `<nome>#<id>`                  |
| Unicidade de SKU   | `SKU#<sku>`           | —          | —                              |
| Outbox             | `OUTBOX#<message_id>` | `OUTBOX`   | `<occurred_at>#<message_id>`   |

Uma tabela só (em vez de uma por tipo) é o que permite gravar a peça, o item
de unicidade do SKU e o evento `PecaCadastrada` numa única
`TransactWriteItems` sem depender de transação entre tabelas, e mantém um só
recurso para o Terraform criar a cada rotação do AWS Academy Lab.

`TABLE_DEFINITION` é a fonte da verdade do schema para o LocalStack e para os
testes (moto); o Terraform do serviço (`infra/`) precisa espelhá-la.
"""

from decimal import Decimal
import unicodedata
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from app.shared.settings import settings

GSI1_NAME = "gsi1"

TABLE_DEFINITION: dict[str, Any] = {
    "AttributeDefinitions": [
        {"AttributeName": "pk", "AttributeType": "S"},
        {"AttributeName": "gsi1pk", "AttributeType": "S"},
        {"AttributeName": "gsi1sk", "AttributeType": "S"},
    ],
    "KeySchema": [{"AttributeName": "pk", "KeyType": "HASH"}],
    "GlobalSecondaryIndexes": [
        {
            "IndexName": GSI1_NAME,
            "KeySchema": [
                {"AttributeName": "gsi1pk", "KeyType": "HASH"},
                {"AttributeName": "gsi1sk", "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"},
        }
    ],
    "BillingMode": "PAY_PER_REQUEST",
}


def get_dynamodb_client() -> Any:
    return boto3.client("dynamodb", region_name=settings.aws_region)


def get_table() -> Any:
    return boto3.resource("dynamodb", region_name=settings.aws_region).Table(settings.table_name)


def create_table_if_missing(table_name: str) -> None:
    """Cria a tabela com `TABLE_DEFINITION` se ainda não existir (LocalStack/testes)."""
    client = get_dynamodb_client()
    if table_name in client.list_tables()["TableNames"]:
        return
    client.create_table(TableName=table_name, **TABLE_DEFINITION)
    client.get_waiter("table_exists").wait(TableName=table_name)


def sort_key(name: str, item_id: str) -> str:
    """`gsi1sk` para listar por nome em ordem alfabética: sem acento e sem
    distinção de maiúsculas (senão "Óleo" viria depois de "Pastilha"), com o
    ID no final para desempatar nomes iguais."""
    without_accents = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return f"{without_accents.casefold()}#{item_id}"


def to_dynamo_number(value: float | int) -> Decimal:
    """O DynamoDB não aceita `float` (só `Decimal`); `str()` evita herdar o
    erro de representação binária do float (ex.: 0.1 → 0.1000000000000000055)."""
    return Decimal(str(value))


def query_gsi1(table: Any, partition: str) -> list[dict[str, Any]]:
    """Todos os itens de uma partição do GSI1, já ordenados por `gsi1sk`, seguindo a paginação."""
    items: list[dict[str, Any]] = []
    kwargs: dict[str, Any] = {
        "IndexName": GSI1_NAME,
        "KeyConditionExpression": Key("gsi1pk").eq(partition),
    }
    while True:
        response = table.query(**kwargs)
        items.extend(response["Items"])
        if "LastEvaluatedKey" not in response:
            return items
        kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]


def batch_get(table: Any, pks: list[str]) -> list[dict[str, Any]]:
    """`BatchGetItem` em lotes de 100 (limite da API), reenviando as chaves não processadas.

    Usa `table.meta.client`, o cliente do *resource*: ele converte sozinho
    entre tipos Python e o formato tipado da API (`{"S": ...}`), então chaves
    e itens entram e saem como dicionários Python comuns, sem serialização
    manual (que aqui seria aplicada duas vezes)."""
    items: list[dict[str, Any]] = []
    client = table.meta.client
    for start in range(0, len(pks), 100):
        request: dict[str, Any] = {table.name: {"Keys": [{"pk": pk} for pk in pks[start : start + 100]]}}
        while request:
            response = client.batch_get_item(RequestItems=request)
            items.extend(response["Responses"].get(table.name, []))
            request = response.get("UnprocessedKeys") or {}
    return items
