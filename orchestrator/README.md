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
