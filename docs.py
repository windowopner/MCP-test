from typing import Any

from googleapiclient.discovery import build

from app.services.google.auth import get_credentials


def _svc():
    return build("docs", "v1", credentials=get_credentials())


def create_doc(title: str, content: str = "") -> dict[str, Any]:
    svc = _svc()
    doc = svc.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    if content:
        svc.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]},
        ).execute()
    return {
        "document_id": doc_id,
        "title": title,
        "url": f"https://docs.google.com/document/d/{doc_id}/edit",
    }


def append_text(document_id: str, text: str) -> dict[str, Any]:
    svc = _svc()
    doc = svc.documents().get(documentId=document_id).execute()
    end_index = doc["body"]["content"][-1]["endIndex"] - 1
    svc.documents().batchUpdate(
        documentId=document_id,
        body={"requests": [{"insertText": {"location": {"index": end_index}, "text": "\n" + text}}]},
    ).execute()
    return {"document_id": document_id, "appended_chars": len(text)}


def create_outline_doc(title: str, sections: list[dict]) -> dict[str, Any]:
    svc = _svc()
    doc = svc.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    parts: list[str] = []
    for section in sections:
        if section.get("heading"):
            parts.append(section["heading"])
        if section.get("body"):
            parts.append(section["body"])
    full_text = "\n".join(parts)
    if full_text:
        svc.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"location": {"index": 1}, "text": full_text}}]},
        ).execute()
    return {
        "document_id": doc_id,
        "title": title,
        "sections": len(sections),
        "url": f"https://docs.google.com/document/d/{doc_id}/edit",
    }
