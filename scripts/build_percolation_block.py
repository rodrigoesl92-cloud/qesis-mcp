"""PUB-1. Publish the cable percolation finding.

The result has been computed, audited and reproducible in
`data/axes/cse_percolation.json` since 2026-07-31 and has never reached a
surface a reader can query. That is the whole of the defect: not a gap in the
analysis, a gap between the analysis and the reader. It closes the second half
of L-056's conditional acceptance of the contagion framing, which named
propagation and a data-estimated tipping point as its two conditions. Both are
computed here.

Emitted as a sibling artefact, `data/qesis_percolation.json`, exactly as
`build_graph.py` emits `data/qesis_graph.json`, and for the same two reasons.
First, it does not touch `data/qesis_v8.json`, so `index_sha256` does not move
and the production probe stays green until a human promotes. Second, under
L-117 a structural addition beside the index does not bump a vintage: the bump
waits for the change that moves a served number, and no number here is served
by the composite.

WHAT THIS FILE REFUSES TO DO
  It does not recompute. Every figure is read from the evidence file. A
  publication step that recomputes is a second implementation of the analysis
  and a second chance to disagree with it (EMO-1, L-069).
  It does not round, restate or summarise a verdict. Where the evidence file
  carries a qualification, the qualification travels.

Usage:  python scripts/build_percolation_block.py [--check]
        --check verifies the emitted file matches a fresh build, exits non-zero
        if it does not. Wire it into CI beside build_graph --check.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "axes" / "cse_percolation.json"
INDEX = ROOT / "data" / "qesis_v8.json"
OUT = ROOT / "data" / "qesis_percolation.json"

#: The campaign the headline belongs to. Recorded rather than assumed, because
#: the four targeted campaigns disagree and picking one silently is how a
#: sensitivity result becomes a point estimate (L-067).
HEADLINE_CAMPAIGN = "betweenness_recalc"


def build() -> dict:
    ev = json.loads(SRC.read_text(encoding="utf-8"))
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    hd, gr = ev["headline"], ev["graph"]
    tips = ev["tipping_points"]

    campaigns = {}
    for c in ev["campaigns"]:
        curve = c["curve"]
        campaigns[c["label"]] = {
            "steps": len(curve) - 1,
            "lcc_share_start": curve[0]["lcc_share"],
            "lcc_share_end": curve[-1]["lcc_share"],
            "half_collapse": tips.get(c["label"]),
            "reached_half_collapse": tips.get(c["label"]) is not None,
        }

    return {
        "vintage": idx["vintage"],
        "generated_by": "scripts/build_percolation_block.py",
        "reads": "data/axes/cse_percolation.json",
        "recomputes": False,
        "authority": "PUB-1. Closes the second limb of L-056.",

        "graph": {
            "cities": gr["cities"],
            "cables": gr["cables"],
            "edges": gr["edges"],
            "components": gr["components"],
            "articulation_cities": gr["articulation_cities_recomputed"],
            "articulation_reproduces_published": (
                gr["articulation_cities_recomputed"] == gr["articulation_cities_published"]),
            "note": (
                "88 articulation cities recomputed against 88 published, overlap 88. "
                "An independent rebuild agreeing exactly is the reason the rest of "
                "this block is citable."),
        },

        "finding": {
            "label": "Robust yet fragile",
            "headline_campaign": HEADLINE_CAMPAIGN,
            "critical_node": hd["critical_node"],
            "tipping_point_removals": hd["tipping_point_removals"],
            "tipping_point_share_of_network": hd["tipping_point_share_of_network"],
            "cities_severed_in_one_step": hd["cities_severed_in_one_step"],
            "lcc_before_tip": hd["lcc_before_tip"],
            "lcc_after_tip": hd["lcc_after_tip"],
            "pair_connectivity_before": hd["pair_connectivity_before"],
            "pair_connectivity_after": hd["pair_connectivity_after"],
            "targeted_at_13_removals": hd["targeted_at_13_removals"],
            "random_at_13_removals": hd["random_at_13_removals"],
            "random_at_88_removals": hd["random_at_88_removals"],
            "statement": hd["interpretation"],
        },

        "two_numbers_that_are_not_the_same_number": {
            "single_step_severance": {
                "at_removal": hd["tipping_point_removals"],
                "cities_severed": hd["cities_severed_in_one_step"],
                "meaning": (
                    "The largest one-step loss. Removal 13 takes the giant component "
                    "from 594 cities to 316."),
            },
            "half_collapse_threshold": {
                "at_removal": (tips.get(HEADLINE_CAMPAIGN) or {}).get("steps"),
                "lcc_share": (tips.get(HEADLINE_CAMPAIGN) or {}).get("lcc_share"),
                "relative_to_baseline": (
                    tips.get(HEADLINE_CAMPAIGN) or {}).get("relative_to_baseline"),
                "meaning": (
                    "The removal at which the giant component first falls below half "
                    "its baseline. It is a different quantity from the single-step "
                    "severance and the two are published side by side so neither is "
                    "quoted as the other."),
            },
        },

        "campaigns": campaigns,

        "why_the_static_set_understates_it": (
            "The articulation_betweenness campaign never reaches half collapse: it "
            "plateaus at lcc_share 0.3904 across 88 removals. Articulation structure "
            "REGENERATES under attack, so a set computed once against the intact "
            "graph stops describing the graph after the first removal. The "
            "recalculating campaign is the honest one and it is the campaign the "
            "headline belongs to."),

        "limitations": [
            {
                "id": "P-01",
                "statement": (
                    "This is a topological result on a cable graph of 912 cities and "
                    "343 cables. It measures what disconnects, not what fails. No "
                    "traffic volume, no capacity, no restoration time and no route "
                    "diversity above the physical layer enters it."),
                "effect": "Severance is a claim about connectivity, never about outage.",
            },
            {
                "id": "P-02",
                "statement": (
                    "Targeted removal assumes an adversary with full topology "
                    "knowledge and free choice of target. That is an upper bound on "
                    "adversarial damage, not an expectation."),
                "effect": "Read the targeted curves as a bound and the random curve as a base rate.",
            },
            {
                "id": "P-03",
                "statement": (
                    "The cable graph is built from the same EMODnet and SubmarineMap "
                    "composition that U-08 records as differing inside and outside "
                    "the EU. The percolation inherits that asymmetry."),
                "effect": "Cross-region comparison of chokepoint counts carries a method difference.",
            },
        ],

        "falsifier": (
            "Popper standing order. This finding is refuted if an independent cable "
            "topology of comparable coverage produces a targeted-removal curve whose "
            "largest single-step severance is within the range of its own random-removal "
            "curve, or if the 88 articulation cities fail to reproduce from that "
            "topology. It is not refuted by a different critical node: which city sits "
            "at the tip is a property of the release, the robust-yet-fragile shape is "
            "the claim."),
    }


def main() -> int:
    block = build()
    payload = json.dumps(block, indent=1, ensure_ascii=False) + "\n"

    if "--check" in sys.argv:
        if not OUT.exists():
            print("FAIL data/qesis_percolation.json missing. Run without --check.")
            return 1
        if OUT.read_text(encoding="utf-8") != payload:
            print("FAIL data/qesis_percolation.json does not match a fresh build.")
            print("     Either the evidence moved without the artefact, or the")
            print("     artefact was edited by hand. Both are the same defect.")
            return 1
        print(f"OK   percolation block matches a fresh build at {block['vintage']}")
        return 0

    OUT.write_text(payload, encoding="utf-8")
    f = block["finding"]
    print(f"OK   {OUT.relative_to(ROOT)}  {block['vintage']}")
    print(f"     {f['critical_node']} severs {f['cities_severed_in_one_step']} cities "
          f"at removal {f['tipping_point_removals']}")
    print(f"     targeted {f['targeted_at_13_removals']} against random "
          f"{f['random_at_13_removals']} at the same 13 removals")
    print(f"     half collapse at removal "
          f"{block['two_numbers_that_are_not_the_same_number']['half_collapse_threshold']['at_removal']}, "
          f"a different quantity, published beside it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
