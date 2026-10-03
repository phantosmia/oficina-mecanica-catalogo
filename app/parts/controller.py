from fastapi import APIRouter, Depends, Response, status

from app.shared.dependencies import get_current_admin
from app.shared.dynamodb import get_table
from app.shared.http_errors import domain_error_handler
from app.parts.adapters.dynamodb_repository import DynamoDBPartRepository
from app.parts.adapters.presenter import to_response
from app.parts.application.use_cases import (
    CreatePartUseCase,
    DeactivatePartUseCase,
    GetPartUseCase,
    ListPartsUseCase,
    UpdatePartUseCase,
)
from app.parts.domain.repository import IPartRepository
from app.parts.schemas import PartCreate, PartRead, PartUpdate

router = APIRouter(prefix="/parts", tags=["parts"])


def get_part_repo() -> IPartRepository:
    return DynamoDBPartRepository(get_table())


# Leitura pública, pelo mesmo motivo de /services (ver service_catalog/controller.py).
@router.get("", response_model=list[PartRead])
def get_parts(include_inactive: bool = False, repo: IPartRepository = Depends(get_part_repo)) -> list[PartRead]:
    return [to_response(p) for p in ListPartsUseCase(repo).execute(include_inactive)]


@router.get("/{part_id}", response_model=PartRead)
def get_part(part_id: str, repo: IPartRepository = Depends(get_part_repo)) -> PartRead:
    with domain_error_handler():
        return to_response(GetPartUseCase(repo).execute(part_id))


@router.post("", response_model=PartRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_admin)])
def post_part(payload: PartCreate, repo: IPartRepository = Depends(get_part_repo)) -> PartRead:
    with domain_error_handler():
        return to_response(
            CreatePartUseCase(repo).execute(
                name=payload.name,
                sku=payload.sku,
                description=payload.description,
                unit_price=payload.unit_price,
                attributes=payload.attributes,
                active=payload.active,
            )
        )


@router.put("/{part_id}", response_model=PartRead, dependencies=[Depends(get_current_admin)])
def put_part(part_id: str, payload: PartUpdate, repo: IPartRepository = Depends(get_part_repo)) -> PartRead:
    with domain_error_handler():
        return to_response(UpdatePartUseCase(repo).execute(part_id, payload.model_dump(exclude_none=True)))


@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_admin)])
def remove_part(part_id: str, repo: IPartRepository = Depends(get_part_repo)) -> Response:
    with domain_error_handler():
        DeactivatePartUseCase(repo).execute(part_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
