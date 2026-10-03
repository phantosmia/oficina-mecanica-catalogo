import boto3
from fastapi.testclient import TestClient

from app.shared.settings import settings


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_reports_table(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "table": settings.table_name, "table_status": "ACTIVE"}


def test_ready_fails_without_table(client: TestClient) -> None:
    boto3.client("dynamodb", region_name="us-east-1").delete_table(TableName=settings.table_name)
    assert client.get("/ready").status_code == 503
