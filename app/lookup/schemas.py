from pydantic import BaseModel, Field

from app.parts.schemas import PartRead
from app.service_catalog.schemas import CatalogServiceRead


class LookupRequest(BaseModel):
    service_ids: list[str] = Field(default_factory=list, max_length=100)
    part_ids: list[str] = Field(default_factory=list, max_length=100)


class LookupResponse(BaseModel):
    services: list[CatalogServiceRead]
    parts: list[PartRead]
    missing_service_ids: list[str]
    missing_part_ids: list[str]
