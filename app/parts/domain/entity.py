from dataclasses import dataclass, field
from datetime import datetime

# Atributos específicos por tipo de peça (pneu: aro e medida; óleo:
# viscosidade e volume...). É o motivo de o Catálogo usar um banco de
# documentos (ADR-0009): cada peça carrega os seus, sem migração de schema.
PartAttributes = dict[str, str | int | float | bool]


@dataclass
class PartEntity:
    id: str
    name: str
    sku: str
    description: str | None
    unit_price: float
    active: bool
    created_at: datetime
    attributes: PartAttributes = field(default_factory=dict)
    updated_at: datetime | None = None
