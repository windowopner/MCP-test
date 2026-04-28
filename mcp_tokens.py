import base64
import hashlib
import secrets
import time
from typing import Optional

# ── In-memory stores (single-instance personal server) ──────────────────────

_pending_auths: dict[str, dict] = {}  # our_google_state → pending OAuth session
_auth_codes: dict[str, dict] = {}      # mcp_code → code metadata
_access_tokens: dict[str, float] = {}  # token → expiry timestamp
_refresh_tokens: dict[str, float] = {} # rtoken → issued_at timestamp

AUTH_STATE_TTL = 600          # 10 min — how long the Google redirect can take
CODE_TTL = 300                # 5 min — MCP auth code lifetime
TOKEN_TTL = 3600              # 1 hour — access token lifetime


def store_pending_auth(client_id: str, redirect_uri: str, claude_state: str, code_challenge: str) -> str:
    """Store OAuth session keyed by the state we'll send to Google. Returns that state."""
    our_state = secrets.token_urlsafe(32)
    _pending_auths[our_state] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "claude_state": claude_state,
        "code_challenge": code_challenge,
        "expiry": time.time() + AUTH_STATE_TTL,
    }
    return our_state


def pop_pending_auth(our_state: str) -> Optional[dict]:
    """Consume a pending auth session by Google state. Returns None if missing/expired."""
    entry = _pending_auths.pop(our_state, None)
    if not entry:
        return None
    if time.time() > entry["expiry"]:
        return None
    return entry


def generate_auth_code(client_id: str, redirect_uri: str, code_challenge: str) -> str:
    code = secrets.token_urlsafe(32)
    _auth_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "expiry": time.time() + CODE_TTL,
    }
    return code


def consume_auth_code(code: str, client_id: str, redirect_uri: str, code_verifier: str) -> bool:
    """Validate and consume an auth code. Returns True on success."""
    entry = _auth_codes.pop(code, None)
    if not entry:
        return False
    if time.time() > entry["expiry"]:
        return False
    if entry["client_id"] != client_id or entry["redirect_uri"] != redirect_uri:
        return False
    # PKCE S256 verification
    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return entry["code_challenge"] == expected


def issue_tokens() -> tuple[str, str]:
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    _access_tokens[access_token] = time.time() + TOKEN_TTL
    _refresh_tokens[refresh_token] = time.time()
    return access_token, refresh_token


def validate_access_token(token: str) -> bool:
    expiry = _access_tokens.get(token)
    if expiry is None:
        return False
    if time.time() > expiry:
        _access_tokens.pop(token, None)
        return False
    return True


def rotate_refresh_token(rtoken: str) -> Optional[tuple[str, str]]:
    """Consume a refresh token and issue new token pair. Returns None if invalid."""
    entry = _refresh_tokens.pop(rtoken, None)
    if entry is None:
        return None
    return issue_tokens()
