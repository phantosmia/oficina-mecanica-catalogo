import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_token

WRITES = [
    ("post", "/services", {"name": "X", "base_price": 1, "estimated_minutes": 1}),
    ("put", "/services/qualquer", {"base_price": 1}),
    ("delete", "/services/qualquer", None),
    ("post", "/parts", {"name": "X", "sku": "X", "unit_price": 1}),
    ("put", "/parts/qualquer", {"unit_price": 1}),
    ("delete", "/parts/qualquer", None),
]


@pytest.mark.parametrize(("method", "path", "body"), WRITES)
def test_writes_require_admin_token(client: TestClient, method: str, path: str, body: dict | None) -> None:
    kwargs = {"json": body} if body is not None else {}
    assert getattr(client, method)(path, **kwargs).status_code == 401


@pytest.mark.parametrize(
    "token",
    [
        "nao-e-um-jwt",
        make_token(secret="outro-segredo"),
        make_token(expires_in=-1),
        make_token(subject="12345678909"),  # token de cliente (CPF), não de admin
    ],
)
def test_invalid_tokens_are_rejected(client: TestClient, token: str) -> None:
    response = client.post(
        "/services",
        json={"name": "X", "base_price": 1, "estimated_minutes": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_reads_are_public(client: TestClient) -> None:
    assert client.get("/services").status_code == 200
    assert client.get("/parts").status_code == 200
    assert client.post("/catalog/lookup", json={}).status_code == 200
