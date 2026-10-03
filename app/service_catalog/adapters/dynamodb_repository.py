from datetime import datetime
from typing import Any

from app.shared.dynamodb import batch_get, query_gsi1, sort_key, to_dynamo_number
from app.service_catalog.domain.entity import CatalogServiceEntity
from app.service_catalog.domain.repository import ICatalogServiceRepository

PARTITION = "SERVICE"


def _pk(service_id: str) -> str:
    return f"{PARTITION}#{service_id}"


def _to_item(service: CatalogServiceEntity) -> dict[str, Any]:
    return {
        "pk": _pk(service.id),
        "gsi1pk": PARTITION,
        "gsi1sk": sort_key(service.name, service.id),
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "base_price": to_dynamo_number(service.base_price),
        "estimated_minutes": service.estimated_minutes,
        "active": service.active,
        "created_at": service.created_at.isoformat(),
        "updated_at": service.updated_at.isoformat() if service.updated_at else None,
    }


def _to_entity(item: dict[str, Any]) -> CatalogServiceEntity:
    return CatalogServiceEntity(
        id=item["id"],
        name=item["name"],
        description=item.get("description"),
        base_price=float(item["base_price"]),
        estimated_minutes=int(item["estimated_minutes"]),
        active=bool(item["active"]),
        created_at=datetime.fromisoformat(item["created_at"]),
        updated_at=datetime.fromisoformat(item["updated_at"]) if item.get("updated_at") else None,
    )


class DynamoDBCatalogServiceRepository(ICatalogServiceRepository):
    def __init__(self, table: Any) -> None:
        self._table = table

    def list_all(self, include_inactive: bool) -> list[CatalogServiceEntity]:
        services = [_to_entity(i) for i in query_gsi1(self._table, PARTITION)]
        return services if include_inactive else [s for s in services if s.active]

    def get_by_id(self, service_id: str) -> CatalogServiceEntity | None:
        item = self._table.get_item(Key={"pk": _pk(service_id)}).get("Item")
        return _to_entity(item) if item else None

    def get_many(self, service_ids: list[str]) -> list[CatalogServiceEntity]:
        return [_to_entity(i) for i in batch_get(self._table, [_pk(i) for i in service_ids])]

    def create(self, service: CatalogServiceEntity) -> CatalogServiceEntity:
        self._table.put_item(Item=_to_item(service))
        return service

    def update(self, service: CatalogServiceEntity) -> CatalogServiceEntity:
        self._table.put_item(Item=_to_item(service))
        return service
