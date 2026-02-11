# Quick Reference: Adding a New Store Platform

This is a condensed checklist for adding a new e-commerce platform to the Store Platform.

## Prerequisites

- [ ] Identify or create a Helm chart for your platform
- [ ] Understand platform's post-deployment setup requirements
- [ ] Know where admin credentials are stored (Kubernetes secrets)
- [ ] Identify platform's pod labels

## Implementation Checklist

### 1. Create Adapter (15-30 min)

**File**: `server/app/adapters/your_platform.py`

```python
from typing import Optional
from .base import StoreAdapter

class YourPlatformAdapter(StoreAdapter):
    def get_chart_dependency(self) -> dict:
        return {
            "name": "your-platform",
            "version": "1.x.x",
            "repository": "https://charts.example.com/",
            "condition": "yourplatform.enabled"
        }
    
    def get_default_values(self, store_name: str, host: str) -> dict:
        return {
            "store": {"name": store_name, "engine": "yourplatform", "host": host},
            "yourplatform": {"enabled": True, ...},
            "ingress": {"enabled": True, "className": "nginx"}
        }
    
    def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
        # Your setup logic here
        return True, None
    
    def get_admin_password(self, namespace: str, release_name: str) -> Optional[str]:
        # Retrieve from K8s secret
        pass
    
    def get_pod_selector(self, release_name: str) -> str:
        return f"app.kubernetes.io/name=yourplatform,app.kubernetes.io/instance={release_name}"
    
    def get_store_url_path(self) -> str:
        return "/"  # or "/shop/", "/store/", etc.
    
    def is_platform_ready(self, namespace: str, release_name: str) -> bool:
        # Check if platform is initialized
        return True
```

**Tip**: Copy `example_template.py` and fill in the TODOs.

### 2. Register Adapter (2 min)

**File**: `server/app/adapters/factory.py`

```python
from .yourplatform import YourPlatformAdapter

StoreEngine = Literal["woocommerce", "medusa", "yourplatform"]  # Add here

def get_store_adapter(engine: StoreEngine) -> StoreAdapter:
    adapters = {
        "woocommerce": WooCommerceAdapter,
        "medusa": MedusaAdapter,
        "yourplatform": YourPlatformAdapter,  # Add here
    }
    # ... rest of code
```

### 3. Update API Model (1 min)

**File**: `server/app/models.py`

```python
class StoreCreate(BaseModel):
    name: str
    engine: Literal["woocommerce", "medusa", "yourplatform"]  # Add here
```

### 4. Update Frontend (2 min)

**File**: `client/src/components/CreateStoreModal.tsx`

```typescript
const ENGINES = [
  { value: 'woocommerce', label: 'WooCommerce' },
  { value: 'medusa', label: 'Medusa' },
  { value: 'yourplatform', label: 'Your Platform' },  // Add here
] as const
```

### 5. Test (10-20 min)

```bash
# Test adapter instantiation
python -c "from app.adapters import get_store_adapter; print(get_store_adapter('yourplatform'))"

# Test store creation via API
curl -X POST http://localhost:8000/api/stores \
  -H "Content-Type: application/json" \
  -d '{"name": "test-store", "engine": "yourplatform"}'

# Check deployment
kubectl get pods -n test-store
kubectl logs -n test-store -l app.kubernetes.io/name=yourplatform

# Verify store is accessible
curl http://test-store.localhost/
```

## Common Implementation Patterns

### Pattern 1: Finding the Application Pod

```python
def _get_app_pod(self, namespace: str, release_name: str) -> Optional[str]:
    cmd = [
        "kubectl", "get", "pods", "-n", namespace,
        "-l", self.get_pod_selector(release_name),
        "-o", "jsonpath={.items[0].metadata.name}"
    ]
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return None
```

### Pattern 2: Running Commands in Pod

```python
def _run_command(self, namespace: str, pod_name: str, command: str) -> bool:
    cmd = [
        "kubectl", "exec", "-n", namespace, pod_name,
        "--", "bash", "-c", command
    ]
    try:
        subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False
```

### Pattern 3: Reading Kubernetes Secret

