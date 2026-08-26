#!/usr/bin/env python3
"""Make every reachable copy of the lessons ledger byte-identical, losslessly.

WHY THIS EXISTS (L-169). The ledger is one file mirrored across two repositories.
On 2026-08-24 the copies diverged by exactly one byte, a trailing newline, because
a session wrote one copy directly instead of through the appender. The singleton
gate refused the qesis-mcp copy, the lander aborted on the gate, and nothing in
the ecosystem could repair a divergence it could name. A gate with no remedy is a
wall, and walls get climbed by editing files by hand, which is how the next
divergence starts.

WHAT IT DOES, AND THE ONE THING IT REFUSES TO DO. It reads every reachable copy,
takes the UNION of entries by id, and writes the union to every copy in one
canonical form (LF line endings, one blank line between entries, exactly one
trailing newline). That is lossless by construction: no entry is dropped, no
entry is invented, and an entry present in one copy only is carried to the other.

It REFUSES, exit 2, writing nothing, when the copies disagree about the same id
(same L- number, different text) or about the prelude, because that is the L-119
and L-120 situation and the correct repair is a renumber recorded inline, never a
choice between two texts made by a script. It also refuses a copy that contains
a duplicate id (R1), because propagating a duplicate is not a repair.

It never runs a git command. The lander stages what this writes.

Usage:
    python scripts/ledger_sync.py            # sync, then run the singleton gate
    python scripts/ledger_sync.py --check    # report only, exit 1 if a sync is needed
    python scripts/ledger_sync.py --json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "ops" / "LESSONS_LEDGER.md"


def _gate_module():
    spec = importlib.util.spec_from_file_location(
        "_vls", ROOT / "scripts" / "verify_ledger_singleton.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canonical(prelude: str, order: list[int], entries: dict[int, str]) -> str:
    body = "\n\n".join(entries[i] for i in order)
    return prelude.rstrip("\n") + "\n\n" + body + "\n"


def plan(copies: list[Path], gate) -> dict:
    """Decide the union, or refuse. Pure: reads files, writes nothing."""
    out: dict = {"copies": [], "status": "NOTHING_TO_DO", "canonical_sha256": None}
    parsed = []
    for p in copies:
        raw = p.read_bytes().decode("utf-8", errors="replace")
        prelude, entries, order = gate.split_entries(raw)
        dupes = sorted({i for i in order if order.count(i) > 1})
        parsed.append((p, raw, prelude, entries, order, dupes))
        out["copies"].append({"path": str(p), "entries": len(order), "max": max(order) if order else 0,
                              "sha256": hashlib.sha256(gate.lf(raw).encode()).hexdigest(),
                              "duplicate_ids": [f"L-{i:03d}" for i in dupes]})
    if any(dupes for *_, dupes in parsed):
        out["status"] = "REFUSED"
        out["why"] = ("a copy holds a duplicate id (R1). Repair that copy first; a sync "
                      "must never propagate a duplicate.")
        return out

    # Prelude must agree.
    preludes = {gate.lf(pr).rstrip("\n") for _, _, pr, *_ in parsed}
    if len(preludes) > 1:
        out["status"] = "REFUSED"
        out["why"] = "the prelude before L-001 differs between copies. Reconcile by hand."
        return out

    # Same id, same text, or refuse.
    conflicts: set[int] = set()
    union: dict[int, str] = {}
    for _, _, _, entries, _, _ in parsed:
        for i, t in entries.items():
            if i in union and union[i] != t:
                conflicts.add(i)
            union.setdefault(i, t)
    if conflicts:
        out["status"] = "REFUSED"
        out["conflicting"] = [f"L-{i:03d}" for i in sorted(conflicts)]
        out["why"] = ("the same id carries different text in two copies: "
                      + ", ".join(out["conflicting"])
                      + ". Renumber and record the renumber inline (L-145); never pick one.")
        return out

    # Order: the copy with the most entries is the base; ids it lacks are
    # appended in the order the other copies file them.
    base = max(parsed, key=lambda x: len(x[4]))
    order = list(base[4])
    for _, _, _, _, o, _ in parsed:
        for i in o:
            if i not in order:
                order.append(i)
    text = canonical(base[2], order, union)
    out["canonical_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    out["entries"] = len(order)
    out["_text"] = text
    for entry, (p, raw, _, entries, o, _) in zip(out["copies"], parsed):
        entry["would_change"] = raw != text
        entry["would_gain"] = [f"L-{i:03d}" for i in order if i not in entries]
        entry["newline_or_form_only"] = raw != text and not entry["would_gain"] \
            and gate.lf(raw).rstrip("\n") == text.rstrip("\n")
    if any(c["would_change"] for c in out["copies"]):
        out["status"] = "SYNC_NEEDED"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    gate = _gate_module()
    copies = [LEDGER] + [p for p in gate.sibling_ledgers(ROOT, LEDGER) if p.exists()]
    if not LEDGER.exists():
        print(f"LEDGER SYNC REFUSED: no ledger at {LEDGER}")
        return 2
    p = plan(copies, gate)
    text = p.pop("_text", None)

    if a.json:
        print(json.dumps(p, indent=1))
    else:
        print(f"LEDGER SYNC: {len(copies)} reachable cop(y/ies), repository "
              f"{gate.repo_identity(ROOT) or 'unknown'}")
        for c in p["copies"]:
            flag = ("REFUSED" if p["status"] == "REFUSED" else
                    "would change" if c.get("would_change") else "canonical")
            extra = ""
            if c.get("would_gain"):
                extra = ", gains " + ", ".join(c["would_gain"])
            elif c.get("newline_or_form_only"):
                extra = ", form only (line endings or trailing newline)"
            print(f"  {flag:12s} {c['path']}  entries {c['entries']} max L-{c['max']:03d} "
                  f"sha256 {c['sha256'][:12]}{extra}")

    if p["status"] == "REFUSED":
        print(f"LEDGER SYNC REFUSED: {p['why']}")
        return 2
    if len(copies) == 1:
        print("  only this copy is reachable; nothing to compare. Reported, not assumed in sync.")
    if p["status"] == "NOTHING_TO_DO":
        print("LEDGER SYNC: every reachable copy is already canonical and identical. Zero is zero.")
        return 0
    if a.check:
        print("LEDGER SYNC NEEDED (check mode, nothing written). Run without --check to repair.")
        return 1

    for c in p["copies"]:
        if c["would_change"]:
            Path(c["path"]).write_bytes(text.encode("utf-8"))
            print(f"  wrote {c['path']}")
    print(f"LEDGER SYNC: {p['entries']} entries, canonical sha256 {p['canonical_sha256'][:16]}, "
          f"written to every changed copy.")

    # Prove it, from the gate, not from this script's own belief.
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_ledger_singleton.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT, timeout=120, check=False)
    print("  gate after sync: " + (r.stdout.strip().splitlines() or ["no output"])[-1])
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
