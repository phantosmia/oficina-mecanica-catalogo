from dataclasses import replace
from datetime import UTC, datetime
import uuid

from app.shared.exceptions import NotFoundError
from app.service_catalog.domain.entity import CatalogServiceEntity
from app.service_catalog.domain.repository import ICatalogServiceRepository


class ListCatalogServicesUseCase:
    def __init__(self, repo: ICatalogServiceRepository) -> None:
        self._repo = repo

    def execute(self, include_inactive: bool = False) -> list[CatalogServiceEntity]:
        return self._repo.list_all(include_inactive)


class GetCatalogServiceUseCase:
    def __init__(self, repo: ICatalogServiceRepository) -> None:
        self._repo = repo

    def execute(self, service_id: str) -> CatalogServiceEntity:
        service = self._repo.get_by_id(service_id)
        if service is None:
            raise NotFoundError("Serviço", service_id)
        return service


class CreateCatalogServiceUseCase:
    def __init__(self, repo: ICatalogServiceRepository) -> None:
        self._repo = repo

    def execute(
        self,
        name: str,
        description: str | None,
        base_price: float,
        estimated_minutes: int,
        active: bool = True,
        service_id: str | None = None,
    ) -> CatalogServiceEntity:
        # `service_id` explícito só é usado pela carga de dados de exemplo
        # (scripts/seed.py), que precisa de IDs estáveis entre execuções.
        return self._repo.create(
            CatalogServiceEntity(
                id=service_id or str(uuid.uuid4()),
                name=name,
                description=description,
                base_price=base_price,
                estimated_minutes=estimated_minutes,
                active=active,
                created_at=datetime.now(UTC),
            )
        )


class UpdateCatalogServiceUseCase:
    def __init__(self, repo: ICatalogServiceRepository) -> None:
        self._repo = repo

    def execute(self, service_id: str, fields: dict[str, object]) -> CatalogServiceEntity:
        service = self._repo.get_by_id(service_id)
        if service is None:
            raise NotFoundError("Serviço", service_id)
        return self._repo.update(replace(service, **fields, updated_at=datetime.now(UTC)))


class DeactivateCatalogServiceUseCase:
    """Remoção lógica: sem chave estrangeira entre microsserviços, apagar o
    item de verdade deixaria OS e orçamentos antigos apontando para um ID que
    não existe mais. Desativado, ele some da listagem e é recusado em
    diagnósticos novos, mas continua consultável pelo ID."""

    def __init__(self, repo: ICatalogServiceRepository) -> None:
        self._repo = repo

    def execute(self, service_id: str) -> None:
        UpdateCatalogServiceUseCase(self._repo).execute(service_id, {"active": False})
