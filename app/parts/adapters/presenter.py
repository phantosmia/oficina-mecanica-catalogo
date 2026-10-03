from app.parts.domain.entity import PartEntity
from app.parts.schemas import PartRead


def to_response(entity: PartEntity) -> PartRead:
    return PartRead(
        id=entity.id,
        name=entity.name,
        sku=entity.sku,
        description=entity.description,
        unit_price=entity.unit_price,
        attributes=entity.attributes,
        active=entity.active,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
