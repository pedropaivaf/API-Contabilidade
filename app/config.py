"""Configurações centrais. Lê do .env via pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    env: str = "dev"
    cors_origins: list[str] = ["*"]

    # Banco / cache
    database_url: str = "postgresql+psycopg://api:api@db:5432/contabil"
    redis_url: str = "redis://redis:6379/0"

    # Autenticação de entrada (clientes da nossa API)
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_ttl_seconds: int = 3600

    # SERPRO Integra Contador
    serpro_base_url: str = "https://gateway.apiserpro.serpro.gov.br/integra-contador/v1"
    serpro_client_id: str = ""
    serpro_client_secret: str = ""
    serpro_cert_pfx_path: str = "/secrets/cert_a1.pfx"
    serpro_cert_password: str = ""

    # Focus NFe
    focusnfe_base_url: str = "https://api.focusnfe.com.br"
    focusnfe_token: str = ""

    # LegisWeb
    legisweb_base_url: str = "https://api.legisweb.com.br"
    legisweb_api_key: str = ""


settings = Settings()
