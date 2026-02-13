"""
Base adapter interface for store platforms.
"""

from abc import ABC, abstractmethod
from typing import Optional


class StoreAdapter(ABC):
    @abstractmethod
    def get_chart_dependency(self) -> dict:
        pass

    @abstractmethod
    def get_default_values(self, store_name: str, host: str) -> dict:
        pass

    @abstractmethod
    def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
        pass

    @abstractmethod
    def get_admin_password(self, namespace: str, release_name: str) -> Optional[str]:
        pass

    @abstractmethod
    def get_pod_selector(self, release_name: str) -> str:
        pass

    @abstractmethod
    def get_store_url_path(self) -> str:
        pass

    @abstractmethod
    def is_platform_ready(self, namespace: str, release_name: str) -> bool:
        pass
