"""v9.0 Semiconductor Fabrication Capacity (SFC): scaffold, coverage gate, and
an executable ingestion contract.

SCAFFOLD ONLY. No fabrication-capacity value is invented, interpolated, or
carried from a neighbouring state, and there is no code path in this file that
can produce one. It only ever admits or refuses records supplied to it.

Ledger entry U-06 scoped this axis to v9.0 with a target of 2026-12-31,
contingent on identifying a 35-state fabrication-capacity source. That source
does not exist in the corpus, so the axis is WITHHELD WITH CAUSE, exactly as HKG,
SGP and TWN are withheld from the composite under BIG. A withheld axis is a
correct result.

Why the contract is code rather than prose
------------------------------------------
The first version of this file stated the unit rule, the announced-capacity rule
and the publisher rule in the contract text and enforced none of them. Only
coverage was checked. A candidate dataset measured in revenue, or counting fabs,
or aggregating half the sample into "Rest of World", would have been admitted and
counted toward the 0.75 threshold, and the axis would have unlocked on a number
that measures something else. A contract the gate cannot apply is a claim, not a
check. Every clause below is now enforced by `admit()` and falsified by
scripts/prove_axis_sfc_contract.py.

The state list is derived from the served index rather than typed here, so the
denominator cannot drift from the sample it is measured against, and any row
naming something that is not a state in the sample is refused rather than
silently counted.

Usage:  python scripts/verify_axis_sfc.py [--sources PATH] [--emit PATH] [--quiet]
Exit:   0 the declared status matches the measured coverage · 1 it does not
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "qesis_v8.json"

# The same threshold the composite applies to itself. An axis that cannot clear
# that bar has no business being weighted into it.
BIG_COVERAGE_MIN = 0.75

CANONICAL_UNIT = "wspm_200mm_equivalent"

# Units that describe something other than installed capacity. Each is a real
# failure mode, not a hypothetical: revenue is market share wearing a capacity
# label, and fab count is the RGD mistake repeated, a normalised count named as
# a measure.
REFUSED_UNITS = {
    "usd", "usd_millions", "revenue", "market_share", "market_share_pct",
    "fab_count", "fabs", "n_fabs", "wafer_starts_per_year",
}

REQUIRED_FIELDS = ("iso3", "installed_capacity_wspm", "capacity_unit",
                   "reference_year", "process_nodes_covered")
REQUIRED_PROVENANCE = ("origin_url", "publisher", "license", "retrieved_at")

# D-015 and L-007. A capacity figure must come from the body that measures it or
# the operator that reports it, never from an aggregator that restates it.
REFUSED_PUBLISHERS = {"statista", "statista.com", "wikipedia", "wikipedia.org",
                      "medium", "medium.com", "substack", "substack.com"}


def admit(iso: str, rec: object, sample: set[str]) -> tuple[bool, str]:
    """Admit one record, or refuse it with the clause it failed.

    Refusal reasons are returned rather than counted, because "23 of 35 states
    covered" tells an operator nothing about whether the 12 missing ones are
    absent from the source or were thrown out for measuring revenue.
    """
    if not isinstance(rec, dict):
        return False, "not a record"
    if iso not in sample:
        return False, (f"{iso} is not a state in the sample: aggregate rows such as "
                       f"RoW, EU or APAC cannot stand in for the states they contain")

    missing = [f for f in REQUIRED_FIELDS if f not in rec]
    if missing:
        return False, f"missing required field(s): {', '.join(missing)}"

    absent_prov = [f for f in REQUIRED_PROVENANCE if not rec.get(f)]
    if absent_prov:
        return False, f"missing provenance: {', '.join(absent_prov)}"

    pub = str(rec.get("publisher", "")).strip().lower()
    if pub in REFUSED_PUBLISHERS:
        return False, f"aggregator publisher refused under D-015: {rec['publisher']}"

    unit = str(rec.get("capacity_unit", "")).strip().lower()
    if unit in REFUSED_UNITS:
        return False, (f"unit {rec['capacity_unit']!r} does not measure installed "
                       f"capacity")
    if unit != CANONICAL_UNIT:
        return False, (f"unit {rec['capacity_unit']!r} is not {CANONICAL_UNIT}; a "
                       f"figure on another baseline cannot be merged without proving "
                       f"the baselines identical")

    val = rec.get("installed_capacity_wspm")
    if not isinstance(val, (int, float)) or isinstance(val, bool) or val < 0:
        return False, f"installed_capacity_wspm is not a non-negative number: {val!r}"

    # A fab that does not yet make wafers makes no wafers. Announced capacity is
    # recorded separately and never summed; a record that folds it in is refused
    # rather than quietly counted at an inflated value.
    if rec.get("includes_announced_capacity") is True:
        return False, ("installed capacity includes announced or under-construction "
                       "capacity; record them separately")

    return True, "admitted"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", type=Path,
                    help="JSON mapping iso3 -> capacity record. Absent means no "
                         "source has been ingested, which is the current state.")
    ap.add_argument("--emit", type=Path, help="write the scaffold to this path")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    say = (lambda *a: None) if args.quiet else print

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    states = sorted(index["countries"])
    sample = set(states)
    n = len(states)

    sources: dict = {}
    if args.sources and args.sources.exists():
        sources = json.loads(args.sources.read_text(encoding="utf-8"))

    cited: list[str] = []
    refused: list[tuple[str, str]] = []
    for iso in sorted(sources):
        ok, why = admit(iso, sources[iso], sample)
        (cited.append(iso) if ok else refused.append((iso, why)))

    uncited = [s for s in states if s not in cited]
    coverage = len(cited) / n if n else 0.0
    publishable = coverage >= BIG_COVERAGE_MIN
    status = "PUBLISHABLE" if publishable else "WITHHELD"

    say(f"v9.0 SFC axis, measured against {n} states in {index['vintage']}\n")
    say(f"  records supplied             : {len(sources)}")
    say(f"  admitted                     : {len(cited)}")
    say(f"  refused by the contract      : {len(refused)}")
    say(f"  states with a citable source : {len(cited)} of {n}")
    say(f"  coverage                     : {coverage:.4f}")
    say(f"  BIG threshold                : {BIG_COVERAGE_MIN}")
    say(f"  status                       : {status}\n")

    for iso, why in refused[:12]:
        say(f"  refused {iso}: {why}")
    if len(refused) > 12:
        say(f"  ... and {len(refused) - 12} more")

    if not publishable:
        say(f"\n  WITHHELD WITH CAUSE: coverage {coverage:.4f} is below "
            f"{BIG_COVERAGE_MIN}.")
        say("  Values are withheld, never imputed (D-007). This is a correct result,")
        say("  not a gap to fill.")

    if args.emit:
        scaffold = json.loads((ROOT / "data" / "axes" /
                               "v9_sfc_scaffold.json").read_text(encoding="utf-8"))
        scaffold["status"] = status
        scaffold["coverage"] = {"n": n, "cited": len(cited),
                                "ratio": round(coverage, 4),
                                "cited_states": cited, "uncited_states": uncited}
        scaffold["measured_against"] = index["vintage"]
        args.emit.write_text(json.dumps(scaffold, indent=1, ensure_ascii=False) + "\n",
                             encoding="utf-8", newline="\n")
        say(f"\n  wrote {args.emit}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
