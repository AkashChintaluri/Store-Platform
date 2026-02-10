# Store Platform

A Kubernetes-based e-commerce store deployment platform that supports WooCommerce and Medusa stores with automated provisioning and management.

## Architecture Overview

The Store Platform consists of three main components:

### 1. **FastAPI Backend** (`server/`)
- MongoDB-backed REST API for store management
- Store lifecycle operations (create, list, delete)
- MongoDB Atlas integration for data persistence
- Environment-based configuration

### 2. **React Frontend** (`client/`)
- Modern React dashboard for store management
- Store creation and monitoring interface
- Real-time store status updates

### 3. **Helm-Based Store Deployment** (`charts/`)
- **Each store is a Helm release** - Every store deployment is managed as an independent Helm release
- **Namespace-per-store enforces isolation** - Each store gets its own Kubernetes namespace for complete resource isolation
- **Deletion is deterministic via Helm uninstall** - Store removal is clean and predictable through Helm's lifecycle management

## Store Deployment Architecture

```
Store Platform API
├── MongoDB Atlas (store metadata)
├── Kubernetes Cluster
│   ├── store-1 namespace
│   │   └── Helm Release: store-1
│   │       ├── WordPress/WooCommerce
│   │       ├── MariaDB
│   │       └── Ingress
│   ├── store-2 namespace
│   │   └── Helm Release: store-2
│   │       ├── Medusa.js
│   │       ├── PostgreSQL
│   │       └── Ingress
│   └── store-n namespace
│       └── Helm Release: store-n
```

### Key Benefits

- **Complete Isolation**: Each store runs in its own namespace with dedicated resources
- **Predictable Lifecycle**: Helm manages the entire store lifecycle (install, upgrade, uninstall)
- **Resource Management**: Per-store quotas and network policies
- **Clean Deletion**: `helm uninstall` removes all store resources deterministically
- **Scalability**: Independent scaling per store
- **Multi-Engine Support**: WooCommerce and Medusa stores using the same infrastructure

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

3. **Deploy a Store**:
   ```bash
   # Create store via API
   curl -X POST "http://localhost:8000/api/stores" \
     -H "Content-Type: application/json" \
     -d '{"name": "my-store", "engine": "woocommerce"}'

   # Deploy using Helm
   helm install my-store ./charts/store \
     --namespace my-store \
     --create-namespace \
     -f ./charts/store/values.yaml \
     -f ./charts/store/values-local.yaml
   ```

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
- `GET /api/stores` - List all stores
- `POST /api/stores` - Create a new store
- `DELETE /api/stores/{store_id}` - Mark store for deletion

### System
- `GET /health` - Health check
- `GET /docs` - API documentation

## Development

### Project Structure
```
├── server/           # FastAPI backend
│   ├── app/         # Application package
│   │   ├── main.py  # FastAPI app setup
│   │   ├── db.py    # MongoDB connection
│   │   ├── models.py # Pydantic models
│   │   └── routes/  # API endpoints
│   └── main.py      # Application entry point
├── client/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   └── pages/
│   └── package.json
└── charts/          # Helm charts
    └── store/       # Store deployment chart
        ├── Chart.yaml
        ├── values.yaml
        ├── values-local.yaml
        ├── values-prod.yaml
        └── templates/
```

### Adding Support for New Store Engines

1. Update `charts/store/values.yaml` with new engine configuration
2. Add engine-specific templates in `charts/store/templates/`
3. Update API models in `server/app/models.py`
4. Add engine option to frontend store creation form

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.