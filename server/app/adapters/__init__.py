"""
Store platform adapters package.

This package provides a type erasure system for different e-commerce platforms.
Each platform (WooCommerce, Medusa, etc.) implements the StoreAdapter interface.
"""

from .base import StoreAdapter
from .factory import get_store_adapter

__all__ = ["StoreAdapter", "get_store_adapter"]
