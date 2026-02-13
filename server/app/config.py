"""
Centralized application configuration.

- Loads environment variables from server/config.env (fallback: .env)
- Exposes strongly-typed settings
- Validates required variables for startup
"""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv, dotenv_values


APP_ROOT = Path(__file__).resolve().parent
SERVER_ROOT = APP_ROOT.parent
WORKSPACE_ROOT = SERVER_ROOT.parent
ENV_CANDIDATES = [
    SERVER_ROOT / "config.env",
    APP_ROOT / "config.env",
    WORKSPACE_ROOT / "config.env",
    SERVER_ROOT / ".env",
    APP_ROOT / ".env",
    WORKSPACE_ROOT / ".env",
]
ENV_PATH = next((path for path in ENV_CANDIDATES if path.exists()), ENV_CANDIDATES[0])

# Force-load config file so reloader/inherited shell vars cannot mask local config.
load_dotenv(dotenv_path=ENV_PATH, override=True)
ENV_FILE_VALUES = {k: (v if v is not None else "") for k, v in dotenv_values(ENV_PATH).items()}


class ConfigError(RuntimeError):
    """Raised when required environment configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str
    mongodb_db: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    orchestrator_url: str
    orchestrator_token: str
    allowed_origins: list[str]
    store_base_domain: str
    store_base_port: str


def _required(name: str) -> str:
    value = os.getenv(name, "").strip() or ENV_FILE_VALUES.get(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name} (file: {ENV_PATH})")
    return value


def _optional(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    file_value = ENV_FILE_VALUES.get(name, "").strip()
    if file_value:
        return file_value
    return default.strip()


def load_settings() -> Settings:
    jwt_expire_raw = _optional("JWT_EXPIRE_MINUTES", "30")
    try:
        jwt_expire_minutes = int(jwt_expire_raw)
    except ValueError as exc:
        raise ConfigError("JWT_EXPIRE_MINUTES must be an integer") from exc

    allowed_origins_raw = _optional("ALLOWED_ORIGINS", "http://localhost:5173")
    allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]

    return Settings(
        mongodb_uri=_required("MONGODB_URI"),
        mongodb_db=_required("MONGODB_DB"),
        jwt_secret=_required("JWT_SECRET"),
        jwt_algorithm=_required("JWT_ALGORITHM"),
        jwt_expire_minutes=jwt_expire_minutes,
        orchestrator_url=_optional("ORCHESTRATOR_URL", "http://localhost:9000/orchestrate"),
        orchestrator_token=_optional("ORCHESTRATOR_TOKEN", ""),
        allowed_origins=allowed_origins,
        store_base_domain=_optional("STORE_BASE_DOMAIN", "localhost"),
        store_base_port=_optional("STORE_BASE_PORT", ""),
    )


SETTINGS = load_settings()


def get_settings() -> Settings:
    return SETTINGS
