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
  R3  every reachable copy in the OTHER repository hashes identically

R3 degrades rather than fails when no sibling is reachable, because CI checks out
one repository and the check must not invent an escalation out of a checkout
boundary. That degradation is class B under G-07: a declared safe failure mode,
recorded, never imputed. Absence of the sibling is reported, never assumed clean.

THE DEFECT THE 2026-08-24 EVENING REWRITE CLOSES (L-169). The sibling list was a
fixed list of sovereign-infra paths. Run from sovereign-infra, the first path that
existed was the ledger itself, so R3 compared the file with itself and printed
"sibling agrees" for a mirror that was one byte out of sync. A check that can only
fail from one side of a pair is not a check of the pair. The sibling is now
resolved from the identity of the repository the gate runs in, a candidate that
resolves to the ledger itself is reported as DEGRADED and never as agreement, and
on disagreement the gate names WHAT differs (ids only on one side, ids whose text
differs, a trailing-newline difference) so the next reader repairs instead of
guessing. scripts/ledger_sync.py is the lossless repair for the mechanical cases.

V-2: every gate owns one fixture it must refuse and one it must accept.
Run `--selftest` to execute them. `scripts/test_gate.py` calls it.

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

#: Where each repository lives on the operator's host, in probe order. The paths
#: are the authoritative ones from ops/PATH_REGISTRY.json. The decoy stub for
#: sovereign-infra (L-143) is listed LAST and is probed, because a stale copy
#: left there is a divergence to be named, not a path to be silently ignored.
REPOS: dict[str, list[Path]] = {
    "qesis-mcp": [Path(r"C:\Users\Lenovo\qesis-mcp")],
    "sovereign-infra": [
        Path(r"C:\Users\Lenovo\OneDrive\sovereign-infra"),
        Path(r"C:\Users\Lenovo\sovereign-infra"),  # decoy stub, L-143
    ],
}

HEADER = re.compile(r"^\*\*L-(\d{3})", re.M)


def repo_identity(root: Path = ROOT) -> str | None:
    """Which repository this checkout is, decided from the checkout itself.

    The directory name answers on the host and on a GitHub runner, where the
    checkout is named after the repository. Where it does not (a renamed clone,
    an upload mount), marker files answer. None means unknown, and an unknown
    identity compares against every declared copy that is not this file.
    """
    name = root.name.lower()
    for key in REPOS:
        if key in name:
            return key
    if (root / "server.py").exists() and (root / "data" / "qesis_v8.json").exists():
        return "qesis-mcp"
    if (root / "qesis_cloud.py").exists() or (root / "agents").is_dir():
        return "sovereign-infra"
    return None


def _is_self(candidate: Path, ledger: Path) -> bool:
    try:
        return candidate.exists() and ledger.exists() and candidate.resolve() == ledger.resolve()
    except OSError:
        return False


def sibling_ledgers(root: Path = ROOT, ledger: Path = LEDGER) -> list[Path]:
    """Every declared location of the OTHER repository's ledger, self excluded.

    Also probes a checkout beside this one under the sibling's name, which is
    how the analysis mount and a fresh clone lay the two repositories out.
    """
    me = repo_identity(root)
    others = [k for k in REPOS if k != me] if me else list(REPOS)
    seen: list[Path] = []
    for key in others:
        bases = [*REPOS[key], root.parent / key]
        # The analysis mount names a connected folder `<parent>--<name>`, e.g.
        # `OneDrive--sovereign-infra`, so a checkout beside this one can carry
        # that shape too. Probed, never assumed; sorted so the order is stable.
        try:
            bases += sorted(root.parent.glob(f"*--{key}"))
        except OSError:
            pass
        for base in bases:
            p = base / "ops" / "LESSONS_LEDGER.md"
            if p not in seen:
                seen.append(p)
    return [p for p in seen if not _is_self(p, ledger)]


def ids_of(text: str) -> list[int]:
    return [int(m.group(1)) for m in HEADER.finditer(text)]


def lf(text: str) -> str:
    return text.replace("\r\n", "\n")


def sha256(text: str) -> str:
    # Hash the LF form explicitly. L-101: a hash computed over what was intended
    # rather than over what landed is a function of the host platform.
    return hashlib.sha256(lf(text).encode("utf-8")).hexdigest()


