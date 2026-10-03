from datetime import datetime

from pydantic import BaseModel, Field


class CatalogServiceBase(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    base_price: float = Field(gt=0)
    estimated_minutes: int = Field(gt=0)
    active: bool = True


class CatalogServiceCreate(CatalogServiceBase):
    pass


class CatalogServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    base_price: float | None = Field(default=None, gt=0)
    estimated_minutes: int | None = Field(default=None, gt=0)
    active: bool | None = None


class CatalogServiceRead(CatalogServiceBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None
