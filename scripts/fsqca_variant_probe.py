"""Conceptual-independence probe against an externally-derived outcome.

The published fsQCA calibrates HIGH_SOV_VULN from the composite, and the
composite is a weighted sum of four of the six conditions. The index states this
plainly rather than resolving it (fsqca.conceptual_independence_test:
"coherent and it is circular"). Any pathway inherits that limitation.

The percolation gives, for the first time, an outcome computed from a different
dataset: each state's share of the betweenness mass of the 1,489-edge cable
graph. That quantity comes from network position in TeleGeography-derived
topology, not from the QESIS axes. It is not fully independent, because the
CABLE condition is itself cable-derived, but the 2026-07-31 audit established
that betweenness is not a rescaled degree (Pearson 0.584 against cable count).

This re-runs the same minimisation against that outcome and reports how far the
solution deflates. A solution that survives is partly earned. One that collapses
was an artefact of the composite.

Reads data/fsqca/equifinality_v85.json and data/axes/cse_percolation.json.
Writes the probe back into the equifinality file under `variant_outcome_probe`.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fsqca_equifinality import (  # noqa: E402
    CONDITIONS, INCL_CUT, FREQ_CUT, calibrate, term_membership,
    consistency, pri, raw_coverage, prime_implicants, minimal_cover,
    prime_to_term, prime_to_expr, bits_to_string, covers,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EQUI = os.path.join(REPO, "data", "fsqca", "equifinality_v85.json")
PERC = os.path.join(REPO, "data", "axes", "cse_percolation.json")

NAME_TO_ISO = {
    "United Kingdom": "GBR", "United States": "USA", "France": "FRA",
    "Germany": "DEU", "Spain": "ESP", "Netherlands": "NLD", "Belgium": "BEL",
    "Denmark": "DNK", "Sweden": "SWE", "Norway": "NOR", "Finland": "FIN",
    "Poland": "POL", "Italy": "ITA", "Japan": "JPN", "Australia": "AUS",
    "Brazil": "BRA", "Canada": "CAN", "Chile": "CHL", "India": "IND",
    "Indonesia": "IDN", "Israel": "ISR", "Korea, Republic of": "KOR",
    "South Korea": "KOR", "Malaysia": "MYS", "Mexico": "MEX",
    "New Zealand": "NZL", "Qatar": "QAT", "Saudi Arabia": "SAU",
    "South Africa": "ZAF", "United Arab Emirates": "ARE", "Bahrain": "BHR",
    "Austria": "AUT", "Switzerland": "CHE",
}


def country_betweenness(scratch):
    """Sum of landing-city betweenness per state, from the chokepoints sheet."""
    import openpyxl
    wb = openpyxl.load_workbook(
        os.path.join(scratch, "connectivity_L1_full.xlsx"),
        read_only=True, data_only=True)
    ws = wb["chokepoints"]
    rows = ws.iter_rows(values_only=True)
    next(rows)
    agg = {}
    for cid, betw, is_art, name, country, lon, lat, cables in rows:
        iso = NAME_TO_ISO.get(country)
        if iso is None:
            continue
        agg.setdefault(iso, {"betweenness": 0.0, "cities": 0, "articulation": 0})
        agg[iso]["betweenness"] += float(betw or 0.0)
        agg[iso]["cities"] += 1
        agg[iso]["articulation"] += 1 if str(is_art).strip().lower() == "true" else 0
    wb.close()
    return agg


def main():
    scratch = os.environ.get("QESIS_SCRATCH", "")
    equi = json.load(open(EQUI, encoding="utf-8"))
    agg = country_betweenness(scratch)

    isos = [i for i in equi["sample"]["cases"]]
    mem = equi["case_memberships"]

    # Variant outcome: betweenness mass, percentile-anchored on the same 80/50/20
    # rule the published calibration uses, so the comparison is like for like.
    vals = {i: agg.get(i, {}).get("betweenness", 0.0) for i in isos}
    ordered = sorted(vals.values())
    n = len(ordered)

    def pct(p):
        return ordered[min(n - 1, int(round(p * (n - 1))))]

    x_in, x_cross, x_out = pct(0.80), pct(0.50), pct(0.20)
    if not (x_out < x_cross < x_in):
        raise SystemExit("variant outcome anchors are not ordered; probe aborted")

    ys = [calibrate(vals[i], x_in, x_cross, x_out) for i in isos]
    cases = {i: {"mem": {c: mem[i][c] for c in CONDITIONS}} for i in isos}

    # Same truth table, same bars, different outcome.
    pos = []
    for bits in range(2 ** len(CONDITIONS)):
        term = {c: (bits >> j) & 1 for j, c in enumerate(CONDITIONS)}
        xs = [term_membership(cases[i]["mem"], term) for i in isos]
        members = [isos[k] for k, v in enumerate(xs) if v > 0.5]
        if len(members) >= FREQ_CUT and consistency(xs, ys) >= INCL_CUT:
            pos.append({"config": term, "bits": bits})

    pos_bits = [bits_to_string(r["config"]) for r in pos]
    primes = prime_implicants(pos_bits)
    usable = [p for p in primes if any(covers(p, m) for m in pos_bits)]
    chosen = minimal_cover(usable, pos_bits)

    paths, term_xs = [], []
    for p in chosen:
        term = prime_to_term(p)
        xs = [term_membership(cases[i]["mem"], term) for i in isos]
        term_xs.append(xs)
        paths.append({
            "expression": prime_to_expr(p),
            "consistency": round(consistency(xs, ys), 4),
            "pri": round(pri(xs, ys), 4),
            "raw_coverage": round(raw_coverage(xs, ys), 4),
            "cases_above_0.5": [isos[k] for k, v in enumerate(xs) if v > 0.5],
        })

    if term_xs:
        sol_xs = [max(t[i] for t in term_xs) for i in range(len(isos))]
        sol_cons = round(consistency(sol_xs, ys), 4)
        sol_cov = round(raw_coverage(sol_xs, ys), 4)
    else:
        sol_cons = sol_cov = 0.0

    published = equi["solutions"]["complex"]["solution_consistency"]
    deflation = round(published - sol_cons, 4)

    # Which published pathways survive against the external outcome?
    survivors = []
    for path in equi["solutions"]["intermediate"]["pathways"]:
        imp = path["implicant"]
        term = prime_to_term(imp)
        xs = [term_membership(cases[i]["mem"], term) for i in isos]
        c = round(consistency(xs, ys), 4)
        survivors.append({
            "expression": path["expression"],
            "consistency_vs_composite": path["consistency"],
            "consistency_vs_betweenness": c,
            "survives_0.80_bar": c >= INCL_CUT,
            "deflation": round(path["consistency"] - c, 4),
        })

    probe = {
        "generated_by": "scripts/fsqca_variant_probe.py",
        "status": "AD HOC probe, not an established named procedure. Not citable as one.",
        "variant_outcome": "Sum of landing-city betweenness per state, from the 1,489-edge cable graph.",
        "independence_caveat": (
            "Partial, not full. The CABLE condition is cable-derived, so the probe "
            "shares a source with one of six conditions. Betweenness is not a "
            "rescaled degree (Pearson 0.584 against cable count, 2026-07-31 audit), "
            "so the constructs differ even where the source overlaps."),
        "anchors": {"x_in": round(x_in, 6), "x_cross": round(x_cross, 6),
                    "x_out": round(x_out, 6), "rule": "sample percentiles 80/50/20"},
        "states_with_no_landing_cities": [i for i in isos if i not in agg],
        "variant_solution": {
            "n_pathways": len(paths),
            "solution_consistency": sol_cons,
            "solution_coverage": sol_cov,
            "pathways": paths,
        },
        "published_complex_consistency": published,
        "deflation": deflation,
        "pathway_survival": survivors,
    }
    equi["variant_outcome_probe"] = probe
    equi["standing_limitation"] = equi_limitation()
    json.dump(equi, open(EQUI, "w", encoding="utf-8"), indent=2)

    print(f"variant outcome anchors  in={x_in:.5f} cross={x_cross:.5f} out={x_out:.5f}")
    print(f"variant solution         paths={len(paths)} cons={sol_cons} cov={sol_cov}")
    print(f"published complex        cons={published}")
    print(f"deflation                {deflation}")
    print()
    for s in survivors:
        mark = "SURVIVES" if s["survives_0.80_bar"] else "does not survive"
        print(f"  {mark:16s} {s['consistency_vs_composite']:.4f} -> "
              f"{s['consistency_vs_betweenness']:.4f}  {s['expression']}")
    return probe


def equi_limitation():
    return (
        "The outcome of the primary analysis is calibrated from the published "
        "composite, and the composite is a weighted sum of four of the six "
        "conditions (WSE 0.30, CSE 0.30, ODI 0.17, REE 0.15). The pathways are "
        "therefore combinatorial decompositions of the index, not independently "
        "validated causal routes. This is the standing limitation the index "
        "already declares under fsqca.conceptual_independence_test, and it "
        "travels with every pathway published here. The variant-outcome probe "
        "reports how far each pathway deflates against an externally computed "
        "outcome; it narrows the limitation and does not remove it.")


if __name__ == "__main__":
    main()