def split_entries(text: str) -> tuple[str, dict[int, str], list[int]]:
    """Prelude, entry text by id (trailing newlines stripped), ids in file order."""
    text = lf(text)
    marks = list(HEADER.finditer(text))
    if not marks:
        return text, {}, []
    prelude = text[: marks[0].start()]
    entries: dict[int, str] = {}
    order: list[int] = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        lid = int(m.group(1))
        order.append(lid)
        entries.setdefault(lid, text[m.start():end].rstrip("\n"))
    return prelude, entries, order


def describe_delta(this: str, other: str) -> dict:
    """Name what differs between two copies, so a reader repairs rather than guesses."""
    a, b = lf(this), lf(other)
    p1, e1, o1 = split_entries(a)
    p2, e2, o2 = split_entries(b)
    only_here = sorted(set(e1) - set(e2))
    only_there = sorted(set(e2) - set(e1))
    conflicting = sorted(i for i in set(e1) & set(e2) if e1[i] != e2[i])
    prelude_differs = p1.rstrip("\n") != p2.rstrip("\n")
    newline_only = a.rstrip("\n") == b.rstrip("\n") and a != b
    mechanical = not conflicting and not prelude_differs
    parts = []
    if newline_only:
        parts.append("differs only in trailing newline(s)")
    if only_here:
        parts.append("only in this copy: " + ", ".join(f"L-{i:03d}" for i in only_here))
    if only_there:
        parts.append("only in the sibling: " + ", ".join(f"L-{i:03d}" for i in only_there))
    if conflicting:
        parts.append("same id, different text: " + ", ".join(f"L-{i:03d}" for i in conflicting))
    if prelude_differs:
        parts.append("the prelude before L-001 differs")
    if not parts:
        parts.append("entries agree; whitespace inside an entry differs")
        mechanical = False
    return {
        "only_here": [f"L-{i:03d}" for i in only_here],
        "only_there": [f"L-{i:03d}" for i in only_there],
        "conflicting": [f"L-{i:03d}" for i in conflicting],
        "prelude_differs": prelude_differs,
        "newline_only": newline_only,
        "mechanical": mechanical,
        "summary": "; ".join(parts)
                   + (". Repair: python scripts/ledger_sync.py" if mechanical
                      else ". NOT mechanical: reconcile by hand, never by dropping an entry (L-145)."),
    }


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
    siblings = sibling_ledgers(ROOT, ledger) if siblings is None else list(siblings)
    result: dict = {"rules": {}, "status": "PASS", "degraded": [], "ledger": str(ledger),
                    "repository": repo_identity(ROOT), "siblings": []}

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

    # R3 sibling agreement, against EVERY reachable copy of the other repository.
    compared: list[str] = []
    disagreements: list[str] = []
    self_hits: list[str] = []
    for sib in siblings:
        if _is_self(sib, ledger):
            self_hits.append(str(sib))
            result["siblings"].append({"path": str(sib), "status": "self"})
            continue
        if not sib.exists():
            result["siblings"].append({"path": str(sib), "status": "absent"})
            continue
        other_text = sib.read_text(encoding="utf-8", errors="replace")
        other = sha256(other_text)
        if other != result["sha256"]:
            delta = describe_delta(text, other_text)
            result["siblings"].append({"path": str(sib), "status": "disagree",
                                       "sha256": other, "delta": delta})
            disagreements.append(
                f"{sib} hashes {other[:12]}, this copy {result['sha256'][:12]}: "
                f"{delta['summary']}")
        else:
            result["siblings"].append({"path": str(sib), "status": "agree", "sha256": other})
            compared.append(str(sib))

    if disagreements:
        result["status"] = "FAIL"
        result["rules"]["R3"] = ("sibling disagrees: " + " | ".join(disagreements)
                                 + ". The ledger is not a singleton.")
    elif compared:
        result["rules"]["R3"] = "sibling agrees (" + ", ".join(compared) + ")"
    elif self_hits:
        # A candidate that IS this file proves nothing about the pair. Reported,
        # never counted as agreement. L-169.
        result["degraded"].append({
            "rule": "R3",
            "degradation": "sibling_resolved_to_self",
            "why": "every reachable candidate resolved to this very file, so no copy of "
                   "the other repository was compared. Reported, not imputed (D-007).",
            "probed": [str(p) for p in siblings],
        })
        result["rules"]["R3"] = "DEGRADED, candidate resolved to this file, nothing compared"
    else:
        result["degraded"].append({
            "rule": "R3",
            "degradation": "sibling_not_reachable",
            "why": "no declared sibling ledger path exists from here. Expected under CI, "
                   "which checks out one repository. Reported, not imputed (D-007).",
            "probed": [str(p) for p in siblings],
        })
        result["rules"]["R3"] = "DEGRADED, sibling not reachable"
    return result


