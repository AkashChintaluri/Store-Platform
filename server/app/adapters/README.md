# Store Platform Adapters

This directory contains the **type erasure adapter system** for supporting multiple e-commerce platforms.

## Overview

The adapter system allows the Store Platform to support different e-commerce platforms (WooCommerce, Medusa, Shopify, etc.) without modifying core orchestration logic. Each platform implements the `StoreAdapter` interface, providing platform-specific behavior while maintaining a consistent API.

## Files

### Core System

- **`base.py`** - Abstract `StoreAdapter` interface that all platforms must implement
- **`factory.py`** - Factory pattern for creating adapter instances
- **`__init__.py`** - Package exports

### Platform Implementations

- **`woocommerce.py`** - ✅ Fully implemented WooCommerce adapter
- **`medusa.py`** - 🚧 Placeholder for Medusa (ready for implementation)

### Developer Tools

- **`example_template.py`** - Template for implementing new platform adapters

## Quick Start

### Using an Adapter

```python
from app.adapters import get_store_adapter

# Get adapter for a specific platform
adapter = get_store_adapter("woocommerce")

# Generate platform-specific Helm values
values = adapter.get_default_values("my-store", "my-store.example.com")

# Configure the platform after deployment
success, error = adapter.configure_platform("my-store", "my-store")

# Get admin password
password = adapter.get_admin_password("my-store", "my-store")
```

### Adding a New Platform

1. Copy `example_template.py` to `yourplatform.py`
2. Implement all 7 required methods
3. Register in `factory.py`
4. Update `models.py` to add the new engine type

See [../docs/QUICK_REFERENCE.md](../docs/QUICK_REFERENCE.md) for detailed instructions.

## StoreAdapter Interface

All adapters must implement these methods:

| Method | Purpose | Returns |
|--------|---------|---------|
| `get_chart_dependency()` | Helm chart configuration | `dict` |
| `get_default_values(name, host)` | Platform-specific Helm values | `dict` |
| `configure_platform(namespace, release)` | Post-deployment setup | `tuple[bool, str \| None]` |
| `get_admin_password(namespace, release)` | Retrieve admin password | `str \| None` |
| `get_pod_selector(release)` | Kubernetes pod selector | `str` |
| `get_store_url_path()` | Store URL path | `str` |
| `is_platform_ready(namespace, release)` | Check if platform is ready | `bool` |

## Platform Support

| Platform | Status | File |
|----------|--------|------|
| WooCommerce | ✅ Implemented | `woocommerce.py` |
| Medusa | 🚧 Placeholder | `medusa.py` |
| Others | 📝 Use Template | `example_template.py` |

## Architecture

```
┌─────────────────────────────────────┐
│      StoreAdapter (Interface)       │
│  - Defines contract for platforms   │
└──────────────┬──────────────────────┘
               │
               │ Implements
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌─────────┐ ┌────────┐ ┌────────┐
│WooCom-  │ │ Medusa │ │ Future │
│merce    │ │        │ │        │
└─────────┘ └────────┘ └────────┘
```

## Design Pattern: Type Erasure

The factory returns the `StoreAdapter` interface type, hiding the concrete implementation:

```python
def get_store_adapter(engine: str) -> StoreAdapter:
    # Returns interface type, not concrete class
    return adapters[engine]()
```

This allows the orchestrator to work with any platform without knowing implementation details.

## Documentation

- **Architecture Guide**: [../docs/ADAPTER_SYSTEM.md](../docs/ADAPTER_SYSTEM.md)
- **Quick Reference**: [../docs/QUICK_REFERENCE.md](../docs/QUICK_REFERENCE.md)
- **Diagrams**: [../docs/ARCHITECTURE_DIAGRAMS.md](../docs/ARCHITECTURE_DIAGRAMS.md)

## Examples

### WooCommerce Adapter

```python
class WooCommerceAdapter(StoreAdapter):
    def configure_platform(self, namespace, release):
        # Install WooCommerce plugin
        self._install_woocommerce(namespace, pod_name)
        # Create test product
        self._create_test_product(namespace, pod_name)
        # Enable payment gateway
        self._enable_cod_payment(namespace, pod_name)
        return True, None
```

### Medusa Adapter (Placeholder)

```python
class MedusaAdapter(StoreAdapter):
    def configure_platform(self, namespace, release):
        # TODO: Implement Medusa configuration
        # - Run database migrations
        # - Create admin user
        # - Seed initial data
        raise NotImplementedError("Medusa adapter not yet implemented")
```

## Testing

```bash
# Test adapter instantiation
python -c "from app.adapters import get_store_adapter; print(get_store_adapter('woocommerce'))"

# Test adapter methods
python -c "
from app.adapters import get_store_adapter
adapter = get_store_adapter('woocommerce')
print(adapter.get_store_url_path())  # Should print '/shop/'
"

# List supported engines
python -c "from app.adapters.factory import get_supported_engines; print(get_supported_engines())"
```

## Contributing

When adding a new platform adapter:

1. Follow the interface defined in `base.py`
2. Use `example_template.py` as a starting point
3. Add comprehensive docstrings
4. Handle errors gracefully
5. Return clear error messages
6. Test thoroughly before committing

## License

Part of the Store Platform project - MIT License
