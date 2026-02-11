"""
Factory for creating store adapters.

This module provides the factory function to instantiate the correct adapter
based on the store engine type. This is the main entry point for the type erasure system.
"""

from typing import Literal

from .base import StoreAdapter
from .woocommerce import WooCommerceAdapter
from .medusa import MedusaAdapter


# Type alias for supported engines
StoreEngine = Literal["woocommerce", "medusa"]


def get_store_adapter(engine: StoreEngine) -> StoreAdapter:
    """
    Factory function to get the appropriate store adapter.
    
    This function implements type erasure - it returns a StoreAdapter interface,
    hiding the concrete implementation details from the caller.
    
    Args:
        engine: The store engine type ("woocommerce" or "medusa")
        
    Returns:
        StoreAdapter: The appropriate adapter instance
        
    Raises:
        ValueError: If the engine type is not supported
        NotImplementedError: If the adapter exists but is not yet implemented
    """
    adapters = {
        "woocommerce": WooCommerceAdapter,
        "medusa": MedusaAdapter,
    }
    
    adapter_class = adapters.get(engine)
    
    if adapter_class is None:
        raise ValueError(
            f"Unsupported store engine: {engine}. "
            f"Supported engines: {', '.join(adapters.keys())}"
        )
    
    return adapter_class()


def get_supported_engines() -> list[str]:
    """
    Get a list of all supported store engines.
    
    Returns:
        list[str]: List of supported engine names
    """
    return ["woocommerce", "medusa"]


def is_engine_implemented(engine: StoreEngine) -> bool:
    """
    Check if a store engine is fully implemented.
    
    Args:
        engine: The store engine type
        
    Returns:
        bool: True if the engine is fully implemented, False if it's a placeholder
    """
    try:
        adapter = get_store_adapter(engine)
        # Try calling a method to see if it raises NotImplementedError
        adapter.get_store_url_path()
        return True
    except NotImplementedError:
        return False
    except Exception:
        # Other errors mean it's implemented but something else went wrong
        return True
