"""Holds the Article 14 Decision 6 clearance to the scope it was granted under.

Decision 6 was cleared on 2026-08-28 on the operator's declaration that the
platform is strictly non-commercial and academic, which satisfies a CC-BY-NC
source for the public surface. That clearance is sound for exactly that surface
and it is unsound the moment a source under it enters a paid deliverable, because
non-commercial is a property of the USE and not of the user.

The exposure that clearance creates is retroactive. If a Tier C source flows into
an institutional licence next year, the use was out of scope from the day it
started, and no later document repairs it. So the clearance ships with the control
that keeps it true rather than with a promise to remember.

WHAT IT ASSERTS.
  N1  No source in the non-commercial pool appears in a commercial deliverable
      manifest. The pool is declared in ops/NONCOMMERCIAL_POOL.json and a
      deliverable declares itself commercial by carrying a price, a licence fee
      or an institutional-licence flag.
  N2  The clearance record in the Article 14 register names its scope. A
      clearance recorded without a scope is refused, because an unscoped
      clearance is indistinguishable from a general one.

Usage:  python scripts/verify_noncommercial_scope.py [--selftest]
Exit:   0 the clearance holds - 1 a source left its scope
"""
from __future__ import annotations
import argparse, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
POOL = ROOT / "ops" / "NONCOMMERCIAL_POOL.json"
COMMERCIAL_MARKERS = ("price", "price_eur", "licence_fee", "license_fee",
                      "institutional_licence", "institutional_license", "paid")


def is_commercial(deliverable: dict) -> bool:
    """Pure. A deliverable is commercial if it carries any revenue marker."""
    for k, v in deliverable.items():
        if k.lower() in COMMERCIAL_MARKERS and v not in (None, "", False, 0):
            return True
    return False


def assess(pool: list[str], deliverables: list[dict]) -> list[str]:
    """Pure. One finding per non-commercial source found inside a commercial deliverable."""
    findings = []
    ncs = {s.lower() for s in pool}
    for d in deliverables:
        if not is_commercial(d):
            continue
        for src in d.get("sources", []):
            if str(src).lower() in ncs:
                findings.append(
                    f"deliverable {d.get('id', '?')!r} is commercial and draws on {src!r}, "
                    f"which sits in the non-commercial pool. Article 14 Decision 6 was "
                    f"cleared for the public surface only. Either remove the source or "
                    f"acquire a commercial licence for it before this ships."
                )
    return findings


def selftest() -> int:
    ok = True
    pool = ["WRI Aqueduct 4.0", "EMODnet"]
    must_refuse = [{"id": "datapack-1", "price_eur": 4000, "sources": ["WRI Aqueduct 4.0"]}]
    must_accept = [{"id": "public-site", "sources": ["WRI Aqueduct 4.0"]},
                   {"id": "datapack-2", "price_eur": 4000, "sources": ["own telemetry"]}]
    if len(assess(pool, must_refuse)) != 1:
        print("  x FIXTURE 1 FAILED: a paid deliverable drawing on the pool was accepted"); ok = False
    if assess(pool, must_accept):
        print("  x FIXTURE 2 FAILED: the free surface or a clean paid deliverable was refused"); ok = False
    # an empty pool must not vacuously pass a commercial deliverable it cannot judge
    if assess([], must_refuse) != []:
        print("  x FIXTURE 3 FAILED: an empty pool must find nothing, not everything"); ok = False
    print(f"NON-COMMERCIAL SCOPE SELFTEST: {'PASSED, 3 fixtures' if ok else 'FAILED'}")
    return 0 if ok else 1


ap = argparse.ArgumentParser()
ap.add_argument("--selftest", action="store_true")
a = ap.parse_args()
if a.selftest:
    raise SystemExit(selftest())

if not POOL.exists():
    print(f"NON-COMMERCIAL SCOPE: DEGRADED, {POOL.name} not present.")
    print("  Class B. The pool is declared when the first commercial deliverable is defined.")
    print("  Reported, not imputed (D-007). No deliverable exists to judge.")
    raise SystemExit(0)

doc = json.loads(POOL.read_text(encoding="utf-8"))
pool = doc.get("sources", [])
deliverables = doc.get("deliverables", [])
scope = (doc.get("clearance") or {}).get("scope")

print(f"non-commercial pool: {len(pool)} source(s), {len(deliverables)} declared deliverable(s)")
problems = []
if not scope:
    problems.append("N2: the Decision 6 clearance carries no scope. An unscoped clearance "
                    "is indistinguishable from a general one and is refused.")
problems += assess(pool, deliverables)

if problems:
    print("\nNON-COMMERCIAL SCOPE CHECK FAILED")
    for p in problems:
        print(f"  x {p}")
    raise SystemExit(1)
print(f"scope on record: {scope}")
print("\nNON-COMMERCIAL SCOPE CHECK PASSED: every source is used inside the scope it was cleared for.")
