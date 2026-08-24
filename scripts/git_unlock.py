#!/usr/bin/env python3
"""Enumerate and clear every git lock. Host-side only.

Fourth occurrence of the `git_lock_family`. L-115 established that clearing one
lock and declaring the repository unlocked is V-4 restated at the filesystem: a
claim about a property is only sound after enumerating the set. L-122 and L-123
established that the analysis mount cannot unlink inside `.git`, so an agent that
runs git from there manufactures the blocker it then reports. On 2026-08-24 a
stale `index.lock`, four days old in sovereign-infra, made `git add -A` fail
inside a lander whose next line asked "is anything staged", correctly received
"no", and reported a clean tree. Two pull requests were opened containing none of
the work they were named for.

This script refuses to run where it cannot unlink, rather than half-clearing and
reporting success.

Usage:
    python scripts/git_unlock.py --repo "C:\\Users\\Lenovo\\qesis-mcp"
    python scripts/git_unlock.py --repo ... --dry-run
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

#: The full set. L-115: git takes several locks and each blocks a different
#: operation. packed-refs.lock blocked a branch update and REBASE_HEAD.lock
#: blocked an abort, both surfacing as "Another git process seems to be running"
#: while no git process existed.
FIXED = [
    "index.lock",
    "HEAD.lock",
    "ORIG_HEAD.lock",
    "packed-refs.lock",
    "REBASE_HEAD.lock",
    "MERGE_HEAD.lock",
    "FETCH_HEAD.lock",
    "config.lock",
    "shallow.lock",
]

#: Age below which a lock is presumed live rather than stale, in seconds. A lock
#: younger than this with no owning process is still reported, never silently
#: removed, because the competing hypothesis is a process starting up.
STALE_AFTER = 30


def git_processes() -> list[str]:
    """Return running git process descriptions. Empty list means none."""
    try:
        if os.name == "nt":
            out = subprocess.run(
                ["tasklist", "/fi", "imagename eq git.exe", "/fo", "csv", "/nh"],
                capture_output=True, text=True, timeout=30, check=False,
            ).stdout
            return [l for l in out.splitlines() if "git.exe" in l.lower()]
        out = subprocess.run(["pgrep", "-a", "git"], capture_output=True,
                             text=True, timeout=30, check=False).stdout
        return [l for l in out.splitlines() if l.strip()]
    except Exception:
        return []


def find_locks(gitdir: Path) -> list[Path]:
    found = [gitdir / n for n in FIXED]
    found = [p for p in found if p.exists()]
    # Per-branch ref locks, which the fixed list cannot enumerate.
    refs = gitdir / "refs"
    if refs.is_dir():
        found += sorted(refs.rglob("*.lock"))
    logs = gitdir / "logs"
    if logs.is_dir():
        found += sorted(logs.rglob("*.lock"))
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    repo = Path(a.repo)
    gitdir = repo / ".git"
    if not gitdir.is_dir():
        print(f"UNLOCK SKIP: no .git directory at {repo}")
        return 0

    # L-082: a precondition states its abort action inline, next to the check.
    procs = git_processes()
    if procs:
        print("UNLOCK REFUSED: a git process is running. Close it and re-run.")
        for p in procs:
            print(f"  {p}")
        return 2

    locks = find_locks(gitdir)
    if not locks:
        print(f"UNLOCK: {repo.name} has 0 locks. Zero is zero.")
        return 0

    print(f"UNLOCK: {repo.name} has {len(locks)} lock(s), no git process running")
    failed, cleared, held = [], [], []
    for p in locks:
        try:
            age = time.time() - p.stat().st_mtime
        except OSError:
            age = STALE_AFTER + 1
        rel = p.relative_to(gitdir)
        if age < STALE_AFTER:
            held.append(rel)
            print(f"  HELD    {rel}  {age:.0f}s old, below the {STALE_AFTER}s "
                  f"staleness floor. Reported, not removed.")
            continue
        if a.dry_run:
            print(f"  WOULD   {rel}  {age / 3600:.1f}h old")
            continue
        try:
            p.unlink()
            cleared.append(rel)
            print(f"  CLEARED {rel}  {age / 3600:.1f}h old")
        except OSError as exc:
            failed.append((rel, exc.strerror))
            print(f"  FAILED  {rel}  {exc.strerror}")

    if failed:
        # This is the analysis-mount signature. Refuse rather than continue, so
        # the caller never proceeds believing the repository is usable.
        print("\nUNLOCK FAILED. Cannot unlink inside .git from this filesystem. "
              "This is the analysis mount and no git command may be run here at "
              "all, read-only included (L-122, L-123). Run this script on the "
              "host instead.")
        return 1

    print(f"\nUNLOCK DONE: {len(cleared)} cleared, {len(held)} held, 0 failed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
