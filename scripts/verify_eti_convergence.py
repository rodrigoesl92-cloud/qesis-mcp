#!/usr/bin/env python3
"""Convergent validity check: QESIS+ ESE against WEF ETI 2026 system performance.

WHAT THIS IS AND WHAT IT IS NOT
-------------------------------
This is an EXTERNAL BENCHMARK, not an input. ETI 2026 is itself a weighted
composite over 44 indicators. Feeding it into the QESIS+ composite would be a
composite on a composite and would defeat the derivation doctrine that R1.24
exists to enforce. Nothing here writes to any axis or to the composite.

It is also NOT an fsQCA outcome. D-110 requires an outcome calibrated from a
source outside the index, with observed outage or incident history as the
candidate. ETI is another weighted composite, and ESE already consumes World
Bank SAIDI (outage duration), so an energy-security outcome would share inputs
with the conditions. This file is deliberately named `convergence`, not
`outcome`, so that substitution cannot happen by accident.

THE FALSIFIABLE PREDICTION (Popper standing order)
--------------------------------------------------
ESE is a STRESS axis: high means more electricity stress exposure.
ETI system performance is a PERFORMANCE score: high means a better performing
energy system. Convergent validity therefore predicts a NEGATIVE rank
correlation. The prediction is falsified if Spearman rho is >= 0, or if
|rho| < 0.30, either of which would say the two instruments are not measuring
overlapping ground and that ESE has no external corroboration.

LICENCE
-------
SA-006: WEF material is derived aggregates only. The per-country ETI scores are
read from `var/restricted/eti_2026_scores.json`, which is gitignored and produced locally by
`scripts/eti_extract.py` from a copy of the report the operator holds. The
evidence file this script writes carries coefficients and counts. It carries no
ETI score and no ETI rank, so the source table cannot be reconstructed from it.

Usage
-----
    python scripts/eti_extract.py            # once, produces the local input
    python scripts/verify_eti_convergence.py # writes the evidence file

Exit codes: 0 pass, 1 prediction falsified, 2 input missing (class C, refuse).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETI_LOCAL = os.path.join(REPO_ROOT, "var", "restricted", "eti_2026_scores.json")
INDEX = os.path.join(REPO_ROOT, "data", "qesis_v8.json")
OUT = os.path.join(REPO_ROOT, "data", "axes", "eti_convergence_evidence.json")

RHO_MIN_ABS = 0.30

RESTRICTED_KEYS = ("eti", "system_performance", "transition_readiness", "rank", "scores")


def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _ranks(values: list[float]) -> list[float]:
    """Average ranks, ties shared. Spearman on tied data needs this, not ordinal position."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = shared
        i = j + 1
    return out


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else float("nan")


def _betacf(a: float, b: float, x: float) -> float:
    tiny, eps = 1e-30, 3e-12
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        c = 1.0 + aa / c
        if abs(d) < tiny:
            d = tiny
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        c = 1.0 + aa / c
        if abs(d) < tiny:
            d = tiny
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def _p_two_sided(r: float, n: int) -> float:
    """Two-sided p for a correlation, via the t transform. Stdlib only, no scipy."""
    if n < 3 or not (-1.0 < r < 1.0):
        return float("nan")
    df = n - 2
    t = r * math.sqrt(df / (1.0 - r * r))
    return _betai(df / 2.0, 0.5, df / (df + t * t))


def assert_no_restricted_values(payload: dict) -> None:
    """SA-006 control. The published evidence carries coefficients, never source values."""
    def walk(node, path="") -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if k in RESTRICTED_KEYS and isinstance(v, (int, float, dict, list)):
                    raise SystemExit(
                        "REFUSED: SA-006. The evidence file would carry a restricted WEF "
                        f"value at '{path}/{k}'. Publish coefficients, never the table."
                    )
                walk(v, f"{path}/{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
    walk(payload)


def main() -> int:
    if not os.path.exists(ETI_LOCAL):
        print(
            "REFUSE, class C. The local ETI input is absent and no value may be guessed.\n"
            "Settle it with:\n  python scripts/eti_extract.py",
            file=sys.stderr,
        )
        return 2

    local = json.load(open(ETI_LOCAL, encoding="utf-8"))
    index = json.load(open(INDEX, encoding="utf-8"))

    eti_sp = {k: v["system_performance"] for k, v in local["scores"].items()}
    countries = index["countries"]

    paired, no_ese, absent = [], [], []
    for iso3 in sorted(countries):
        ese = countries[iso3].get("axes", {}).get("ESE")
        if iso3 not in eti_sp:
            absent.append(iso3)
            continue
        if ese is None:
            no_ese.append(iso3)
            continue
        paired.append((iso3, float(ese), float(eti_sp[iso3])))

    n = len(paired)
    xs = [p[1] for p in paired]
    ys = [p[2] for p in paired]
    rho = _pearson(_ranks(xs), _ranks(ys))
    r = _pearson(xs, ys)

    falsified = (rho >= 0.0) or (abs(rho) < RHO_MIN_ABS)

    payload = {
        "id": "ETI_CONVERGENCE",
        "role": "EXTERNAL BENCHMARK. Not an axis, not an input, not an fsQCA outcome.",
        "generated_by": "scripts/verify_eti_convergence.py",
        "index_vintage": index.get("vintage"),
        "index_sha256": _sha256(INDEX),
        "benchmark": {
            "publisher": "World Economic Forum",
            "work": "Energy Transition Index 2026",
            "edition": "16th edition, June 2026, in collaboration with Accenture",
            "instrument": "system performance sub-index, 22 indicators, 60 percent of the ETI",
            "population": "120 countries",
            "licence": "All rights reserved. Derived aggregates only, acquisition register SA-006.",
            "source_file_sha256": local["source"]["sha256"],
        },
        "coverage": {
            "sample_n": len(countries),
            "benchmark_covers": len(eti_sp),
            "ratio": round(len(eti_sp) / len(countries), 4),
            "absent_from_benchmark": sorted(absent),
            "absent_cause": "HKG and TWN are absent from the ETI population. They are two of "
                            "the three states already withheld from the QESIS+ composite under BIG.",
            "paired_n": n,
            "dropped_no_ese": sorted(no_ese),
        },
        "prediction": {
            "statement": "ESE is a stress axis and ETI system performance is a performance score, "
                         "so convergent validity predicts a negative rank correlation.",
            "falsified_if": f"spearman_rho >= 0, or abs(spearman_rho) < {RHO_MIN_ABS}",
            "authority": "Popper standing order, ANALYST mandate",
        },
        "result": {
            "spearman_rho": round(rho, 4),
            "spearman_p_two_sided": round(_p_two_sided(rho, n), 6),
            "pearson_r": round(r, 4),
            "pearson_p_two_sided": round(_p_two_sided(r, n), 6),
            "n": n,
            "verdict": "FALSIFIED" if falsified else "CORROBORATED",
        },
        "what_this_does_not_license": [
            "It does not license using ETI as an input to the composite. ETI is itself a "
            "weighted composite and the QESIS+ composite is derived from published axes at "
            "build time, never carried.",
            "It does not license using ETI as the fsQCA outcome. D-110 KG-4 requires an "
            "outcome from outside the index, and ESE already consumes World Bank SAIDI, so an "
            "energy-security outcome shares inputs with the conditions.",
            "It is a statement about ESE, which is a DIAGNOSTIC axis excluded from the "
            "composite under D-044. It corroborates ESE, not the headline number.",
        ],
    }

    assert_no_restricted_values(payload)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)

    print(f"paired states      {n} of {len(countries)}")
    print(f"absent from ETI    {sorted(absent)}")
    print(f"spearman rho       {rho:+.4f}   p {_p_two_sided(rho, n):.6f}")
    print(f"pearson r          {r:+.4f}   p {_p_two_sided(r, n):.6f}")
    print(f"verdict            {payload['result']['verdict']}")
    print(f"written            {os.path.relpath(OUT, REPO_ROOT)}")
    return 1 if falsified else 0


if __name__ == "__main__":
    sys.exit(main())
