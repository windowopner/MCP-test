import secrets
import time
from typing import Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.core.config import settings
from app.core.logger import log
from app.services.storage import token_store

_oauth_states: dict[str, float] = {}
_STATE_TTL = 600


def _client_config() -> dict:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def build_auth_url() -> Tuple[str, str]:
    flow = Flow.from_client_config(_client_config(), scopes=settings.google_scopes)
    flow.redirect_uri = settings.google_redirect_uri
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = time.time() + _STATE_TTL
    auth_url, _ = flow.authorization_url(
        state=state,
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url, state


def exchange_code(code: str, state: str) -> None:
    expiry = _oauth_states.pop(state, None)
    if expiry is None or time.time() > expiry:
        raise ValueError("Invalid or expired OAuth state parameter")
    flow = Flow.from_client_config(_client_config(), scopes=settings.google_scopes, state=state)
    flow.redirect_uri = settings.google_redirect_uri
    flow.fetch_token(code=code)
    token_store.save(flow.credentials)
    log.info("oauth_complete scopes=%d", len(flow.credentials.scopes or []))


def get_credentials() -> Credentials:
    creds = token_store.load()
    if creds is None:
        raise RuntimeError("No Google credentials found. Complete OAuth at /auth/login.")
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_store.save(creds)
        log.info("token_refreshed")
    if not creds.valid:
        raise RuntimeError("Google credentials are invalid. Re-authenticate at /auth/login.")
    return creds


def build_auth_url_with_state(state: str) -> Tuple[str, str]:
    """Build Google OAuth URL using an externally supplied state (for MCP OAuth flow)."""
    flow = Flow.from_client_config(_client_config(), scopes=settings.google_scopes)
    flow.redirect_uri = settings.google_redirect_uri
    auth_url, _ = flow.authorization_url(
        state=state,
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url, state


def exchange_code_for_mcp(code: str) -> None:
    """Exchange a Google auth code when state was already validated by the MCP OAuth layer."""
    flow = Flow.from_client_config(_client_config(), scopes=settings.google_scopes)
    flow.redirect_uri = settings.google_redirect_uri
    flow.fetch_token(code=code)
    token_store.save(flow.credentials)
    log.info("oauth_complete_mcp")


def is_authenticated() -> bool:
    try:
        creds = token_store.load()
        if creds is None:
            return False
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_store.save(creds)
        return bool(creds.valid)
    except Exception:
        return False
