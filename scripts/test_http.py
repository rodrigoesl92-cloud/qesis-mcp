"""Verify the serverless ASGI entry constructs and answers a real MCP call.

Vercel cannot be tested from here, but the failure modes that actually bite are
local and checkable: the entry not importing, the app not being ASGI, the
transport being session-bound so a serverless invocation cannot answer, the tool
list coming back empty, and -- the one that cost a production window -- the
lifespan not running, which leaves an app that builds, imports, routes, and then
raises `Task group is not initialized` on the first request.

This drives the app in-process over ASGI, through the real lifespan protocol.

Usage:  python scripts/test_http.py
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "api"))

fails: list[str] = []


def need(cond, msg):
    if not cond:
        fails.append(msg)


@contextlib.asynccontextmanager
async def lifespan(app):
    """Run the app's real ASGI lifespan, as a server would.

    Not a convenience. FastMCP's streamable-HTTP app starts its session manager
    here and dispatches every request into the task group it creates, so an entry
    point that loses this is indistinguishable from a healthy one until traffic
    arrives.
    """
    inbound: asyncio.Queue = asyncio.Queue()
    outbound: asyncio.Queue = asyncio.Queue()

    async def receive():
        return await inbound.get()

    async def send(message):
        await outbound.put(message)

    scope = {"type": "lifespan",
             "asgi": {"version": "3.0", "spec_version": "2.0"}}
    task = asyncio.create_task(app(scope, receive, send))
    await inbound.put({"type": "lifespan.startup"})
    started = await asyncio.wait_for(outbound.get(), timeout=20)
    if started["type"] != "lifespan.startup.complete":
        raise RuntimeError(f"lifespan startup failed: {started}")
    try:
        yield
    finally:
        await inbound.put({"type": "lifespan.shutdown"})
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(outbound.get(), timeout=20)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await task


async def request(app, method: str, path: str, body: bytes = b"",
                  accept: str = "application/json, text/event-stream",
                  host: str = "qesis-mcp.vercel.app") -> tuple[int, dict, bytes]:
    """Minimal ASGI client: one request, collected to completion."""
    headers = [(b"host", host.encode()),
               (b"accept", accept.encode()),
               (b"mcp-protocol-version", b"2025-06-18")]
    if body:
        headers += [(b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode())]
    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1", "method": method, "scheme": "https",
        "path": path, "raw_path": path.encode(), "query_string": b"",
        "root_path": "", "server": (host.split(":")[0], 443),
        "client": ("127.0.0.1", 0), "headers": headers,
    }
    sent = {"status": None, "headers": {}, "body": b""}

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            sent["status"] = msg["status"]
            sent["headers"] = {k.decode().lower(): v.decode()
                               for k, v in msg.get("headers", [])}
        elif msg["type"] == "http.response.body":
            sent["body"] += msg.get("body", b"")

    await app(scope, receive, send)
    return sent["status"], sent["headers"], sent["body"]


async def rpc(app, payload: dict, path: str = "/mcp") -> tuple[int, dict]:
    status, _, raw = await request(app, "POST", path, json.dumps(payload).encode())
    return status, parse(raw)


def parse(raw: bytes) -> dict:
    """Accept a plain JSON body or an SSE frame carrying one."""
    text = raw.decode("utf-8", "replace").strip()
    if text.startswith("data:"):
        for line in text.splitlines():
            if line.startswith("data:"):
                text = line[5:].strip()
                break
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_unparsed": text[:400]}


INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "smoke", "version": "0"}}}


async def main() -> int:
    import index as entry                                        # api/index.py

    app = getattr(entry, "app", None)
    need(app is not None, "api/index.py exports no `app`")
    need(callable(app), "`app` is not callable, so it is not an ASGI application")
    if fails:
        return report()

    from server import mcp
    need(mcp.settings.stateless_http,
         "stateless_http is off; a serverless invocation cannot resume a session")

    # ── the lifespan is load-bearing, and this proves the check can fail ──
    # Without startup there is no task group to dispatch into. If this ever
    # stops raising, the assertion below stops meaning anything, so it is
    # asserted rather than assumed.
    try:
        await request(app, "POST", "/mcp", json.dumps(INIT).encode())
    except Exception as exc:                                     # noqa: BLE001
        print(f"  lifespan is load-bearing: without startup, {type(exc).__name__}")
    else:
        fails.append("a request succeeded without the lifespan having run; the "
                     "session manager is no longer started there, so this test no "
                     "longer proves the entry point starts it")

    async with lifespan(app):
        status, headers, raw = await request(app, "POST", "/mcp",
                                             json.dumps(INIT).encode())
        need(status == 200, f"initialize returned HTTP {status}: {raw[:200]!r}")
        doc = parse(raw)
        srv = (doc.get("result") or {}).get("serverInfo", {})
        need(srv.get("name") == "qesis_mcp",
             f"initialize did not identify the server: {str(doc)[:200]}")
        print(f"  initialize: HTTP {status}, server {srv.get('name')} "
              f"{srv.get('version', '')}".rstrip())

        status, doc = await rpc(app, {"jsonrpc": "2.0", "id": 2,
                                      "method": "tools/list", "params": {}})
        tools = sorted(t["name"] for t in (doc.get("result") or {}).get("tools", []))
        need(status == 200, f"tools/list returned HTTP {status}")
        need(len(tools) == 8, f"expected 8 tools over HTTP, got {len(tools)}: {tools}")
        need(all(t.startswith("qesis_") for t in tools),
             f"tool names are not the real qesis_* tools: {tools}")
        print(f"  tools/list: {len(tools)} tools -> {', '.join(tools)}")

        # The Vercel rewrite may forward either path; both must reach the same
        # session manager or the deployment is one routing detail from a 404.
        status, doc = await rpc(app, INIT, path="/api/index")
        need(status == 200, f"/api/index returned HTTP {status}, so a rewritten "
                            f"path would 404 on Vercel")
        need((doc.get("result") or {}).get("serverInfo", {}).get("name") == "qesis_mcp",
             "/api/index did not answer as qesis_mcp")
        print(f"  /api/index alias: HTTP {status}")

        status, doc = await rpc(app, {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "qesis_get_integrity", "arguments": {}}})
        content = (doc.get("result") or {}).get("content") or []
        text = content[0].get("text", "") if content else str(doc)[:300]
        need("vintage" in text, f"qesis_get_integrity returned no vintage: {text[:200]}")
        if "vintage" in text:
            payload = json.loads(text.split("\n\n[DEMO")[0])
            ok = payload["self_check"]["composites_reproducing_from_axes"]
            chain = payload.get("chain") or {}
            need(ok, "served index reports composite drift over HTTP")
            need(chain.get("status") == "VERIFIED",
                 f"chain did not verify at runtime: {chain.get('status')} "
                 f"{chain.get('reason', '')}")
            need(chain.get("entries") == 604,
                 f"chain entries={chain.get('entries')}, expected 604")
            need(chain.get("link_breaks") == 0,
                 f"chain link_breaks={chain.get('link_breaks')}, expected 0")
            need((chain.get("attestation") or {}).get("agrees") is True,
                 "the committed attestation does not agree with the recomputed spine")
            print(f"  tools/call qesis_get_integrity: {payload['vintage']}, "
                  f"{payload['self_check']['ranked']} ranked, "
                  f"{payload['self_check']['withheld_epis']} EPIS, "
                  f"reproducing={ok}")
            print(f"  chain recomputed in-process: {chain.get('entries')} entries, "
                  f"{chain.get('link_breaks')} link breaks, "
                  f"attestation agrees={(chain.get('attestation') or {}).get('agrees')}")

        status, _, raw = await request(app, "GET", "/api/health", accept="application/json")
        health = parse(raw)
        need(status == 200, f"/api/health returned HTTP {status}: {str(health)[:200]}")
        need(health.get("tool_count") == 8,
             f"/api/health reports {health.get('tool_count')} tools")
        need(health.get("chain", {}).get("entries") == 604,
             f"/api/health chain entries={health.get('chain', {}).get('entries')}")
        print(f"  /api/health: HTTP {status}, vintage {health.get('vintage')}, "
              f"index {str(health.get('index_sha256'))[:12]}, "
              f"chain head {str(health.get('chain', {}).get('head_sha256'))[:12]}")

        # The rebinding guard must still refuse a Host it was not told about,
        # otherwise widening the allowlist for www.qesis.eu quietly disabled it.
        status, _, _ = await request(app, "POST", "/mcp", json.dumps(INIT).encode(),
                                     host="evil.example.com")
        need(status in (400, 421, 403),
             f"an unknown Host got HTTP {status}; the DNS-rebinding guard is off")
        print(f"  rebinding guard: unknown Host -> HTTP {status}")

        for allowed in ("www.qesis.eu", "qesis.eu"):
            status, _, _ = await request(app, "POST", "/mcp",
                                         json.dumps(INIT).encode(), host=allowed)
            need(status == 200, f"Host {allowed} got HTTP {status}; production "
                                f"traffic would be refused by the guard")
        print("  rebinding guard: www.qesis.eu and qesis.eu accepted")

    return report()


def report() -> int:
    if fails:
        print("\nHTTP ENTRY FAILED:", file=sys.stderr)
        for f in fails:
            print(f"  x {f}", file=sys.stderr)
        return 1
    print("\nserverless entry is sound: ASGI app answers MCP over HTTP, stateless, "
          "lifespan started, chain recomputed.")
    return 0


if __name__ == "__main__":
    print("serverless ASGI entry test (api/index.py)\n")
    raise SystemExit(asyncio.run(main()))
