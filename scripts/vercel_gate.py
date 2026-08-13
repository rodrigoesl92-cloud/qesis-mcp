"""Vercel Ignored Build Step: refuse to build a tree whose gates fail.

Why this exists
---------------
On 2026-08-12 a production deployment went out carrying a landing page three
vintages stale and a dashboard asserting a figure the index could not produce.
Every gate for that already existed and CI ran them. Vercel does not consult
GitHub checks before deploying, and required-status-checks-before-promotion is
not available on the Hobby plan, so the repository was red and the deployment
was green at the same moment.

This closes that gap in code rather than in a dashboard setting, which means it
is versioned, reviewable and cannot be switched off by accident.

The exit codes are Vercel's and they are inverted from intuition
-----------------------------------------------------------------
  exit 1  -> the build CONTINUES
  exit 0  -> the build is IGNORED

So a passing gate set exits 1 and a failing one exits 0. Getting this backwards
would deploy exactly the builds it is meant to stop, so the mapping is asserted
here in one place and never re-derived at a call site.

What "blocked" means, precisely
-------------------------------
A refused build is skipped, not failed. Production keeps serving the last good
deployment. That is the correct failure mode for a public index: an instrument
that cannot verify itself should keep showing the last thing it could verify,
not go dark and not go wrong. The skip is visible in the Vercel dashboard as an
ignored deployment, so it is not silent.

Runs BEFORE install, so only stdlib gates are listed. The suite that needs the
MCP runtime, test_http and test_routes, stays in CI where the dependencies are
installed. Asserted below rather than assumed.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BUILD_CONTINUES = 1
BUILD_IGNORED = 0

GATES = [
    ("verify_index",     ["scripts/verify_index.py", "--json", "data/qesis_v8.json"]),
    ("verify_dashboard", ["scripts/verify_dashboard.py"]),
    ("build_landing",    ["scripts/build_landing.py", "--check"]),
    ("verify_domains",   ["scripts/verify_domains.py"]),
    ("verify_chain",     ["scripts/verify_chain.py"]),
]


def main() -> int:
    print("QESIS+ pre-build gate. exit 1 builds, exit 0 skips (Vercel semantics).")
    failed: list[str] = []
    for name, argv in GATES:
        r = subprocess.run([sys.executable, *argv], cwd=ROOT,
                           capture_output=True, text=True)
        ok = r.returncode == 0
        print(f"  {'OK  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failed.append(name)
            tail = (r.stdout + r.stderr).strip().splitlines()[-6:]
            for line in tail:
                print(f"        {line}")

    if failed:
        print(f"\nBUILD REFUSED: {', '.join(failed)} failed.")
        print("Production keeps the last deployment it could verify. Fix the")
        print("gate, push again, and this step will let the build through.")
        return BUILD_IGNORED

    print("\nall pre-build gates green, building.")
    return BUILD_CONTINUES


if __name__ == "__main__":
    raise SystemExit(main())
