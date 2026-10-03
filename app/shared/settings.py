from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    log_level: str
    # JWT de admin: emitido pelo OS Service (`POST /auth/token` em
    # oficina-mecanica-fiap) — este serviço só valida, com o mesmo segredo.
    jwt_secret_key: str
    jwt_algorithm: str
    admin_username: str
    # AWS: em produção as credenciais vêm do ambiente (role do node no EKS);
    # localmente/testes, AWS_ENDPOINT_URL aponta pro LocalStack (o boto3 lê
    # essa variável sozinho, não precisa passar endpoint_url manualmente).
    aws_region: str
    table_name: str
    events_topic_arn: str
    outbox_poll_interval_seconds: float


settings = Settings(
    app_name="Oficina Mecânica — Catálogo",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    jwt_secret_key=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
    jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    admin_username=os.getenv("ADMIN_USERNAME", "admin"),
    aws_region=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1")),
    table_name=os.getenv("CATALOG_TABLE_NAME", "oficina-catalogo"),
    events_topic_arn=os.getenv("CATALOG_EVENTS_TOPIC_ARN", ""),
    outbox_poll_interval_seconds=float(os.getenv("OUTBOX_POLL_INTERVAL_SECONDS", "2")),
)