```python
def get_admin_password(self, namespace: str, release_name: str) -> Optional[str]:
    try:
        cmd = [
            "kubectl", "get", "secret", f"{release_name}-secret",
            "-n", namespace, "-o", "jsonpath={.data.password}"
        ]
        encoded = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        import base64
        return base64.b64decode(encoded).decode("utf-8")
    except:
        return None
```

### Pattern 4: Checking Platform Readiness

```python
def is_platform_ready(self, namespace: str, release_name: str) -> bool:
    pod_name = self._get_app_pod(namespace, release_name)
    if not pod_name:
        return False
    
    # Check if API responds
    cmd = [
        "kubectl", "exec", "-n", namespace, pod_name,
        "--", "curl", "-f", "http://localhost/health"
    ]
    try:
        subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False
```

## Platform-Specific Examples

### Example: Node.js Platform (like Medusa)

```python
def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
    pod_name = self._get_app_pod(namespace, release_name)
    if not pod_name:
        return False, "Pod not found"
    
    # Run database migrations
    if not self._run_command(namespace, pod_name, "npm run migrate"):
        return False, "Migration failed"
    
    # Create admin user
    if not self._run_command(namespace, pod_name, "npm run create-admin"):
        return False, "Admin creation failed"
    
    # Seed data
    if not self._run_command(namespace, pod_name, "npm run seed"):
        return False, "Seeding failed"
    
    return True, None
```

### Example: PHP Platform (like WooCommerce)

```python
def configure_platform(self, namespace: str, release_name: str) -> tuple[bool, Optional[str]]:
    pod_name = self._get_app_pod(namespace, release_name)
    if not pod_name:
        return False, "Pod not found"
    
    # Install plugin
    cmd = "cd /var/www/html && wp plugin install myplugin --activate --allow-root"
    if not self._run_command(namespace, pod_name, cmd):
        return False, "Plugin installation failed"
    
    # Configure settings
    cmd = "cd /var/www/html && wp option update myoption myvalue --allow-root"
    if not self._run_command(namespace, pod_name, cmd):
        return False, "Configuration failed"
    
    return True, None
```

## Troubleshooting

### Issue: Adapter not found
```python
# Error: ValueError: Unsupported store engine: myplatform
# Solution: Check factory.py - is your adapter registered?
```

### Issue: NotImplementedError
```python
# Error: NotImplementedError: Method not implemented
# Solution: Implement all 7 required methods in your adapter
```

### Issue: Pod not found
```python
# Error: Application pod not found
# Solution: Check get_pod_selector() returns correct labels
# Debug: kubectl get pods -n namespace -l your-selector --show-labels
```

### Issue: Command fails in pod
```python
# Error: Failed to run command in pod
# Solution: 
# 1. Check pod is running: kubectl get pods -n namespace
# 2. Test command manually: kubectl exec -n namespace pod-name -- your-command
# 3. Check command path and permissions
```

## Time Estimates

| Task | Estimated Time |
|------|----------------|
| Create adapter class | 15-30 min |
| Implement configure_platform() | 10-30 min (depends on complexity) |
| Register in factory | 2 min |
| Update models | 1 min |
| Update frontend | 2 min |
| Testing | 10-20 min |
| **Total** | **40-85 min** |

## Resources

- **Full Guide**: [ADAPTER_SYSTEM.md](ADAPTER_SYSTEM.md)
- **Architecture**: [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)
- **Template**: `server/app/adapters/example_template.py`
- **Reference Implementation**: `server/app/adapters/woocommerce.py`

## Need Help?

1. Check the WooCommerce adapter for a working example
2. Review the example template for guidance
3. Read the full adapter system documentation
4. Check Kubernetes logs for deployment issues

## Quick Commands

```bash
# List all adapters
python -c "from app.adapters.factory import get_supported_engines; print(get_supported_engines())"

# Test adapter
python -c "from app.adapters import get_store_adapter; a = get_store_adapter('yourplatform'); print(a.get_store_url_path())"

# Check store status
kubectl get all -n your-store-name

# View logs
kubectl logs -n your-store-name -l app.kubernetes.io/name=yourplatform

# Delete test store
helm uninstall your-store-name -n your-store-name
kubectl delete namespace your-store-name
```
