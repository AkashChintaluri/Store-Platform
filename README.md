# Store Platform

A **Kubernetes-based e-commerce store deployment platform** with support for multiple store engines (WooCommerce, Medusa, and more) using a **type erasure adapter pattern** for extensibility.

## 🆕 What's New: Type Erasure Adapter System

The platform now features a **type erasure adapter pattern** that makes adding new e-commerce platforms incredibly simple:

- ✅ **WooCommerce** - Fully implemented and production-ready
- 🚧 **Medusa** - Interface ready, implementation pending
- 📝 **Any Platform** - Add in 40-85 minutes using our template

**Key Innovation**: Platform-specific logic is isolated in adapters, so adding Shopify, Magento, or any other platform requires **zero changes** to core orchestration code. Just implement the adapter interface and register it!

👉 **See**: [ADAPTER_SYSTEM.md](docs/ADAPTER_SYSTEM.md) for the complete guide.

---

## ✨ Key Features

- 🏪 **Multi-Platform Support** - WooCommerce (fully implemented), Medusa (ready for implementation), and easy to add more
- 🔌 **Type Erasure Architecture** - Add new platforms without modifying core orchestration code
- ☸️ **Kubernetes-Native** - Each store is an isolated Helm release with dedicated namespace
- 🚀 **Automated Provisioning** - One-click store deployment with platform-specific configuration
- 📊 **MongoDB Persistence** - Store metadata and state management
- 🎨 **Modern React UI** - Clean dashboard for store management
- 🔒 **Complete Isolation** - Per-store namespaces, quotas, and network policies

## Architecture Overview

The Store Platform uses a **three-tier architecture** with a unique **adapter pattern** for multi-platform support:

### 1. **FastAPI Backend** (`server/`)
- **REST API** - Store lifecycle management (create, list, delete)
- **Adapter System** - Type erasure pattern for platform-agnostic orchestration
- **MongoDB Atlas** - Persistent store metadata and state
- **Kubernetes Orchestration** - Helm-based deployment automation

### 2. **React Frontend** (`client/`)
- **Store Dashboard** - Create and monitor stores
- **Real-time Updates** - Live store status and health
- **Multi-Platform UI** - Select engine type during creation

### 3. **Helm-Based Deployment** (`charts/`)
- **Isolated Releases** - Each store is an independent Helm release
- **Namespace Isolation** - Dedicated Kubernetes namespace per store
- **Deterministic Cleanup** - Clean removal via `helm uninstall`

### 4. **Platform Adapters** (`server/app/adapters/`) ⭐ NEW
- **Type Erasure Pattern** - Common interface for all platforms
- **WooCommerce Adapter** - WordPress + WooCommerce + MariaDB
- **Medusa Adapter** - Placeholder ready for implementation
- **Extensible** - Add new platforms in 40-85 minutes

## Multi-Platform Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Store Platform API                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Platform Adapter System                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │ WooCommerce│  │   Medusa   │  │   Future   │    │  │
│  │  │  Adapter   │  │  Adapter   │  │  Adapters  │    │  │
│  │  └────────────┘  └────────────┘  └────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│                    Helm Deployment                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                         │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                 │
│  │ store-1 (WooCom)│  │ store-2 (Medusa)│                 │
│  │ ├── WordPress   │  │ ├── Medusa.js   │                 │
│  │ ├── MariaDB     │  │ ├── PostgreSQL  │                 │
│  │ └── Ingress     │  │ └── Ingress     │                 │
│  └─────────────────┘  └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Platform Support Status

| Platform | Status | Implementation | Documentation |
|----------|--------|----------------|---------------|
| **WooCommerce** | ✅ **Production Ready** | WordPress + WooCommerce plugin + MariaDB | Fully functional |
| **Medusa** | 🚧 **Placeholder Ready** | Interface defined, awaiting implementation | [Implementation Guide](docs/ADAPTER_SYSTEM.md) |
| **Others** | 📝 **Template Available** | Use adapter template | [Quick Reference](docs/QUICK_REFERENCE.md) |

## Key Benefits

- ✅ **Extensible Architecture** - Add new platforms without modifying core code
- ✅ **Type-Safe** - Python type hints and abstract base classes
- ✅ **Complete Isolation** - Each store runs in its own namespace with dedicated resources
- ✅ **Predictable Lifecycle** - Helm manages install, upgrade, and uninstall operations
- ✅ **Resource Management** - Per-store quotas and network policies
- ✅ **Clean Deletion** - `helm uninstall` removes all store resources deterministically
- ✅ **Independent Scaling** - Scale each store based on its needs
- ✅ **Production Ready** - WooCommerce fully tested and operational

## Getting Started

### Prerequisites

- **Kubernetes Cluster** (local or cloud)
- **Helm 3.x** installed
- **MongoDB Atlas** account and cluster
- **Node.js 18+** for the frontend
- **Python 3.8+** for the backend

### Quick Start

1. **Start the Backend API**:
   ```bash
   cd server
   cp .env.example .env
   # Edit .env with your MongoDB Atlas connection
   pip install -r requirements.txt
   python main.py
   ```

