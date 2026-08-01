"""Integrity gate for the served QESIS+ index.

Reads ONLY the committed data/qesis_v8.json: no OneDrive, no database, no
network. That is deliberate: the gate must run on a clean CI runner in the
cloud, so the machine that builds the index never has to carry the check.

Exit code 0 = publishable. Non-zero = do not deploy.

Usage:  python scripts/verify_index.py [--json PATH] [--quiet]
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOL = 0.051                      # published to 1 decimal
BANNED_CITATIONS = ["Ontological Blind-Spots"]

failures: list[str] = []
warnings: list[str] = []
checks = 0


def check(cond: bool, label: str, detail: str = "") -> bool:
    global checks
    checks += 1
    if not cond:
        failures.append(f"{label}{(': ' + detail) if detail else ''}")
    return cond


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(ROOT / "data" / "qesis_v8.json"))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    d = json.loads(Path(args.json).read_text(encoding="utf-8"))
    C = d["countries"]
    model = d.get("composite_model") or {}
    W = model.get("weights") or {}

    say = (lambda *a: None) if args.quiet else print
    say(f"QESIS+ integrity gate: {d.get('vintage')}, {len(C)} states\n")

    # ── 1. the model must be declared, not implied ──────────────────────
    model_ok = check(bool(W), "R1.1 composite_model.weights declared")
    check(model.get("formula_id"), "R1.2 formula_id declared")
    check(abs(sum(W.values()) - 1.0) < 1e-9 if W else False,
          "R1.3 weights sum to 1", f"sum={sum(W.values()):.4f}" if W else "absent")

    # Without a declared model every downstream check would evaluate over an
    # empty weight set and pass, or fail, vacuously. A gate that reports
    # vacuous results is worse than one that stops, so it stops.
    if not model_ok:
        print("\nFAILED:", file=sys.stderr)
        for f in failures:
            print(f"  x {f}", file=sys.stderr)
        print("\n  x R1.4-R1.14 NOT EVALUATED: no declared composite model to "
              "check against. Fix the model declaration and re-run.", file=sys.stderr)
        print(f"\nGATE FAILED: index declares no composite model. Do not deploy.",
              file=sys.stderr)
        return 2

    # ── 2. every composite recomputes from its own published axes ───────
    #     This is the check whose absence let v8.0 ship.
    drift = []
    for iso, c in C.items():
        ax, comp = c["axes"], c["composite"]
        if comp is None:
            continue
        if any(ax.get(a) is None for a in W):
            drift.append(f"{iso} ranked with missing weighted axis")
            continue
        calc = round(sum(W[a] * ax[a] for a in W), 1)
        if abs(calc - comp) > TOL:
            drift.append(f"{iso} served {comp} vs recomputed {calc} (Δ{comp-calc:+.1f})")
    check(not drift, f"R1.4 all composites reproduce from published axes",
          "; ".join(drift[:6]) + (f" (+{len(drift)-6} more)" if len(drift) > 6 else ""))

    # ── 3. BIG must hold at aggregate level, not only per axis ──────────
    big_bad = []
    for iso, c in C.items():
        cov = sum(w for a, w in W.items() if c["axes"].get(a) is not None)
        gate = d.get("composite_model", {}).get("big_coverage_min", 0.75)
        missing = [a for a in W if c["axes"].get(a) is None]
        if missing and c["composite"] is not None:
            big_bad.append(f"{iso} emits {c['composite']} over missing {missing}")
        if abs(cov - c.get("coverage", cov)) > 1e-6:
            big_bad.append(f"{iso} coverage {c.get('coverage')} != computed {cov:.2f}")
        if c["composite"] is None and c.get("composite_status") != "EPIS":
            big_bad.append(f"{iso} withheld but not marked EPIS")
    check(not big_bad, "R1.5 BIG gate holds at aggregate level", "; ".join(big_bad[:6]))

    # every EPIS state must carry a published finding
    epis_iso = {e["iso3"] for e in d.get("epis_findings", [])}
    withheld = {i for i, c in C.items() if c["composite"] is None}
    check(withheld == epis_iso, "R1.6 every withheld composite has an EPIS finding",
          f"withheld={sorted(withheld)} findings={sorted(epis_iso)}")

    # ── 4. monotonicity: dominance must not invert ──────────────────────
    #     The property that caught the v8.0 defect. Weights are non-negative,
    #     so if A >= B on every weighted axis, comp(A) >= comp(B). Always.
    inversions = []
    # Only states carrying every weighted axis can be compared. A state that is
    # ranked while missing one is a BIG failure, caught above at R1.4 and R1.5;
    # comparing it here would raise on the null instead of reporting it.
    ranked = {i: c for i, c in C.items()
              if c["composite"] is not None
              and all(c["axes"].get(a) is not None for a in W)}
    for a, b in itertools.permutations(ranked, 2):
        A, B = ranked[a], ranked[b]
        if all(A["axes"][x] >= B["axes"][x] for x in W) and \
                A["composite"] < B["composite"] - TOL:
            inversions.append(f"{a}>={b} on all weighted axes but "
                              f"{A['composite']} < {B['composite']}")
    check(not inversions, "R1.7 no dominance inversion", "; ".join(inversions[:4]))

    # ── 5. lineage must identify which generation is being served ───────
    lin = d.get("lineage") or {}
    check(bool(lin.get("sources")), "R1.8 lineage names its sources")
    check(bool(lin.get("generated_at_utc")), "R1.9 lineage carries a build stamp")
    check(lin.get("formula_id") == model.get("formula_id"),
          "R1.10 lineage formula_id matches the model")
    n_ranked = sum(1 for c in C.values() if c["composite"] is not None)
    check(lin.get("n_ranked") == n_ranked, "R1.11 lineage n_ranked is accurate",
          f"stamped {lin.get('n_ranked')} vs actual {n_ranked}")

    # ── 6. coupling exclusions must be named, never silent (gap G5) ─────
    cp = d.get("coupling") or {}
    excl = cp.get("excluded_from_global")
    check(excl is not None, "R1.12 global coupling exclusions are named")
    if excl is not None:
        check(cp.get("global", {}).get("n", 0) + len(excl) == len(C),
              "R1.13 coupling n + exclusions == sample",
              f"{cp.get('global',{}).get('n')} + {len(excl)} != {len(C)}")
        check(sorted(excl) == sorted(withheld),
              "R1.14 coupling exclusions are exactly the flagged states")

    # ── 7. fsQCA conditions must be queryable (gap G2) ──────────────────
    missing_cond = [i for i, c in C.items()
                    if not (c.get("fsqca_conditions") or {}).get("ESC_inv")
                    and not (c.get("fsqca_conditions") or {}).get("GCI_inv")]
    check(len(missing_cond) < len(C), "R1.15 fsQCA conditions exposed",
          f"{len(missing_cond)}/{len(C)} states expose neither ESC_inv nor GCI_inv")

    # ── 8. no superseded citation on a public surface ───────────────────
    blob = json.dumps(d, ensure_ascii=False)
    for bad in BANNED_CITATIONS:
        check(bad not in blob, f"R1.16 superseded citation absent", f"found '{bad}'")

    # ── 9. every withholding states its cause (C-02) ────────────────────
    # The generic string told a reviewer that Singapore and Taiwan are missing
    # for the same reason. They are not: one is a catchment-resolution limit and
    # the other is the source's territorial schema. A single label over two
    # causes is checked once and then distrusted throughout.
    causes = (d.get("withholding_causes") or {}).get("codes") or {}
    bad_cause = []
    for e in d.get("epis_findings", []):
        code = e.get("withholding_cause")
        if not code:
            bad_cause.append(f"{e['iso3']} withheld with no stated cause")
        elif code not in causes:
            bad_cause.append(f"{e['iso3']} cites cause {code} that is not declared")
        if not (e.get("cause_statement") or "").strip():
            bad_cause.append(f"{e['iso3']} has no cause statement")
    check(not bad_cause, "R1.17 every BIG withholding states a declared cause",
          "; ".join(bad_cause[:6]))

    # ── 10. the citation concordance is present and points somewhere ────
    cc = d.get("citation_concordance") or {}
    rows, errata = cc.get("rows") or [], cc.get("errata") or []
    check(bool(rows) and bool(errata),
          "R1.18 citation concordance carries rows and errata",
          f"{len(rows)} rows, {len(errata)} errata")
    known = {e.get("id") for e in errata} | {"D-045", "U-08", None}
    dangling = [r.get("figure") for r in rows if r.get("erratum") not in known]
    check(not dangling, "R1.19 every concordance row resolves to a known erratum",
          "; ".join(str(x) for x in dangling[:4]))
    # A row that carries no status is a row that says nothing, and a concordance
    # of rows that say nothing reads as diligence while providing none.
    unstated = [r.get("figure") for r in rows if not (r.get("status") or "").strip()]
    check(not unstated, "R1.20 every concordance row states a status",
          "; ".join(str(x) for x in unstated[:4]))

    # ── 11. a scoped roadmap item carries its date (C-05) ───────────────
    # An undated roadmap item is indistinguishable from an abandoned one, which
    # is what U-06 was through three vintages.
    for u in (d.get("uncertainty_ledger") or {}).get("entries") or []:
        if u.get("status") == "PENDING" or u.get("target_vintage"):
            check(bool(u.get("target_date")) and bool(u.get("target_vintage")),
                  f"R1.21 scoped ledger item {u.get('id')} carries a date and a "
                  f"target vintage",
                  f"date={u.get('target_date')} vintage={u.get('target_vintage')}")

    # ── 9. soft checks ──────────────────────────────────────────────────
    # Axes are derived from the declared model, never a literal list. A stale
    # literal does not fail loudly here: `.get(a)` returns None for a renamed
    # axis, so the range check silently stops covering it. That is how RGD
    # went unvalidated after the v8.3 rename of CRD.
    axes = list(W) + list(model.get("diagnostic_axes_excluded") or [])
    for iso, c in C.items():
        for a in axes:
            v = c["axes"].get(a)
            if v is not None and not (0.0 <= v <= 100.0):
                warnings.append(f"{iso}.{a}={v} outside 0-100")
        if c.get("odi_continuous") is None:
            warnings.append(f"{iso} has no continuous ODI")

    # ── report ──────────────────────────────────────────────────────────
    say(f"{checks} checks · {len(failures)} failed · {len(warnings)} warnings")
    if warnings and not args.quiet:
        say("\nwarnings:")
        for w in warnings[:10]:
            say(f"  ! {w}")
        if len(warnings) > 10:
            say(f"  ! (+{len(warnings)-10} more)")
    if failures:
        print("\nFAILED:", file=sys.stderr)
        for f in failures:
            print(f"  x {f}", file=sys.stderr)
        print(f"\nGATE FAILED: {len(failures)} of {checks} checks. Do not deploy.",
              file=sys.stderr)
        return 1
    say(f"\nGATE PASSED: index is publishable.")
    return 0


if __name__ == "__main__":
    # An unhandled exception must read as a gate failure, not as an ambiguous
    # traceback that an unattended run could mistake for a passing build.
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:                                  # noqa: BLE001
        print(f"GATE FAILED: verifier raised {type(exc).__name__}: {exc}. "
              f"Treat as not publishable.", file=sys.stderr)
        raise SystemExit(3)
