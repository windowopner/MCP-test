from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="MCP Server", version="1.0.0")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ToolRequest(BaseModel):
    tool: str
    input: dict[str, Any] = {}


class ToolResponse(BaseModel):
    tool: str
    result: dict[str, Any]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def handle_echo(input: dict[str, Any]) -> dict[str, Any]:
    return input


def handle_create_doc(input: dict[str, Any]) -> dict[str, Any]:
    # TODO: Replace with real Google Docs API call.
    # from google.oauth2.credentials import Credentials
    # from googleapiclient.discovery import build
    # creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # service = build("docs", "v1", credentials=creds)
    # doc = service.documents().create(body={"title": input.get("title", "Untitled")}).execute()
    # return {"doc_id": doc["documentId"], "status": "created"}
    return {"doc_id": "mock-doc-123", "status": "created"}


# TODO: Add handle_create_slide() for Google Slides API integration.
# TODO: Add handle_list_courses() for Google Classroom API integration.
# TODO: Add handle_send_email() / handle_search_email() for Gmail API integration.
# TODO: Add OAuth token exchange endpoint (POST /auth/callback) for Google OAuth2 flow.

TOOL_REGISTRY: dict[str, Any] = {
    "echo": handle_echo,
    "create_doc": handle_create_doc,
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "mcp-server"}


@app.get("/health")
def health() -> dict[str, bool]:
    return {"healthy": True}


@app.post("/tool/run", response_model=ToolResponse)
def run_tool(request: ToolRequest) -> ToolResponse:
    handler = TOOL_REGISTRY.get(request.tool)
    if handler is None:
        raise HTTPException(
            status_code=400,
            detail={"error": f"Unknown tool '{request.tool}'", "available_tools": list(TOOL_REGISTRY)},
        )
    result = handler(request.input)
    return ToolResponse(tool=request.tool, result=result)