2. **Start the Frontend Dashboard**:
   ```bash
   cd client
   npm install
   npm run dev
   ```

3. **Create a Store** (API handles Helm deployment automatically):
   ```bash
   # Create WooCommerce store
   curl -X POST "http://localhost:8000/api/stores" \
     -H "Content-Type: application/json" \
     -d '{"name": "my-store", "engine": "woocommerce"}'
   
   # Or create Medusa store (when implemented)
   curl -X POST "http://localhost:8000/api/stores" \
     -H "Content-Type: application/json" \
     -d '{"name": "my-medusa", "engine": "medusa"}'
   
   # The API will:
   # - Generate platform-specific Helm values
   # - Deploy the Helm chart
   # - Configure the platform (install plugins, run migrations, etc.)
   # - Return the store URL and admin password
   ```

4. **Access Your Store**:
   - **WooCommerce**: `http://my-store.localhost/shop/`
   - **Admin**: `http://my-store.localhost/wp-admin/`
   - Password returned in API response

## Store Management Commands

### Deploy a New Store
```bash
helm install <store-name> ./charts/store \
  --namespace <store-name> \
  --create-namespace \
  -f ./charts/store/values.yaml \
  -f ./charts/store/values-local.yaml
```

### Update a Store
```bash
helm upgrade <store-name> ./charts/store \
  --namespace <store-name> \
  -f ./charts/store/values.yaml \
  -f ./charts/store/values-local.yaml
```

### Delete a Store
```bash
# Clean removal of all store resources
helm uninstall <store-name> -n <store-name>
kubectl delete namespace <store-name>
```

### Monitor Store Status
```bash
# Check store pods
kubectl get pods -n <store-name>

# Check store services
kubectl get svc -n <store-name>

# Check store ingress
kubectl get ingress -n <store-name>
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB Atlas connection string | `mongodb://localhost:27017` |
| `MONGODB_DB` | Database name | `store_platform` |

### Helm Chart Values

The store chart supports different configurations:

- **Local Development**: `values-local.yaml`
- **Production**: `values-prod.yaml`
- **Custom Engine**: Override `store.engine` (woocommerce/medusa)

## API Endpoints

### Store Management

#### Create Store
```http
POST /api/stores
Content-Type: application/json

{
  "name": "my-store",
  "engine": "woocommerce"  // or "medusa"
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "my-store",
  "engine": "woocommerce",
  "namespace": "my-store",
  "host": "my-store.example.com",
  "status": "PROVISIONING",  // → "READY" when complete
  "url": "http://my-store.example.com/shop/",
  "created_at": "2026-02-11T18:00:00Z",
  "password": "admin-password"  // Available when status is READY
}
```

#### List Stores
```http
GET /api/stores
```

#### Delete Store
```http
DELETE /api/stores/{store_id}
```

### System
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)

## Platform Adapter System

The Store Platform uses a **type erasure adapter pattern** to support multiple e-commerce platforms without coupling the core orchestration logic to specific implementations.

### How It Works

```python
# 1. Factory creates the appropriate adapter
adapter = get_store_adapter(engine)  # Returns StoreAdapter interface

# 2. Adapter generates platform-specific configuration
values = adapter.get_default_values(store_name, host)

# 3. Adapter handles platform-specific setup
success, error = adapter.configure_platform(namespace, release_name)
```

### Adapter Interface

All platform adapters implement these methods:

| Method | Purpose |
|--------|---------|
| `get_chart_dependency()` | Helm chart configuration |
| `get_default_values()` | Platform-specific Helm values |
| `configure_platform()` | Post-deployment setup (plugins, migrations, etc.) |
| `get_admin_password()` | Retrieve admin credentials |
| `get_pod_selector()` | Kubernetes pod label selector |
| `get_store_url_path()` | Store frontend URL path |
| `is_platform_ready()` | Platform initialization check |

### Current Implementations

**WooCommerce Adapter** (`server/app/adapters/woocommerce.py`)
- ✅ WordPress + WooCommerce plugin installation
- ✅ MariaDB database configuration
- ✅ Test product creation
- ✅ Payment gateway setup (COD)
- ✅ Admin password retrieval

**Medusa Adapter** (`server/app/adapters/medusa.py`)
- 🚧 Interface defined with placeholders
- 📝 Ready for implementation
- 📚 See [ADAPTER_SYSTEM.md](docs/ADAPTER_SYSTEM.md) for guide

## Development

