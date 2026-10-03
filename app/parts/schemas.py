from datetime import datetime

from pydantic import BaseModel, Field

AttributeValue = str | int | float | bool


class PartBase(BaseModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    description: str | None = None
    unit_price: float = Field(gt=0)
    attributes: dict[str, AttributeValue] = Field(
        default_factory=dict,
        description="Atributos específicos do tipo de peça, ex.: {\"viscosidade\": \"5W30\", \"volume_litros\": 1}",
    )
    active: bool = True


class PartCreate(PartBase):
    pass


class PartUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    sku: str | None = Field(default=None, min_length=1)
    description: str | None = None
    unit_price: float | None = Field(default=None, gt=0)
    attributes: dict[str, AttributeValue] | None = None
    active: bool | None = None


class PartRead(PartBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None
