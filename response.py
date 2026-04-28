from app.services.mcp.schemas import ToolResponse


def ok(tool: str, result: dict) -> ToolResponse:
    return ToolResponse(success=True, tool=tool, result=result, error=None)


def err(tool: str, message: str) -> ToolResponse:
    return ToolResponse(success=False, tool=tool, result={}, error=message)
