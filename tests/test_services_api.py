from fastapi.testclient import TestClient

SERVICE = {"name": "Troca de óleo", "description": "Troca completa", "base_price": 150.0, "estimated_minutes": 30}


def test_service_crud(client: TestClient, admin_headers: dict[str, str]) -> None:
    created = client.post("/services", json=SERVICE, headers=admin_headers)
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Troca de óleo"
    assert body["base_price"] == 150.0
    assert body["active"] is True
    service_id = body["id"]

    assert client.get(f"/services/{service_id}").json()["estimated_minutes"] == 30

    updated = client.put(f"/services/{service_id}", json={"base_price": 175.5}, headers=admin_headers)
    assert updated.status_code == 200
    assert updated.json()["base_price"] == 175.5
    assert updated.json()["name"] == "Troca de óleo"
    assert updated.json()["updated_at"] is not None


def test_services_are_listed_by_name(client: TestClient, admin_headers: dict[str, str]) -> None:
    for name in ["Revisão de freios", "Óleo e filtro", "alinhamento", "Troca de óleo"]:
        client.post("/services", json={**SERVICE, "name": name}, headers=admin_headers)

    names = [s["name"] for s in client.get("/services").json()]
    # Sem acento e sem diferença de maiúsculas: "Óleo" entre "alinhamento" e "Revisão".
    assert names == ["alinhamento", "Óleo e filtro", "Revisão de freios", "Troca de óleo"]


def test_delete_deactivates_instead_of_removing(client: TestClient, admin_headers: dict[str, str]) -> None:
    service_id = client.post("/services", json=SERVICE, headers=admin_headers).json()["id"]

    assert client.delete(f"/services/{service_id}", headers=admin_headers).status_code == 204

    assert client.get("/services").json() == []
    assert [s["id"] for s in client.get("/services", params={"include_inactive": True}).json()] == [service_id]
    assert client.get(f"/services/{service_id}").json()["active"] is False


def test_service_not_found(client: TestClient, admin_headers: dict[str, str]) -> None:
    assert client.get("/services/nao-existe").status_code == 404
    assert client.put("/services/nao-existe", json={"base_price": 10}, headers=admin_headers).status_code == 404
    assert client.delete("/services/nao-existe", headers=admin_headers).status_code == 404


def test_service_validation(client: TestClient, admin_headers: dict[str, str]) -> None:
    assert client.post("/services", json={**SERVICE, "base_price": 0}, headers=admin_headers).status_code == 422
    assert client.post("/services", json={**SERVICE, "estimated_minutes": -1}, headers=admin_headers).status_code == 422
