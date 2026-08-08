"""The fsQCA equifinality engine: full 2^k truth table and all three solutions.

The v8.5 index publishes a conservative solution only. Conservative minimisation
excludes every logical remainder, which is the most cautious choice and also the
one that hides equifinality: it splits what is really one pathway into several
near-identical terms because it refuses the counterfactuals that would merge
them. The distinct routes a state can take are visible in the intermediate
solution, which is what QCA practice reports and what a policy reader needs.

This produces, from the committed axes and the declared anchors:

  1. calibration of six conditions and the outcome, Ragin direct method
  2. the complete 2^6 = 64 row truth table, observed rows and remainders
  3. the complex solution   (no remainders)
  4. the parsimonious one   (all remainders available)
  5. the intermediate one   (easy counterfactuals only, directional expectations)
  6. per-path consistency, PRI, raw coverage and unique coverage
  7. a necessity pass over all six conditions and their negations

Reads only data/qesis_v8.json. Writes data/fsqca/equifinality_v85.json.
Pure stdlib. Anchors are not re-derived here: they are part of the published
result (see fsqca.calibration.declared_because) and changing them changes the
finding, so they are read from the index and echoed into the output.
"""

import json
import os
from itertools import combinations
from math import exp, log

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "data", "qesis_v8.json")
OUT = os.path.join(REPO, "data", "fsqca", "equifinality_v85.json")

CONDITIONS = ["WSE", "CABLE", "REE", "HYPER", "ESC_inv", "GCI_inv"]
OUTCOME = "HIGH_SOV_VULN"

# Consistency bar and frequency bar, carried from the published model string
# "n=32; freq>=1; incl>=0.80".
INCL_CUT = 0.80
FREQ_CUT = 1
PRI_CONVENTION = 0.75

# Directional expectations for the intermediate solution. Every condition is a
# stress or exposure measure, so its PRESENCE is expected to contribute to high
# sovereignty vulnerability. This is a substantive claim, stated rather than
# assumed silently.
DIRECTIONAL = {c: 1 for c in CONDITIONS}


# --------------------------------------------------------------------------
# calibration
# --------------------------------------------------------------------------

def calibrate(x, x_in, x_cross, x_out):
    """Ragin direct method, two-sided logistic, capped to (0, 1)."""
    if x is None:
        return None
    # log odds of 0.95 is the conventional full-membership target
    target = log(0.95 / 0.05)
    if x >= x_cross:
        span = x_in - x_cross
        dev = (x - x_cross) * (target / span) if span else 0.0
    else:
        span = x_cross - x_out
        dev = (x - x_cross) * (target / span) if span else 0.0
    m = exp(dev) / (1.0 + exp(dev))
    # QCA convention: never exactly 0 or 1, which would make min/max degenerate
    return min(0.999, max(0.001, round(m, 6)))


def build_cases(index):
    fs = index["fsqca"]
    anchors = fs["calibration"]["anchors"]
    excluded = set(fs["sample"]["excluded"])
    cases = {}
    for iso, rec in index["countries"].items():
        if iso in excluded:
            continue
        ax = rec["axes"]
        cond = rec.get("fsqca_conditions", {})
        raw = {
            "WSE": ax.get("WSE"),
            "CABLE": ax.get("CSE"),
            "REE": ax.get("REE"),
            "HYPER": ax.get("ODI"),
            "ESC_inv": cond.get("ESC_inv"),
            "GCI_inv": cond.get("GCI_inv"),
        }
        outcome_raw = rec.get("composite")
        if any(v is None for v in raw.values()) or outcome_raw is None:
            continue
        m = {k: calibrate(v, anchors[k]["x_in"], anchors[k]["x_cross"], anchors[k]["x_out"])
             for k, v in raw.items()}
        m[OUTCOME] = calibrate(outcome_raw, anchors[OUTCOME]["x_in"],
                               anchors[OUTCOME]["x_cross"], anchors[OUTCOME]["x_out"])
        cases[iso] = {"raw": raw, "raw_outcome": outcome_raw, "mem": m}
    return cases, anchors


# --------------------------------------------------------------------------
# set arithmetic
# --------------------------------------------------------------------------

def term_membership(case_mem, term):
    """Membership in a conjunction. term maps condition -> 1 present, 0 absent."""
    vals = []
    for cond, present in term.items():
        v = case_mem[cond]
        vals.append(v if present else 1.0 - v)
    return min(vals) if vals else 1.0


def consistency(xs, ys):
    denom = sum(xs)
    return sum(min(a, b) for a, b in zip(xs, ys)) / denom if denom else 0.0


