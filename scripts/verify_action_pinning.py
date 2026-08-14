"""SEC-1 gate. Every GitHub Action is pinned to a full-length commit SHA.

A rule held only in prose has been described, not applied (L-054). This is the
control behind the claim `MODELING_LAYERS_MDA.md` section 5(b) once made without
one, while zero actions were pinned.

Why this is an ops gate and not only a security gate: a mutable tag moves under
you. The daily 06:00 integrity run and the two hourly probes all inherit that, so
a green pipeline turns red with no change on your side and the morning protocol
starts by debugging someone else's release.

V-2: one fixture it must refuse and one it must accept, both in test_gate.py.

Usage:  python scripts/verify_action_pinning.py
        python scripts/verify_action_pinning.py --allow-unresolved actions/github-script
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows"

USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.M)
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def scan(allow: set[str]) -> tuple[list[str], list[str], int]:
    pinned: list[str] = []
    unpinned: list[str] = []
    total = 0
    for f in sorted(WF.glob("*.yml")) + sorted(WF.glob("*.yaml")):
        for m in USES.finditer(f.read_text(encoding="utf-8")):
            ref = m.group(1)
            total += 1
            if "@" not in ref:
                unpinned.append(f"{f.name}: {ref} has no ref at all")
                continue
            action, at = ref.rsplit("@", 1)
            # Local (./path) and container (docker://) uses carry no SHA.
            if action.startswith(("./", "docker://")):
                continue
            if SHA40.match(at):
                pinned.append(f"{f.name}: {action}")
            elif action in allow:
                print(f"  ALLOWED (declared unresolved) {f.name}: {ref}")
            else:
                unpinned.append(f"{f.name}: {action}@{at} is a mutable tag")
    return pinned, unpinned, total


def main() -> int:
    allow: set[str] = set()
    if "--allow-unresolved" in sys.argv:
        i = sys.argv.index("--allow-unresolved")
        allow = set(sys.argv[i + 1].split(","))

    if not WF.exists():
        print("no workflows directory, nothing to check")
        return 0

    pinned, unpinned, total = scan(allow)
    print(f"  {len(pinned)} pinned to a 40-char SHA, {len(unpinned)} not, {total} uses: lines")
    if unpinned:
        print("\nSEC-1 FAIL. Resolve each with, and never guess a SHA:")
        print("  gh api repos/<owner>/<repo>/commits/<tag> --jq .sha")
        for u in unpinned:
            print("  FAIL", u)
        return 1
    print("SEC-1 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
