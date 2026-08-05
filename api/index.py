"""Serverless entry point: the canonical QESIS+ MCP surface over streamable HTTP.

This file used to answer MCP itself, from literals. `initialize` returned
`{"server": "qesis-mcp", "version": "v8.5", "tools_expected": 8}`, `tools/list`
returned eight objects named "Tool 1".."Tool 8", and `qesis_get_integrity`
returned a fixed `{"status": "intact"}` beside a truncated hash and a vintage
string. None of it touched the index, the spine, or the eight real tools. A
client could not tell that apart from a working server, which is the property
that makes a fabricated attestation worse than an outage: an outage is visible.

There is exactly one implementation of the tools, in `server.py`, and this module
serves it. It adds no MCP behaviour of its own.

WHY THERE IS NO PARENT APPLICATION HERE
    `FastMCP.streamable_http_app()` returns a Starlette app whose lifespan is
    `lambda app: self.session_manager.run()`. That lifespan is not decoration: it
    creates the anyio task group every request is dispatched into. Wrap this app
    inside another Starlette app and the child's lifespan is not run unless it is
    explicitly propagated, and `StreamableHTTPSessionManager._handle_request`
    then raises `RuntimeError: Task group is not initialized` on the first
    request -- a 500 from a deployment that built, routed and imported cleanly.
    The manager also refuses to start twice (`.run() can only be called once per
    instance`), so "just call it again in a parent lifespan" fails the other way.

    Rather than propagate a lifespan correctly and hope it stays correct, this
    module adds its own endpoints through `mcp.custom_route(...)`, which the
    library folds into the same app it builds (they are appended last, so they
    never shadow /mcp). One app, one lifespan, owned by the library that
    requires it. `scripts/test_http.py` drives the real ASGI lifespan protocol
    against this module so the property is tested, not assumed.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from mcp.server.fastmcp.server import StreamableHTTPASGIApp

import server as qesis
from server import mcp

# The operational database. The previous path here was `var/qesis.sqlite`, which
# has never existed in this repository, so the status line read "missing" on
# every deployment including the healthy ones and was therefore worth nothing.
DB_PATH = ROOT / "data" / "sqlite" / "qesis_ops.sqlite"


def _db_status() -> str:
    try:
        return "connected" if DB_PATH.is_file() else f"absent at {DB_PATH.relative_to(ROOT)}"
    except OSError as exc:  # pragma: no cover - stat can fail on a broken mount
        return f"not checked: {type(exc).__name__}"


def _commit() -> str | None:
    return (os.environ.get("VERCEL_GIT_COMMIT_SHA") or "").strip() or None


# ─── endpoints that are not MCP ──────────────────────────────────────────────
# Registered before streamable_http_app() is called, because that is when the
# library reads _custom_starlette_routes.


@mcp.custom_route("/api/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """What this process is serving, computed now.

    G-01b in one endpoint. A READY deployment proves a bundle was produced; it
    does not prove the index loaded, the spine verifies, or the tools registered.
    This project has shipped a green build over a dark service more than once,
    and every time it was found by a human opening a browser. Everything below is
    read or recomputed while answering the request, so a monitor can catch it.

    Answers 501, not 200 with a caveat, when the chain cannot be verified. A
    health endpoint that returns 200 next to the word "UNVERIFIED" gets read as
    green by everything that is not a person.
    """
    qesis._refresh()

    try:
        index_sha256 = hashlib.sha256(qesis.DATA_PATH.read_bytes()).hexdigest()
    except OSError as exc:
        return JSONResponse(
            {"status": "UNSERVICEABLE",
             "reason": f"the index is unreadable at {qesis.DATA_PATH.name}: "
                       f"{type(exc).__name__}",
             "deployment_commit": _commit()},
            status_code=501)

    chain = qesis._chain()
    tools = sorted(t.name for t in await mcp.list_tools())
    verified = chain.get("status") == "VERIFIED"

    body = {
        "status": "ok" if verified else "degraded",
        "service": "qesis-mcp",
        "mcp_endpoint": "/mcp",
        "transport": "streamable-http",
        "vintage": qesis.DATA.get("vintage"),
        "index_sha256": index_sha256,
        "chain": {
            "status": chain.get("status"),
            "entries": chain.get("entries"),
            "link_breaks": chain.get("link_breaks"),
            "head_sha256": chain.get("head_sha256"),
            "attestation_agrees": (chain.get("attestation") or {}).get("agrees"),
        },
        "tools": tools,
        "tool_count": len(tools),
        "licensed": qesis.LICENSED,
        "deployment_commit": _commit(),
        "database": _db_status(),
        "verify": ("git checkout <deployment_commit> && sha256sum data/qesis_v8.json "
                   "must equal index_sha256; python scripts/verify_chain.py must exit 0"),
    }
    if not verified:
        body["reason"] = chain.get("reason") or chain.get("effect") or (
            "the committed spine does not verify on this deployment")
    return JSONResponse(body, status_code=200 if verified else 501)


@mcp.custom_route("/api/telemetry", methods=["POST", "OPTIONS"])
@mcp.custom_route("/api/ingest", methods=["POST", "OPTIONS"])
async def telemetry(request: Request) -> JSONResponse:
    """Compatibility shim for the dashboard's beacon.

    On Vercel this path is served by `api/telemetry.py`, which wins because the
    filesystem router maps /api/telemetry to it directly. This exists so the same
    beacon works when the ASGI app is driven locally or in tests, and so the
    endpoint does not silently disappear from this app's route table.
    """
    if request.method == "OPTIONS":
        return JSONResponse({}, status_code=204)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001 - any malformed body is the same outcome
        body = {}
    return JSONResponse({
        "status": "logged",
        "event": body.get("event", "unknown"),
        "database_status": _db_status(),
    }, headers={"Cache-Control": "no-store"})


@mcp.custom_route("/mcp/_diag", methods=["GET"])
async def route_diagnostic(request: Request) -> JSONResponse:
    """Report which path Vercel actually hands to this ASGI app.

    Vercel rewrites /mcp to /api/index. Whether the function then receives the
    ORIGINAL path or the REWRITTEN one is not something to assume: the Starlette
    route the MCP library installs is an exact match on "/mcp", so guessing wrong
    means a 404 from a deployment that built and imported perfectly. Both paths
    are bound, so the answer does not change what works -- it just makes the
    routing legible instead of folkloric.

    /mcp/_diag is rewritten to the same function. Reaching THIS handler proves
    the original path is forwarded; being answered by the MCP handler instead
    proves the rewritten path is.
    """
    return JSONResponse({
        "asgi_path": request.url.path,
        "forwarded": "original" if request.url.path.startswith("/mcp") else "rewritten",
        "bound_mcp_paths": ["/mcp", "/api/index"],
        "vercel_deployment_url": os.environ.get("VERCEL_URL"),
        "deployment_commit": _commit(),
    })


# ─── the application ─────────────────────────────────────────────────────────

app = mcp.streamable_http_app()

# Vercel's filesystem router maps this file to /api/index, and a rewrite from
# /mcp may forward either the original or the rewritten path depending on how the
# request was routed. The Starlette route the library installs is an exact match
# on "/mcp", so a forwarded "/api/index" would 404 against an otherwise perfect
# deployment. Both paths are bound to the same ASGI handler and the same session
# manager, which removes the guess entirely -- whichever path arrives is served.
_mcp_asgi = StreamableHTTPASGIApp(mcp.session_manager)
app.router.routes.append(Route("/api/index", endpoint=_mcp_asgi, name="mcp_via_api_index"))

# allow_origins=["*"] with allow_credentials=True is rejected by the CORS spec:
# a wildcard origin cannot carry credentials, and browsers drop the response
# rather than honour it. The pair was invalid, so the middleware was doing
# nothing it appeared to do. MCP over HTTP authenticates with headers, not
# cookies, so the wildcard is kept and credentials are turned off.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id", "Mcp-Protocol-Version"],
)
