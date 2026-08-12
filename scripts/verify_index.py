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

    # ── 10a. CONC-1: one erratum, one status, across the whole payload ───
    # L-074. Through v8.6 this payload said three things at once about the
    # same fsQCA re-run: the concordance rows said "withdrawn pending re-run",
    # recalibration_required said RESOLVED_DECLINED, and the D-103 erratum
    # said OPEN. No amount of cross-document diligence catches that, because
    # the contradiction is internal to a single JSON response. The assertion
    # has to live in the builder's own gate.
    bindings = cc.get("resolution_bindings") or []
    unbound = cc.get("unbound_errata") or []

    # A gate that can be defeated by declining to declare a binding is not a
    # gate. Every erratum is bound or is explicitly unbound with a reason.
    declared = {b.get("erratum") for b in bindings}
    excused = {u.get("erratum") for u in unbound if (u.get("reason") or "").strip()}
    undeclared = sorted({e.get("id") for e in errata} - declared - excused)
    check(not undeclared,
          "R1.22 every erratum is bound to a resolution field or declared unbound "
          "with a reason",
          "; ".join(str(x) for x in undeclared[:6]))

    def _resolve(path: str):
        node = d
        for part in path.split("."):
            if not isinstance(node, dict):
                return None
            node = node.get(part)
        return node

    conflicts: list[str] = []
    for b in bindings:
        eid, path = b.get("erratum"), b.get("resolution_path") or ""
        state = _resolve(path)
        if state is None:
            conflicts.append(f"{eid}: resolution_path {path} resolves to nothing")
            continue
        if str(state) not in (b.get("resolved_when") or []):
            continue  # not yet resolved; rows may legitimately say "pending"
        banned = [s for s in (b.get("forbidden_when_resolved") or []) if s]
        for e in errata:
            if e.get("id") != eid:
                continue
            hit = [s for s in banned if s.lower() in str(e.get("status") or "").lower()]
            if hit:
                conflicts.append(
                    f"{eid}: {path} is {state} but the erratum status still says "
                    f"{hit[0]!r}")
        for r in rows:
            if r.get("erratum") != eid:
                continue
            hit = [s for s in banned if s.lower() in str(r.get("status") or "").lower()]
            if hit:
                conflicts.append(
                    f"{eid}: {path} is {state} but row {r.get('figure')!r} still "
                    f"says {hit[0]!r}")
    check(not conflicts,
          "R1.23 no erratum is resolved in one field and pending in another",
          "; ".join(conflicts[:4]))

    # ── 10b. CONC-2: one necessity rule, applied, not typed ─────────────
    # D-109, 2026-08-12. v8.7 carried two decision rules that disagreed.
    # necessity_gate_method declared RoN >= 0.60 with coverage_N >= 0.60 and
    # labelled five conditions NECESSARY. necessity_verdict in the same payload
    # said nothing was publishable as necessary, applying the conventional
    # consistency >= 0.90 bar. Five conditions were necessary and not necessary
    # at once, depending on which sentence a reader reached first.
    #
    # The resolution is conjunctive and it is not a matter of taste. Under a
    # bare consistency rule, REE returns consistency_N 0.9672 against the fixed
    # 75/50/25 sensitivity anchors and is relabelled NECESSARY, which walks the
    # withdrawn section 4.5 claim back in through the sensitivity regime. RoN
    # 0.195 is the only measure that refuses it. Consistency alone cannot
    # establish necessity (Schneider and Wagemann 2012, ch. 5), which is why the
    # REE withdrawal is grounded on triviality rather than threshold failure.
    #
    # This gate does not read the stored verdict. It recomputes it from the
    # published measures and the declared thresholds, and fails on disagreement.
    # A label that is asserted rather than derived is the defect CONC-2 was.
    gate = (d.get("fsqca") or {}).get("necessity_gate") or {}
    if gate:
        def verdict_from_rule(m: dict) -> str:
            t = m.get("thresholds") or {}
            cons_bar = t.get("consistency_N_publishable")
            ron_bar = t.get("RoN_publishable")
            cov_bar = t.get("coverage_N_publishable")
            triv_bar = t.get("RoN_trivial_below")
            if None in (cons_bar, ron_bar, cov_bar, triv_bar):
                return "UNDECLARED"
            cons, ron, cov = (m.get("consistency_N"), m.get("relevance_of_necessity"),
                              m.get("coverage_N"))
            if None in (cons, ron, cov):
                return "UNDECLARED"
            neg = m.get("negated_outcome") or {}
            if neg.get("also_necessary_for_negation") or neg.get("no_better_than_negation"):
                return "TRIVIAL"
            if ron < triv_bar:
                return "TRIVIAL"
            if cons >= cons_bar and ron >= ron_bar and cov >= cov_bar:
                return "NECESSARY"
            return "LABEL-DECLINED"

        mismatched, undeclared = [], []
        for cond, m in gate.items():
            want = verdict_from_rule(m)
            if want == "UNDECLARED":
                undeclared.append(cond)
            elif want != m.get("verdict"):
                mismatched.append(f"{cond}: stored {m.get('verdict')}, rule says {want}")
        check(not undeclared,
              "R1.24 every necessity condition declares all four thresholds",
              "; ".join(undeclared[:6]))
        check(not mismatched,
              "R1.24 every necessity verdict is derived from the declared rule",
              "; ".join(mismatched[:4]))

        # The prose verdict is the sentence a reader quotes. It may not contradict
        # the labels sitting beside it.
        necessary = sorted(c for c, m in gate.items() if m.get("verdict") == "NECESSARY")
        prose = str((d.get("fsqca") or {}).get("necessity_verdict") or "").lower()
        claims_none = "no condition" in prose and "necessary" in prose
        check(not (necessary and claims_none),
              "R1.25 the prose necessity verdict agrees with the per-condition labels",
              f"labels say {necessary} are NECESSARY while the verdict says none is")
        check(not (not necessary and not claims_none),
              "R1.25 the prose necessity verdict agrees with the per-condition labels",
              "no condition is labelled NECESSARY but the verdict does not say so")

    # ── 10c. R1.26: governance travels as data, and carries its content ──
    # QT-0007. The alternative on the table was to inject these limitations into
    # the agent's prompt. Prompt text is advisory: a model may ignore it and an
    # editor may delete it without tripping anything. Served as fields they are
    # read deterministically and asserted here.
    #
    # Each flag must ship its statement. A bare boolean is a pointer to a fact,
    # and a retrieval layer that receives only the pointer has been told a
    # limitation exists and nothing about what it is. The R&D pool's RAG guide
    # makes the same argument from the other direction: shape structured fields
    # so the meaning survives retrieval, rather than leaving the model to infer
    # it from a bare value.
    arc = d.get("agent_reading_contract") or {}
    flags = arc.get("flags") or {}
    check(bool(flags),
          "R1.26 the agent reading contract is served with at least one flag",
          f"{len(flags)} flags")
    if flags:
        thin = []
        for name, f in flags.items():
            if not isinstance(f, dict):
                thin.append(f"{name} is a bare value, not a flag with a statement")
                continue
            if f.get("value") is None:
                thin.append(f"{name} carries no value")
            if not str(f.get("statement") or "").strip():
                thin.append(f"{name} carries no statement")
            if not str(f.get("authority") or "").strip():
                thin.append(f"{name} names no authority")
            vocab = f.get("vocabulary")
            if vocab and f.get("value") not in vocab:
                thin.append(f"{name} value {f.get('value')!r} is outside its declared vocabulary")
        check(not thin,
              "R1.26 every served flag carries a value, a statement and an authority",
              "; ".join(thin[:5]))
        # The two the operator asked for by name, so a later edit cannot quietly
        # drop them while leaving the block populated and the gate green.
        required = ["theory_informed_limitation", "trilemma_status"]
        absent = [r for r in required if r not in flags]
        check(not absent,
              "R1.26 the declared limitation flags are present",
              "; ".join(absent))

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
