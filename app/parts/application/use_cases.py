from dataclasses import replace
from datetime import UTC, datetime
import uuid

from app.shared.exceptions import NotFoundError
from app.parts.domain.entity import PartAttributes, PartEntity
from app.parts.domain.events import PartRegistered
from app.parts.domain.repository import IPartRepository


class ListPartsUseCase:
    def __init__(self, repo: IPartRepository) -> None:
        self._repo = repo

    def execute(self, include_inactive: bool = False) -> list[PartEntity]:
        return self._repo.list_all(include_inactive)


class GetPartUseCase:
    def __init__(self, repo: IPartRepository) -> None:
        self._repo = repo

    def execute(self, part_id: str) -> PartEntity:
        part = self._repo.get_by_id(part_id)
        if part is None:
            raise NotFoundError("Peça/insumo", part_id)
        return part


class CreatePartUseCase:
    def __init__(self, repo: IPartRepository) -> None:
        self._repo = repo

    def execute(
        self,
        name: str,
        sku: str,
        description: str | None,
        unit_price: float,
        attributes: PartAttributes | None = None,
        active: bool = True,
        part_id: str | None = None,
    ) -> PartEntity:
        # `part_id` explícito só é usado pela carga de dados de exemplo
        # (scripts/seed.py), que precisa de IDs estáveis entre execuções.
        part = PartEntity(
            id=part_id or str(uuid.uuid4()),
            name=name,
            sku=sku,
            description=description,
            unit_price=unit_price,
            attributes=attributes or {},
            active=active,
            created_at=datetime.now(UTC),
        )
        return self._repo.create(part, PartRegistered(part_id=part.id, sku=part.sku, name=part.name))


class UpdatePartUseCase:
    def __init__(self, repo: IPartRepository) -> None:
        self._repo = repo

    def execute(self, part_id: str, fields: dict[str, object]) -> PartEntity:
        part = self._repo.get_by_id(part_id)
        if part is None:
            raise NotFoundError("Peça/insumo", part_id)
        return self._repo.update(replace(part, **fields, updated_at=datetime.now(UTC)), previous_sku=part.sku)


class DeactivatePartUseCase:
    """Remoção lógica, pelo mesmo motivo de `DeactivateCatalogServiceUseCase`."""

    def __init__(self, repo: IPartRepository) -> None:
        self._repo = repo

    def execute(self, part_id: str) -> None:
        UpdatePartUseCase(self._repo).execute(part_id, {"active": False})
