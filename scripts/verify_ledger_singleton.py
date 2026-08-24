#!/usr/bin/env python3
"""Refuse a lessons ledger that is not a singleton.

Opened by the 2026-08-24 reconciliation. The ledger existed in two repositories,
the copies diverged, and L-119 and L-120 named two different lessons each. L-073
has made a duplicate id a build failure since it was written, and nothing failed,
because no gate had ever been pointed at the ledger itself. L-054: a rule held
only in prose has been described, not applied.

Three rules, each with its own exit reason:

  R1  no duplicate id anywhere in the file
  R2  every absent id is declared in ops/LEDGER_GAPS.json with a reason
  R3  when the sibling repository is reachable, both copies hash identically

R3 degrades rather than fails when the sibling is absent, because CI checks out
one repository and the check must not invent an escalation out of a checkout
boundary. That degradation is class B under G-07: a declared safe failure mode,
recorded, never imputed. Absence of the sibling is reported, never assumed clean.

V-2: every gate owns one fixture it must refuse and one it must accept.
Run `--selftest` to execute both. `scripts/test_gate.py` calls it.

Usage:
    python scripts/verify_ledger_singleton.py [--quiet] [--selftest] [--json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "ops" / "LESSONS_LEDGER.md"
GAPS = ROOT / "ops" / "LEDGER_GAPS.json"

#: Declared sibling locations, in probe order. The first that exists wins.
#: L-120: a connected folder that should hold a repository and does not is a fact
#: about that one path, never a fact about the repository. So the list is plural
#: and the check reports which member answered.
SIBLINGS = [
    Path(r"C:\Users\Lenovo\OneDrive\sovereign-infra") / "ops" / "LESSONS_LEDGER.md",
    Path(r"C:\Users\Lenovo\sovereign-infra") / "ops" / "LESSONS_LEDGER.md",
    ROOT.parent / "sovereign-infra" / "ops" / "LESSONS_LEDGER.md",
]

HEADER = re.compile(r"^\*\*L-(\d{3})", re.M)


def ids_of(text: str) -> list[int]:
    return [int(m.group(1)) for m in HEADER.finditer(text)]


def sha256(text: str) -> str:
    # Hash the LF form explicitly. L-101: a hash computed over what was intended
    # rather than over what landed is a function of the host platform.
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def declared_gaps(path: Path = GAPS) -> tuple[set[int], dict]:
    if not path.exists():
        return set(), {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    out: set[int] = set()
    for entry in doc.get("declared_absent", []):
        lo = int(str(entry["from"]).removeprefix("L-"))
        hi = int(str(entry.get("to", entry["from"])).removeprefix("L-"))
        out.update(range(lo, hi + 1))
    return out, doc


def check(ledger: Path = LEDGER, gaps: Path = GAPS, siblings=None) -> dict:
    siblings = SIBLINGS if siblings is None else siblings
    result: dict = {"rules": {}, "status": "PASS", "degraded": [], "ledger": str(ledger)}

    if not ledger.exists():
        result["status"] = "FAIL"
        result["rules"]["R0"] = f"ledger absent at {ledger}"
        return result

    text = ledger.read_text(encoding="utf-8", errors="replace")
    found = ids_of(text)
    result["entries"] = len(found)
    result["unique"] = len(set(found))
    result["max"] = max(found) if found else 0
    result["sha256"] = sha256(text)

    # R1 duplicates
    dupes = sorted({i for i in found if found.count(i) > 1})
    if dupes:
        result["status"] = "FAIL"
        result["rules"]["R1"] = "duplicate ids: " + ", ".join(f"L-{i:03d}" for i in dupes)
    else:
        result["rules"]["R1"] = "no duplicate id"

    # R2 undeclared gaps
    declared, _doc = declared_gaps(gaps)
    absent = {i for i in range(1, result["max"] + 1)} - set(found)
    undeclared = sorted(absent - declared)
    if undeclared:
        result["status"] = "FAIL"
        result["rules"]["R2"] = "undeclared absent ids: " + ", ".join(
            f"L-{i:03d}" for i in undeclared
        )
    else:
        result["rules"]["R2"] = f"{len(absent)} absent ids, all declared"

    # R3 sibling agreement
    sibling = next((p for p in siblings if p.exists()), None)
    if sibling is None:
        result["degraded"].append(
            {
                "rule": "R3",
                "degradation": "sibling_not_reachable",
                "why": "no declared sibling ledger path exists from here. Expected under CI, "
                "which checks out one repository. Reported, not imputed (D-007).",
                "probed": [str(p) for p in siblings],
            }
        )
        result["rules"]["R3"] = "DEGRADED, sibling not reachable"
    else:
        other = sha256(sibling.read_text(encoding="utf-8", errors="replace"))
        if other != result["sha256"]:
            result["status"] = "FAIL"
            result["rules"]["R3"] = (
                f"sibling disagrees: {sibling} hashes {other[:12]}, this copy "
                f"{result['sha256'][:12]}. The ledger is not a singleton."
            )
        else:
            result["rules"]["R3"] = f"sibling agrees ({sibling})"
    return result


# --------------------------------------------------------------------------- #
# V-2 fixtures. One the gate must refuse, one it must accept.
# --------------------------------------------------------------------------- #
_ACCEPT = "# L\n\n**L-001 · d ·** a.\n\n**L-003 · d ·** b.\n"
_REFUSE_DUP = "# L\n\n**L-001 · d ·** a.\n\n**L-001 · d ·** b.\n"
_REFUSE_GAP = "# L\n\n**L-001 · d ·** a.\n\n**L-004 · d ·** b.\n"
_GAPS_DOC = {"declared_absent": [{"from": "L-002", "to": "L-002", "reason": "fixture"}]}


def selftest() -> int:
    fails = []
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        g = d / "gaps.json"
        g.write_text(json.dumps(_GAPS_DOC), encoding="utf-8")

        acc = d / "accept.md"
        acc.write_text(_ACCEPT, encoding="utf-8")
        r = check(acc, g, siblings=[])
        if r["status"] != "PASS":
            fails.append(f"accept fixture was refused: {r['rules']}")

        dup = d / "dup.md"
        dup.write_text(_REFUSE_DUP, encoding="utf-8")
        r = check(dup, g, siblings=[])
        if r["status"] != "FAIL" or "R1" not in r["rules"] or "duplicate" not in r["rules"]["R1"]:
            fails.append("duplicate-id fixture was not refused by R1")

        gap = d / "gap.md"
        gap.write_text(_REFUSE_GAP, encoding="utf-8")
        r = check(gap, g, siblings=[])
        if r["status"] != "FAIL" or "undeclared" not in r["rules"].get("R2", ""):
            fails.append("undeclared-gap fixture was not refused by R2")

        # R3 refuse fixture: a sibling that disagrees.
        other = d / "sibling.md"
        other.write_text(_ACCEPT.replace("b.", "different."), encoding="utf-8")
        r = check(acc, g, siblings=[other])
        if r["status"] != "FAIL" or "not a singleton" not in r["rules"].get("R3", ""):
            fails.append("disagreeing-sibling fixture was not refused by R3")

        # R3 accept fixture: a sibling that agrees.
        same = d / "same.md"
        same.write_text(_ACCEPT, encoding="utf-8")
        r = check(acc, g, siblings=[same])
        if r["status"] != "PASS":
            fails.append(f"agreeing-sibling fixture was refused: {r['rules']}")

    for f in fails:
        print(f"SELFTEST FAIL: {f}")
    print("LEDGER SINGLETON SELFTEST: " + ("PASSED, 5 fixtures" if not fails else "FAILED"))
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    r = check()
    if a.json:
        print(json.dumps(r, indent=1))
        return 0 if r["status"] == "PASS" else 1

    if not a.quiet or r["status"] != "PASS":
        print(f"ledger: {r['ledger']}")
        print(
            f"  entries {r.get('entries')}, unique {r.get('unique')}, "
            f"max L-{r.get('max', 0):03d}, sha256 {r.get('sha256', '')[:16]}"
        )
        for rule, msg in r["rules"].items():
            print(f"  {rule}  {msg}")
        for deg in r["degraded"]:
            print(f"  DEGRADED {deg['rule']}: {deg['why']}")
    print("LEDGER SINGLETON CHECK " + ("PASSED" if r["status"] == "PASS" else "FAILED"))
    return 0 if r["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
