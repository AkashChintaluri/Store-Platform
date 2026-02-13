"""
Medusa store adapter (placeholder).
"""

from typing import Optional

from .base import StoreAdapter


class MedusaAdapter(StoreAdapter):
    def get_chart_dependency(self) -> dict:
        raise NotImplementedError("Medusa adapter not yet implemented")

    def get_default_values(self, store_name: str, host: str) -> dict:
        raise NotImplementedError("Medusa adapter not yet implemented")

    def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
        raise NotImplementedError("Medusa adapter not yet implemented")

    def get_admin_password(self, namespace: str, release_name: str) -> Optional[str]:
        raise NotImplementedError("Medusa adapter not yet implemented")

    def get_pod_selector(self, release_name: str) -> str:
        raise NotImplementedError("Medusa adapter not yet implemented")

    def get_store_url_path(self) -> str:
        return "/"

    def is_platform_ready(self, namespace: str, release_name: str) -> bool:
        raise NotImplementedError("Medusa adapter not yet implemented")
