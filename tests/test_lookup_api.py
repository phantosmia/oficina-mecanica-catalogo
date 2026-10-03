from fastapi.testclient import TestClient


def test_lookup_returns_prices_and_reports_missing_items(client: TestClient, admin_headers: dict[str, str]) -> None:
    service_id = client.post(
        "/services", json={"name": "Troca de óleo", "base_price": 150, "estimated_minutes": 30}, headers=admin_headers
    ).json()["id"]
    part_id = client.post(
        "/parts", json={"name": "Óleo 5W30", "sku": "OLEO", "unit_price": 45}, headers=admin_headers
    ).json()["id"]
    inactive_part_id = client.post(
        "/parts", json={"name": "Filtro antigo", "sku": "FILTRO", "unit_price": 20, "active": False}, headers=admin_headers
    ).json()["id"]

    response = client.post(
        "/catalog/lookup",
        json={
            "service_ids": [service_id, "servico-fantasma", service_id],
            "part_ids": [part_id, inactive_part_id, "peca-fantasma"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert [(s["id"], s["base_price"]) for s in body["services"]] == [(service_id, 150.0)]
    assert {p["id"]: p["active"] for p in body["parts"]} == {part_id: True, inactive_part_id: False}
    assert body["missing_service_ids"] == ["servico-fantasma"]
    assert body["missing_part_ids"] == ["peca-fantasma"]


def test_lookup_limits_batch_size(client: TestClient) -> None:
    response = client.post("/catalog/lookup", json={"part_ids": [str(i) for i in range(101)]})
    assert response.status_code == 422
