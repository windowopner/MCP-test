import base64
import json
import os
from typing import Optional

from google.oauth2.credentials import Credentials

from app.core.config import settings
from app.core.logger import log


def save(creds: Credentials) -> None:
    data = _serialize(creds)
    if _env_mode():
        os.environ["GOOGLE_TOKEN_JSON"] = base64.b64encode(json.dumps(data).encode()).decode()
        return
    with open(settings.token_storage_path, "w") as f:
        json.dump(data, f)
    log.info("token_saved path=%s", settings.token_storage_path)


def load() -> Optional[Credentials]:
    if _env_mode():
        return _load_from_env()
    return _load_from_file()


def _env_mode() -> bool:
    return bool(os.environ.get("GOOGLE_TOKEN_JSON"))


def _load_from_env() -> Optional[Credentials]:
    try:
        raw = os.environ["GOOGLE_TOKEN_JSON"]
        data = json.loads(base64.b64decode(raw))
        return _deserialize(data)
    except Exception as exc:
        log.warning("token_env_load_failed error=%s", exc)
        return None


def _load_from_file() -> Optional[Credentials]:
    path = settings.token_storage_path
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return _deserialize(data)
    except Exception as exc:
        log.warning("token_file_load_failed error=%s", exc)
        return None


def _serialize(creds: Credentials) -> dict:
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }


def _deserialize(data: dict) -> Credentials:
    return Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )
