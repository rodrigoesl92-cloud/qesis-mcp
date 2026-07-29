"""Two-tier substrate coupling, derived rather than carried.

CODEBOOK: rho = C/6 trace-normalised; CR = 1 - S(rho)/ln 6, where C is the
Pearson correlation matrix over the six coupling axes and S is the von Neumann
entropy -sum(lambda_i * ln lambda_i) over its eigenvalues.

The published v8.0 coupling numbers were carried, exactly like the composite
that turned out to be stale. This module recomputes them, and `selftest` checks
the implementation against the published values before anything relies on it.

Pure stdlib: Jacobi rotation for the symmetric eigenproblem, no numpy.
"""
from __future__ import annotations

import math

# Six coupling axes. CRD is excluded, per the canonical two-tier declaration.
COUPLING_AXES = ["WSE", "CSE", "REE", "FPE", "ODI", "ESE"]
CORE_EXCLUDED = ["ARE", "BHR", "IDN", "MYS", "QAT", "SAU"]


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = sum((a - mx) ** 2 for a in xs)
    dy = sum((b - my) ** 2 for b in ys)
    den = math.sqrt(dx * dy)
    return num / den if den else 0.0


def corr_matrix(rows: dict[str, dict[str, float]], axes: list[str]):
    cols = {a: [rows[i][a] for i in sorted(rows)] for a in axes}
    return [[1.0 if a == b else pearson(cols[a], cols[b]) for b in axes] for a in axes]


def jacobi_eigenvalues(m: list[list[float]], iters: int = 100, tol: float = 1e-12):
    """Eigenvalues of a real symmetric matrix by cyclic Jacobi rotation."""
    n = len(m)
    a = [row[:] for row in m]
    for _ in range(iters):
        off = math.sqrt(sum(a[i][j] ** 2 for i in range(n) for j in range(n) if i != j))
        if off < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(a[p][q]) < tol:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = (1.0 if theta >= 0 else -1.0) / (
                    abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
    return sorted((a[i][i] for i in range(n)), reverse=True)


def von_neumann(rho_eigs: list[float]) -> float:
    return -sum(l * math.log(l) for l in rho_eigs if l > 1e-15)


def coupling(rows: dict[str, dict[str, float]], axes: list[str] = None) -> dict:
    """Coupling statistics for one tier."""
    axes = axes or COUPLING_AXES
    k = len(axes)
    C = corr_matrix(rows, axes)
    eigs = jacobi_eigenvalues(C)
    rho_eigs = [max(e, 0.0) / k for e in eigs]          # rho = C/k, trace 1
    S = von_neumann(rho_eigs)
    CR = 1.0 - S / math.log(k)
    frob = math.sqrt(sum(C[i][j] ** 2 for i in range(k) for j in range(k) if i != j))
    return {
        "n": len(rows),
        "CR": round(CR, 3),
        "S_nats": round(S, 3),
        "dominant_eigenmode": round(rho_eigs[0], 3),
        "frobenius": round(frob, 3),
        "matrix": {a: {b: round(C[i][j], 3) for j, b in enumerate(axes)}
                   for i, a in enumerate(axes)},
        "axes": axes,
    }


def selftest(countries: dict) -> tuple[bool, str]:
    """Reproduce the published v8.0 coupling from the v8.0 axes.

    A reimplementation that is not checked against the numbers it replaces is
    exactly the silently divergent port the operating guideline warns about.
    """
    rows = {i: c["axes"] for i, c in countries.items()
            if all(c["axes"].get(a) is not None for a in COUPLING_AXES)}
    g = coupling(rows)
    core = coupling({i: r for i, r in rows.items() if i not in CORE_EXCLUDED})
    lines, ok = [], True
    for label, got, exp_cr, exp_s, exp_n in (
            ("global", g, 0.110, 1.595, 32), ("core", core, 0.163, 1.499, 26)):
        hit = (got["n"] == exp_n and abs(got["CR"] - exp_cr) <= 0.002
               and abs(got["S_nats"] - exp_s) <= 0.003)
        ok &= hit
        lines.append(f"  {'ok ' if hit else 'X  '}{label}: n={got['n']} (exp {exp_n}) "
                     f"CR={got['CR']} (exp {exp_cr}) S={got['S_nats']} (exp {exp_s})")
    return ok, "\n".join(lines)


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    src = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parent.parent / "data" / "qesis_v8.0_superseded.json")
    doc = json.loads(src.read_text(encoding="utf-8"))
    good, report = selftest(doc["countries"])
    print(f"coupling selftest against published v8.0 values ({src.name}):")
    print(report)
    print("\nPASS: implementation reproduces the published coupling." if good
          else "\nFAIL: implementation does not reproduce the published coupling.")
    raise SystemExit(0 if good else 1)
