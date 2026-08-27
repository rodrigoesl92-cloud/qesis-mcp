#!/usr/bin/env python3
"""RC-1 to RC-6. The evidence hierarchy is data, and this is what reads it.

WHY. On 2026-08-26 a session reported the serving plane from a fetch tool that
caches for fifteen minutes, asserted the cached value as the live one, and put
an item on the operator that had already been done (L-182). The remedy is not a
better habit. A habit is advisory and deletable; ops/SOURCE_PRECEDENCE.json is
data and this gate is its contract, so the rule survives the session that wrote
it. That is the same move R1.26 makes for the fsQCA reading flags.

The contract, in one line each:

  RC-1  four precedence tiers, ranks contiguous from 1, each with a rule
  RC-2  every plane declares its question and one authoritative, non-caching reader
  RC-3  WebFetch is named forbidden, with why, evidence and permitted use
  RC-4  every forbidden reader named on a plane exists in the forbidden table
  RC-5  every register entry carries id, apa and tier; ids unique; tiers 2 or 3
  RC-6  the assertion rule names the clauses that make it binding

Usage:  python scripts/verify_reading_contract.py [--file PATH] [--quiet]
        python scripts/verify_reading_contract.py --selftest
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "ops" / "SOURCE_PRECEDENCE.json"
REQUIRED_PLANES = ("artefact", "evidence", "delivery", "serving")
MUST_BE_GUARDED = ("delivery", "serving")


def check(doc: dict) -> list[str]:
    """Return the list of violations. Empty means the contract holds."""
    bad: list[str] = []

    tiers = doc.get("precedence") or []
    ranks = [t.get("rank") for t in tiers]
    if ranks != list(range(1, len(ranks) + 1)) or len(ranks) != 4:
        bad.append(f"RC-1: precedence ranks are {ranks}, expected 1 to 4 contiguous")
    for t in tiers:
        if not t.get("rule"):
            bad.append(f"RC-1: tier {t.get('tier')!r} carries no rule")

    planes = doc.get("planes") or {}
    for name in REQUIRED_PLANES:
        p = planes.get(name)
        if not isinstance(p, dict):
            bad.append(f"RC-2: plane {name!r} is not declared")
            continue
        if not p.get("question"):
            bad.append(f"RC-2: plane {name!r} declares no question")
        if not p.get("authoritative_reader"):
            bad.append(f"RC-2: plane {name!r} declares no authoritative reader")
        if p.get("caching") != "none":
            bad.append(f"RC-2: plane {name!r} declares caching {p.get('caching')!r}, "
                       "and a cached reader is not authoritative")
        if name in MUST_BE_GUARDED and not p.get("forbidden_readers"):
            bad.append(f"RC-2: plane {name!r} names no forbidden reader, and it is a "
                       "remote plane where L-182 happened")

    forbidden = doc.get("forbidden_readers") or {}
    wf = forbidden.get("WebFetch")
    if not isinstance(wf, dict):
        bad.append("RC-3: WebFetch is not in the forbidden table")
    else:
        for field in ("why", "evidence", "permitted_use"):
            if not wf.get(field):
                bad.append(f"RC-3: WebFetch entry carries no {field}. A prohibition "
                           "without its reason is a rule nobody can apply.")

    for name, p in planes.items():
        if not isinstance(p, dict):
            continue
        for r in (p.get("forbidden_readers") or []):
            if r not in forbidden:
                bad.append(f"RC-4: plane {name!r} forbids {r!r}, which the forbidden "
                           "table does not define")

    seen: set[str] = set()
    for key in ("academic_register", "empirical_register"):
        for e in (doc.get(key) or []):
            eid = e.get("id")
            if not eid:
                bad.append(f"RC-5: an entry in {key} carries no id")
                continue
            if eid in seen:
                bad.append(f"RC-5: duplicate register id {eid!r}")
            seen.add(eid)
            if not e.get("apa"):
                bad.append(f"RC-5: {eid} carries no APA citation")
            if e.get("tier") not in (2, 3):
                bad.append(f"RC-5: {eid} sits at tier {e.get('tier')!r}; a source is "
                           "tier 2 or tier 3, never tier 1 and never tier 4")

    ar = doc.get("assertion_rule") or {}
    if not ar.get("statement") or not ar.get("authority"):
        bad.append("RC-6: the assertion rule carries no statement or no authority")
    return bad


def selftest() -> int:
    """One fixture per rule that must be refused, and the live file accepted."""
    base = json.loads(CONTRACT.read_text(encoding="utf-8"))
    cases: list[tuple[str, callable, bool]] = [
        ("the committed contract is accepted", lambda d: d, True),
        ("a missing precedence tier is refused",
         lambda d: {**d, "precedence": d["precedence"][:3]}, False),
        ("a tier with no rule is refused",
         lambda d: _drop(d, ["precedence", 0, "rule"]), False),
        ("a plane with no authoritative reader is refused",
         lambda d: _drop(d, ["planes", "serving", "authoritative_reader"]), False),
        ("a plane that admits a cached reader is refused",
         lambda d: _set(d, ["planes", "serving", "caching"], "15 minutes"), False),
        ("a remote plane with no forbidden reader is refused",
         lambda d: _drop(d, ["planes", "delivery", "forbidden_readers"]), False),
        ("removing WebFetch from the forbidden table is refused",
         lambda d: _drop(d, ["forbidden_readers", "WebFetch"]), False),
        ("a prohibition with no evidence is refused",
         lambda d: _drop(d, ["forbidden_readers", "WebFetch", "evidence"]), False),
        ("a forbidden reader named on a plane but undefined is refused",
         lambda d: _set(d, ["planes", "serving", "forbidden_readers"], ["SomeOtherTool"]), False),
        ("a register entry with no APA citation is refused",
         lambda d: _drop(d, ["academic_register", 0, "apa"]), False),
        ("a source promoted to tier 1 is refused",
         lambda d: _set(d, ["academic_register", 0, "tier"], 1), False),
        ("an assertion rule with no authority is refused",
         lambda d: _drop(d, ["assertion_rule", "authority"]), False),
    ]
    ok = 0
    for label, mutate, should_pass in cases:
        bad = check(mutate(copy.deepcopy(base)))
        good = (not bad) if should_pass else bool(bad)
        ok += good
        print(f"{'PASS' if good else 'FAIL'}  reading-contract: {label}")
        if not good:
            print(f"        violations: {bad}")
    print(f"{ok}/{len(cases)} reading-contract behaviours verified")
    return 0 if ok == len(cases) else 1


def _walk(d, path):
    for k in path[:-1]:
        d = d[k]
    return d, path[-1]


def _drop(d, path):
    parent, last = _walk(d, path)
    if isinstance(parent, list):
        parent.pop(last)
    else:
        parent.pop(last, None)
    return d


def _set(d, path, value):
    parent, last = _walk(d, path)
    parent[last] = value
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=str(CONTRACT))
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    p = Path(a.file)
    if not p.exists():
        print(f"READING CONTRACT: {p} is absent. The hierarchy is data, and absent "
              "data is not a passing gate.", file=sys.stderr)
        return 1
    bad = check(json.loads(p.read_text(encoding="utf-8")))
    for b in bad:
        print(f"  FAIL {b}")
    if bad:
        print(f"READING CONTRACT FAILED: {len(bad)} violation(s).", file=sys.stderr)
        return 1
    if not a.quiet:
        doc = json.loads(p.read_text(encoding="utf-8"))
        print(f"  {len(doc['precedence'])} precedence tiers, "
              f"{len(doc['planes']) - 1} planes, "
              f"{len(doc['forbidden_readers'])} forbidden reader(s), "
              f"{len(doc['academic_register']) + len(doc['empirical_register'])} registered sources")
    print("RC PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