def pri(xs, ys):
    """Proportional reduction in inconsistency."""
    num = sum(min(a, b) for a, b in zip(xs, ys)) - sum(min(a, b, 1 - b) for a, b in zip(xs, ys))
    den = sum(xs) - sum(min(a, b, 1 - b) for a, b in zip(xs, ys))
    return num / den if den > 0 else 0.0


def raw_coverage(xs, ys):
    denom = sum(ys)
    return sum(min(a, b) for a, b in zip(xs, ys)) / denom if denom else 0.0


# --------------------------------------------------------------------------
# truth table
# --------------------------------------------------------------------------

def truth_table(cases):
    """All 2^k corners with observed cases, consistency and PRI."""
    isos = sorted(cases)
    ys = [cases[i]["mem"][OUTCOME] for i in isos]
    rows = []
    k = len(CONDITIONS)
    for bits in range(2 ** k):
        term = {c: (bits >> j) & 1 for j, c in enumerate(CONDITIONS)}
        xs = [term_membership(cases[i]["mem"], term) for i in isos]
        # A case belongs to the corner where its membership exceeds 0.5.
        members = [isos[i] for i, v in enumerate(xs) if v > 0.5]
        rows.append({
            "bits": bits,
            "config": {c: term[c] for c in CONDITIONS},
            "label": " * ".join((c if term[c] else "~" + c) for c in CONDITIONS),
            "n_cases": len(members),
            "cases": members,
            "consistency": round(consistency(xs, ys), 4),
            "pri": round(pri(xs, ys), 4),
            "raw_coverage": round(raw_coverage(xs, ys), 4),
        })
    return rows, isos, ys


def classify(rows):
    """Split rows into positive, negative and remainder by the published bars."""
    pos, neg, rem = [], [], []
    for r in rows:
        if r["n_cases"] < FREQ_CUT:
            rem.append(r)
        elif r["consistency"] >= INCL_CUT:
            pos.append(r)
        else:
            neg.append(r)
    return pos, neg, rem


# --------------------------------------------------------------------------
# Quine-McCluskey
# --------------------------------------------------------------------------

def _combine(a, b):
    """Combine two implicants differing in exactly one position. '-' is a gap."""
    diff, out = 0, []
    for x, y in zip(a, b):
        if x == y:
            out.append(x)
        else:
            diff += 1
            out.append("-")
        if diff > 1:
            return None
    return "".join(out) if diff == 1 else None


def prime_implicants(minterms):
    """Standard iterative merging until nothing more combines."""
    if not minterms:
        return []
    current = {m: False for m in minterms}
    primes = set()
    while True:
        nxt = {}
        used = {m: False for m in current}
        keys = list(current)
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                c = _combine(keys[i], keys[j])
                if c is not None:
                    nxt[c] = False
                    used[keys[i]] = True
                    used[keys[j]] = True
        for m in keys:
            if not used[m]:
                primes.add(m)
        if not nxt:
            break
        current = nxt
    return sorted(primes)


def covers(prime, minterm):
    return all(p == "-" or p == m for p, m in zip(prime, minterm))


def minimal_cover(primes, minterms):
    """Essential primes first, then a greedy pass on the remainder."""
    remaining = set(minterms)
    chosen = []
    # essential prime implicants
    for m in list(remaining):
        hit = [p for p in primes if covers(p, m)]
        if len(hit) == 1 and hit[0] not in chosen:
            chosen.append(hit[0])
    remaining = {m for m in remaining if not any(covers(p, m) for p in chosen)}
    while remaining:
        best, best_n = None, -1
        for p in primes:
            if p in chosen:
                continue
            n = sum(1 for m in remaining if covers(p, m))
            if n > best_n:
                best, best_n = p, n
        if best is None or best_n <= 0:
            break
        chosen.append(best)
        remaining = {m for m in remaining if not covers(best, m)}
    return chosen


def bits_to_string(config):
    return "".join(str(config[c]) for c in CONDITIONS)


def prime_to_term(prime):
    return {c: int(v) for c, v in zip(CONDITIONS, prime) if v != "-"}


def prime_to_expr(prime):
    parts = [(c if v == "1" else "~" + c) for c, v in zip(CONDITIONS, prime) if v != "-"]
    return " * ".join(parts) if parts else "<empty>"


# --------------------------------------------------------------------------
# solutions
# --------------------------------------------------------------------------

