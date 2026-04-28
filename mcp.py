import json
import secrets
from typing import Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, Response

from app.core.config import APP_VERSION
from app.core.logger import log
from app.services.auth import mcp_tokens
from app.services.mcp.executor import execute
from app.services.mcp.registry import TOOL_DEFINITIONS

router = APIRouter()

PROTOCOL_VERSION = "2024-11-05"
_sessions: dict[str, bool] = {}


# ── Auth helper ───────────────────────────────────────────────────────────────

def _check_auth(authorization: str) -> bool:
    if not authorization or not authorization.startswith("Bearer "):
        return False
    return mcp_tokens.validate_access_token(authorization.removeprefix("Bearer ").strip())


def _unauth_response() -> Response:
    return Response(
        status_code=401,
        headers={
            "WWW-Authenticate": 'Bearer error="invalid_token"',
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── JSON-RPC helpers ──────────────────────────────────────────────────────────

def _ok(id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "result": result, "id": id}


def _err(id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": id}


# ── Message dispatcher ────────────────────────────────────────────────────────

def _dispatch(msg: dict) -> dict | None:
    method: str = msg.get("method", "")
    msg_id: Any = msg.get("id")
    params: dict = msg.get("params") or {}
    is_notification = "id" not in msg  # notifications get no response

    log.info("mcp_method method=%s id=%s", method, msg_id)

    if method == "initialize":
        session_id = secrets.token_urlsafe(16)
        _sessions[session_id] = True
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "Google Workspace MCP", "version": APP_VERSION},
            "_sessionId": session_id,
        }
        return _ok(msg_id, result) if not is_notification else None

    if method in ("notifications/initialized", "initialized"):
        return None  # notification — no response

    if method == "ping":
        return _ok(msg_id, {}) if not is_notification else None

    if method == "tools/list":
        return _ok(msg_id, {"tools": TOOL_DEFINITIONS}) if not is_notification else None

    if method == "tools/call":
        name: str = params.get("name", "")
        arguments: dict = params.get("arguments") or {}
        tool_result = execute(name, arguments)
        if tool_result.success:
            content_text = json.dumps(tool_result.result, ensure_ascii=False, indent=2)
            result = {"content": [{"type": "text", "text": content_text}], "isError": False}
        else:
            result = {
                "content": [{"type": "text", "text": tool_result.error or "Tool execution failed"}],
                "isError": True,
            }
        return _ok(msg_id, result) if not is_notification else None

    if is_notification:
        return None
    return _err(msg_id, -32601, f"Method not found: {method}")


# ── HTTP endpoints ────────────────────────────────────────────────────────────

@router.post("/mcp")
async def mcp_post(request: Request, authorization: str = Header(default="")):
    if not _check_auth(authorization):
        return _unauth_response()

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(_err(None, -32700, "Parse error"), status_code=400)

    if isinstance(body, list):
        responses = [r for msg in body if (r := _dispatch(msg)) is not None]
        return JSONResponse(responses)

    result = _dispatch(body)
    if result is None:
        return Response(status_code=202)  # notification acknowledged
    return JSONResponse(result)


@router.get("/mcp")
async def mcp_get(request: Request, authorization: str = Header(default="")):
    """SSE endpoint for server-initiated messages. Not used for tool-only servers."""
    if not _check_auth(authorization):
        return _unauth_response()
    return Response(status_code=405, content="Server-sent events not required for this server.")
