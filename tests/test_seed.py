from fastapi.testclient import TestClient

from scripts.seed import PARTS, SERVICES, part_id_for, seed


def test_seed_is_idempotent_and_uses_stable_ids(client: TestClient) -> None:
    assert seed() == (len(SERVICES), len(PARTS))
    assert seed() == (0, 0)

    parts = client.get("/parts").json()
    assert len(parts) == len(PARTS)
    oil = next(p for p in parts if p["sku"] == "OLEO-5W30-1L")
    assert oil["id"] == part_id_for("OLEO-5W30-1L")
    assert oil["attributes"] == {"viscosidade": "5W30", "volume_litros": 1}
    assert len(client.get("/services").json()) == len(SERVICES)


def test_bootstrap_local_is_idempotent() -> None:
    from scripts.bootstrap_local import bootstrap

    assert bootstrap() == bootstrap() == "arn:aws:sns:us-east-1:123456789012:catalogo-eventos"