def solve(positives, remainders_allowed, cases, isos, ys, label, easy_only=False):
    """Minimise the positive rows, optionally using remainders as don't-cares."""
    pos_bits = [bits_to_string(r["config"]) for r in positives]
    dontcare = []
    for r in remainders_allowed:
        s = bits_to_string(r["config"])
        if easy_only:
            # An easy counterfactual only flips a condition toward its
            # directional expectation, i.e. adds a present stress condition.
            if not any(r["config"][c] == DIRECTIONAL[c] for c in CONDITIONS):
                continue
        dontcare.append(s)

    primes = prime_implicants(pos_bits + dontcare)
    # Only primes that actually cover an observed positive may enter the cover.
    usable = [p for p in primes if any(covers(p, m) for m in pos_bits)]
    chosen = minimal_cover(usable, pos_bits)

    paths = []
    term_xs = []
    for p in chosen:
        term = prime_to_term(p)
        xs = [term_membership(cases[i]["mem"], term) for i in isos]
        term_xs.append(xs)
        members = [isos[i] for i, v in enumerate(xs) if v > 0.5]
        paths.append({
            "expression": prime_to_expr(p),
            "implicant": p,
            "consistency": round(consistency(xs, ys), 4),
            "pri": round(pri(xs, ys), 4),
            "raw_coverage": round(raw_coverage(xs, ys), 4),
            "cases_above_0.5": members,
            "n_cases": len(members),
        })

    # Solution-level figures from the union of the chosen terms.
    if term_xs:
        sol_xs = [max(t[i] for t in term_xs) for i in range(len(isos))]
        sol_cons = round(consistency(sol_xs, ys), 4)
        sol_cov = round(raw_coverage(sol_xs, ys), 4)
        for idx, path in enumerate(paths):
            others = [t for j, t in enumerate(term_xs) if j != idx]
            if others:
                without = [max(t[i] for t in others) for i in range(len(isos))]
                unique = raw_coverage(sol_xs, ys) - raw_coverage(without, ys)
            else:
                unique = raw_coverage(sol_xs, ys)
            path["unique_coverage"] = round(max(0.0, unique), 4)
            if path["pri"] < PRI_CONVENTION:
                path["pri_flag"] = f"below the {PRI_CONVENTION} working convention"
    else:
        sol_cons = sol_cov = 0.0

    return {
        "type": label,
        "n_pathways": len(paths),
        "solution_consistency": sol_cons,
        "solution_coverage": sol_cov,
        "counterfactuals_used": len(dontcare),
        "pathways": sorted(paths, key=lambda p: -p["raw_coverage"]),
    }


def intermediate_solution(complex_sol, parsimonious, cases, isos, ys):
    """Ragin's intermediate solution: parsimonious, with difficult counterfactuals blocked.

    Directional expectation here is that the PRESENCE of each stress condition
    contributes to the outcome. So for a literal the parsimonious solution
    dropped:

      dropping ~X  assumes rows with X present are also positive. Presence is
                   expected to contribute, so that is an EASY counterfactual and
                   the drop stands.
      dropping  X  assumes rows with X absent are also positive. That runs
                   against the expectation, so it is DIFFICULT and X is added
                   back.

    The result sits between the complex and parsimonious solutions, which is the
    definition of an intermediate solution rather than a third independent one.
    """
    paths, term_xs = [], []
    seen = set()
    for cpath in complex_sol["pathways"]:
        c_imp = cpath["implicant"]
        # the parsimonious prime that covers this complex configuration
        parent = None
        for ppath in parsimonious["pathways"]:
            p_imp = ppath["implicant"]
            if all(p == "-" or p == c for p, c in zip(p_imp, c_imp)):
                parent = p_imp
                break
        if parent is None:
            parent = c_imp
        # add back every PRESENT literal the parsimonious solution dropped
        merged = []
        for j, (p, c) in enumerate(zip(parent, c_imp)):
            if p != "-":
                merged.append(p)
            elif c == "1":  # difficult counterfactual, block it
                merged.append("1")
            else:
                merged.append("-")
        imp = "".join(merged)
        if imp in seen:
            continue
        seen.add(imp)
        term = prime_to_term(imp)
        xs = [term_membership(cases[i]["mem"], term) for i in isos]
        term_xs.append(xs)
        members = [isos[i] for i, v in enumerate(xs) if v > 0.5]
        paths.append({
            "expression": prime_to_expr(imp),
            "implicant": imp,
            "consistency": round(consistency(xs, ys), 4),
            "pri": round(pri(xs, ys), 4),
            "raw_coverage": round(raw_coverage(xs, ys), 4),
            "cases_above_0.5": members,
            "n_cases": len(members),
        })

    if term_xs:
        sol_xs = [max(t[i] for t in term_xs) for i in range(len(isos))]
        sol_cons = round(consistency(sol_xs, ys), 4)
        sol_cov = round(raw_coverage(sol_xs, ys), 4)
        for idx, path in enumerate(paths):
            others = [t for j, t in enumerate(term_xs) if j != idx]
            if others:
                without = [max(t[i] for t in others) for i in range(len(isos))]
                unique = raw_coverage(sol_xs, ys) - raw_coverage(without, ys)
            else:
                unique = raw_coverage(sol_xs, ys)
            path["unique_coverage"] = round(max(0.0, unique), 4)
            if path["pri"] < PRI_CONVENTION:
                path["pri_flag"] = f"below the {PRI_CONVENTION} working convention"
    else:
        sol_cons = sol_cov = 0.0

    return {
        "type": "intermediate",
        "n_pathways": len(paths),
        "solution_consistency": sol_cons,
        "solution_coverage": sol_cov,
        "directional_expectations": {c: "presence contributes" for c in CONDITIONS},
        "pathways": sorted(paths, key=lambda p: -p["raw_coverage"]),
    }


