"""
Factory for creating store adapters.
"""

from typing import Literal

from .base import StoreAdapter
from .woocommerce import WooCommerceAdapter
from .medusa import MedusaAdapter

StoreEngine = Literal["woocommerce", "medusa"]


def get_store_adapter(engine: StoreEngine) -> StoreAdapter:
    adapters = {
        "woocommerce": WooCommerceAdapter,
        "medusa": MedusaAdapter,
    }
    adapter_class = adapters.get(engine)
    if adapter_class is None:
        raise ValueError(f"Unsupported store engine: {engine}")
    return adapter_class()
