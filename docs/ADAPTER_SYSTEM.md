# Store Platform Adapter System

## Overview

The Store Platform uses a **type erasure pattern** to support multiple e-commerce platforms (WooCommerce, Medusa, etc.) without coupling the core orchestration logic to specific platform implementations.

## Architecture

### Type Erasure Pattern

Type erasure is a design pattern where:
1. **Interface defines behavior** - `StoreAdapter` abstract base class defines what all platforms must do
2. **Concrete implementations** - Each platform (WooCommerce, Medusa) implements the interface
3. **Factory creates instances** - `get_store_adapter()` returns the interface type, hiding implementation details
4. **Orchestrator uses interface** - Core logic works with `StoreAdapter` interface, not concrete classes

This allows adding new platforms without modifying existing orchestration code.

### Component Structure

```
server/app/
├── adapters/                    # Platform adapter system
│   ├── __init__.py             # Package exports
│   ├── base.py                 # StoreAdapter interface
│   ├── factory.py              # Adapter factory
│   ├── woocommerce.py          # WooCommerce implementation
│   └── medusa.py               # Medusa placeholder
├── orchestrator/               # Platform-agnostic orchestration
│   ├── provisioner.py          # Uses adapters for provisioning
│   ├── status.py               # Uses adapters for status checks
│   └── helm.py                 # Helm wrapper
└── routes/                     # API endpoints
    └── stores.py               # Uses orchestrator functions
```

## StoreAdapter Interface

All platform adapters must implement these methods:

### 1. `get_chart_dependency() -> dict`
Returns Helm chart dependency configuration.

**Example (WooCommerce):**
```python
{
    "name": "wordpress",
    "version": "28.x.x",
    "repository": "https://charts.bitnami.com/bitnami",
    "condition": "wordpress.enabled"
}
```

### 2. `get_default_values(store_name: str, host: str) -> dict`
Generates platform-specific Helm values.

**Example (WooCommerce):**
```python
{
    "store": {"name": "my-store", "engine": "wordpress", "host": "my-store.example.com"},
    "wordpress": {
        "enabled": True,
        "wordpressUsername": "user",
        "mariadb": {"enabled": True, ...}
    },
    "ingress": {"enabled": True, "className": "nginx"}
}
```

### 3. `configure_platform(namespace: str, release_name: str) -> tuple[bool, Optional[str]]`
Performs post-deployment configuration.

**WooCommerce:** Installs WooCommerce plugin, creates test product, enables COD payment  
**Medusa:** Would run migrations, create admin user, seed data

Returns: `(success: bool, error_message: Optional[str])`

### 4. `get_admin_password(namespace: str, release_name: str) -> Optional[str]`
Retrieves admin password from Kubernetes secrets.

### 5. `get_pod_selector(release_name: str) -> str`
Returns Kubernetes label selector for the main pod.

**Example:** `"app.kubernetes.io/name=wordpress,app.kubernetes.io/instance=my-store"`

### 6. `get_store_url_path() -> str`
Returns URL path suffix for the store frontend.

**WooCommerce:** `/shop/`  
**Medusa:** `/`

### 7. `is_platform_ready(namespace: str, release_name: str) -> bool`
Checks if the platform is fully initialized (beyond pod readiness).

**WooCommerce:** Checks if WordPress core is installed  
**Medusa:** Would check if migrations completed and API is responding

## Adding a New Platform

To add support for a new platform (e.g., Shopify, Magento):

### Step 1: Create Adapter Class

Create `server/app/adapters/shopify.py`:

```python
from typing import Optional
from .base import StoreAdapter

class ShopifyAdapter(StoreAdapter):
    def get_chart_dependency(self) -> dict:
        return {
            "name": "shopify",
            "version": "1.x.x",
            "repository": "https://charts.shopify.com/",
            "condition": "shopify.enabled"
        }
    
    def get_default_values(self, store_name: str, host: str) -> dict:
        return {
            "store": {
                "name": store_name,
                "engine": "shopify",
                "host": host,
            },
            "shopify": {
                "enabled": True,
                # Shopify-specific config
            }
        }
    
    def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
        # Shopify-specific setup
        pass
    
    # Implement other required methods...
```

### Step 2: Register in Factory

Update `server/app/adapters/factory.py`:

```python
from .shopify import ShopifyAdapter

StoreEngine = Literal["woocommerce", "medusa", "shopify"]

def get_store_adapter(engine: StoreEngine) -> StoreAdapter:
    adapters = {
        "woocommerce": WooCommerceAdapter,
        "medusa": MedusaAdapter,
        "shopify": ShopifyAdapter,  # Add new adapter
    }
    # ... rest of factory logic
```

### Step 3: Update Models

