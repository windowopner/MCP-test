import uuid
from typing import Any

from googleapiclient.discovery import build

from app.services.google.auth import get_credentials


def _svc():
    return build("slides", "v1", credentials=get_credentials())


def _id() -> str:
    return uuid.uuid4().hex[:10]


def create_deck(title: str) -> dict[str, Any]:
    pres = _svc().presentations().create(body={"title": title}).execute()
    pres_id = pres["presentationId"]
    return {
        "presentation_id": pres_id,
        "title": title,
        "url": f"https://docs.google.com/presentation/d/{pres_id}/edit",
    }


def add_slide(presentation_id: str, layout: str = "BLANK") -> dict[str, Any]:
    slide_id = _id()
    _svc().presentations().batchUpdate(
        presentationId=presentation_id,
        body={
            "requests": [
                {
                    "createSlide": {
                        "objectId": slide_id,
                        "slideLayoutReference": {"predefinedLayout": layout},
                    }
                }
            ]
        },
    ).execute()
    return {"presentation_id": presentation_id, "slide_id": slide_id}


def generate_from_outline(title: str, slides: list[dict]) -> dict[str, Any]:
    svc = _svc()
    pres = svc.presentations().create(body={"title": title}).execute()
    pres_id = pres["presentationId"]
    requests: list[dict] = []
    for slide in slides:
        if slide.get("type") == "title":
            requests.extend(_title_slide_reqs(slide.get("title", ""), slide.get("subtitle", "")))
        else:
            requests.extend(_bullet_slide_reqs(slide.get("title", ""), slide.get("bullets", [])))
    if requests:
        svc.presentations().batchUpdate(presentationId=pres_id, body={"requests": requests}).execute()
    return {
        "presentation_id": pres_id,
        "title": title,
        "slides_added": len(slides),
        "url": f"https://docs.google.com/presentation/d/{pres_id}/edit",
    }


def _title_slide_reqs(title: str, subtitle: str) -> list[dict]:
    slide_id, title_id, subtitle_id = _id(), _id(), _id()
    return [
        {
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": "TITLE"},
                "placeholderIdMappings": [
                    {"layoutPlaceholder": {"type": "CENTERED_TITLE"}, "objectId": title_id},
                    {"layoutPlaceholder": {"type": "SUBTITLE"}, "objectId": subtitle_id},
                ],
            }
        },
        {"insertText": {"objectId": title_id, "insertionIndex": 0, "text": title}},
        {"insertText": {"objectId": subtitle_id, "insertionIndex": 0, "text": subtitle}},
    ]


def _bullet_slide_reqs(title: str, bullets: list[str]) -> list[dict]:
    slide_id, title_id, body_id = _id(), _id(), _id()
    return [
        {
            "createSlide": {
                "objectId": slide_id,
                "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                "placeholderIdMappings": [
                    {"layoutPlaceholder": {"type": "TITLE"}, "objectId": title_id},
                    {"layoutPlaceholder": {"type": "BODY"}, "objectId": body_id},
                ],
            }
        },
        {"insertText": {"objectId": title_id, "insertionIndex": 0, "text": title}},
        {"insertText": {"objectId": body_id, "insertionIndex": 0, "text": "\n".join(bullets)}},
    ]
