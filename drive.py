import io
from typing import Any, Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from app.services.google.auth import get_credentials


def _svc():
    return build("drive", "v3", credentials=get_credentials())


def list_files(query: str = "", max_results: int = 20) -> dict[str, Any]:
    q = query if query else "trashed=false"
    result = (
        _svc()
        .files()
        .list(
            q=q,
            pageSize=max_results,
            fields="files(id,name,mimeType,createdTime,modifiedTime,webViewLink)",
        )
        .execute()
    )
    files = result.get("files", [])
    return {"files": files, "count": len(files)}


def create_folder(name: str, parent_id: Optional[str] = None) -> dict[str, Any]:
    body: dict[str, Any] = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    folder = _svc().files().create(body=body, fields="id,name,webViewLink").execute()
    return {"folder_id": folder["id"], "name": folder["name"], "url": folder.get("webViewLink")}


def upload_file(
    name: str,
    content: str,
    mime_type: str = "text/plain",
    parent_id: Optional[str] = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"name": name, "mimeType": mime_type}
    if parent_id:
        body["parents"] = [parent_id]
    media = MediaIoBaseUpload(io.BytesIO(content.encode("utf-8")), mimetype=mime_type)
    file = _svc().files().create(body=body, media_body=media, fields="id,name,webViewLink").execute()
    return {"file_id": file["id"], "name": file["name"], "url": file.get("webViewLink")}
