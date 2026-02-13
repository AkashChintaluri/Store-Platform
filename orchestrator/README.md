# Orchestrator Service

This service handles store provisioning (Helm + adapters) separately from the API. Run it as its own process or package for Lambda/containers.

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

## CI/CD to AWS Lambda

Workflow: `.github/workflows/deploy-orchestrator-lambda.yml`

On push to `main` (changes under `orchestrator/**`), GitHub Actions will:
1. Install orchestrator dependencies
2. Package `app/`, `charts/`, and `lambda_handler.py`
3. Create the target Lambda function only if it does not already exist
4. Run `aws lambda update-function-code` on that same function name

### Required GitHub repository secrets
- `AWS_ACCESS_KEY_ID` — IAM user access key id
- `AWS_SECRET_ACCESS_KEY` — IAM user secret access key
- `AWS_REGION` — AWS region (example: `ap-south-1`)
- `ORCHESTRATOR_LAMBDA_FUNCTION_NAME` — target Lambda function name
- `ORCHESTRATOR_LAMBDA_EXECUTION_ROLE_ARN` — Lambda execution role ARN (or IAM role name) used when function is created for the first time

### Lambda runtime settings
- Runtime: `python3.11`
- Handler: `lambda_handler.handler`

### Lambda environment variables
Set these in Lambda configuration:
- `BACKEND_API_BASE`
- `ORCHESTRATOR_TOKEN`
- `ORCH_POLL_ATTEMPTS` (optional)
- `ORCH_POLL_INTERVAL` (optional)
- `ORCH_MOCK` (optional)
- `APP_ENV` (optional)
- `STORE_VALUES_FILE` (optional)