Update `server/app/models.py`:

```python
class StoreCreate(BaseModel):
    name: str
    engine: Literal["woocommerce", "medusa", "shopify"]  # Add new engine
```

### Step 4: Update Frontend

Update `client/src/components/CreateStoreModal.tsx`:

```typescript
const ENGINES = [
  { value: 'woocommerce', label: 'WooCommerce' },
  { value: 'medusa', label: 'Medusa' },
  { value: 'shopify', label: 'Shopify' },  // Add new option
] as const
```

### Step 5: Create Helm Chart (if needed)

If the platform needs a custom Helm chart:
1. Add chart to `charts/store/charts/`
2. Update `charts/store/Chart.yaml` dependencies
3. Create platform-specific templates in `charts/store/templates/`

## Usage Examples

### Provisioning a Store

```python
from app.adapters import get_store_adapter
from app.orchestrator.provisioner import generate_values, install_store, configure_platform

# Type erasure in action - works with any platform
engine = "woocommerce"  # or "medusa", "shopify", etc.
adapter = get_store_adapter(engine)

# Generate platform-specific values
values_file = generate_values("my-store", "my-store.example.com", engine)

# Install Helm chart
install_store("my-store", "my-store", values_file)

# Configure platform (delegates to adapter)
success, error = configure_platform("my-store", "my-store", engine)
```

### Getting Store Password

```python
from app.orchestrator.status import get_store_password

# Works for any platform
password = get_store_password("my-store", "my-store", "woocommerce")
```

## Benefits

### 1. **Separation of Concerns**
- Core orchestration logic is platform-agnostic
- Platform-specific details are encapsulated in adapters
- Easy to test each component independently

### 2. **Open/Closed Principle**
- Open for extension (add new platforms)
- Closed for modification (no changes to core logic)

### 3. **Single Responsibility**
- Each adapter handles one platform
- Orchestrator handles Kubernetes/Helm operations
- API routes handle HTTP requests

### 4. **Easy Maintenance**
- Bug fixes in one platform don't affect others
- Platform-specific logic is isolated and easy to find
- Clear contracts via abstract interface

### 5. **Testability**
- Mock adapters for testing
- Test platforms independently
- Test orchestrator with any adapter

## Current Implementation Status

| Platform | Status | Adapter | Notes |
|----------|--------|---------|-------|
| WooCommerce | ✅ Implemented | `WooCommerceAdapter` | Fully functional with WordPress + WooCommerce |
| Medusa | 🚧 Placeholder | `MedusaAdapter` | Interface defined, implementation pending |

## Medusa Implementation Checklist

To complete Medusa support:

- [ ] Create Medusa Helm chart or find existing one
- [ ] Implement `MedusaAdapter.get_chart_dependency()`
- [ ] Implement `MedusaAdapter.get_default_values()`
- [ ] Implement `MedusaAdapter.configure_platform()` with:
  - [ ] Database migration commands
  - [ ] Admin user creation
  - [ ] Initial data seeding
- [ ] Implement `MedusaAdapter.get_admin_password()`
- [ ] Implement `MedusaAdapter.get_pod_selector()`
- [ ] Implement `MedusaAdapter.is_platform_ready()`
- [ ] Add Medusa-specific templates to Helm chart
- [ ] Test end-to-end deployment
- [ ] Update documentation

## Design Decisions

### Why Type Erasure?

Alternative approaches considered:

1. **If/else chains** - Would clutter orchestrator with platform-specific logic
2. **Strategy pattern without interface** - Less type safety, harder to enforce contracts
3. **Plugin system** - Overkill for this use case, adds complexity

Type erasure provides the right balance of flexibility and simplicity.

### Why Factory Pattern?

The factory pattern (`get_store_adapter()`) provides:
- Single point of adapter creation
- Easy to add validation logic
- Clear error messages for unsupported platforms
- Consistent adapter instantiation

### Why Abstract Base Class?

Using ABC instead of Protocol or duck typing:
- Enforces implementation of all required methods
- Clear contract for adapter developers
- Better IDE support and type checking
- Explicit inheritance relationship

## Future Enhancements

1. **Adapter Registry** - Dynamic adapter registration without modifying factory
2. **Adapter Capabilities** - Query what features each adapter supports
3. **Adapter Versioning** - Support multiple versions of the same platform
4. **Adapter Plugins** - Load adapters from external packages
5. **Adapter Validation** - Validate adapter implementations at startup

## References

- [Type Erasure Pattern](https://en.wikipedia.org/wiki/Type_erasure)
- [Adapter Pattern](https://refactoring.guru/design-patterns/adapter)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)
- [Open/Closed Principle](https://en.wikipedia.org/wiki/Open%E2%80%93closed_principle)
