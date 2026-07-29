"""Verify the serverless ASGI entry constructs and answers a real MCP call.

Vercel cannot be tested from here, but the failure modes that actually bite are
local and checkable: the entry not importing, the app not being ASGI, the
transport being session-bound so a serverless invocation cannot answer, and the
tool list coming back empty. This drives the app in-process over ASGI.

Usage:  python scripts/test_http.py
"""
from __future__ import annotations

import asyncio
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


async def call(app, payload: dict) -> tuple[int, dict, bytes]:
    """Minimal ASGI client: one JSON-RPC POST to /mcp."""
    body = json.dumps(payload).encode()
    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.1"},
        "http_version": "1.1", "method": "POST", "scheme": "https",
        "path": "/mcp", "raw_path": b"/mcp", "query_string": b"",
        "root_path": "", "server": ("qesis-mcp.vercel.app", 443),
        "client": ("127.0.0.1", 0),
        "headers": [
            (b"host", b"qesis-mcp.vercel.app"),
            (b"content-type", b"application/json"),
            (b"accept", b"application/json, text/event-stream"),
            (b"content-length", str(len(body)).encode()),
        ],
    }
    sent = {"status": None, "headers": {}, "body": b""}
    done = asyncio.Event()

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            sent["status"] = msg["status"]
            sent["headers"] = {k.decode().lower(): v.decode()
                               for k, v in msg.get("headers", [])}
        elif msg["type"] == "http.response.body":
            sent["body"] += msg.get("body", b"")
            if not msg.get("more_body"):
                done.set()

    await app(scope, receive, send)
    return sent["status"], sent["headers"], sent["body"]


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

    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18",
                       "capabilities": {},
                       "clientInfo": {"name": "smoke", "version": "0"}}}
    status, headers, raw = await call(app, init)
    need(status == 200, f"initialize returned HTTP {status}: {raw[:200]!r}")
    doc = parse(raw)
    srv = (doc.get("result") or {}).get("serverInfo", {})
    need(srv.get("name") == "qesis_mcp",
         f"initialize did not identify the server: {str(doc)[:200]}")
    print(f"  initialize: HTTP {status}, server {srv.get('name')} "
          f"{srv.get('version', '')}".rstrip())

    status, _, raw = await call(app, {"jsonrpc": "2.0", "id": 2,
                                      "method": "tools/list", "params": {}})
    doc = parse(raw)
    tools = [t["name"] for t in (doc.get("result") or {}).get("tools", [])]
    need(status == 200, f"tools/list returned HTTP {status}")
    need(len(tools) >= 8, f"expected 8 tools over HTTP, got {len(tools)}: {tools}")
    print(f"  tools/list: {len(tools)} tools")

    status, _, raw = await call(app, {
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "qesis_get_integrity", "arguments": {}}})
    doc = parse(raw)
    content = (doc.get("result") or {}).get("content") or []
    text = content[0].get("text", "") if content else str(doc)[:300]
    need("vintage" in text, f"qesis_get_integrity returned no vintage: {text[:200]}")
    if "vintage" in text:
        payload = json.loads(text.split("\n\n[DEMO")[0])
        ok = payload["self_check"]["composites_reproducing_from_axes"]
        need(ok, "served index reports composite drift over HTTP")
        print(f"  tools/call qesis_get_integrity: {payload['vintage']}, "
              f"{payload['self_check']['ranked']} ranked, "
              f"{payload['self_check']['withheld_epis']} EPIS, "
              f"reproducing={ok}")
    return report()


def report() -> int:
    if fails:
        print("\nHTTP ENTRY FAILED:", file=sys.stderr)
        for f in fails:
            print(f"  x {f}", file=sys.stderr)
        return 1
    print("\nserverless entry is sound: ASGI app answers MCP over HTTP, stateless.")
    return 0


if __name__ == "__main__":
    print("serverless ASGI entry test (api/index.py)\n")
    raise SystemExit(asyncio.run(main()))
