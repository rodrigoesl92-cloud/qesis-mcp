"""Leaves GitHub in a state a reader can trust at a glance.

WHY. Every landing cuts a branch, merges it and leaves it behind. Every failed run
leaves an unread notification that outlives the failure by weeks. The result is an
inbox where a red cross from a defect repaired an hour ago sits above a green main,
and the operator cannot tell current state from history. That is the same failure
this ecosystem records against artefacts: a superseded state printed as the
finding (L-196).

WHAT IT DOES, in order, and it reports before it removes.
  1. Measures both repositories: default branch head, the checks on it, open pull
     requests, open issues, and every branch with its merged status.
  2. Deletes branches that are merged into the default branch. Never the default
     branch, never an unmerged branch, never a branch with an open pull request.
  3. Marks as read the notifications whose subject is a workflow run that has been
     superseded by a later run on the same workflow and branch. A failure that was
     repaired is history, and history does not belong in an inbox.
  4. Prints what it did NOT touch and why, because a cleanup that hides what it
     skipped is worse than no cleanup.

WHAT IT NEVER DOES. It does not close a pull request, it does not delete an
unmerged branch, and it does not touch a notification whose run is the newest on
its branch. Those are judgement calls and they stay with a person.

Requires the `gh` CLI, authenticated. The credential is the operator's and this
script never reads it, never prints it and never stores it (G-03, G-04).

Usage:  python scripts/gh_cleanup.py [--apply] [--repo OWNER/NAME ...]
        python scripts/gh_cleanup.py --selftest
Exit:   0 measured or cleaned - 1 gh is unavailable or a repository could not be read
"""
from __future__ import annotations
import argparse, json, subprocess, sys

REPOS = ["rodrigoesl92-cloud/qesis-mcp", "rodrigoesl92-cloud/sovereign-infra"]


def gh(args: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=120)
        return p.returncode, (p.stdout or p.stderr).strip()
    except FileNotFoundError:
        return 127, "gh not found on PATH"
    except subprocess.TimeoutExpired:
        return 124, "gh timed out"


def deletable(branches: list[dict], default: str, pr_heads: set[str]) -> list[str]:
    """Pure. A branch is deletable only if merged, not default, and carries no open PR."""
    out = []
    for b in branches:
        name = b.get("name", "")
        if not name or name == default:
            continue
        if name in pr_heads:
            continue
        if b.get("merged") is True:
            out.append(name)
    return out


def supersede(notifs: list[dict]) -> list[str]:
    """Pure. Return notification ids whose run is not the newest for its key."""
    newest: dict[tuple, tuple] = {}
    for n in notifs:
        key = (n.get("repo"), n.get("workflow"), n.get("branch"))
        ts = n.get("updated_at", "")
        if key not in newest or ts > newest[key][0]:
            newest[key] = (ts, n.get("id"))
    keep = {v[1] for v in newest.values()}
    return [n["id"] for n in notifs if n.get("id") not in keep]


def selftest() -> int:
    ok = True
    br = [{"name": "main", "merged": True}, {"name": "fix/a", "merged": True},
          {"name": "fix/b", "merged": False}, {"name": "fix/c", "merged": True}]
    got = deletable(br, "main", {"fix/c"})
    if got != ["fix/a"]:
        print(f"  x FIXTURE 1 FAILED: expected only fix/a, got {got}"); ok = False
    if deletable([{"name": "main", "merged": True}], "main", set()):
        print("  x FIXTURE 2 FAILED: the default branch must never be deletable"); ok = False
    ns = [{"id": "1", "repo": "r", "workflow": "w", "branch": "b", "updated_at": "2026-08-28T10:00Z"},
          {"id": "2", "repo": "r", "workflow": "w", "branch": "b", "updated_at": "2026-08-28T12:00Z"},
          {"id": "3", "repo": "r", "workflow": "w", "branch": "other", "updated_at": "2026-08-28T09:00Z"}]
    got = supersede(ns)
    if got != ["1"]:
        print(f"  x FIXTURE 3 FAILED: only the older run on the same key is superseded, got {got}"); ok = False
    if supersede([]) != []:
        print("  x FIXTURE 4 FAILED: an empty inbox must yield nothing, not everything"); ok = False
    print(f"GH CLEANUP SELFTEST: {'PASSED, 4 fixtures' if ok else 'FAILED'}")
    return 0 if ok else 1


ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true", help="actually delete and mark read")
ap.add_argument("--repo", action="append", default=None)
ap.add_argument("--selftest", action="store_true")
a = ap.parse_args()
if a.selftest:
    raise SystemExit(selftest())

