"""Falsify the SFC ingestion contract: every clause must refuse what it names.

A contract stated in prose is a claim. This makes each clause fail on demand, so
the claim becomes a check. The fixtures below are SYNTHETIC and exist only inside
this process: none is written into data/, none is ever admitted as a real record,
and no fabrication-capacity value produced here describes any actual state. They
are wrong on purpose, which is the point.

The suite also requires a conforming set at exactly the 26-state minimum to be
ADMITTED. A gate that refuses everything is not correct, it is broken in the safe
direction, and only the acceptance case tells the two apart.

Usage:  python scripts/prove_axis_sfc_contract.py
Exit:   0 every clause refuses what it names and admits what conforms · 1 not
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from verify_axis_sfc import (                                      # noqa: E402
    admit, BIG_COVERAGE_MIN, CANONICAL_UNIT)

INDEX = json.loads((ROOT / "data" / "qesis_v8.json").read_text(encoding="utf-8"))
SAMPLE = set(INDEX["countries"])
STATES = sorted(SAMPLE)


def conforming(iso: str) -> dict:
    """A record that satisfies every clause. Values are synthetic placeholders and
    describe nothing: the suite asserts admission, never a magnitude."""
    return {
        "iso3": iso,
        "installed_capacity_wspm": 1000,
        "capacity_unit": CANONICAL_UNIT,
        "reference_year": 2025,
        "process_nodes_covered": ">=180nm,>=40nm",
        "origin_url": "https://example.invalid/fixture",
        "publisher": "SEMI",
        "license": "licensed-slice",
        "retrieved_at": "2026-08-07",
    }


CASES = [
    ("revenue passed off as capacity",
     {**conforming("DEU"), "capacity_unit": "usd_millions"}, "DEU"),
    ("fab count as a measure",
     {**conforming("DEU"), "capacity_unit": "fab_count"}, "DEU"),
    ("market share by revenue",
     {**conforming("DEU"), "capacity_unit": "market_share_pct"}, "DEU"),
    ("a foreign baseline, unproven equivalence",
     {**conforming("DEU"), "capacity_unit": "wspm_300mm"}, "DEU"),
    ("announced capacity folded into installed",
     {**conforming("DEU"), "includes_announced_capacity": True}, "DEU"),
    ("aggregate row standing in for its states",
     conforming("DEU") | {"iso3": "RoW"}, "RoW"),
    ("EU aggregate row",
     conforming("DEU") | {"iso3": "EU"}, "EU"),
    ("aggregator publisher (D-015)",
     {**conforming("DEU"), "publisher": "Statista"}, "DEU"),
    ("missing provenance",
     {k: v for k, v in conforming("DEU").items() if k != "origin_url"}, "DEU"),
    ("missing a required field",
     {k: v for k, v in conforming("DEU").items()
      if k != "installed_capacity_wspm"}, "DEU"),
    ("capacity is not a number",
     {**conforming("DEU"), "installed_capacity_wspm": "lots"}, "DEU"),
    ("negative capacity",
     {**conforming("DEU"), "installed_capacity_wspm": -5}, "DEU"),
]


def main() -> int:
    failures: list[str] = []

    print("clauses that must refuse:\n")
    for name, rec, iso in CASES:
        ok, why = admit(iso, rec, SAMPLE)
        print(f"  {'FAIL' if ok else 'ok  '}  {name}")
        if ok:
            failures.append(f"admitted a record that should be refused: {name}")
        else:
            print(f"          refused: {why}")

    print("\nthe acceptance case, so the gate is not merely refusing everything:\n")
    ok, why = admit("DEU", conforming("DEU"), SAMPLE)
    print(f"  {'ok  ' if ok else 'FAIL'}  a fully conforming record is admitted")
    if not ok:
        failures.append(f"refused a conforming record: {why}")

    # Coverage arithmetic at the boundary. 26 of 35 is 0.7429, which is BELOW
    # 0.75: the stated "minimum 26 states" and the stated ratio disagree, and the
    # ratio governs. Recording it here so the scaffold's own numbers are checked
    # against each other rather than trusted.
    n = len(STATES)
    smallest = next(k for k in range(n + 1) if k / n >= BIG_COVERAGE_MIN)
    declared = json.loads((ROOT / "data" / "axes" / "v9_sfc_scaffold.json")
                          .read_text(encoding="utf-8"))["big_gate"]["minimum_states"]
    print(f"\ncoverage arithmetic on {n} states:")
    print(f"  {smallest - 1}/{n} = {(smallest - 1) / n:.4f}  does not clear "
          f"{BIG_COVERAGE_MIN}")
    print(f"  {smallest}/{n} = {smallest / n:.4f}  clears {BIG_COVERAGE_MIN}")
    print(f"  scaffold declares minimum_states {declared}")
    if declared != smallest:
        print(f"  MISMATCH: {smallest} is required, {declared} is declared.")
        failures.append(
            f"scaffold declares minimum_states {declared} but {smallest} states are "
            f"required to reach coverage {BIG_COVERAGE_MIN} on {n} states")
    else:
        print(f"  ok    the declared count agrees with the ratio it implements")

    # The real axis must still be withheld at zero coverage after all this.
    ok_zero, _ = admit("DEU", None, SAMPLE)
    if ok_zero:
        failures.append("admitted a null record")

    if failures:
        print("\nPROOF FAILED:")
        for f in failures:
            print(f"  x {f}")
        return 1
    print("\nPROOF PASSED: every clause refuses what it names, a conforming record "
          "is admitted, and the coverage arithmetic agrees with itself.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
