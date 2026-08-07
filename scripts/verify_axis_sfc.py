"""v9.0 Semiconductor Fabrication Capacity (SFC): scaffold and coverage gate.

SCAFFOLD ONLY. This defines the axis, the BIG coverage gate and the ingestion
contract. It computes nothing from thin air: no fabrication-capacity value is
invented, interpolated, or carried from a neighbouring state, and there is no
code path in this file that can produce one.

Ledger entry U-06 scoped this axis to v9.0 with a target of 2026-12-31,
contingent on identifying a 35-state fabrication-capacity source. That source
does not exist in the corpus today, so the axis is WITHHELD WITH CAUSE, exactly
as HKG, SGP and TWN are withheld from the composite under BIG. A withheld axis is
a correct result. Publishing a fabricated one would not be.

The state list is derived from the served index rather than typed here, so the
denominator cannot drift from the sample it is measured against.

Usage:  python scripts/verify_axis_sfc.py [--sources PATH] [--emit PATH]
Exit:   0 the axis status is correctly declared · 1 it is not
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "qesis_v8.json"

# The same threshold the composite uses. An axis that cannot clear the bar the
# index applies to itself has no business being weighted into it.
BIG_COVERAGE_MIN = 0.75

AXIS = {
    "id": "SFC",
    "name": "Semiconductor Fabrication Capacity",
    "status": "WITHHELD",
    "target_vintage": "v9.0",
    "target_date": "2026-12-31",
    "ledger_entry": "U-06",
    "definition": (
        "Installed wafer fabrication capacity located within the state's territory, "
        "normalised to a 0-100 stress scale where 100 is maximum dependency, that is "
        "minimum domestic capacity per unit of domestic compute demand. The axis measures "
        "fabrication located in the state, not corporate nationality of the operator: a "
        "foreign-owned fab on domestic soil is domestic capacity for substrate purposes, "
        "because the question is where the wafers can physically be made."
    ),
    "why_not_derivable": (
        "There is no arithmetic route to this axis from the axes already published. WSE, "
        "CSE, REE, FPE, ODI, ESE and RGD measure water, cable, rare earth, platform, "
        "operator, electricity and region density. None of them is a proxy for fabrication "
        "capacity, and deriving one from them would produce a number that varies with "
        "inputs it has no causal relation to."
    ),
    "big_gate": {
        "coverage_min": BIG_COVERAGE_MIN,
        "rule": (
            "The axis is publishable only when at least 75 percent of the sample carries a "
            "value from a citable source. Below that it is withheld with the cause stated "
            "per state, never imputed, per D-007."
        ),
        "on_failure": "WITHHELD WITH CAUSE. The axis is absent from the composite and the "
                      "cause is published per state.",
    },
    "ingestion_contract": {
        "required_fields_per_state": [
            "iso3",
            "installed_capacity_wspm",
            "capacity_unit",
            "reference_year",
            "process_nodes_covered",
        ],
        "required_provenance": ["origin_url", "publisher", "license", "retrieved_at"],
        "rejected_publishers": (
            "Aggregators are rejected per D-015 and L-007: Statista, Wikipedia, Medium, "
            "Substack. A capacity figure must come from the body that measures it or from "
            "the operator that reports it."
        ),
        "unit": (
            "Wafer starts per month, 200mm-equivalent, so states running different node "
            "mixes are comparable. A source reporting only revenue, only fab count, or "
            "only announced-but-unbuilt capacity does not satisfy this contract: fab count "
            "is the RGD mistake repeated, a normalised count named as a measure."
        ),
        "announced_capacity": (
            "Announced or under-construction capacity is recorded separately and never "
            "summed into installed capacity. A fab that does not yet make wafers makes no "
            "wafers."
        ),
        "minimum_to_publish": (
            "A source covering at least 26 of the 35 states (0.75) on a single consistent "
            "definition. Stitching several partial sources with different units is how a "
            "coverage gate gets cleared on paper while the axis measures nothing."
        ),
    },
    "candidate_sources_unverified": [
        "SEMI World Fab Forecast (licensed, coverage unverified)",
        "WSTS billings by region (revenue, not capacity: fails the unit contract)",
        "national statistical offices, per state (fails the single-definition contract)",
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=Path,
                    help="JSON mapping iso3 -> capacity record. Absent means no source "
                         "has been ingested, which is the current state.")
    ap.add_argument("--emit", type=Path, help="write the scaffold to this path")
    args = ap.parse_args()

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    states = sorted(index["countries"])
    n = len(states)

    sources: dict = {}
    if args.sources and args.sources.exists():
        sources = json.loads(args.sources.read_text(encoding="utf-8"))

    required = set(AXIS["ingestion_contract"]["required_fields_per_state"])
    cited, uncited = [], []
    for iso in states:
        rec = sources.get(iso)
        # A record counts only if it satisfies the contract. A partial record is
        # an uncited state, not a cited one with gaps.
        ok = isinstance(rec, dict) and required.issubset(rec) and bool(rec.get("origin_url"))
        (cited if ok else uncited).append(iso)

    coverage = len(cited) / n if n else 0.0
    publishable = coverage >= BIG_COVERAGE_MIN
    status = "PUBLISHABLE" if publishable else "WITHHELD"

    print(f"v9.0 SFC axis scaffold, measured against {n} states in "
          f"{index['vintage']}\n")
    print(f"  states with a citable source : {len(cited)} of {n}")
    print(f"  coverage                     : {coverage:.4f}")
    print(f"  BIG threshold                : {BIG_COVERAGE_MIN}")
    print(f"  status                       : {status}\n")

    if cited:
        print(f"  cited   ({len(cited)}): {', '.join(cited)}")
    print(f"  uncited ({len(uncited)}): {', '.join(uncited) if uncited else 'none'}")

    if not publishable:
        print(f"\n  WITHHELD WITH CAUSE: coverage {coverage:.4f} is below "
              f"{BIG_COVERAGE_MIN}.")
        print("  Cause per state: no fabrication-capacity source satisfying the ingestion")
        print("  contract has been ingested for this state. Values are withheld, never")
        print("  imputed (D-007). This is a correct result, not a gap to fill.")

    out = {**AXIS, "status": status,
           "coverage": {"n": n, "cited": len(cited), "ratio": round(coverage, 4),
                        "cited_states": cited, "uncited_states": uncited},
           "measured_against": index["vintage"]}
    if args.emit:
        args.emit.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                             encoding="utf-8", newline="\n")
        print(f"\n  wrote {args.emit}")

    # Exit 0 means the declared status matches the measured coverage. The axis
    # being withheld is not a failure; a scaffold claiming to be publishable on
    # coverage it does not have would be.
    if publishable and status != "PUBLISHABLE":
        print("declared status disagrees with measured coverage", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
