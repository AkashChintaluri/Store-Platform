"""
Store platform adapters package for the orchestrator service.
"""

from .base import StoreAdapter
from .factory import get_store_adapter

__all__ = ["StoreAdapter", "get_store_adapter"]
