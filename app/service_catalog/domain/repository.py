from abc import ABC, abstractmethod

from app.service_catalog.domain.entity import CatalogServiceEntity


class ICatalogServiceRepository(ABC):
    @abstractmethod
    def list_all(self, include_inactive: bool) -> list[CatalogServiceEntity]: ...

    @abstractmethod
    def get_by_id(self, service_id: str) -> CatalogServiceEntity | None: ...

    @abstractmethod
    def get_many(self, service_ids: list[str]) -> list[CatalogServiceEntity]:
        """Serviços encontrados entre `service_ids`; os inexistentes são omitidos."""
        ...

    @abstractmethod
    def create(self, service: CatalogServiceEntity) -> CatalogServiceEntity: ...

    @abstractmethod
    def update(self, service: CatalogServiceEntity) -> CatalogServiceEntity: ...
