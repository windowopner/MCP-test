import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, mcp, routes
from app.api import oauth
from app.core.config import APP_VERSION, settings
from app.core.errors import AuthError, ToolError, auth_error_handler, global_error_handler, tool_error_handler
from app.core.logger import log
from app.services.mcp.registry import TOOL_REGISTRY


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_startup()
    log.info("startup_ok version=%s tools=%d", APP_VERSION, len(TOOL_REGISTRY))
    yield


app = FastAPI(title="Google Workspace MCP Server", version=APP_VERSION, docs_url="/docs", redoc_url=None, lifespan=lifespan)

# Required so Claude.ai browser-side OAuth redirects and preflight requests work
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ToolError, tool_error_handler)    # type: ignore[arg-type]
app.add_exception_handler(AuthError, auth_error_handler)    # type: ignore[arg-type]
app.add_exception_handler(Exception, global_error_handler)  # type: ignore[arg-type]

app.include_router(routes.router)
app.include_router(mcp.router)
app.include_router(auth.router)
app.include_router(oauth.router)  # /.well-known/..., /oauth/authorize, /oauth/token, /oauth/register


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), reload=False)
