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
# The service identity is declared once, in data/domains.json (L-089).
_HOST = json.loads((ROOT / "data" / "domains.json").read_text(encoding="utf-8"))["test_host"]
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
        "query_string": b"", "root_path": "", "server": (_HOST, 443),
        "client": ("127.0.0.1", 0),
        "headers": [(b"host", _HOST.encode()), (b"accept", b"application/json")],
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

    # The other half. A route with no platform routing entry is unreachable in
    # production even though it passes the check above.
    #
    # This block used to read vercel.json["rewrites"] and it passed for three
    # days while /health returned 404 in production. Two reasons, and both are
    # the same mistake:
    #
    #   1. Vercel's `routes` is the legacy routing property and it is exclusive.
    #      When `routes` is present the platform ignores `rewrites`, `redirects`,
    #      `headers` and `cleanUrls` entirely. `routes` was added by cdd4c2c to
    #      configure the static pages, which silently switched off the rewrites
    #      block that made /health reachable. Then a11f5b4, "restore missing
    #      rewrites key to resolve test_routes.py KeyError", put the key back to
    #      satisfy THIS TEST, in a block the platform does not read.
    #
    #   2. The rewrite pointed /health at /index.html, the static landing page,
    #      not at the Python function that answers it.
    #
    # So the assertion is now made against the property the platform actually
    # honours, and it checks the destination as well as the presence of the key.
    # Reading a config key is not checking the routing. (L-088, and the render
    # contract doctrine: a gate that checks the text of an artefact is not
    # checking the artefact.)
    cfg = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    print()

    inert = [k for k in ("rewrites", "redirects", "headers", "cleanUrls",
                         "trailingSlash") if k in cfg and "routes" in cfg]
    ok = not inert
    print(f"  {'OK  ' if ok else 'FAIL'}  vercel.json declares one routing mechanism")
    if not ok:
        failures.append(
            f"vercel.json carries `routes` together with {inert}. Vercel ignores "
            f"the latter when `routes` is present, so those entries are inert and "
            f"read as configuration that is not applied")

    routes = cfg.get("routes") or []
    FUNCTION_DEST = "/api/index"
    for path, _ in PUBLIC:
        hit = next((r for r in routes if r.get("src") == path), None)
        ok = hit is not None and hit.get("dest") == FUNCTION_DEST
        where = "absent" if hit is None else f"-> {hit.get('dest')}"
        print(f"  {'OK  ' if ok else 'FAIL'}  vercel.json route for {path:14} {where}")
        if hit is None:
            failures.append(f"{path} has an app route but no vercel.json `routes` "
                            f"entry, so production cannot reach it")
        elif hit.get("dest") != FUNCTION_DEST:
            failures.append(f"{path} routes to {hit.get('dest')}, not to the "
                            f"function at {FUNCTION_DEST}. A path that resolves to "
                            f"a static page is reachable and still wrong: it "
                            f"answers 200 with HTML instead of the handler")

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
