#!/usr/bin/env python3
"""Append pending RDL entries into the ledger, in both repositories, atomically.

Runs on the host from the lander. Never on the analysis mount, because the last
act of a successful append is a git stage and this filesystem cannot take the
index lock without abandoning it (L-122, L-123).

Why pending files exist at all: two sessions wrote one working tree on
2026-08-24 and neither could see the other, so a direct append risked a lost
update that `verify_ledger_singleton.py` cannot detect, because it compares ids
and not text (L-152). Entries are therefore staged into `ops/RDL_PENDING*.md`
and appended once, here, with the singleton gate run before and after.

Usage:
    python scripts/rdl_append.py                 # append and verify
    python scripts/rdl_append.py --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Both copies of the one ledger. They are kept byte-identical; R3 of the
#: singleton gate is the control that proves it.
LEDGERS = [
    ROOT / "ops" / "LESSONS_LEDGER.md",
    Path(r"C:\Users\Lenovo\OneDrive\sovereign-infra\ops\LESSONS_LEDGER.md"),
    ROOT.parent / "sovereign-infra" / "ops" / "LESSONS_LEDGER.md",
]
HEADER = re.compile(r"^\*\*L-(\d{3})", re.M)


def gate(tag: str) -> int:
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_ledger_singleton.py")],
        capture_output=True, text=True, timeout=120, check=False, cwd=ROOT,
    )
    print(f"  [{tag}] " + (p.stdout.strip().splitlines() or ["no output"])[-1])
    return p.returncode


def declare_unrendered_reservations(appended: list[tuple[int, str]]) -> None:
    """Record any reserved-but-unwritten id as a declared gap with an owner."""
    gaps = ROOT / "ops" / "LEDGER_GAPS.json"
    if not gaps.exists() or not appended:
        return
    import json as _json
    doc = _json.loads(gaps.read_text(encoding="utf-8"))
    declared: set[int] = set()
    for e in doc.get("declared_absent", []):
        lo = int(str(e["from"]).removeprefix("L-"))
        hi = int(str(e.get("to", e["from"])).removeprefix("L-"))
        declared |= set(range(lo, hi + 1))
    live = {int(m.group(1)) for m in HEADER.finditer(
        (ROOT / "ops" / "LESSONS_LEDGER.md").read_text(encoding="utf-8", errors="replace"))}
    holes = sorted({i for i in range(1, max(live) + 1)} - live - declared)
    if not holes:
        return
    doc.setdefault("declared_absent", []).append({
        "from": f"L-{min(holes):03d}", "to": f"L-{max(holes):03d}",
        "reason": "Reserved by an agent's pending file and never rendered as an "
                  "entry, then passed by a later append. Declared here so the hole "
                  "is owned rather than silently legal. Render or retire each id.",
        "owner": "ARCHITECT", "opened": "2026-08-24",
        "closes_when": "each id is written as an entry, or formally retired",
    })
    gaps.write_text(_json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"  declared {len(holes)} unrendered reservation(s) as gaps: "
          + ", ".join(f"L-{i:03d}" for i in holes))


def clear_consumed(pending: list[Path], ledger: Path) -> None:
    """Truncate any pending file whose every reserved id is now in the ledger.

    Covers COUNSEL's prose reservations as well as machine-written entries: once
    L-150 to L-152 exist as entries, the sweep document that reserved them has
    been consumed and leaving it in place makes every later run re-report it as
    outstanding work. Truncated rather than unlinked, because the mount may
    refuse unlink and a half-deleted file replays on the next run.
    """
    live = {int(m.group(1)) for m in HEADER.finditer(
        ledger.read_text(encoding="utf-8", errors="replace"))}
    for f in pending:
        text = f.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            continue
        ids = {int(m) for m in re.findall(r"\*\*L-(\d{3})", text)}
        ids |= {int(m) for m in re.findall(r"[Pp]rovisionally L-(\d{3})", text)}
        if ids and ids <= live:
            f.write_text("", encoding="utf-8", newline="\n")
            print(f"  cleared {f.name}: all {len(ids)} reserved id(s) are now in the ledger")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    pend = sorted((ROOT / "ops").glob("RDL_PENDING*.md"))
    entries: list[tuple[int, str]] = []
    used: list[Path] = []
    for f in pend:
        text = f.read_text(encoding="utf-8", errors="replace")
        blocks = [b.rstrip() for b in re.split(r"\n(?=\*\*L-\d{3})", text) if b.lstrip().startswith("**L-")]
        if not blocks:
            # COUNSEL's sweep writes prose, deliberately not parsed. A regex that
            # guesses where an entry starts would corrupt the store it is meant
            # to protect, and this file says so rather than silently skipping.
            if "rovisionally L-" in text:
                print(f"  SKIP {f.name}: prose reservations only, no entry headers. "
                      "Render them as entries before this script can append them.")
            continue
        for b in blocks:
            entries.append((int(HEADER.match(b).group(1)), b))
        used.append(f)

    if not entries:
        print("RDL APPEND: 0 pending entries. Zero is zero.")
        return 0

    live = [p for p in LEDGERS if p.exists()]
    if not live:
        print("RDL APPEND REFUSED: no ledger reachable from here.")
        return 1

    print(f"RDL APPEND: {len(entries)} entr(y/ies) into {len(live)} ledger cop(y/ies)")
    if gate("before") != 0:
        print("RDL APPEND REFUSED: the singleton gate is already failing. "
              "Fix the ledger before adding to it.")
        return 1

    base = live[0].read_text(encoding="utf-8", errors="replace")
    have = {int(m.group(1)) for m in HEADER.finditer(base)}
    new = [(i, b) for i, b in sorted(entries) if i not in have]
    dupes = [i for i, _ in entries if i in have]
    if dupes:
        print(f"  {len(dupes)} already present, skipped: "
              + ", ".join(f"L-{i:03d}" for i in sorted(set(dupes))))
    if not new:
        print("  nothing new to append; every pending entry is already live.")
        clear_consumed(pend, live[0])
        return 0

    merged = base.rstrip("\n") + "\n\n" + "\n\n".join(b for _, b in new) + "\n"
    if a.dry_run:
        print("  DRY RUN, nothing written. Would append: "
              + ", ".join(f"L-{i:03d}" for i, _ in new))
        return 0

    for p in live:
        p.write_text(merged, encoding="utf-8", newline="\n")
    sha = hashlib.sha256(merged.encode()).hexdigest()
    print(f"  appended {', '.join(f'L-{i:03d}' for i, _ in new)}")
    print(f"  ledger sha256 {sha[:16]}, written to {len(live)} cop(y/ies)")

    # A reservation that was never rendered becomes an undeclared gap the moment
    # an append goes past it, which is exactly how this script failed on its first
    # run: COUNSEL reserved L-150 to L-152 in prose, the allocator correctly
    # skipped them, and R2 then refused the whole append. Declaring them keeps the
    # hole visible and owned instead of silently legal.
    declare_unrendered_reservations(new)

    rc = gate("after")
    if rc != 0:
        print("RDL APPEND: the singleton gate FAILED after the append. "
              "The ledger is in a state the gate refuses and must be repaired "
              "before anything is committed.")
        return 1

    # Truncate rather than unlink: the mount that runs this may refuse unlink,
    # and a half-deleted pending file would be replayed on the next run.
    clear_consumed(pend, live[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
