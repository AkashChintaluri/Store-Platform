"""
Minimal FastAPI orchestrator entrypoint.

- POST /orchestrate : accepts store jobs from the backend (requires X-Orchestrator-Token)
- Provisions via Helm/adapters, then callbacks backend /api/stores/{id}/status
"""

import asyncio
import hashlib
import logging
import sys
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request

# Allow running as a script: python app/main.py
ORCH_ROOT = Path(__file__).resolve().parents[1]      # .../orchestrator
WORKSPACE_ROOT = ORCH_ROOT.parent                    # repo root
for p in (WORKSPACE_ROOT, ORCH_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.provisioner import (
    generate_values,
    install_store,
    configure_platform,
    get_store_url_path,
)
from app.config import get_settings
from app.status import namespace_ready, get_store_password
from app.schemas import OrchestrateRequest, StatusPayload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

settings = get_settings()
BACKEND_API_BASE = settings.backend_api_base
ORCHESTRATOR_TOKEN = settings.orchestrator_token
POLL_ATTEMPTS = settings.orch_poll_attempts
POLL_INTERVAL = settings.orch_poll_interval
MOCK_MODE = settings.orch_mock

app = FastAPI(title="Store Orchestrator", version="1.0.0")


def _token_fingerprint(value: str | None) -> str:
    if not value:
        return "empty"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]


def _token_ok(incoming: str | None) -> bool:
    return incoming == ORCHESTRATOR_TOKEN


async def callback_status(store_id: str, payload: StatusPayload) -> None:
    url = f"{BACKEND_API_BASE}/stores/{store_id}/status"
    headers = {"X-Orchestrator-Token": ORCHESTRATOR_TOKEN, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload.dict(exclude_none=True), headers=headers)
        if resp.status_code >= 400:
            raise RuntimeError(f"Callback failed: {resp.status_code} {resp.text}")


@app.on_event("startup")
async def startup_event() -> None:
    logger.info(
        "Orchestrator startup config: token_len=%s token_fp=%s backend=%s",
        len(ORCHESTRATOR_TOKEN) if ORCHESTRATOR_TOKEN else 0,
        _token_fingerprint(ORCHESTRATOR_TOKEN),
        BACKEND_API_BASE,
    )


async def _run_orchestration(req: OrchestrateRequest) -> None:
    logger.info("Processing orchestration job for store %s", req.store_id)

    if MOCK_MODE:
        await callback_status(
            req.store_id,
            StatusPayload(status="READY", url=req.store_url, password="mock-password"),
        )
        return

    values_file = generate_values(req.name, req.host, req.engine)

    try:
        install_store(req.name, req.namespace, values_file)
    except Exception as e:
        await callback_status(req.store_id, StatusPayload(status="FAILED", error=str(e)))
        logger.exception("Helm install failed for store %s", req.store_id)
        return

    for _ in range(POLL_ATTEMPTS):
        if namespace_ready(req.namespace):
            success, cfg_error = configure_platform(req.namespace, req.name, req.engine)
            if success:
                password = get_store_password(req.namespace, req.name, req.engine)
                await callback_status(
                    req.store_id,
                    StatusPayload(status="READY", url=req.store_url, password=password),
                )
                logger.info("Store %s ready", req.store_id)
                return
            if cfg_error and "not installed" not in cfg_error:
                await callback_status(req.store_id, StatusPayload(status="FAILED", error=cfg_error))
                logger.error("Configure failed for store %s: %s", req.store_id, cfg_error)
                return
        await asyncio.sleep(POLL_INTERVAL)

    await callback_status(req.store_id, StatusPayload(status="FAILED", error="Platform configuration timed out"))
    logger.error("Platform configuration timed out for store %s", req.store_id)


@app.post("/orchestrate")
async def orchestrate(
    request: Request,
    req: OrchestrateRequest,
    background_tasks: BackgroundTasks,
):
    incoming_token = request.headers.get("x-orchestrator-token") or request.headers.get("x_orchestrator_token")
    if not _token_ok(incoming_token):
        logger.warning(
            "Invalid orchestrator token: incoming_len=%s incoming_fp=%s expected_len=%s expected_fp=%s",
            len(incoming_token) if incoming_token else 0,
            _token_fingerprint(incoming_token),
            len(ORCHESTRATOR_TOKEN) if ORCHESTRATOR_TOKEN else 0,
            _token_fingerprint(ORCHESTRATOR_TOKEN),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid orchestrator token")

    logger.info("Accepted orchestration request for store %s", req.store_id)
    background_tasks.add_task(_run_orchestration, req)
    return {"ok": True, "accepted": True, "store_id": req.store_id}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("orchestrator.app.main:app", host="0.0.0.0", port=9000, reload=True)
