import time
from typing import Any

from app.core.logger import log
from app.services.mcp.registry import TOOL_REGISTRY
from app.services.mcp.response import err, ok
from app.services.mcp.schemas import ToolResponse


def execute(tool: str, input: dict[str, Any]) -> ToolResponse:
    log.info("tool_call tool=%s input_keys=%s", tool, list(input.keys()))
    t0 = time.perf_counter()

    handler = TOOL_REGISTRY.get(tool)
    if handler is None:
        log.warning("unknown_tool tool=%s available=%s", tool, sorted(TOOL_REGISTRY))
        return err(tool, f"Unknown tool '{tool}'. Available: {sorted(TOOL_REGISTRY)}")

    try:
        result = handler(input)
        log.info("tool_ok tool=%s elapsed_ms=%.1f", tool, (time.perf_counter() - t0) * 1000)
        return ok(tool, result)
    except KeyError as exc:
        log.warning("tool_missing_field tool=%s field=%s", tool, exc)
        return err(tool, f"Missing required field: {exc}")
    except Exception as exc:
        log.exception("tool_error tool=%s elapsed_ms=%.1f", tool, (time.perf_counter() - t0) * 1000)
        return err(tool, str(exc))