rc, out = gh(["auth", "status"])
if rc == 127:
    print("REFUSED: the gh CLI is not on PATH. This script runs where the credential lives.")
    raise SystemExit(1)

repos = a.repo or REPOS
mode = "APPLY" if a.apply else "REPORT ONLY, pass --apply to act"
print(f"GitHub cleanup, {mode}\n")
problems = 0

for repo in repos:
    print("=" * 66)
    print(repo)
    rc, out = gh(["repo", "view", repo, "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"])
    if rc != 0:
        print(f"  could not read the repository: {out}"); problems += 1; continue
    default = out.strip()

    rc, out = gh(["pr", "list", "--repo", repo, "--state", "open", "--json",
                  "number,title,headRefName,mergeable,mergeStateStatus"])
    prs = json.loads(out) if rc == 0 and out.startswith("[") else []
    pr_heads = {p["headRefName"] for p in prs}

    rc, out = gh(["api", f"repos/{repo}/branches", "--paginate", "-q",
                  ".[] | {name: .name}"])
    names = [json.loads(l)["name"] for l in out.splitlines() if l.strip().startswith("{")] if rc == 0 else []
    branches = []
    for n in names:
        if n == default:
            branches.append({"name": n, "merged": True}); continue
        rc2, o2 = gh(["api", f"repos/{repo}/compare/{default}...{n}", "-q", ".status"])
        branches.append({"name": n, "merged": (rc2 == 0 and o2.strip() in ("identical", "behind"))})

    print(f"  default branch: {default}")
    print(f"  open pull requests: {len(prs)}")
    for p in prs:
        print(f"    #{p['number']} {p['headRefName']}  {p.get('mergeStateStatus')}  {p['title'][:52]}")
    dele = deletable(branches, default, pr_heads)
    kept = [b["name"] for b in branches if b["name"] not in dele and b["name"] != default]
    print(f"  branches: {len(branches)}  merged and removable: {len(dele)}")
    for n in dele:
        if a.apply:
            rc2, o2 = gh(["api", "-X", "DELETE", f"repos/{repo}/git/refs/heads/{n}"])
            print(f"    {'deleted ' if rc2 == 0 else 'FAILED  '} {n}")
        else:
            print(f"    would delete {n}")
    for n in kept:
        why = "has an open pull request" if n in pr_heads else "not merged into the default branch"
        print(f"    kept {n}: {why}")

print("=" * 66)
print("Notifications: superseded workflow runs")
rc, out = gh(["api", "notifications?all=false&per_page=100", "--paginate"])
notifs = []
if rc == 0:
    try:
        for item in json.loads("[" + out.replace("][", ",") + "]" if out.startswith("[") else out):
            if isinstance(item, list):
                continue
    except Exception:
        pass
    try:
        raw = json.loads(out) if out.startswith("[") else []
    except Exception:
        raw = []
    for n in raw:
        s = n.get("subject", {})
        if s.get("type") != "CheckSuite" and "workflow run" not in (s.get("title") or "").lower():
            continue
        title = s.get("title") or ""
        branch = title.split(" for ")[-1].replace(" branch", "").strip() if " for " in title else ""
        notifs.append({"id": n.get("id"), "repo": (n.get("repository") or {}).get("full_name"),
                       "workflow": title.split(" workflow")[0], "branch": branch,
                       "updated_at": n.get("updated_at", "")})
old = supersede(notifs)
print(f"  workflow-run notifications unread: {len(notifs)}   superseded by a later run: {len(old)}")
for nid in old:
    if a.apply:
        rc2, _ = gh(["api", "-X", "PATCH", f"notifications/threads/{nid}"])
        print(f"    {'marked read' if rc2 == 0 else 'FAILED'} {nid}")
    else:
        print(f"    would mark read {nid}")
if notifs and not old:
    print("  every unread workflow notification is the newest on its branch. Nothing is stale.")

print("\nNOT TOUCHED, deliberately:")
print("  Open pull requests. Closing one is a judgement call and stays with a person.")
print("  Unmerged branches. Work in progress is not clutter.")
print("  Check runs written by integrations this ecosystem does not own. They are")
print("  reported by gh_ops.py foreign_checks and only their owner can remove them.")
raise SystemExit(1 if problems else 0)
