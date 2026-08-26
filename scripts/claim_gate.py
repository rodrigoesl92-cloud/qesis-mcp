#!/usr/bin/env python3
"""Refuse a completion claim that no command established.

THE QUESTION THIS ANSWERS. The operator asked, correctly, how we solve a defect
that instruction cannot solve. Sixteen times on 2026-08-24 a rule that was
already written down was violated by the agent that had just cited it. SH-7,
V-1, D-115 and L-110 were all in force and all broken. Writing an eighteenth
rule has a measured failure rate and the measurement is today.

Three layers, in order of what actually held:

  Layer 1  a rule in CLAUDE.md or in memory.  FAILED, repeatedly, all day.
  Layer 2  a script that exits non-zero.      HELD, every single time one ran.
  Layer 3  that script running WITHOUT the agent choosing to run it.

Layer 2 only works when layer 3 exists, because an agent that decides when to
verify will eventually decide not to. So the gates run from the lander before
staging, from qesis-integrity on every push, and from selfheal hourly. None of
those three ask the agent's permission.

This file is the remaining hole. An agent can still WRITE that something is done
without running anything. So a completion claim is now an artefact with
evidence, and this refuses one without it.

Usage:
    python scripts/claim_gate.py --claim "both repositories are on main" \\
        --evidence-file ops/EVIDENCE_20260824.json
    python scripts/claim_gate.py --record "gh pr list ..." --exit 0 --out ops/EVIDENCE.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Words that assert a terminal state. A sentence containing one of these needs
#: a command behind it, because these are precisely the words that were wrong.
TERMINAL = {
    "done", "finished", "complete", "completed", "solved", "fixed", "merged",
    "landed", "green", "passing", "passed", "resolved", "closed", "deployed",
    "on main", "nothing further", "no further", "ready",
}


def record(cmd: str, out_path: Path) -> int:
    """Run a command and append its real result to the evidence file."""
    p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True,
                       text=True, timeout=600)
    doc = {"entries": []}
    if out_path.exists():
        try:
            doc = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    doc.setdefault("entries", []).append({
        "command": cmd,
        "exit": p.returncode,
        "tail": (p.stdout + p.stderr).strip().splitlines()[-12:],
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=1) + "\n",
                        encoding="utf-8", newline="\n")
    print(f"recorded: {cmd}  exit {p.returncode}")
    return p.returncode


def check(claim: str, evidence: Path) -> int:
    low = claim.lower()
    asserts_terminal = any(w in low for w in TERMINAL)
    if not asserts_terminal:
        print("CLAIM GATE: the claim asserts no terminal state. Nothing to prove.")
        return 0

    if not evidence.exists():
        print("CLAIM GATE REFUSES: the claim asserts a terminal state and no "
              f"evidence file exists at {evidence}.")
        print("  A completion claim is an artefact with commands behind it. "
              "Record them with --record before making it.")
        return 1

    doc = json.loads(evidence.read_text(encoding="utf-8"))
    entries = doc.get("entries", [])
    if not entries:
        print("CLAIM GATE REFUSES: the evidence file holds zero commands.")
        return 1

    failed = [e for e in entries if e.get("exit") != 0]
    print(f"CLAIM GATE: {len(entries)} command(s) on file, {len(failed)} non-zero.")
    for e in entries:
        mark = "ok  " if e.get("exit") == 0 else "FAIL"
        print(f"  {mark} exit {e.get('exit')}  {e.get('command')[:70]}")

    if failed:
        print("\nCLAIM GATE REFUSES: the claim asserts a terminal state while "
              f"{len(failed)} recorded command(s) exited non-zero. The claim and "
              "the evidence disagree, and the evidence wins (V-6).")
        return 1
    print("\nCLAIM GATE PASSED: every recorded command exited zero. "
          "The claim is supported by the commands beside it.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim")
    ap.add_argument("--evidence-file", default="ops/EVIDENCE_LATEST.json")
    ap.add_argument("--record")
    ap.add_argument("--out", default="ops/EVIDENCE_LATEST.json")
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()

    if a.reset:
        Path(ROOT / a.out).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / a.out).write_text('{"entries": []}\n', encoding="utf-8", newline="\n")
        print(f"evidence reset: {a.out}")
        return 0
    if a.record:
        return record(a.record, ROOT / a.out)
    if a.claim:
        return check(a.claim, ROOT / a.evidence_file)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
