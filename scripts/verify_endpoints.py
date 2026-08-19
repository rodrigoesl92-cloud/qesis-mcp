"""Every outbound MCP endpoint literal is declared in data/endpoints.json.

The sibling of verify_domains.py. That gate binds the identity this service
answers on; this one binds the addresses it dials. Same failure family, L-089:
one value typed in several places, nothing asserting the copies agree, and the
drift invisible until a client connects to a process that is not there.

The horizon endpoint reached three copies before this gate existed. Two were
`local_endpoint = "http://127.0.0.1:8000/sse"` in infrastructure_mcp.py and
test_client.py. The third was an untracked file at the repository root, and it
was the only copy carrying the operator instruction that the port moves between
runs. A prior session listed that file as litter without reading it, so the
instruction was discarded and the two stale literals were kept.

A declaration is not a fix on its own: the literal can always be typed again
next to it. This gate is what makes the declaration binding.

Usage:  python scripts/verify_endpoints.py [--root DIR] [--quiet]
Exit:   0 every literal is declared, 1 an undeclared literal exists
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))

# Broad on purpose. It must catch an endpoint nobody thought to declare, which
# is the whole failure mode; narrowing it to known ports would make the gate
# agree with the defect. Matches a transport URL carrying an MCP stream path,
# and any loopback authority with an explicit port.
PATTERN = re.compile(
    r"""(?P<url>https?://[^\s"'`]+/(?:sse|mcp)\b)"""
    r"""|(?P<loop>https?://(?:127\.0\.0\.1|localhost|0\.0\.0\.0):\d+[^\s"'`]*)""")

SEARCH = ("*.py", "*.ts", "*.yml", "*.yaml")
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "Digital Twin R&D",
             "data", "var", ".venv", "venv", "dist", "build"}
# The declaration holds the values by definition. The reader is allowed to name
# the declaration's path. The gate carries the pattern that matches them.
SKIP_FILES = {"endpoints.json", "qesis_endpoints.py", "verify_endpoints.py"}


def declared(root: Path) -> tuple[set[str], set[str]]:
    """Return the declared URLs and the declared environment variable names."""
    spec = json.loads((root / "data" / "endpoints.json").read_text(
        encoding="utf-8"))["endpoints"]
    return ({e["default"] for e in spec.values()},
            {e["env"] for e in spec.values()})


def files(root: Path):
    from _walk import iter_files
    # Shared walker, same reason as verify_domains: pruning during traversal,
    # never filtering after it (L-131, L-138).
    yield from iter_files(root, tuple(SEARCH), SKIP_DIRS, SKIP_FILES)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    # --root exists so the mutation self-test can point the gate at a fixture
    # tree. A gate with no way to be aimed at a known-bad input cannot be shown
    # to refuse anything, and V-2 requires that demonstration.
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()

    try:
        urls, envs = declared(root)
    except FileNotFoundError:
        print("E1.0 ENDPOINT CHECK FAILED: data/endpoints.json is absent. The "
              "declaration is the control; without it every literal is undeclared.")
        return 1

    undeclared: list[str] = []
    for f in files(root):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in PATTERN.finditer(line):
                hit = m.group("url") or m.group("loop")
                if hit in urls:
                    # Declared value, but retyped rather than resolved. That is
                    # the defect this gate exists for: agreement today, drift
                    # tomorrow, and no reader of the declaration.
                    undeclared.append(
                        f"E1.1 {f.relative_to(root)}:{n}: {hit} (declared, but "
                        f"written here instead of resolved)")
                else:
                    undeclared.append(
                        f"E1.2 {f.relative_to(root)}:{n}: {hit} (not declared)")

    if not a.quiet:
        print(f"declared endpoints: {sorted(urls)}")
        print(f"declared variables: {sorted(envs)}")

    if undeclared:
        print("\nENDPOINT CHECK FAILED: literals not resolved through "
              "data/endpoints.json")
        for u in sorted(undeclared):
            print(f"  x {u}")
        print("\nDeclare the endpoint in data/endpoints.json and read it with "
              "qesis_endpoints.resolve(). A literal beside a declaration is how "
              "the horizon endpoint reached three copies, one of which was the "
              "only one carrying the operator instruction.")
        return 1

    if not a.quiet:
        print("\nENDPOINT CHECK PASSED: every outbound endpoint literal resolves "
              "to the single declaration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
