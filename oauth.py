import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.logger import log
from app.services.auth import mcp_tokens
from app.services.google.auth import build_auth_url_with_state

router = APIRouter()


@router.get("/.well-known/oauth-authorization-server")
def oauth_metadata(request: Request):
    base = str(request.base_url).rstrip("/")
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "registration_endpoint": f"{base}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
    }


@router.post("/oauth/register")
async def register_client(request: Request):
    """Dynamic client registration (RFC 7591). Claude.ai calls this on first connect."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "invalid_request"})
    redirect_uris = body.get("redirect_uris", [])
    client_id = f"claude-{secrets.token_urlsafe(8)}"
    log.info("client_registered client_id=%s redirect_uris=%s", client_id, redirect_uris)
    return JSONResponse(
        status_code=201,
        content={
            "client_id": client_id,
            "redirect_uris": redirect_uris,
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        },
    )


@router.get("/oauth/authorize")
def authorize(
    response_type: str = "code",
    client_id: str = "",
    redirect_uri: str = "",
    state: str = "",
    code_challenge: str = "",
    code_challenge_method: str = "S256",
    scope: str = "",
):
    if response_type != "code":
        return JSONResponse(status_code=400, content={"error": "unsupported_response_type"})
    if not redirect_uri:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_request", "error_description": "redirect_uri is required"},
        )
    if code_challenge_method != "S256":
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_request", "error_description": "Only code_challenge_method=S256 is supported"},
        )

    our_state = mcp_tokens.store_pending_auth(client_id, redirect_uri, state, code_challenge)
    auth_url, _ = build_auth_url_with_state(our_state)
    log.info("oauth_authorize_redirect client_id=%s", client_id)
    return RedirectResponse(auth_url)


@router.post("/oauth/token")
async def token(
    grant_type: str = Form(...),
    code: str = Form(default=""),
    redirect_uri: str = Form(default=""),
    client_id: str = Form(default=""),
    code_verifier: str = Form(default=""),
    refresh_token: str = Form(default=""),
):
    if grant_type == "authorization_code":
        ok = mcp_tokens.consume_auth_code(code, client_id, redirect_uri, code_verifier)
        if not ok:
            log.warning("token_exchange_failed client_id=%s", client_id)
            return JSONResponse(status_code=400, content={"error": "invalid_grant"})
        access_token, rtoken = mcp_tokens.issue_tokens()
        log.info("token_issued client_id=%s", client_id)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": mcp_tokens.TOKEN_TTL,
            "refresh_token": rtoken,
            "scope": "mcp",
        }

    if grant_type == "refresh_token":
        result = mcp_tokens.rotate_refresh_token(refresh_token)
        if result is None:
            return JSONResponse(status_code=400, content={"error": "invalid_grant"})
        access_token, rtoken = result
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": mcp_tokens.TOKEN_TTL,
            "refresh_token": rtoken,
            "scope": "mcp",
        }

    return JSONResponse(status_code=400, content={"error": "unsupported_grant_type"})
