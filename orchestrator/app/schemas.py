from pydantic import BaseModel
from typing import Optional, Literal


class OrchestrateRequest(BaseModel):
    store_id: str
    name: str
    engine: Literal["woocommerce", "medusa"]
    namespace: str
    host: str
    base_url: str
    store_url: str
    creator_id: Optional[str] = None


class StatusPayload(BaseModel):
    status: Literal["PROVISIONING", "READY", "FAILED"]
    url: Optional[str] = None
    error: Optional[str] = None
    password: Optional[str] = None
