"""
Centralized orchestrator configuration.

- Loads environment variables from orchestrator/app/config.env (fallback: .env)
- Exposes typed settings
- Validates required variables for startup
"""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv, dotenv_values


APP_ROOT = Path(__file__).resolve().parent
ORCH_ROOT = APP_ROOT.parent
WORKSPACE_ROOT = ORCH_ROOT.parent
ENV_CANDIDATES = [
    APP_ROOT / "config.env",
    ORCH_ROOT / "config.env",
    WORKSPACE_ROOT / "config.env",
    APP_ROOT / ".env",
    ORCH_ROOT / ".env",
    WORKSPACE_ROOT / ".env",
]
ENV_PATH = next((path for path in ENV_CANDIDATES if path.exists()), ENV_CANDIDATES[0])

# Force-load local config so inherited shell values cannot mask expected config.
load_dotenv(dotenv_path=ENV_PATH, override=True)
ENV_FILE_VALUES = {k: (v if v is not None else "") for k, v in dotenv_values(ENV_PATH).items()}


class ConfigError(RuntimeError):
    """Raised when required environment configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    backend_api_base: str
    orchestrator_token: str
    orch_poll_attempts: int
    orch_poll_interval: int
    orch_mock: bool
    app_env: str
    store_values_file: str


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


def _to_int(name: str, default: str) -> int:
    value = _optional(name, default)
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def _to_bool(name: str, default: str = "0") -> bool:
    value = _optional(name, default)
    return value in {"1", "true", "True", "yes", "on"}


def load_settings() -> Settings:
    return Settings(
        backend_api_base=_required("BACKEND_API_BASE").rstrip("/"),
        orchestrator_token=_required("ORCHESTRATOR_TOKEN"),
        orch_poll_attempts=_to_int("ORCH_POLL_ATTEMPTS", "30"),
        orch_poll_interval=_to_int("ORCH_POLL_INTERVAL", "10"),
        orch_mock=_to_bool("ORCH_MOCK", "0"),
        app_env=_optional("APP_ENV", "development").lower(),
        store_values_file=_optional("STORE_VALUES_FILE", ""),
    )


SETTINGS = load_settings()


def get_settings() -> Settings:
    return SETTINGS
