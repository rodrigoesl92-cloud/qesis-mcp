"""Every domain literal in the ecosystem is declared in data/domains.json.

L-089. The service identity was declared in four places with three different
values. server.py allowed qesis-mcp.vercel.app; test_http.py, verify_production.py
and production-integrity-probe.yml used qesis-public.vercel.app; the hourly probe
in production-probe.yml used a fourth path on a fifth combination. Nothing
asserted they agreed, so each was fixed in isolation and drifted apart, and a
deployment whose build, routes, index and tools were all correct answered HTTP
421 to its own test suite.

A single declaration is not a fix on its own: a literal can always be typed again
next to it. This gate is what makes the declaration binding.

Usage:  python scripts/verify_domains.py
Exit:   0 every literal is declared · 1 an undeclared literal exists
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = json.loads((ROOT / "data" / "domains.json").read_text(encoding="utf-8"))

DECLARED = (set(DOMAINS["canonical"]) | set(DOMAINS["vercel"]) | set(DOMAINS["local"])
            | set(DOMAINS.get("retired") or []))
# `retired` is declared and never canonical: a name this ecosystem used to publish
# stays known, so a historical reference in a test or a comment is not an undeclared
# literal, while no live control asserts an address nobody serves any more (L-191).
DECLARED |= {DOMAINS["serving"], DOMAINS["test_host"]}
DECLARED |= {DOMAINS["probe_base"].replace("https://", "").replace("http://", "")}

# The pattern is deliberately broad: it must catch a domain nobody thought to
# declare, which is the whole failure mode. Narrowing it to known names would
# make the gate agree with the defect.
PATTERN = re.compile(r"\b((?:[a-z0-9-]+\.)+(?:vercel\.app|eu|com|dev))\b")

SEARCH = [
    ("*.py", ["server.py", "api", "scripts", "qesis_mcp"]),
    ("*.yml", [".github/workflows"]),
    ("*.json", ["vercel.json"]),
]
SKIP_FILES = {"domains.json", "verify_domains.py", "settings.local.json"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "Digital Twin R&D", "data"}
# Third-party and documentation hosts are not service identity.
ALLOWLIST = {
    "openapi.vercel.sh", "schemas.vercel.app", "docs.vercel.com",
    "vercel.app", "github.com", "api.github.com", "raw.githubusercontent.com",
    "transparency.entsoe.eu", "ec.europa.eu", "eur-lex.europa.eu",
    "emodnet.ec.europa.eu", "www.emodnet.eu", "openapi.vercel.app",
}


def files():
    for pat, roots in SEARCH:
        for r in roots:
            p = ROOT / r
            if p.is_file():
                yield p
            elif p.is_dir():
                # Shared walker. rglob stats every entry before the skip list can
                # exclude it, so an unreadable subtree killed the gate on a path
                # the skip list existed to avoid (L-131, L-138).
                from _walk import iter_files
                yield from iter_files(p, (pat,), SKIP_DIRS, SKIP_FILES)


def main() -> int:
    undeclared: list[str] = []
    seen: set[str] = set()
    for f in files():
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for hit in PATTERN.findall(line):
                if hit in ALLOWLIST or hit in DECLARED:
                    continue
                # only care about names that look like ours
                if "qesis" not in hit.lower():
                    continue
                key = f"{f.relative_to(ROOT)}:{n}:{hit}"
                if key in seen:
                    continue
                seen.add(key)
                undeclared.append(key)

    print(f"declared identity: {sorted(DECLARED)}")
    print(f"serving: {DOMAINS['serving']} | probe: {DOMAINS['probe_base']} "
          f"| test host: {DOMAINS['test_host']}")
    if undeclared:
        print("\nDOMAIN CHECK FAILED: literals not declared in data/domains.json")
        for u in undeclared:
            print(f"  x {u}")
        print("\nAdd the name to data/domains.json, or read it from there instead "
              "of retyping it. A literal beside a declaration is how the four "
              "copies drifted.")
        return 1
    print("\nDOMAIN CHECK PASSED: every service domain literal resolves to the "
          "single declaration.")
    return 0



def live() -> int:
    """Prove the declared probe target answers with the vintage this repo serves.

    L-094. The first version of this file consolidated four scattered copies of
    a domain into one declaration, and consolidated on the wrong value:
    qesis-mcp.vercel.app, an orphaned Vercel project serving a build from
    2026-08-01. Every consumer agreed with every other consumer, the gate passed,
    and the hourly production probe tested a dead deployment for three days.

    A single source of truth checked only against itself certifies agreement, not
    correctness. This is the check against reality. Network-dependent, so it is
    opt-in and never runs in the pre-build gate, where a transient failure would
    block a deployment for a reason that has nothing to do with the build.
    """
    import urllib.request

    local = json.loads((ROOT / "data" / "qesis_v8.json").read_text(
        encoding="utf-8"))["vintage"]
    url = DOMAINS["probe_base"].rstrip("/") + "/health"
    print(f"declared probe target: {url}")
    print(f"vintage in this repo : {local}")
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            served = json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        print(f"\nLIVE CHECK FAILED: {url} did not answer: "
              f"{exc.__class__.__name__}: {exc}")
        print("The declared probe target is not the deployment. Fix "
              "data/domains.json, not the probe.")
        return 1

    checks = [
        ("vintage", served.get("vintage"), local),
        ("status", served.get("status"), "ok"),
    ]
    bad = [f"{k}: served {s!r}, expected {e!r}" for k, s, e in checks if s != e]
    print(f"vintage served       : {served.get('vintage')}")
    print(f"index_sha256         : {str(served.get('index_sha256'))[:16]}")
    print(f"deployment_commit    : {str(served.get('deployment_commit'))[:12]}")
    ch = served.get("chain") or {}
    print(f"chain                : {ch.get('status')}, {ch.get('entries')} entries, "
          f"{ch.get('link_breaks')} link breaks, agrees={ch.get('attestation_agrees')}")
    print(f"tools                : {served.get('tool_count')}")
    if bad:
        print("\nLIVE CHECK FAILED:")
        for b in bad:
            print(f"  x {b}")
        return 1
    print("\nLIVE CHECK PASSED: the declared probe target serves this vintage.")
    return 0


if __name__ == "__main__":
    if "--live" in sys.argv:
        raise SystemExit(main() or live())
    raise SystemExit(main())
