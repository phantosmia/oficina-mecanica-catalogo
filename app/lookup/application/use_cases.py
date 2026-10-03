from dataclasses import dataclass

from app.parts.domain.entity import PartEntity
from app.parts.domain.repository import IPartRepository
from app.service_catalog.domain.entity import CatalogServiceEntity
from app.service_catalog.domain.repository import ICatalogServiceRepository


@dataclass
class LookupResult:
    services: list[CatalogServiceEntity]
    parts: list[PartEntity]
    missing_service_ids: list[str]
    missing_part_ids: list[str]


class LookupItemsUseCase:
    """Consulta em lote usada pela Execução ao concluir um diagnóstico
    (docs/saga.md): valida os serviços e peças escolhidos pelo mecânico e
    devolve os preços que serão copiados para a OS e o orçamento.

    Não levanta erro para item inexistente ou desativado: devolve o que
    encontrou, com o campo `active`, e lista os IDs ausentes. Quem chama
    decide o que fazer com isso (a Execução recusa o diagnóstico)."""

    def __init__(self, services: ICatalogServiceRepository, parts: IPartRepository) -> None:
        self._services = services
        self._parts = parts

    def execute(self, service_ids: list[str], part_ids: list[str]) -> LookupResult:
        unique_service_ids = list(dict.fromkeys(service_ids))
        unique_part_ids = list(dict.fromkeys(part_ids))
        found_services = self._services.get_many(unique_service_ids)
        found_parts = self._parts.get_many(unique_part_ids)
        found_service_ids = {s.id for s in found_services}
        found_part_ids = {p.id for p in found_parts}
        return LookupResult(
            services=found_services,
            parts=found_parts,
            missing_service_ids=[i for i in unique_service_ids if i not in found_service_ids],
            missing_part_ids=[i for i in unique_part_ids if i not in found_part_ids],
        )
