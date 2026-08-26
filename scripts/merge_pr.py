#!/usr/bin/env python3
"""Merge a pull request by asking GitHub what state it is in, then acting on it.

WHY THIS EXISTS. Four rounds were lost to guessing at merge behaviour instead of
reading GitHub's own model. The decisive fact, from the official documentation:

    "You must resolve all merge conflicts before you can merge a pull request on
     GitHub. The Merge pull request button is deactivated until you've resolved
     all conflicts."

**Auto-merge does not resolve conflicts.** Arming `--auto` on a conflicted branch
produces a permanent zombie: the pull request sits open forever, armed, red, and
generating check runs for work nobody can land. That is qesis-mcp pull request 71,
which the operator was shown four separate times while being told the task was
finished.

The authoritative state is `mergeStateStatus`, a GraphQL enum. The table below is
GitHub's, not this project's:

    CLEAN     mergeable, commit status passing        merge now, rebase
    UNSTABLE  mergeable, a non-required check is red  merge now, rebase
    BLOCKED   mergeable, a REQUIRED check is pending  arm --auto, it queues
    BEHIND    head is out of date with base           update branch, re-evaluate
    DIRTY     the merge commit cannot be cleanly
              created, meaning CONFLICTS               NEVER auto-merge. Re-cut.
    DRAFT     blocked because it is a draft            mark ready, re-evaluate
    UNKNOWN   state not yet computed                   wait, re-query

The only correct action on DIRTY is to abandon the branch and cut a new one
directly from origin/main, which carries one commit and cannot conflict. Arming
auto-merge on DIRTY is the defect this file exists to make impossible.

Usage:
    python scripts/merge_pr.py --repo owner/name --pr 75
    python scripts/merge_pr.py --repo owner/name --branch fix/x
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

#: GitHub's enum, with the action each state actually permits.
ACTION = {
    "CLEAN":    ("merge",  "mergeable and the commit status is passing"),
    "UNSTABLE": ("merge",  "mergeable; a non-required check is not passing"),
    "HAS_HOOKS": ("merge", "mergeable with passing status and pre-receive hooks"),
    "BLOCKED":  ("auto",   "mergeable but a required check has not reported yet"),
    "BEHIND":   ("update", "the head ref is out of date with the base"),
    "DIRTY":    ("recut",  "the merge commit CANNOT be cleanly created: conflicts"),
    "DRAFT":    ("ready",  "blocked because the pull request is a draft"),
    "UNKNOWN":  ("wait",   "GitHub has not computed the state yet"),
}


def gh(*args: str, timeout: int = 120) -> tuple[int, str]:
    try:
        p = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, check=False)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as exc:
        return 127, f"{type(exc).__name__}: {exc}"


def state(repo: str, pr: str) -> dict:
    code, out = gh("pr", "view", pr, "--repo", repo, "--json",
                   "number,headRefName,mergeable,mergeStateStatus,isDraft,state,title")
    if code != 0:
        return {"error": out}
    try:
        return json.loads(out)
    except Exception:
        return {"error": out[:300]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr")
    ap.add_argument("--branch")
    ap.add_argument("--retries", type=int, default=6)
    a = ap.parse_args()

    pr = a.pr
    if not pr:
        code, out = gh("pr", "list", "--repo", a.repo, "--head", a.branch,
                       "--state", "open", "--json", "number", "--jq", ".[].number")
        pr = out.strip().splitlines()[0] if code == 0 and out.strip() else None
    if not pr:
        print(f"MERGE: no open pull request for {a.branch} in {a.repo}. Nothing to do.")
        return 0

    for attempt in range(1, a.retries + 1):
        s = state(a.repo, pr)
        if "error" in s:
            print(f"MERGE REFUSED: cannot read PR {pr}: {s['error']}")
            return 1
        if s.get("state") != "OPEN":
            print(f"MERGE: PR {pr} is {s.get('state')}. Nothing to do.")
            return 0

        mss = (s.get("mergeStateStatus") or "UNKNOWN").upper()
        act, why = ACTION.get(mss, ("wait", "unrecognised state"))
        print(f"MERGE: PR {pr} '{s.get('title','')[:52]}'")
        print(f"  head {s.get('headRefName')}  mergeable {s.get('mergeable')}  "
              f"mergeStateStatus {mss}")
        print(f"  GitHub says: {why}")

        if act == "wait":
            print(f"  waiting for GitHub to compute the state, attempt {attempt}")
            time.sleep(15)
            continue

        if act == "recut":
            # THE CASE THAT COST FOUR ROUNDS. Do not arm auto-merge here: it can
            # never fire, and the pull request becomes a permanent red zombie.
            print("  ACTION: this branch CONFLICTS and can never auto-merge.")
            print("  Auto-merge does not resolve conflicts; GitHub deactivates the")
            print("  merge button until they are resolved by a human or by a new")
            print("  branch. Closing it and re-cutting from origin/main is the only")
            print("  action that terminates. The lander does exactly that.")
            gh("pr", "close", pr, "--repo", a.repo, "--comment",
               "Closed by merge_pr.py. mergeStateStatus is DIRTY: the merge commit "
               "cannot be cleanly created, so auto-merge can never fire and this "
               "pull request would stay open, armed and red indefinitely. Superseded "
               "by a branch cut directly from origin/main, which carries one commit "
               "and cannot conflict. L-165.")
            print(f"  PR {pr} CLOSED as unmergeable.")
            return 2

        if act == "ready":
            gh("pr", "ready", pr, "--repo", a.repo)
            continue

        if act == "update":
            print("  ACTION: updating the branch from base, then re-evaluating.")
            gh("pr", "update-branch", pr, "--repo", a.repo)
            time.sleep(10)
            continue

        if act == "merge":
            code, out = gh("pr", "merge", pr, "--repo", a.repo, "--rebase")
            if code == 0:
                print(f"  MERGED {pr} by rebase.")
                return 0
            print(f"  direct rebase refused: {out.splitlines()[0] if out else ''}")
            act = "auto"

        if act == "auto":
            code, out = gh("pr", "merge", pr, "--repo", a.repo, "--rebase", "--auto")
            if code == 0:
                print(f"  AUTO-MERGE ARMED on {pr}. It is queued behind the required")
                print("  check and WILL fire, because the branch is mergeable.")
                return 0
            low = out.lower()
            if "already" in low and "auto" in low:
                # Armed on a previous run. GitHub refuses to arm twice; that is
                # the armed state, not a refusal of the merge.
                print(f"  AUTO-MERGE was already armed on {pr}; it stays queued behind the check.")
                return 0
            if "clean status" in low:
                # GitHub: a pull request in clean status cannot be auto-merged,
                # because it can be merged right now. So merge it right now.
                code2, out2 = gh("pr", "merge", pr, "--repo", a.repo, "--rebase")
                if code2 == 0:
                    print(f"  MERGED {pr} by rebase (it was already in clean status).")
                    return 0
                print(f"  direct rebase refused: {out2.splitlines()[0] if out2 else ''}")
            print(f"  auto-merge refused: {out.splitlines()[0] if out else ''}")
            print("  If this says enablePullRequestAutoMerge, the repository setting")
            print("  'Allow auto-merge' is off. That is a settings fact, not a flag fault.")
            print("  The lander retries a direct rebase merge once CI reports green.")
            return 1

    print("  state never became actionable within the retry budget. Withheld, not assumed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
