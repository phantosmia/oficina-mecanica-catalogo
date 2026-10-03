from datetime import datetime
from typing import Any

from botocore.exceptions import ClientError

from app.shared.dynamodb import batch_get, query_gsi1, sort_key, to_dynamo_number
from app.shared.events import Envelope
from app.shared.exceptions import ConflictError
from app.shared.outbox import outbox_put
from app.parts.domain.entity import PartEntity
from app.parts.domain.events import PartRegistered
from app.parts.domain.repository import IPartRepository

PARTITION = "PART"


def _pk(part_id: str) -> str:
    return f"{PARTITION}#{part_id}"


def _sku_pk(sku: str) -> str:
    return f"SKU#{sku}"


def _to_item(part: PartEntity) -> dict[str, Any]:
    return {
        "pk": _pk(part.id),
        "gsi1pk": PARTITION,
        "gsi1sk": sort_key(part.name, part.id),
        "id": part.id,
        "name": part.name,
        "sku": part.sku,
        "description": part.description,
        "unit_price": to_dynamo_number(part.unit_price),
        "attributes": {
            key: to_dynamo_number(value) if isinstance(value, float) else value
            for key, value in part.attributes.items()
        },
        "active": part.active,
        "created_at": part.created_at.isoformat(),
        "updated_at": part.updated_at.isoformat() if part.updated_at else None,
    }


def _attribute_value(value: Any) -> Any:
    # Números voltam do DynamoDB como Decimal: inteiro vira int, o resto float.
    if hasattr(value, "as_integer_ratio") and not isinstance(value, bool):
        return int(value) if value == int(value) else float(value)
    return value


def _to_entity(item: dict[str, Any]) -> PartEntity:
    return PartEntity(
        id=item["id"],
        name=item["name"],
        sku=item["sku"],
        description=item.get("description"),
        unit_price=float(item["unit_price"]),
        attributes={key: _attribute_value(value) for key, value in (item.get("attributes") or {}).items()},
        active=bool(item["active"]),
        created_at=datetime.fromisoformat(item["created_at"]),
        updated_at=datetime.fromisoformat(item["updated_at"]) if item.get("updated_at") else None,
    )


def _cancellation_codes(error: ClientError) -> list[str]:
    return [reason.get("Code", "None") for reason in error.response.get("CancellationReasons", [])]


class DynamoDBPartRepository(IPartRepository):
    """O DynamoDB não tem restrição `UNIQUE` além da chave primária. A
    unicidade do SKU é garantida por um item `SKU#<sku>` gravado na mesma
    transação que a peça, com a condição de ainda não existir: duas peças
    com o mesmo SKU nunca conseguem as duas gravar esse item."""

    def __init__(self, table: Any) -> None:
        self._table = table
        self._client = table.meta.client

    def list_all(self, include_inactive: bool) -> list[PartEntity]:
        parts = [_to_entity(i) for i in query_gsi1(self._table, PARTITION)]
        return parts if include_inactive else [p for p in parts if p.active]

    def get_by_id(self, part_id: str) -> PartEntity | None:
        item = self._table.get_item(Key={"pk": _pk(part_id)}).get("Item")
        return _to_entity(item) if item else None

    def get_many(self, part_ids: list[str]) -> list[PartEntity]:
        return [_to_entity(i) for i in batch_get(self._table, [_pk(i) for i in part_ids])]

    def create(self, part: PartEntity, event: PartRegistered) -> PartEntity:
        envelope = Envelope(type=event.event_type, payload=event.payload())
        try:
            self._client.transact_write_items(
                TransactItems=[
                    self._put(_to_item(part), condition="attribute_not_exists(pk)"),
                    self._put({"pk": _sku_pk(part.sku), "part_id": part.id}, condition="attribute_not_exists(pk)"),
                    outbox_put(self._table.name, envelope),
                ]
            )
        except ClientError as error:
            codes = _cancellation_codes(error)
            if codes[:1] == ["ConditionalCheckFailed"]:
                raise ConflictError("Peça já cadastrada.") from error
            if codes[1:2] == ["ConditionalCheckFailed"]:
                raise ConflictError("SKU já cadastrado.") from error
            raise
        return part

    def update(self, part: PartEntity, previous_sku: str) -> PartEntity:
        if part.sku == previous_sku:
            self._table.put_item(Item=_to_item(part))
            return part
        try:
            self._client.transact_write_items(
                TransactItems=[
                    self._put(_to_item(part), condition="attribute_exists(pk)"),
                    {"Delete": {"TableName": self._table.name, "Key": {"pk": _sku_pk(previous_sku)}}},
                    self._put({"pk": _sku_pk(part.sku), "part_id": part.id}, condition="attribute_not_exists(pk)"),
                ]
            )
        except ClientError as error:
            if _cancellation_codes(error)[2:3] == ["ConditionalCheckFailed"]:
                raise ConflictError("SKU já cadastrado.") from error
            raise
        return part

    def _put(self, item: dict[str, Any], condition: str) -> dict[str, Any]:
        return {"Put": {"TableName": self._table.name, "Item": item, "ConditionExpression": condition}}
