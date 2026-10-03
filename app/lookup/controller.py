from fastapi import APIRouter, Depends

from app.lookup.application.use_cases import LookupItemsUseCase
from app.lookup.schemas import LookupRequest, LookupResponse
from app.parts.adapters.presenter import to_response as part_to_response
from app.parts.controller import get_part_repo
from app.parts.domain.repository import IPartRepository
from app.service_catalog.adapters.presenter import to_response as service_to_response
from app.service_catalog.controller import get_service_repo
from app.service_catalog.domain.repository import ICatalogServiceRepository

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.post("/lookup", response_model=LookupResponse)
def lookup_items(
    payload: LookupRequest,
    services: ICatalogServiceRepository = Depends(get_service_repo),
    parts: IPartRepository = Depends(get_part_repo),
) -> LookupResponse:
    """Consulta em lote usada pela Execução ao concluir um diagnóstico.

    Sempre responde 200: itens inexistentes aparecem em `missing_*_ids` e
    itens desativados voltam com `active=false`. Quem chama decide se aceita."""
    result = LookupItemsUseCase(services, parts).execute(payload.service_ids, payload.part_ids)
    return LookupResponse(
        services=[service_to_response(s) for s in result.services],
        parts=[part_to_response(p) for p in result.parts],
        missing_service_ids=result.missing_service_ids,
        missing_part_ids=result.missing_part_ids,
    )
