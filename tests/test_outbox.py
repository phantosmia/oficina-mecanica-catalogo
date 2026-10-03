import json
from typing import Any

import boto3
from fastapi.testclient import TestClient

from app.shared.outbox import OUTBOX_PARTITION, OutboxRelay
from app.shared.dynamodb import query_gsi1
from app.shared.settings import settings
from app.shared.sns_publisher import SnsEventPublisher, message_attributes


def _receive_all(queue_url: str) -> list[dict[str, Any]]:
    response = boto3.client("sqs", region_name="us-east-1").receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=10, MessageAttributeNames=["All"]
    )
    return response.get("Messages", [])


def test_part_registration_is_published_through_the_outbox(
    client: TestClient, admin_headers: dict[str, str], table: Any, subscriber_queue_url: str
) -> None:
    part = client.post(
        "/parts", json={"name": "Óleo 5W30", "sku": "OLEO-5W30-1L", "unit_price": 45}, headers=admin_headers
    ).json()

    # Gravado na outbox junto com a peça, mas ainda não publicado.
    assert len(query_gsi1(table, OUTBOX_PARTITION)) == 1
    assert _receive_all(subscriber_queue_url) == []

    relay = OutboxRelay(table, SnsEventPublisher(settings.events_topic_arn))
    assert relay.run_once() == 1

    messages = _receive_all(subscriber_queue_url)
    assert len(messages) == 1
    envelope = json.loads(messages[0]["Body"])
    assert envelope["type"] == "PecaCadastrada"
    assert envelope["payload"] == {"part_id": part["id"], "sku": "OLEO-5W30-1L", "name": "Óleo 5W30"}
    assert envelope["saga_id"] is None
    assert messages[0]["MessageAttributes"]["type"]["StringValue"] == "PecaCadastrada"
    assert messages[0]["MessageAttributes"]["correlation_id"]["StringValue"] == envelope["message_id"]

    # Publicado uma vez só: a outbox ficou vazia.
    assert query_gsi1(table, OUTBOX_PARTITION) == []
    assert relay.run_once() == 0


def test_failed_part_registration_does_not_emit_event(
    client: TestClient, admin_headers: dict[str, str], table: Any
) -> None:
    payload = {"name": "Óleo", "sku": "OLEO", "unit_price": 45}
    client.post("/parts", json=payload, headers=admin_headers)
    assert client.post("/parts", json=payload, headers=admin_headers).status_code == 409

    # A transação inteira foi cancelada: só o evento da primeira peça existe.
    assert len(query_gsi1(table, OUTBOX_PARTITION)) == 1


def test_services_do_not_emit_events(client: TestClient, admin_headers: dict[str, str], table: Any) -> None:
    client.post("/services", json={"name": "Alinhamento", "base_price": 120, "estimated_minutes": 45}, headers=admin_headers)
    assert query_gsi1(table, OUTBOX_PARTITION) == []


def test_message_attributes_carry_saga_and_trace_context() -> None:
    envelope = {"type": "PecasReservadas", "message_id": "m-1", "saga_id": "s-1", "order_id": 42}

    attributes = message_attributes(envelope, {"traceparent": "00-abc-def-01"})

    assert {k: v["StringValue"] for k, v in attributes.items()} == {
        "type": "PecasReservadas",
        "correlation_id": "s-1",
        "saga_id": "s-1",
        "order_id": "42",
        "traceparent": "00-abc-def-01",
    }
