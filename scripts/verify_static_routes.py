"""Every static route the platform declares resolves to a file it can serve.

Found by measurement on 2026-08-28, not by reading a config file.

`vercel.json` declares eighteen routes. `scripts/test_routes.py` asserts three
of them, the function paths `/health`, `/diag` and `/mcp/_diag`, against the
ASGI app and against the `routes` property the platform actually honours. That
check is correct and it is complete for what it covers. It covers no static
route at all.

The other eight static entries were asserted by nothing, and four of them are
dead in production right now:

    GET https://qesis-mcp.vercel.app/overview    404
    GET https://qesis-mcp.vercel.app/method      404
    GET https://qesis-mcp.vercel.app/console     404
    GET https://qesis-mcp.vercel.app/dashboard   404

The cause is a moved file, not a bad route. Vercel serves this project's static
assets from `public/`, which the same probe run establishes:
`/` returns 15167 bytes, exactly `public/index.html`, and `/blueprint.html`
returns 82582 bytes, exactly `public/blueprint.html`. `overview.html`,
`method.html`, `console.html` and `STIR_Governance_Dashboard.html` are still in
the repository ROOT, where the platform does not look, and their route
declarations have been pointing at nothing since the landing page moved.

Family `surface_added_without_its_control`, occurrence 2. L-191 recorded
occurrence 1: the public domain qesis.eu was a dead end while every gate was
green, because the probe asserted the platform alias instead of the address the
ecosystem gives to people. Same shape, one layer in: a declaration hands out an
address and nothing follows it.

## Why this script is not wired into the required check yet

Arming it today would turn `qesis-integrity` red on `main`, every run, until a
decision is made about four pages, and a gate no correct action can satisfy is
a deadlock wearing the costume of a control (SH-10f, and L-063 before it). The
decision is the operator's under FS-14, because both available remedies are
file moves or public surface changes:

  A. move the four pages into `public/`, restoring the surface
  B. delete the four route entries, retiring the surface deliberately

`ops/FILESYSTEM_REORG_PLAN_2026-08-28.md` carries both with a recommendation.
This script lands now so the remedy has a control waiting for it, and the
wiring into `.github/workflows/qesis-integrity.yml` lands in the same change
set as whichever remedy is signed.

Usage:
    python scripts/verify_static_routes.py            assert the local tree
    python scripts/verify_static_routes.py --live     also probe the origin
    python scripts/verify_static_routes.py --selftest the fixtures
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "vercel.json"

#: Vercel serves static assets from this directory for this project. Measured,
#: not assumed: `/` returns the byte count of `public/index.html` and not the
#: byte count of the root `index.html`, which differs from it by 13193 bytes.
SERVED_DIR = "public"

#: A destination under this prefix is answered by the Python function, not by a
#: static file, and `scripts/test_routes.py` owns those.
FUNCTION_DEST = "/api/index"


def static_routes(cfg: dict) -> list[dict]:
    return [r for r in (cfg.get("routes") or [])
            if r.get("dest") and not str(r["dest"]).startswith(FUNCTION_DEST)]


def assess(routes: list[dict], served_files: set[str]) -> list[str]:
    """Pure function over data. No filesystem, no network, so it is testable.

    A static route names a file the platform can serve, or the address it
    publishes is a 404 that no gate will ever see.
    """
    fails = []
    for r in routes:
        dest = str(r["dest"]).lstrip("/")
        if dest not in served_files:
            fails.append(
                f"route {r.get('src')} points at /{dest}, which is not in "
                f"{SERVED_DIR}/. The platform serves {SERVED_DIR}/ and does not "
                f"look in the repository root, so this address returns 404.")
    return fails


def served_files() -> set[str]:
    base = ROOT / SERVED_DIR
    if not base.exists():
        return set()
    return {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()}


def live_probe(origin: str, routes: list[dict]) -> list[str]:
    """The resource, not a proxy for it. D-115, V-1."""
    fails = []
    for r in routes:
        url = origin.rstrip("/") + str(r.get("src"))
        req = urllib.request.Request(
            url, headers={"User-Agent": "qesis-static-route-probe/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                print(f"  OK    {url} -> {resp.status} {len(resp.read())} bytes")
        except urllib.error.HTTPError as e:
            print(f"  FAIL  {url} -> {e.code} {e.reason}")
            fails.append(f"{r.get('src')} returns {e.code} at the origin")
        except OSError as e:
            print(f"  SKIP  {url} -> network unavailable: {e}")
    return fails


def selftest() -> int:
    checks: list[tuple[str, bool]] = []

    def hold(label: str, cond: bool) -> None:
        checks.append((label, bool(cond)))

    served = {"index.html", "blueprint.html"}

    accept = [{"src": "/", "dest": "/index.html"},
              {"src": "/blueprint", "dest": "/blueprint.html"}]
    hold("accepts routes whose destinations are all in the served directory",
         not assess(accept, served))

    refuse = [{"src": "/overview", "dest": "/overview.html"}]
    hold("refuses the live defect exactly as it stands on 2026-08-28",
         len(assess(refuse, served)) == 1)

    hold("refuses every dead route, not only the first",
         len(assess([{"src": "/overview", "dest": "/overview.html"},
                     {"src": "/method", "dest": "/method.html"},
                     {"src": "/console", "dest": "/console.html"},
                     {"src": "/dashboard",
                      "dest": "/STIR_Governance_Dashboard.html"}], served)) == 4)

    hold("an empty served directory refuses rather than passing vacuously",
         len(assess(accept, set())) == 2)

    cfg = {"routes": [{"src": "/health", "dest": "/api/index"},
                      {"src": "/", "dest": "/index.html"}]}
    hold("function routes are not this gate's business and are excluded",
         [r["src"] for r in static_routes(cfg)] == ["/"])

    hold("a config with no routes property yields nothing to assert",
         static_routes({}) == [])

    for label, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    n = sum(1 for _, ok in checks if ok)
    print(f"{n}/{len(checks)} static-route behaviours hold")
    return 0 if n == len(checks) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--live", metavar="ORIGIN", nargs="?",
                    const="https://qesis-mcp.vercel.app",
                    help="probe the origin as well as the tree")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    routes = static_routes(cfg)
    files = served_files()
    print(f"{len(routes)} static route(s) declared, {len(files)} file(s) in "
          f"{SERVED_DIR}/")
    fails = assess(routes, files)
    for r in routes:
        dest = str(r["dest"]).lstrip("/")
        print(f"  {'OK  ' if dest in files else 'DEAD'}  {r.get('src'):32} "
              f"-> /{dest}")

    if args.live:
        print(f"\nOrigin probe against {args.live}")
        fails.extend(live_probe(args.live, routes))

    if fails:
        print("\nSTATIC ROUTE CHECK FAILED")
        for f in fails:
            print("  x", f)
        return 1
    print("\nSTATIC ROUTE CHECK PASSED: every declared address resolves to a "
          "file the platform serves.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
