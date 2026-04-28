from typing import Any

from pydantic import BaseModel, field_validator

from app.core.security import is_valid_tool_name


class ToolRequest(BaseModel):
    tool: str
    input: dict[str, Any] = {}

    @field_validator("tool")
    @classmethod
    def validate_tool(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("tool name must not be empty")
        if not is_valid_tool_name(v):
            raise ValueError(
                f"invalid tool name '{v}': must start with a letter and contain only letters, digits, and underscores"
            )
        return v


class ToolResponse(BaseModel):
    success: bool
    tool: str
    result: dict[str, Any]
    error: str | None = None
