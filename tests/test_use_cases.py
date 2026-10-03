"""Testes unitários dos casos de uso, com repositórios em memória: sem
DynamoDB, só as regras da camada de aplicação."""

from dataclasses import replace

import pytest

from app.lookup.application.use_cases import LookupItemsUseCase
from app.parts.application.use_cases import CreatePartUseCase, DeactivatePartUseCase, UpdatePartUseCase
from app.parts.domain.entity import PartEntity
from app.parts.domain.events import PartRegistered
from app.parts.domain.repository import IPartRepository
from app.service_catalog.application.use_cases import (
    CreateCatalogServiceUseCase,
    DeactivateCatalogServiceUseCase,
    GetCatalogServiceUseCase,
)
from app.service_catalog.domain.entity import CatalogServiceEntity
from app.service_catalog.domain.repository import ICatalogServiceRepository
from app.shared.exceptions import NotFoundError


class InMemoryServices(ICatalogServiceRepository):
    def __init__(self) -> None:
        self.items: dict[str, CatalogServiceEntity] = {}

    def list_all(self, include_inactive: bool) -> list[CatalogServiceEntity]:
        return [s for s in self.items.values() if include_inactive or s.active]

    def get_by_id(self, service_id: str) -> CatalogServiceEntity | None:
        return self.items.get(service_id)

    def get_many(self, service_ids: list[str]) -> list[CatalogServiceEntity]:
        return [self.items[i] for i in service_ids if i in self.items]

    def create(self, service: CatalogServiceEntity) -> CatalogServiceEntity:
        self.items[service.id] = service
        return service

    def update(self, service: CatalogServiceEntity) -> CatalogServiceEntity:
        self.items[service.id] = service
        return service


class InMemoryParts(IPartRepository):
    def __init__(self) -> None:
        self.items: dict[str, PartEntity] = {}
        self.events: list[PartRegistered] = []

    def list_all(self, include_inactive: bool) -> list[PartEntity]:
        return [p for p in self.items.values() if include_inactive or p.active]

    def get_by_id(self, part_id: str) -> PartEntity | None:
        return self.items.get(part_id)

    def get_many(self, part_ids: list[str]) -> list[PartEntity]:
        return [self.items[i] for i in part_ids if i in self.items]

    def create(self, part: PartEntity, event: PartRegistered) -> PartEntity:
        self.items[part.id] = part
        self.events.append(event)
        return part

    def update(self, part: PartEntity, previous_sku: str) -> PartEntity:
        self.items[part.id] = part
        return part


def test_create_part_emits_part_registered_event() -> None:
    repo = InMemoryParts()

    part = CreatePartUseCase(repo).execute(name="Filtro", sku="FILTRO", description=None, unit_price=25.0)

    assert repo.events == [PartRegistered(part_id=part.id, sku="FILTRO", name="Filtro")]
    assert repo.events[0].event_type == "PecaCadastrada"
    assert repo.events[0].payload() == {"part_id": part.id, "sku": "FILTRO", "name": "Filtro"}


def test_explicit_ids_are_kept_for_seed_data() -> None:
    parts, services = InMemoryParts(), InMemoryServices()

    part = CreatePartUseCase(parts).execute(name="Filtro", sku="F", description=None, unit_price=1, part_id="fixo")
    service = CreateCatalogServiceUseCase(services).execute(
        name="Troca", description=None, base_price=1, estimated_minutes=1, service_id="fixo-2"
    )

    assert (part.id, service.id) == ("fixo", "fixo-2")


def test_update_preserves_unchanged_fields_and_stamps_updated_at() -> None:
    repo = InMemoryParts()
    part = CreatePartUseCase(repo).execute(name="Filtro", sku="F", description="d", unit_price=10, attributes={"a": 1})

    updated = UpdatePartUseCase(repo).execute(part.id, {"unit_price": 12.0})

    assert updated == replace(part, unit_price=12.0, updated_at=updated.updated_at)
    assert updated.updated_at is not None


def test_deactivation_is_logical() -> None:
    services, parts = InMemoryServices(), InMemoryParts()
    service = CreateCatalogServiceUseCase(services).execute(name="T", description=None, base_price=1, estimated_minutes=1)
    part = CreatePartUseCase(parts).execute(name="P", sku="P", description=None, unit_price=1)

    DeactivateCatalogServiceUseCase(services).execute(service.id)
    DeactivatePartUseCase(parts).execute(part.id)

    assert GetCatalogServiceUseCase(services).execute(service.id).active is False
    assert parts.items[part.id].active is False


def test_missing_items_raise_not_found() -> None:
    with pytest.raises(NotFoundError):
        GetCatalogServiceUseCase(InMemoryServices()).execute("x")
    with pytest.raises(NotFoundError):
        UpdatePartUseCase(InMemoryParts()).execute("x", {"unit_price": 1.0})
    with pytest.raises(NotFoundError):
        DeactivatePartUseCase(InMemoryParts()).execute("x")


def test_lookup_deduplicates_and_reports_missing_ids() -> None:
    services, parts = InMemoryServices(), InMemoryParts()
    service = CreateCatalogServiceUseCase(services).execute(name="T", description=None, base_price=1, estimated_minutes=1)

    result = LookupItemsUseCase(services, parts).execute([service.id, service.id, "x"], ["y", "y"])

    assert result.services == [service]
    assert result.parts == []
    assert result.missing_service_ids == ["x"]
    assert result.missing_part_ids == ["y"]
