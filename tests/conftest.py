import os

# Configuração antes de importar a aplicação (settings é lido no import).
# Credenciais falsas: o moto intercepta todas as chamadas boto3, nada sai pra AWS.
os.environ.update(
    {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_REGION": "us-east-1",
        "CATALOG_TABLE_NAME": "oficina-catalogo-test",
        "CATALOG_EVENTS_TOPIC_ARN": "arn:aws:sns:us-east-1:123456789012:catalogo-eventos",
        "JWT_SECRET_KEY": "test-secret-key",
        "ADMIN_USERNAME": "admin",
    }
)
os.environ.pop("AWS_ENDPOINT_URL", None)

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
import pytest
from fastapi.testclient import TestClient
from jose import jwt
from moto import mock_aws

from app.main import app
from app.shared.dynamodb import create_table_if_missing, get_table
from app.shared.settings import settings


@pytest.fixture(autouse=True)
def aws() -> Iterator[None]:
    with mock_aws():
        create_table_if_missing(settings.table_name)
        boto3.client("sns", region_name="us-east-1").create_topic(Name="catalogo-eventos")
        yield


@pytest.fixture
def subscriber_queue_url(aws: None) -> str:
    """Fila SQS assinando o tópico de eventos, como o Estoque fará (RFC-0007)."""
    sqs = boto3.client("sqs", region_name="us-east-1")
    queue_url = sqs.create_queue(QueueName="estoque-catalogo-eventos")["QueueUrl"]
    queue_arn = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
    boto3.client("sns", region_name="us-east-1").subscribe(
        TopicArn=settings.events_topic_arn,
        Protocol="sqs",
        Endpoint=queue_arn,
        Attributes={"RawMessageDelivery": "true"},
    )
    return queue_url


@pytest.fixture
def table(aws: None) -> Any:
    return get_table()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def make_token(subject: str = "admin", secret: str = "test-secret-key", expires_in: int = 60) -> str:
    payload = {"sub": subject, "exp": datetime.now(UTC) + timedelta(minutes=expires_in)}
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token()}"}
