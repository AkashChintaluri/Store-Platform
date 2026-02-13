# Orchestrator Service

This service handles store provisioning (Helm + adapters) separately from the API. Run it as its own process in Kubernetes.

## Layout
- `app/helm.py` — Helm execution helper
- `app/provisioner.py` — install/delete/configure stores
- `app/status.py` — readiness/password helpers
- `app/adapters/` — platform adapters (WooCommerce implemented; Medusa placeholder)

## Contract with API
- API → Orchestrator: POST to `$ORCHESTRATOR_URL` with store payload (`store_id`, `name`, `engine`, `namespace`, `host`, `base_url`, `store_url`, `creator_id`) and header `X-Orchestrator-Token`.
- Orchestrator → API: POST to `/api/stores/{store_id}/status` with header `X-Orchestrator-Token` and body `{ status, url?, error?, password? }`.

## Running locally (example)
1. `python -m venv .venv && source .venv/bin/activate` (or Windows equivalent)
2. `pip install -r requirements.txt`
3. Run your entrypoint (FastAPI, Lambda runtime, or CLI) that imports from `orchestrator.app` and exposes the contract above.

## Notes
- Helm, kubectl, and cluster access must be available to this service.
- Keep the token in sync with API env `ORCHESTRATOR_TOKEN`.
- Charts now live at `orchestrator/charts/store`; provisioner resolves them relative to this directory.

## CI/CD to AWS EKS

Workflow: `.github/workflows/deploy-orchestrator-eks.yml`

On push to `main` (changes under `orchestrator/**`), GitHub Actions will:
1. Create EKS cluster if it does not exist
2. Create nodegroup if it does not exist
3. Build orchestrator Docker image from `orchestrator/Dockerfile`
4. Push the image to Amazon ECR
5. Configure kubectl context to your EKS cluster
6. Apply/update runtime secrets
7. Apply deployment manifests and roll out update

### Required GitHub repository secrets
- `AWS_ACCESS_KEY_ID` — IAM user access key id
- `AWS_SECRET_ACCESS_KEY` — IAM user secret access key
- `AWS_REGION` — AWS region (example: `ap-south-1`)
- `EKS_CLUSTER_NAME` — target EKS cluster name
- `ORCHESTRATOR_ECR_REPOSITORY` — ECR repository name for orchestrator image
- `BACKEND_API_BASE`
- `ORCHESTRATOR_TOKEN`

### Optional GitHub repository secrets
- `ORCH_POLL_ATTEMPTS` (default `30`)
- `ORCH_POLL_INTERVAL` (default `10`)
- `ORCH_MOCK` (default `0`)
- `APP_ENV` (default `production`)
- `STORE_VALUES_FILE` (default empty)
- `EKS_NODEGROUP_NAME` (default `orchestrator-ng`)
- `EKS_NODE_INSTANCE_TYPE` (default `t3.medium`)
- `EKS_NODE_COUNT` (default `2`)

### Kubernetes manifests
- `orchestrator/deploy/orchestrator-eks.yaml` creates namespace, service account, RBAC binding, deployment, and LoadBalancer service.
