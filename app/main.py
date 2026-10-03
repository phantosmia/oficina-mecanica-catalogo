from fastapi import FastAPI

from app.lookup.controller import router as lookup_router
from app.parts.controller import router as parts_router
from app.service_catalog.controller import router as services_router
from app.shared.logging_config import RequestIDMiddleware, configure_logging
from app.shared.settings import settings
from app.system.controller import router as system_router

configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Microsserviço de Catálogo da oficina mecânica: serviços oferecidos e fichas de peças. "
        "Leitura pública; escrita exige o JWT de admin emitido pelo OS Service."
    ),
    version="1.0.0",
)

app.add_middleware(RequestIDMiddleware)

app.include_router(system_router)
app.include_router(services_router)
app.include_router(parts_router)
app.include_router(lookup_router)
