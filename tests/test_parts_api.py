from fastapi.testclient import TestClient

OIL = {
    "name": "Óleo sintético 5W30",
    "sku": "OLEO-5W30-1L",
    "description": "Óleo sintético para motores",
    "unit_price": 45.0,
    "attributes": {"viscosidade": "5W30", "volume_litros": 1, "sintetico": True, "densidade": 0.85},
}


def test_part_crud_keeps_type_specific_attributes(client: TestClient, admin_headers: dict[str, str]) -> None:
    created = client.post("/parts", json=OIL, headers=admin_headers)
    assert created.status_code == 201
    part = created.json()
    assert part["attributes"] == {"viscosidade": "5W30", "volume_litros": 1, "sintetico": True, "densidade": 0.85}

    fetched = client.get(f"/parts/{part['id']}").json()
    assert fetched["attributes"] == part["attributes"]
    assert fetched["unit_price"] == 45.0

    updated = client.put(
        f"/parts/{part['id']}",
        json={"unit_price": 49.9, "attributes": {"viscosidade": "5W30", "volume_litros": 4}},
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["unit_price"] == 49.9
    assert updated.json()["attributes"] == {"viscosidade": "5W30", "volume_litros": 4}


def test_duplicate_sku_is_rejected(client: TestClient, admin_headers: dict[str, str]) -> None:
    assert client.post("/parts", json=OIL, headers=admin_headers).status_code == 201

    duplicate = client.post("/parts", json={**OIL, "name": "Outro óleo"}, headers=admin_headers)

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "SKU já cadastrado."
    assert len(client.get("/parts").json()) == 1


def test_changing_sku_frees_the_old_one(client: TestClient, admin_headers: dict[str, str]) -> None:
    part_id = client.post("/parts", json=OIL, headers=admin_headers).json()["id"]

    renamed = client.put(f"/parts/{part_id}", json={"sku": "OLEO-5W30-4L"}, headers=admin_headers)
    assert renamed.status_code == 200
    assert renamed.json()["sku"] == "OLEO-5W30-4L"

    # O SKU antigo ficou livre; o novo está ocupado.
    assert client.post("/parts", json={**OIL, "name": "Óleo 1L"}, headers=admin_headers).status_code == 201
    assert client.post("/parts", json={**OIL, "sku": "OLEO-5W30-4L"}, headers=admin_headers).status_code == 409


def test_changing_sku_to_one_in_use_is_rejected(client: TestClient, admin_headers: dict[str, str]) -> None:
    client.post("/parts", json=OIL, headers=admin_headers)
    filter_id = client.post(
        "/parts", json={"name": "Filtro de óleo", "sku": "FILTRO-OLEO", "unit_price": 25.0}, headers=admin_headers
    ).json()["id"]

    response = client.put(f"/parts/{filter_id}", json={"sku": "OLEO-5W30-1L"}, headers=admin_headers)

    assert response.status_code == 409
    assert client.get(f"/parts/{filter_id}").json()["sku"] == "FILTRO-OLEO"


def test_delete_deactivates_part(client: TestClient, admin_headers: dict[str, str]) -> None:
    part_id = client.post("/parts", json=OIL, headers=admin_headers).json()["id"]

    assert client.delete(f"/parts/{part_id}", headers=admin_headers).status_code == 204

    assert client.get("/parts").json() == []
    assert client.get(f"/parts/{part_id}").json()["active"] is False
    assert len(client.get("/parts", params={"include_inactive": True}).json()) == 1


def test_part_not_found(client: TestClient, admin_headers: dict[str, str]) -> None:
    assert client.get("/parts/nao-existe").status_code == 404
    assert client.put("/parts/nao-existe", json={"unit_price": 10}, headers=admin_headers).status_code == 404
    assert client.delete("/parts/nao-existe", headers=admin_headers).status_code == 404
