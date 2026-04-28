import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app.core.config import APP_VERSION
from app.services.mcp.registry import TOOL_REGISTRY

router = APIRouter()

_START_TIME = time.time()


@router.get("/")
def root() -> dict[str, Any]:
    return {"status": "ok", "service": "mcp-server", "version": APP_VERSION, "ready": True}


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "healthy": True,
        "service": "mcp-server",
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "registered_tools": sorted(TOOL_REGISTRY),
    }