def necessity(cases, isos, ys):
    out = []
    for c in CONDITIONS:
        for present in (1, 0):
            xs = [cases[i]["mem"][c] if present else 1 - cases[i]["mem"][c] for i in isos]
            # Necessity reverses the ratio: sum(min)/sum(Y)
            cons_n = sum(min(a, b) for a, b in zip(xs, ys)) / sum(ys)
            cov_n = sum(min(a, b) for a, b in zip(xs, ys)) / sum(xs)
            # Relevance of necessity guards against a near-constant condition.
            ron = sum(1 - a for a in xs) / sum(1 - min(a, b) for a, b in zip(xs, ys))
            out.append({
                "condition": ("~" if not present else "") + c,
                "consistency_N": round(cons_n, 4),
                "coverage_N": round(cov_n, 4),
                "RoN": round(ron, 4),
                "publishable": bool(cons_n >= 0.90 and ron >= 0.60),
            })
    return sorted(out, key=lambda r: -r["consistency_N"])


def main():
    index = json.load(open(INDEX, encoding="utf-8"))
    cases, anchors = build_cases(index)
    rows, isos, ys = truth_table(cases)
    pos, neg, rem = classify(rows)

    print(f"cases {len(isos)}  truth-table rows {len(rows)}  "
          f"positive {len(pos)}  negative {len(neg)}  remainders {len(rem)}")

    complex_sol = solve(pos, [], cases, isos, ys, "complex_conservative")
    parsimonious = solve(pos, rem, cases, isos, ys, "parsimonious")
    intermediate = intermediate_solution(complex_sol, parsimonious, cases, isos, ys)

    for s in (complex_sol, parsimonious, intermediate):
        print(f"  {s['type']:22s} paths={s['n_pathways']:2d}  "
              f"cons={s['solution_consistency']:.4f}  cov={s['solution_coverage']:.4f}")

    result = {
        "generated_by": "scripts/fsqca_equifinality.py",
        "vintage": index.get("vintage"),
        "model": f"{', '.join(CONDITIONS)} -> {OUTCOME}",
        "bars": {"consistency": INCL_CUT, "frequency": FREQ_CUT,
                 "pri_convention": PRI_CONVENTION},
        "calibration": {"method": "Ragin direct, two-sided logistic",
                        "anchors": anchors,
                        "note": index["fsqca"]["calibration"]["declared_because"]},
        "sample": {"n": len(isos), "cases": isos,
                   "excluded": index["fsqca"]["sample"]["excluded"]},
        "truth_table": {
            "k": len(CONDITIONS), "rows": 2 ** len(CONDITIONS),
            "observed_rows": len(pos) + len(neg),
            "positive_rows": len(pos), "negative_rows": len(neg),
            "remainder_rows": len(rem),
            "limited_diversity": round(len(rem) / 2 ** len(CONDITIONS), 4),
            "all_rows": rows,
        },
        "solutions": {
            "complex": complex_sol,
            "parsimonious": parsimonious,
            "intermediate": intermediate,
        },
        "necessity": necessity(cases, isos, ys),
        "case_memberships": {
            i: {**cases[i]["mem"], "composite_raw": cases[i]["raw_outcome"]} for i in isos
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(result, open(OUT, "w", encoding="utf-8"), indent=2)
    print(f"wrote {OUT}")
    return result


if __name__ == "__main__":
    main()
