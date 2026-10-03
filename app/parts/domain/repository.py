from abc import ABC, abstractmethod

from app.parts.domain.entity import PartEntity
from app.parts.domain.events import PartRegistered


class IPartRepository(ABC):
    @abstractmethod
    def list_all(self, include_inactive: bool) -> list[PartEntity]: ...

    @abstractmethod
    def get_by_id(self, part_id: str) -> PartEntity | None: ...

    @abstractmethod
    def get_many(self, part_ids: list[str]) -> list[PartEntity]:
        """Peças encontradas entre `part_ids`; as inexistentes são omitidas."""
        ...

    @abstractmethod
    def create(self, part: PartEntity, event: PartRegistered) -> PartEntity:
        """Grava a peça e o evento atomicamente. Levanta `ConflictError` se o SKU já existir."""
        ...

    @abstractmethod
    def update(self, part: PartEntity, previous_sku: str) -> PartEntity:
        """Levanta `ConflictError` se o novo SKU já pertencer a outra peça."""
        ...
