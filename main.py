import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("mcp-server")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MCP Server",
    version="2.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ToolRequest(BaseModel):
    tool: str
    input: dict[str, Any] = {}

    @field_validator("tool")
    @classmethod
    def tool_must_be_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("tool name must not be empty")
        return v.strip()


class ToolResponse(BaseModel):
    success: bool
    tool: str
    result: dict[str, Any]
    error: str | None = None

# ---------------------------------------------------------------------------
# Global exception handler — never leak tracebacks to callers
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "tool": "", "result": {}, "error": "Internal server error"},
    )

# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def handle_echo(data: dict[str, Any]) -> dict[str, Any]:
    return data


def handle_health_check(data: dict[str, Any]) -> dict[str, Any]:
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


def handle_create_doc(data: dict[str, Any]) -> dict[str, Any]:
    # TODO (Google Docs): swap mock for real API call.
    # from google.oauth2.credentials import Credentials
    # from googleapiclient.discovery import build
    # creds = Credentials.from_authorized_user_info(get_token(), DOCS_SCOPES)
    # service = build("docs", "v1", credentials=creds)
    # doc = service.documents().create(body={"title": data.get("title", "Untitled")}).execute()
    # return {"doc_id": doc["documentId"], "status": "created"}
    return {"doc_id": "mock-doc-id", "status": "created"}


# TODO (Google Slides): implement handle_create_slide(data) using the Slides API.
# TODO (Google Classroom): implement handle_list_courses(data) using the Classroom API.
# TODO (Gmail): implement handle_send_email(data) and handle_search_email(data).
# TODO (OAuth): add POST /auth/callback to exchange Google authorization codes for tokens.


# Registry maps tool name → handler function.
# To add a new tool: write a handler above, then add one line here.
TOOL_REGISTRY: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "echo": handle_echo,
    "health_check": handle_health_check,
    "create_doc": handle_create_doc,
}

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "mcp-server", "version": "2.0.0"}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"healthy": True, "service": "mcp-server"}


@app.post("/tool/run", response_model=ToolResponse)
def run_tool(request: ToolRequest) -> ToolResponse:
    log.info("tool_call tool=%s input_keys=%s", request.tool, list(request.input.keys()))
    t0 = time.perf_counter()

    handler = TOOL_REGISTRY.get(request.tool)

    if handler is None:
        log.warning("unknown_tool tool=%s", request.tool)
        return ToolResponse(
            success=False,
            tool=request.tool,
            result={},
            error=f"Unknown tool '{request.tool}'. Available: {sorted(TOOL_REGISTRY)}",
        )

    try:
        result = handler(request.input)
        elapsed = (time.perf_counter() - t0) * 1000
        log.info("tool_ok tool=%s elapsed_ms=%.1f", request.tool, elapsed)
        return ToolResponse(success=True, tool=request.tool, result=result)
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        log.exception("tool_error tool=%s elapsed_ms=%.1f", request.tool, elapsed)
        return ToolResponse(
            success=False,
            tool=request.tool,
            result={},
            error="Tool execution failed",
        )

# ---------------------------------------------------------------------------
# Entrypoint (local dev only — Render uses the Procfile)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