# --------------------------------------------------------------------------- #
# V-2 fixtures. Each rule owns one it must refuse and one it must accept.
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

        # R3 refuse fixture: a sibling that disagrees, and the delta is named.
        other = d / "sibling.md"
        other.write_text(_ACCEPT.replace("b.", "different."), encoding="utf-8")
        r = check(acc, g, siblings=[other])
        if r["status"] != "FAIL" or "not a singleton" not in r["rules"].get("R3", ""):
            fails.append("disagreeing-sibling fixture was not refused by R3")
        elif "L-003" not in r["rules"]["R3"] or r["siblings"][0]["delta"]["mechanical"]:
            fails.append("R3 refused the conflicting sibling without naming L-003 as a text conflict")

        # R3 accept fixture: a sibling that agrees.
        same = d / "same.md"
        same.write_text(_ACCEPT, encoding="utf-8")
        r = check(acc, g, siblings=[same])
        if r["status"] != "PASS" or "agrees" not in r["rules"].get("R3", ""):
            fails.append(f"agreeing-sibling fixture was refused: {r['rules']}")

        # R3 self fixture (L-169): the ledger offered as its own sibling must be
        # reported as DEGRADED, never as agreement.
        r = check(acc, g, siblings=[acc])
        if "agrees" in r["rules"].get("R3", "") or not any(
                x.get("degradation") == "sibling_resolved_to_self" for x in r["degraded"]):
            fails.append("self-resolution fixture was accepted as sibling agreement")

        # R3 mechanical-delta fixture: a sibling missing the last entry, and one
        # differing only by the trailing newline, are named as mechanical.
        short = d / "short.md"
        short.write_text("# L\n\n**L-001 · d ·** a.\n", encoding="utf-8")
        r = check(acc, g, siblings=[short])
        delta = r["siblings"][0].get("delta", {})
        if r["status"] != "FAIL" or delta.get("only_here") != ["L-003"] or not delta.get("mechanical"):
            fails.append(f"missing-entry sibling was not diagnosed as a mechanical delta: {delta}")
        nl = d / "nl.md"
        nl.write_text(_ACCEPT.rstrip("\n"), encoding="utf-8")
        r = check(acc, g, siblings=[nl])
        delta = r["siblings"][0].get("delta", {})
        if r["status"] != "FAIL" or not delta.get("newline_only") or not delta.get("mechanical"):
            fails.append(f"trailing-newline sibling was not diagnosed as newline-only: {delta}")

        # Identity: a checkout named after a repository resolves the OTHER one,
        # never itself.
        for me, expect_other in (("qesis-mcp", "sovereign-infra"), ("sovereign-infra", "qesis-mcp")):
            root = d / me
            (root / "ops").mkdir(parents=True)
            led = root / "ops" / "LESSONS_LEDGER.md"
            led.write_text(_ACCEPT, encoding="utf-8")
            sibs = sibling_ledgers(root, led)
            if any(_is_self(p, led) for p in sibs) or not all(expect_other in str(p) for p in sibs):
                fails.append(f"identity fixture for {me} resolved {sibs}")

    for f in fails:
        print(f"SELFTEST FAIL: {f}")
    print("LEDGER SINGLETON SELFTEST: " + ("PASSED, 10 fixtures" if not fails else "FAILED"))
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
        print(f"ledger: {r['ledger']}  (repository: {r.get('repository') or 'unknown'})")
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
