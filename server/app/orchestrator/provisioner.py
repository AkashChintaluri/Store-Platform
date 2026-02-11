"""
This module provisions and deletes stores using Helm and platform adapters.

Responsibilities:
- Translate store metadata into Helm values using platform adapters
- Call Helm install / uninstall
- Delegate platform-specific configuration to adapters
- Be safe to retry (idempotent)
- Do NOT talk to MongoDB directly
"""

import os
import tempfile
from pathlib import Path
from typing import Literal

import yaml

from .helm import run_helm
from ..adapters import get_store_adapter


CHART_PATH = str(Path(__file__).resolve().parents[3] / "charts" / "store")
DEFAULT_VALUES_FILE = str(Path(__file__).resolve().parents[3] / "charts" / "store" / "values.yaml")
PROD_VALUES_FILE = str(Path(__file__).resolve().parents[3] / "charts" / "store" / "values-prod.yaml")


def get_values_file() -> str:
    """Get the base values file based on environment."""
    env_values_file = os.getenv("STORE_VALUES_FILE", "").strip()
    if env_values_file:
        return env_values_file
    environment = os.getenv("APP_ENV", "development").lower()
    return PROD_VALUES_FILE if environment == "production" else DEFAULT_VALUES_FILE


def generate_values(store_name: str, host: str, engine: Literal["woocommerce", "medusa"]) -> str:
    """
    Generate a temporary Helm values file for a store using the platform adapter.
    
    Args:
        store_name: Name of the store
        host: Hostname for the store
        engine: Store platform engine
        
    Returns:
        str: Path to the temporary values file
    """
    # Get the platform-specific adapter
    adapter = get_store_adapter(engine)
    
    # Generate platform-specific values
    values = adapter.get_default_values(store_name, host)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml", encoding="utf-8") as tmp:
        yaml.safe_dump(values, tmp)
        return tmp.name


def install_store(store_name: str, namespace: str, values_file: str | None = None):
    """
    Install or upgrade a store Helm release.
    
    Args:
        store_name: Name of the store
        namespace: Kubernetes namespace
        values_file: Path to Helm values file
        
    Returns:
        str: Helm command output
    """
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
    """
    Delete a store and all Kubernetes resources.
    
    Args:
        store_name: Name of the store
        namespace: Kubernetes namespace
        
    Returns:
        str: Helm command output
    """
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
    """
    Configure the store platform using the appropriate adapter.
    
    This delegates to the platform-specific adapter for post-deployment configuration.
    
    Args:
        namespace: Kubernetes namespace
        release_name: Helm release name
        engine: Store platform engine
        
    Returns:
        tuple: (success: bool, error_message: Optional[str])
    """
    adapter = get_store_adapter(engine)
    return adapter.configure_platform(namespace, release_name)


def get_admin_password(
    namespace: str, 
    release_name: str, 
    engine: Literal["woocommerce", "medusa"]
) -> str | None:
    """
    Get the admin password for a store using the appropriate adapter.
    
    Args:
        namespace: Kubernetes namespace
        release_name: Helm release name
        engine: Store platform engine
        
    Returns:
        Optional[str]: Admin password or None if not available
    """
    adapter = get_store_adapter(engine)
    return adapter.get_admin_password(namespace, release_name)


def get_store_url_path(engine: Literal["woocommerce", "medusa"]) -> str:
    """
    Get the URL path for a store using the appropriate adapter.
    
    Args:
        engine: Store platform engine
        
    Returns:
        str: URL path (e.g., "/shop/" for WooCommerce)
    """
    adapter = get_store_adapter(engine)
    return adapter.get_store_url_path()


# Backward compatibility - keep old function name
def configure_woocommerce(namespace: str, release_name: str) -> tuple[bool, str | None]:
    """
    Legacy function for WooCommerce configuration.
    
    This is kept for backward compatibility. New code should use configure_platform().
    """
    return configure_platform(namespace, release_name, "woocommerce")