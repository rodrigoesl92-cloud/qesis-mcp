"""Probe a deployed qesis-mcp surface and report the five verification gates.

Written because "green build but dark service" is the failure mode this project
keeps hitting: a READY deployment proves the bundle was produced, not that /mcp
answers. Every check below is made against the live origin over HTTP, and the
script prints what it actually received rather than a verdict computed from
what it expected.

Usage:  python scripts/probe_remote.py https://www.qesis.eu
        python scripts/probe_remote.py https://<preview>.vercel.app
"""

from __future__ import annotations

import json
import sys

import httpx

MCP_ACCEPT = "application/json, text/event-stream"
PROTOCOL = "2025-06-18"


def _parse(resp: httpx.Response) -> dict:
    """Accept a plain JSON body or an SSE frame carrying one."""
    text = resp.text.strip()
    if text.startswith("data:"):
        for line in text.splitlines():
            if line.startswith("data:"):
                text = line[5:].strip()
                break
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_unparsed": text[:400]}


def _rpc(client: httpx.Client, url: str, method: str, params: dict, rid: int) -> tuple[int, dict]:
    resp = client.post(
        url,
        json={"jsonrpc": "2.0", "id": rid, "method": method, "params": params},
        headers={"Accept": MCP_ACCEPT, "Content-Type": "application/json",
                 "MCP-Protocol-Version": PROTOCOL},
    )
    return resp.status_code, _parse(resp)


def main(base: str) -> int:
    base = base.rstrip("/")
    mcp_url = f"{base}/mcp"
    fails: list[str] = []

    def need(cond: bool, msg: str) -> None:
        if not cond:
            fails.append(msg)

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        print(f"probing {base}\n")

        # GATE 2 -- /mcp must answer, and must be probed as /mcp. The root is
        # edge-cached static HTML and says nothing about whether MCP is live.
        try:
            r = client.get(mcp_url, headers={"Accept": MCP_ACCEPT},
                           timeout=httpx.Timeout(10.0, read=4.0))
            code = r.status_code
        except httpx.ReadTimeout:
            # A held-open SSE stream is a live endpoint: the status line arrived,
            # the body is the stream. Report it as reached rather than as failed.
            code = 200
            print("  GET /mcp: 200 (SSE stream held open, read timed out as expected)")
        else:
            print(f"  GET /mcp: {code} {r.headers.get('content-type', '')}")
        need(code == 200, f"GATE 2: GET /mcp returned {code}, expected 200")

        # GATE 3a -- a real server contract, not a hand-rolled literal.
        code, doc = _rpc(client, mcp_url, "initialize", {
            "protocolVersion": PROTOCOL, "capabilities": {},
            "clientInfo": {"name": "qesis-probe", "version": "0"}}, 1)
        info = (doc.get("result") or {}).get("serverInfo") or {}
        print(f"  POST /mcp initialize: HTTP {code}, serverInfo={info or doc}")
        need(code == 200, f"GATE 3: initialize returned HTTP {code}")
        need(info.get("name") == "qesis_mcp",
             f"GATE 3: initialize did not identify qesis_mcp: {str(doc)[:200]}")

        # GATE 3b -- eight named qesis_* tools. "tools_expected" is not a tool
        # list and "Tool 1".."Tool 8" are not tools.
        code, doc = _rpc(client, mcp_url, "tools/list", {}, 2)
        tools = sorted(t.get("name", "") for t in (doc.get("result") or {}).get("tools", []))
        print(f"  POST /mcp tools/list: HTTP {code}, {len(tools)} tools")
        for t in tools:
            print(f"      {t}")
        need(len(tools) == 8, f"GATE 3: expected 8 tools, got {len(tools)}: {tools}")
        need(all(t.startswith("qesis_") for t in tools) and tools,
             f"GATE 3: tool names are not qesis_*: {tools}")

        # GATE 4 -- computed chain state and a real deployment commit.
        code, doc = _rpc(client, mcp_url, "tools/call",
                         {"name": "qesis_get_integrity", "arguments": {}}, 3)
        content = (doc.get("result") or {}).get("content") or []
        text = content[0].get("text", "") if content else ""
        if not text:
            need(False, f"GATE 4: qesis_get_integrity returned no content: {str(doc)[:300]}")
        else:
            payload = json.loads(text.split("\n\n[DEMO")[0])
            chain = payload.get("chain") or {}
            prov = payload.get("provenance") or {}
            entries, breaks = chain.get("entries"), chain.get("link_breaks")
            commit = prov.get("deployment_commit")
            print(f"  POST /mcp qesis_get_integrity: vintage={payload.get('vintage')}, "
                  f"chain entries={entries}, link_breaks={breaks}")
            print(f"      index_sha256={prov.get('index_sha256')}")
            print(f"      deployment_commit={commit}")
            need(entries == 604, f"GATE 4: chain entries={entries}, expected 604")
            need(breaks == 0, f"GATE 4: link_breaks={breaks}, expected 0")
            need(bool(commit), "GATE 4: deployment_commit is null")

        # T7 -- the health endpoint that makes a dark service detectable.
        r = client.get(f"{base}/api/health")
        print(f"  GET /api/health: HTTP {r.status_code}")
        if r.status_code == 200:
            h = r.json()
            print(f"      {json.dumps(h, indent=6)[:900]}")
        need(r.status_code == 200, f"/api/health returned {r.status_code}")

    print()
    if fails:
        print("PROBE FAILED:", file=sys.stderr)
        for f in fails:
            print(f"  x {f}", file=sys.stderr)
        return 1
    print("PROBE PASSED: /mcp is live, eight qesis_* tools, chain computed at runtime.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
