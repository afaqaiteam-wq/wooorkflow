from typing import Literal

from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from the environment and an optional `.env` file.

    This is the only place the process environment is read. Values reach the
    rest of the application through constructor arguments wired in `bootstrap`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    app_env: Literal["local", "test", "production"] = "local"
    http_host: str = "127.0.0.1"
    http_port: int = 8000

    anthropic_api_key: SecretStr | None = None
    n8n_base_url: AnyHttpUrl | None = None
    n8n_api_key: SecretStr | None = None
