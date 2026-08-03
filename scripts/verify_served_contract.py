"""G-01, code/data atomicity: does the running code serve the vintage it announces?

v8.4 shipped its data ahead of its code. `_refresh()` in server.py watches the index
file and reloads it on change; the module itself is read once at process start. A
resident MCP host therefore advanced its vintage string to v8.4 and served it without
`chain` or `citation_concordance`, which are the two fields v8.4 exists to add. It
announced a vintage whose contract it implemented in part, on a public endpoint, and
nothing anywhere failed.

Cross-repo atomicity (G-01 as originally written) does not cover this. The index and
the server live in the SAME repository. What was missing is atomicity between the data
plane and the code plane inside one service.

This calls every tool the contract names, in this process, against the committed index,
and fails when a declared field is absent. It runs in CI, which is where the drift has
to be caught: CI always starts a fresh process, so if the check fails there the data has
genuinely moved past the code, and the deploy that would have published the mismatch is
stopped before it happens.

What it cannot do is inspect somebody else's long-lived process. That is what the
`contract` block on qesis_get_integrity is for, and it only works from v8.4 forward:
code written before the contract existed cannot report that it is failing one. This
incident is not repairable in retrospect. The next one is caught.

Usage:  python scripts/verify_served_contract.py [--quiet]
Exit:   0 contract satisfied · 1 a declared field is not served · 2 could not check
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def payload(raw: str) -> dict:
    """Strip the demo-tier footer the tools append and parse what is left."""
    return json.loads(raw.split("\n\n[DEMO TIER]")[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    say = (lambda *a: None) if args.quiet else print

    try:
        import server
    except Exception as exc:                                       # noqa: BLE001
        print(f"CONTRACT CHECK FAILED: server.py does not import: "
              f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    contract = server.DATA.get("served_contract") or {}
    tools = contract.get("tools") or {}
    if not tools:
        print("CONTRACT CHECK FAILED: the index declares no served_contract. A "
              "vintage that promises nothing cannot be checked against what it "
              "serves.", file=sys.stderr)
        return 2

    calls = {
        "qesis_get_integrity": lambda: server.qesis_get_integrity(),
        "qesis_get_methodology": lambda: server.qesis_get_methodology(),
        "qesis_get_country": lambda: server.qesis_get_country(
            server.CountryInput(iso3="DEU")),
    }

    failures: list[str] = []
    checked = 0
    for tool, fields in sorted(tools.items()):
        if tool not in calls:
            failures.append(f"K1 contract names {tool}, which this check cannot call")
            continue
        try:
            got = payload(asyncio.run(calls[tool]()))
        except Exception as exc:                                   # noqa: BLE001
            failures.append(f"K2 {tool} raised {type(exc).__name__}: {exc}")
            continue
        missing = [f for f in fields if f not in got]
        checked += len(fields)
        if missing:
            failures.append(f"K3 {tool} declares {fields} and does not serve {missing}")
        say(f"  {'ok ' if not missing else 'X  '} {tool}: "
            f"{len(fields) - len(missing)}/{len(fields)} declared fields served")

    # Conditional fields appear only in a named state. Checking them against a
    # fully covered country would fail for the right reason at the wrong time.
    for tool, cond in (contract.get("conditional") or {}).items():
        iso = cond.get("probe_iso3")
        fields = cond.get("fields") or []
        if tool != "qesis_get_country" or not iso:
            continue
        try:
            got = payload(asyncio.run(
                server.qesis_get_country(server.CountryInput(iso3=iso))))
        except Exception as exc:                                   # noqa: BLE001
            failures.append(f"K2 {tool}({iso}) raised {type(exc).__name__}: {exc}")
            continue
        missing = [f for f in fields if f not in got]
        checked += len(fields)
        if missing:
            failures.append(f"K4 {tool}({iso}) declares {fields} when "
                            f"{cond.get('when')} and does not serve {missing}")
        say(f"  {'ok ' if not missing else 'X  '} {tool}({iso}), conditional: "
            f"{len(fields) - len(missing)}/{len(fields)} served")

    say(f"\n{checked} declared fields checked against {server.DATA.get('vintage')}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for f in failures:
            print(f"  x {f}", file=sys.stderr)
        print("\nCONTRACT CHECK FAILED: the index announces a vintage this code does "
              "not fully serve. Do not deploy a half-implemented contract.",
              file=sys.stderr)
        return 1
    say("CONTRACT CHECK PASSED: every declared field is served.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:                                       # noqa: BLE001
        print(f"CONTRACT CHECK FAILED: {type(exc).__name__}: {exc}.", file=sys.stderr)
        raise SystemExit(2)
