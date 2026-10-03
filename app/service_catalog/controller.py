from fastapi import APIRouter, Depends, Response, status

from app.shared.dependencies import get_current_admin
from app.shared.dynamodb import get_table
from app.shared.http_errors import domain_error_handler
from app.service_catalog.adapters.dynamodb_repository import DynamoDBCatalogServiceRepository
from app.service_catalog.adapters.presenter import to_response
from app.service_catalog.application.use_cases import (
    CreateCatalogServiceUseCase,
    DeactivateCatalogServiceUseCase,
    GetCatalogServiceUseCase,
    ListCatalogServicesUseCase,
    UpdateCatalogServiceUseCase,
)
from app.service_catalog.domain.repository import ICatalogServiceRepository
from app.service_catalog.schemas import CatalogServiceCreate, CatalogServiceRead, CatalogServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


def get_service_repo() -> ICatalogServiceRepository:
    return DynamoDBCatalogServiceRepository(get_table())


# Leitura pública: o catálogo é a tabela de preços da oficina, não um dado
# sensível, e a Execução consulta sem um token de admin. Só escrita exige admin.
@router.get("", response_model=list[CatalogServiceRead])
def get_services(include_inactive: bool = False, repo: ICatalogServiceRepository = Depends(get_service_repo)) -> list[CatalogServiceRead]:
    return [to_response(s) for s in ListCatalogServicesUseCase(repo).execute(include_inactive)]


@router.get("/{service_id}", response_model=CatalogServiceRead)
def get_service(service_id: str, repo: ICatalogServiceRepository = Depends(get_service_repo)) -> CatalogServiceRead:
    with domain_error_handler():
        return to_response(GetCatalogServiceUseCase(repo).execute(service_id))


@router.post("", response_model=CatalogServiceRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_admin)])
def post_service(payload: CatalogServiceCreate, repo: ICatalogServiceRepository = Depends(get_service_repo)) -> CatalogServiceRead:
    return to_response(
        CreateCatalogServiceUseCase(repo).execute(
            name=payload.name,
            description=payload.description,
            base_price=payload.base_price,
            estimated_minutes=payload.estimated_minutes,
            active=payload.active,
        )
    )


@router.put("/{service_id}", response_model=CatalogServiceRead, dependencies=[Depends(get_current_admin)])
def put_service(service_id: str, payload: CatalogServiceUpdate, repo: ICatalogServiceRepository = Depends(get_service_repo)) -> CatalogServiceRead:
    with domain_error_handler():
        return to_response(UpdateCatalogServiceUseCase(repo).execute(service_id, payload.model_dump(exclude_none=True)))


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_admin)])
def remove_service(service_id: str, repo: ICatalogServiceRepository = Depends(get_service_repo)) -> Response:
    with domain_error_handler():
        DeactivateCatalogServiceUseCase(repo).execute(service_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
