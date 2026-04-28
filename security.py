import re
from typing import Any

_TOOL_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,63}$")
_SENSITIVE_KEYS = frozenset({"token", "access_token", "refresh_token", "client_secret", "password", "api_key"})


def is_valid_tool_name(name: str) -> bool:
    return bool(_TOOL_NAME_RE.match(name))


def mask_sensitive(data: dict[str, Any]) -> dict[str, Any]:
    return {k: "[REDACTED]" if k.lower() in _SENSITIVE_KEYS else v for k, v in data.items()}
