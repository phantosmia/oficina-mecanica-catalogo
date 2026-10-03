"""Cria a tabela DynamoDB e o tópico SNS no LocalStack (docker-compose).

Só para desenvolvimento local: na AWS, esses recursos são criados pelo
Terraform do serviço, nunca pela aplicação. Idempotente.

Uso: `python -m scripts.bootstrap_local`
"""

import logging

import boto3

from app.shared.dynamodb import create_table_if_missing
from app.shared.settings import settings


def bootstrap() -> str:
    """Retorna o ARN do tópico de eventos (criar um tópico que já existe devolve o mesmo ARN)."""
    create_table_if_missing(settings.table_name)
    topic_name = settings.events_topic_arn.rsplit(":", 1)[-1] or "catalogo-eventos"
    return boto3.client("sns", region_name=settings.aws_region).create_topic(Name=topic_name)["TopicArn"]


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("bootstrap").info("tabela %s e tópico %s prontos", settings.table_name, bootstrap())
