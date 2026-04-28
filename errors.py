from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logger import log


class ToolError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthError(Exception):
    def __init__(self, message: str = "Not authenticated. Visit /auth/login first.") -> None:
        super().__init__(message)
        self.message = message


async def tool_error_handler(request: Request, exc: ToolError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"success": False, "tool": "", "result": {}, "error": exc.message},
    )


async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"success": False, "tool": "", "result": {}, "error": exc.message},
    )


async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled_error method=%s path=%s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "tool": "", "result": {}, "error": "Internal server error"},
    )
