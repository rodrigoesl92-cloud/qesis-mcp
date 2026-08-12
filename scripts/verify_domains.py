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

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = json.loads((ROOT / "data" / "domains.json").read_text(encoding="utf-8"))

DECLARED = set(DOMAINS["canonical"]) | set(DOMAINS["vercel"]) | set(DOMAINS["local"])
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
                for f in p.rglob(pat):
                    if any(s in f.parts for s in SKIP_DIRS):
                        continue
                    if f.name in SKIP_FILES:
                        continue
                    yield f


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


if __name__ == "__main__":
    raise SystemExit(main())
