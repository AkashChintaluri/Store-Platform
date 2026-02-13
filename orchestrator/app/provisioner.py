"""
Provisioner for stores using Helm and platform adapters.
"""

import tempfile
from pathlib import Path
from typing import Literal

import yaml

from .helm import run_helm
from .adapters import get_store_adapter
from .config import get_settings


BASE_DIR = Path(__file__).resolve().parents[1]
CHART_PATH = str(BASE_DIR / "charts" / "store")
DEFAULT_VALUES_FILE = str(BASE_DIR / "charts" / "store" / "values.yaml")
PROD_VALUES_FILE = str(BASE_DIR / "charts" / "store" / "values-prod.yaml")


def get_values_file() -> str:
    """Get the base values file based on environment."""
    settings = get_settings()
    env_values_file = settings.store_values_file
    if env_values_file:
        return env_values_file
    environment = settings.app_env
    return PROD_VALUES_FILE if environment == "production" else DEFAULT_VALUES_FILE


def generate_values(store_name: str, host: str, engine: Literal["woocommerce", "medusa"]) -> str:
    """Generate a temporary Helm values file for a store using the platform adapter."""
    adapter = get_store_adapter(engine)
    values = adapter.get_default_values(store_name, host)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml", encoding="utf-8") as tmp:
        yaml.safe_dump(values, tmp)
        return tmp.name


def install_store(store_name: str, namespace: str, values_file: str | None = None):
    """Install or upgrade a store Helm release."""
    values_file = values_file or get_values_file()
    cmd = [
        "helm",
        "upgrade",
        "--install",
        store_name,
        CHART_PATH,
        "--namespace",
        namespace,
        "--create-namespace",
        "-f",
        values_file,
    ]
    return run_helm(cmd)


def delete_store(store_name: str, namespace: str):
    """Delete a store and all Kubernetes resources."""
    cmd = [
        "helm",
        "uninstall",
        store_name,
        "-n",
        namespace,
    ]
    return run_helm(cmd)


def configure_platform(
    namespace: str,
    release_name: str,
    engine: Literal["woocommerce", "medusa"]
) -> tuple[bool, str | None]:
    """Configure the store platform using the appropriate adapter."""
    adapter = get_store_adapter(engine)
    return adapter.configure_platform(namespace, release_name)


def get_admin_password(
    namespace: str,
    release_name: str,
    engine: Literal["woocommerce", "medusa"]
) -> str | None:
    """Get the admin password for a store using the appropriate adapter."""
    adapter = get_store_adapter(engine)
    return adapter.get_admin_password(namespace, release_name)


def get_store_url_path(engine: Literal["woocommerce", "medusa"]) -> str:
    """Get the URL path for a store using the appropriate adapter."""
    adapter = get_store_adapter(engine)
    return adapter.get_store_url_path()


def configure_woocommerce(namespace: str, release_name: str) -> tuple[bool, str | None]:
    """Legacy function for WooCommerce configuration."""
    return configure_platform(namespace, release_name, "woocommerce")
