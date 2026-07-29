"""Vercel serverless entry: QESIS+ as a remote MCP endpoint.

Vercel's Python runtime serves an ASGI application exported as `app`. This
mounts the same FastMCP instance the local stdio server uses, so there is one
tool implementation and no second port to keep in sync.

Endpoint:  https://qesis-mcp.vercel.app/mcp

The lifespan problem
--------------------
FastMCP's streamable-HTTP app answers through a session manager whose task group
is opened by the ASGI lifespan. Serverless hosts frequently never send lifespan
events, and the request then dies with "Task group is not initialized", which is
what happened the first time this was driven in-process.

So the entry supports both hosts. If the platform sends lifespan, Starlette
starts the manager as normal. If it does not, the manager is started lazily on
the first request and held open for the life of the process. Serverless
invocations are single-process and short-lived, so holding it costs nothing and
the alternative is a 500 on every call.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# The function runs with the repository root as cwd but not necessarily on
# sys.path. Resolve from __file__ rather than trusting the working directory.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import mcp  # noqa: E402

_inner = mcp.streamable_http_app()

_lifespan_seen = False
_manager_task: asyncio.Task | None = None
_manager_ready: asyncio.Event | None = None


async def _hold_manager_open() -> None:
    """Keep the session manager's task group alive for this process."""
    async with mcp.session_manager.run():
        assert _manager_ready is not None
        _manager_ready.set()
        await asyncio.Event().wait()          # never completes; process exit ends it


async def app(scope, receive, send):
    global _lifespan_seen, _manager_task, _manager_ready

    if scope["type"] == "lifespan":
        _lifespan_seen = True
        return await _inner(scope, receive, send)

    if not _lifespan_seen:
        if _manager_task is None:
            _manager_ready = asyncio.Event()
            _manager_task = asyncio.create_task(_hold_manager_open())
        assert _manager_ready is not None
        if not _manager_ready.is_set():
            done, _ = await asyncio.wait(
                {asyncio.ensure_future(_manager_ready.wait()), _manager_task},
                return_when=asyncio.FIRST_COMPLETED)
            # Surface a startup failure instead of hanging on a dead task.
            if _manager_task in done:
                _manager_task.result()

    return await _inner(scope, receive, send)
