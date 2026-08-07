"""Drive the ASGI app in-process and assert which public paths are matched.

Vercel forwards the ORIGINAL path, so every public surface needs two halves: a
rewrite in vercel.json and a Starlette route matching that same original path.
Either half alone yields a 404 that looks like a broken deployment. /health had
a handler and no rewrite; /api/health had a rewrite and no handler, and Vercel's
filesystem router owns /api/* and preempts the rewrite anyway.

This checks the half that lives in code, and cross-checks it against the half
that lives in vercel.json, so the two cannot drift apart silently.

Usage:  python scripts/test_routes.py
Exit:   0 every declared public path is routable · 1 one is not
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.index import app  # noqa: E402

# Paths that must answer, and the method they answer to. /mcp is excluded: a
# bare GET on the streamable transport correctly returns 406, which is a
# different contract and is covered by scripts/test_http.py.
PUBLIC = [("/health", "GET"), ("/diag", "GET"), ("/mcp/_diag", "GET")]


async def probe(path: str, method: str) -> int:
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": method, "scheme": "https", "path": path, "raw_path": path.encode(),
        "query_string": b"", "root_path": "", "server": ("www.qesis.eu", 443),
        "client": ("127.0.0.1", 0),
        "headers": [(b"host", b"www.qesis.eu"), (b"accept", b"application/json")],
    }
    status = {"code": None}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            status["code"] = msg["status"]

    await app(scope, receive, send)
    return status["code"]


async def main() -> int:
    failures = []

    for path, method in PUBLIC:
        code = await probe(path, method)
        ok = code is not None and code != 404
        print(f"  {'OK  ' if ok else 'FAIL'}  {method:4} {path:14} -> {code}")
        if not ok:
            failures.append(f"{path} is not routable in the app ({code})")

    # The other half. A route with no rewrite is unreachable in production even
    # though it passes the check above.
    rewrites = {r["source"] for r in
                json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))["rewrites"]}
    print()
    for path, _ in PUBLIC:
        ok = path in rewrites
        print(f"  {'OK  ' if ok else 'FAIL'}  vercel.json rewrite for {path}")
        if not ok:
            failures.append(f"{path} has a route but no vercel.json rewrite, so "
                            f"production cannot reach it")

    if failures:
        print("\nROUTE CHECK FAILED:")
        for f in failures:
            print(f"  x {f}")
        return 1
    print(f"\nROUTE CHECK PASSED: {len(PUBLIC)} public paths have both a matching "
          f"route and a rewrite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