### Project Structure
```
├── server/           # FastAPI backend
│   ├── app/         # Application package
│   │   ├── main.py  # FastAPI app setup
│   │   ├── db.py    # MongoDB connection
│   │   ├── models.py # Pydantic models
│   │   ├── routes/  # API endpoints
│   │   ├── adapters/ # Platform adapter system (type erasure)
│   │   │   ├── base.py        # StoreAdapter interface
│   │   │   ├── factory.py     # Adapter factory
│   │   │   ├── woocommerce.py # WooCommerce implementation
│   │   │   └── medusa.py      # Medusa placeholder
│   │   └── orchestrator/ # Platform-agnostic orchestration
│   │       ├── provisioner.py # Store provisioning
│   │       ├── status.py      # Status checking
│   │       └── helm.py        # Helm wrapper
│   └── main.py      # Application entry point
├── client/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   └── pages/
│   └── package.json
├── charts/          # Helm charts
│   └── store/       # Store deployment chart
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-local.yaml
│       ├── values-prod.yaml
│       └── templates/
└── docs/            # Documentation
    ├── ADAPTER_SYSTEM.md  # Adapter system guide
    └── LOCAL_DOMAIN_SETUP.md
```

### Adding Support for New Store Engines

The platform uses a **type erasure adapter system** for supporting multiple e-commerce platforms. This allows adding new platforms without modifying core orchestration logic.

#### Quick Start

1. **Create a new adapter** in `server/app/adapters/your_platform.py`
   - Implement the `StoreAdapter` interface
   - Define platform-specific Helm values
   - Implement post-deployment configuration

2. **Register the adapter** in `server/app/adapters/factory.py`
   - Add to the `adapters` dictionary
   - Update the `StoreEngine` type

3. **Update the API model** in `server/app/models.py`
   - Add the new engine to `StoreCreate.engine` Literal type

4. **Update the frontend** in `client/src/components/CreateStoreModal.tsx`
   - Add the new engine option to the dropdown

5. **Create Helm templates** (if needed) in `charts/store/templates/`
   - Add platform-specific Kubernetes resources

For detailed instructions and examples, see [ADAPTER_SYSTEM.md](docs/ADAPTER_SYSTEM.md).

#### Current Platform Support

| Platform | Status | Documentation |
|----------|--------|---------------|
| WooCommerce | ✅ Fully Implemented | WordPress + WooCommerce plugin |
| Medusa | 🚧 Placeholder Ready | See [ADAPTER_SYSTEM.md](docs/ADAPTER_SYSTEM.md) for implementation guide |


## Deployment Architecture Benefits

### Namespace Isolation
Each store deployment creates:
- Dedicated Kubernetes namespace
- Isolated network policies
- Resource quotas per store
- Independent RBAC permissions

### Helm Release Management
- **Atomic Operations**: Installs/upgrades are atomic
- **Rollback Capability**: Easy rollback to previous versions
- **Consistent State**: Helm ensures desired state
- **Clean Deletion**: Complete resource cleanup

### Scalability
- **Horizontal**: Deploy unlimited stores
- **Vertical**: Scale individual store resources
- **Independent**: Each store scales independently
- **Multi-Region**: Deploy across multiple clusters

## Monitoring and Observability

### Store Health Checks
```bash
# Check all store namespaces
kubectl get namespaces -l app.kubernetes.io/managed-by=Helm

# Get store status
helm list -A

# Monitor store resources
kubectl top pods -n <store-name>
```

### Troubleshooting
```bash
# Check store logs
kubectl logs -n <store-name> -l app=wordpress

# Debug deployment issues
kubectl describe pod -n <store-name> <pod-name>

# Helm release history
helm history <store-name> -n <store-name>
```

## Security

### Network Policies
Each store namespace includes:
- Ingress traffic restrictions
- Inter-namespace isolation
- Database access controls

### Resource Limits
- CPU and memory quotas per store
- Storage limits
- Network bandwidth controls

### Secrets Management
- Database credentials per store
- TLS certificates
- API keys and tokens

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### Architecture & Design
- **[ADAPTER_SYSTEM.md](docs/ADAPTER_SYSTEM.md)** - Complete guide to the type erasure adapter pattern
  - Architecture overview and design decisions
  - Interface documentation
  - Step-by-step implementation guide
  - Medusa implementation checklist

- **[ARCHITECTURE_DIAGRAMS.md](docs/ARCHITECTURE_DIAGRAMS.md)** - Visual architecture diagrams
  - Type erasure flow diagrams
  - Component interaction charts
  - Before/after refactoring comparison
  - Data flow examples

### Developer Guides
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - Quick start for adding new platforms
  - Implementation checklist (40-85 min)
  - Common patterns and examples
  - Troubleshooting guide
  - Time estimates

- **[TYPE_ERASURE_IMPLEMENTATION.md](docs/TYPE_ERASURE_IMPLEMENTATION.md)** - Implementation summary
  - Changes made
  - Files created and modified
  - Code statistics
  - Next steps

- **[IMPLEMENTATION_COMPLETE.md](docs/IMPLEMENTATION_COMPLETE.md)** - Project completion summary
  - Feature overview
  - Success criteria
  - Testing recommendations

### Code Documentation
- **[server/app/adapters/README.md](server/app/adapters/README.md)** - Adapter system overview
- **[server/app/adapters/example_template.py](server/app/adapters/example_template.py)** - Template for new adapters

### Local Development
- **[LOCAL_DOMAIN_SETUP.md](docs/LOCAL_DOMAIN_SETUP.md)** - Local domain configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.