# Store Platform Backend

A FastAPI backend for managing store deployments with MongoDB persistence.

## Features

- ✨ FastAPI framework with automatic API documentation
- 🗄️ MongoDB integration using Motor (async driver)
- 🏪 Store management API (create, list, delete stores)
- 🔄 CORS middleware for cross-origin requests
- 📝 Pydantic models for request/response validation
- 🏥 Health check endpoint
- 📚 Auto-generated interactive API documentation

## Project Structure

```
server/
├── app/                 # Application package
│   ├── __init__.py      # Package init
│   ├── main.py          # FastAPI app configuration
│   ├── db.py            # MongoDB connection setup
│   ├── models.py        # Pydantic data models
│   └── routes/          # API route modules
│       ├── __init__.py  # Routes package init
│       └── stores.py    # Store management routes
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## API Endpoints

### Store Management
- `GET /api/stores` - List all stores (sorted by creation date)
- `POST /api/stores` - Create a new store
- `DELETE /api/stores/{store_id}` - Mark store for deletion

### System
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with API status

## Setup & Installation

### Prerequisites

- Python 3.8 or higher
- MongoDB (local or remote)
- pip (Python package installer)

### Installation Steps

1. **Navigate to the server directory:**
   ```bash
   cd server
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Setup MongoDB:**
   - Install MongoDB locally or use a cloud service like MongoDB Atlas
   - Ensure MongoDB is running on `mongodb://localhost:27017` (default)

6. **Create environment file (optional):**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` to configure your MongoDB connection:
   ```
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB=store_platform
   ```

## Running the Server

### Development Mode

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:

- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Alternative API Documentation (ReDoc):** `http://localhost:8000/redoc`
- **OpenAPI JSON Schema:** `http://localhost:8000/openapi.json`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB` | Database name | `store_platform` |

## Data Models

### StoreCreate (Request)
```json
{
  "name": "my-store",
  "engine": "woocommerce"  // or "medusa"
}
```

### StoreResponse
```json
{
  "id": "uuid-string",
  "name": "my-store",
  "engine": "woocommerce",
  "status": "PROVISIONING",  // or "DELETING"
  "url": null,
  "created_at": "2024-01-01T00:00:00Z",
  "error": null
}
```

## Store Lifecycle

1. **Create Store:** POST request creates store with `PROVISIONING` status
2. **List Stores:** GET request returns all stores sorted by creation date
3. **Delete Store:** DELETE request marks store as `DELETING` (doesn't remove from DB)

## Error Handling

- `404` - Store not found
- `500` - Database errors
- Validation errors return detailed messages

## API Endpoints

### Store Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stores` | List all stores |
| POST | `/api/stores` | Create new store |
| DELETE | `/api/stores/{store_id}` | Mark store for deletion |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |

## Example Usage

**Create a store:**
```bash
curl -X POST "http://localhost:8000/api/stores" \
     -H "Content-Type: application/json" \
     -d '{"name": "my-store", "engine": "woocommerce"}'
```

**Get all stores:**
```bash
curl -X GET "http://localhost:8000/api/stores"
```

**Delete a store:**
```bash
curl -X DELETE "http://localhost:8000/api/stores/{store-id}"
```

## Development

### Architecture

The application follows a clean architecture pattern:
- `app/main.py` - FastAPI app configuration and setup
- `app/db.py` - Database connection and management  
- `app/models.py` - Pydantic data models
- `app/routes/` - API route handlers organized by feature
- `main.py` - Application entry point

### Adding New Features

1. Add models in `app/models.py`
2. Create route handlers in `app/routes/`
3. Include new routers in `app/main.py`
4. Test using the interactive documentation at `/docs`

## Deployment

### Using Docker (Recommended)

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t store-platform-backend .
docker run -p 8000:8000 store-platform-backend
```

### Using Cloud Platforms

This FastAPI application can be easily deployed to:

- **Heroku**
- **AWS Lambda** (with Mangum)
- **Google Cloud Run**
- **Azure Container Instances**
- **DigitalOcean App Platform**

## Contributing

## CI/CD to AWS Lightsail

Workflow: `.github/workflows/deploy-backend-lightsail.yml`

On push to `main` (changes under `server/**`), GitHub Actions will:
1. Build backend Docker image from `server/Dockerfile`
2. Push image to Lightsail container service registry
3. Create/update Lightsail deployment and expose port `8000`

### Required GitHub repository secrets
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (example: `ap-south-1`)
- `LIGHTSAIL_SERVICE_NAME`
- `MONGODB_URI`
- `MONGODB_DB`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `ORCHESTRATOR_URL`
- `ORCHESTRATOR_TOKEN`
- `ALLOWED_ORIGINS`

### Optional secrets
- `JWT_EXPIRE_MINUTES` (default `30`)
- `STORE_BASE_DOMAIN`
- `STORE_BASE_PORT`
- `LIGHTSAIL_SERVICE_POWER` (used only if service must be created; default `nano`)
- `LIGHTSAIL_SERVICE_SCALE` (used only if service must be created; default `1`)

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.