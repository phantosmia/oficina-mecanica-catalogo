"""Carga idempotente de dados de exemplo (os mesmos serviços e peças que o
monólito das fases anteriores populava em `scripts/populate_db.py`).

Os IDs são determinísticos (UUID v5 derivado do nome do serviço / SKU da
peça): o serviço de Estoque usa a mesma regra para semear o saldo inicial
dessas peças sem precisar consultar o Catálogo. Rodar de novo não duplica
nada: item que já existe é ignorado.

Uso: `python -m scripts.seed`
"""

import logging
import uuid

from app.parts.adapters.dynamodb_repository import DynamoDBPartRepository
from app.parts.application.use_cases import CreatePartUseCase
from app.service_catalog.adapters.dynamodb_repository import DynamoDBCatalogServiceRepository
from app.service_catalog.application.use_cases import CreateCatalogServiceUseCase
from app.shared.dynamodb import get_table
from app.shared.exceptions import ConflictError

# Namespace fixo do projeto para os UUID v5 dos dados de exemplo.
SEED_NAMESPACE = uuid.UUID("6f1c2e4a-9b3d-4f5e-8a7c-1d2e3f4a5b6c")

SERVICES = [
    ("Troca de óleo", "Troca completa de óleo do motor", 150.00, 30),
    ("Revisão de freios", "Verificação e ajuste do sistema de freios", 200.00, 60),
    ("Alinhamento e balanceamento", "Alinhamento das rodas e balanceamento dos pneus", 120.00, 45),
    ("Troca de filtros", "Troca de filtro de ar, combustível e óleo", 80.00, 20),
    ("Diagnóstico eletrônico", "Verificação de códigos de erro no sistema eletrônico", 100.00, 30),
]

PARTS = [
    ("Óleo sintético 5W30", "OLEO-5W30-1L", "Óleo sintético para motores", 45.00, {"viscosidade": "5W30", "volume_litros": 1}),
    ("Filtro de óleo", "FILTRO-OLEO-GENERIC", "Filtro de óleo genérico", 25.00, {"rosca": "M20x1.5"}),
    ("Pastilha de freio dianteira", "PAST-FREIO-DIAN", "Conjunto de pastilhas de freio dianteiras", 180.00, {"eixo": "dianteiro", "material": "cerâmica"}),
    ("Disco de freio", "DISCO-FREIO-DIAN", "Disco de freio dianteiro", 250.00, {"eixo": "dianteiro", "diametro_mm": 280}),
    ("Filtro de ar", "FILTRO-AR-GENERIC", "Filtro de ar do motor", 35.00, {}),
]


def service_id_for(name: str) -> str:
    return str(uuid.uuid5(SEED_NAMESPACE, f"service:{name}"))


def part_id_for(sku: str) -> str:
    return str(uuid.uuid5(SEED_NAMESPACE, f"part:{sku}"))


def seed() -> tuple[int, int]:
    """Retorna (serviços criados, peças criadas)."""
    table = get_table()
    services = DynamoDBCatalogServiceRepository(table)
    parts = DynamoDBPartRepository(table)

    created_services = 0
    for name, description, price, minutes in SERVICES:
        if services.get_by_id(service_id_for(name)) is None:
            CreateCatalogServiceUseCase(services).execute(
                name=name, description=description, base_price=price, estimated_minutes=minutes, service_id=service_id_for(name)
            )
            created_services += 1

    created_parts = 0
    for name, sku, description, price, attributes in PARTS:
        try:
            CreatePartUseCase(parts).execute(
                name=name, sku=sku, description=description, unit_price=price, attributes=attributes, part_id=part_id_for(sku)
            )
            created_parts += 1
        except ConflictError:
            pass  # já existe (execução anterior)
    return created_services, created_parts


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    created = seed()
    logging.getLogger("seed").info("dados de exemplo: %s serviços e %s peças criados", *created)
