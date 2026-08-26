#!/usr/bin/env python3
"""Name the commit the lander must diff against, so it restores only what changed.

WHY (L-177). Revision 5 of the lander captured the whole working tree as a
holding commit, cut a branch from origin/main and then ran
`git checkout <snapshot> -- .`: every tracked file on the operator's disk was
written over origin/main. That is correct only while nothing else ever commits
to main. The self-heal loop and the daily ops report commit to main from a
runner (SH-7, G-07), and the moment the repository setting lets them (L-174)
the next click would have silently reverted every one of their commits, with
a green summary. The disk is the source of the SESSION'S changes, not of the
repository.

WHAT IS RESTORED INSTEAD. The delta between a BASE commit and the snapshot:
files the session added, changed or deleted. The base is the most recent
commit on the disk's own history whose TREE is also the tree of a commit on
origin/main, because that is the last state the disk and the remote agreed on:

    normal       HEAD is the commit the lander synced to after the last merge;
                 its tree is on main.                          base = HEAD
    rebased      HEAD is the commit the lander pushed; main carries it as a
                 rebased commit with a different hash and the SAME tree.
                                                                 base = HEAD
    aborted run  HEAD is a holding commit ("wip: capture ...") on top of the
                 pushed commit; its tree is not on main.        base = HEAD~1
    push failed  HEAD is a real commit never pushed; its tree is not on main.
                                                                 base = HEAD~1

Walk back at most --depth commits; if no ancestor's tree is on main, fall back
to `git merge-base HEAD origin/main` and say so, because a wrong base restores
too much (never too little) and too much is the revision 5 defect, reported.

Read-only git only: rev-parse and log. This runs on the host, in the lander,
never on the analysis mount (L-122, L-123).

Usage:
    python scripts/landing_base.py --repo PATH        # prints the sha, exit 0
    python scripts/landing_base.py --selftest
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {(p.stderr or p.stdout).strip()}")
    return p.stdout.strip()


def base_commit(repo: Path, depth: int = 50, main_depth: int = 400) -> tuple[str, str]:
    """(sha, how). Raises RuntimeError when origin/main is not fetched."""
    main_trees = set(git(repo, "log", f"-{main_depth}", "--format=%T", "origin/main").split())
    head_commits = git(repo, "log", f"-{depth}", "--format=%H %T", "HEAD").splitlines()
    for i, line in enumerate(head_commits):
        sha, tree = line.split()
        if tree in main_trees:
            how = "HEAD" if i == 0 else f"HEAD~{i}"
            return sha, f"{how}, its tree is on origin/main"
    mb = git(repo, "merge-base", "HEAD", "origin/main")
    return mb, (f"merge-base fallback: no tree of the last {depth} disk commits is on "
                "origin/main, so the restore may carry already-landed files (reported, L-177)")


def selftest() -> int:
    """Four repositories, one per scenario, built with real git in a temp dir."""
    def sh(cwd: Path, *a: str) -> str:
        return git(cwd, *a)

    def mk() -> tuple[Path, Path]:
        d = Path(tempfile.mkdtemp())
        remote = d / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
        work = d / "work"
        subprocess.run(["git", "clone", "-q", str(remote), str(work)], check=True,
                       capture_output=True)
        sh(work, "config", "user.email", "t@t"); sh(work, "config", "user.name", "t")
        sh(work, "checkout", "-q", "-b", "main")
        (work / "a.txt").write_text("a\n"); sh(work, "add", "-A"); sh(work, "commit", "-q", "-m", "m0")
        sh(work, "push", "-q", "-u", "origin", "main")
        return remote, work

    results = []
    # normal: HEAD synced to origin/main
    _, w = mk()
    sha, how = base_commit(w)
    results.append(("normal: base is HEAD", sha == sh(w, "rev-parse", "HEAD") and how.startswith("HEAD,")))

    # rebased: pushed commit P on a branch, main carries a rebased twin with the same tree
    remote, w = mk()
    sh(w, "checkout", "-q", "-b", "fix/x")
    (w / "b.txt").write_text("b\n"); sh(w, "add", "-A"); sh(w, "commit", "-q", "-m", "p")
    p_sha = sh(w, "rev-parse", "HEAD")
    sh(w, "push", "-q", "-u", "origin", "fix/x")
    # simulate GitHub's rebase merge: a new commit on main with P's tree and a different hash
    other = Path(tempfile.mkdtemp()) / "o"
    subprocess.run(["git", "clone", "-q", str(remote), str(other)], check=True, capture_output=True)
    sh(other, "config", "user.email", "t@t"); sh(other, "config", "user.name", "t")
    sh(other, "fetch", "-q", "origin", "fix/x")
    tree = sh(other, "rev-parse", f"{p_sha}^{{tree}}")
    m1 = sh(other, "commit-tree", tree, "-p", sh(other, "rev-parse", "HEAD"), "-m", "p (rebased)")
    sh(other, "update-ref", "refs/heads/main", m1); sh(other, "push", "-q", "origin", "main")
    sh(w, "fetch", "-q", "origin")
    sha, how = base_commit(w)
    results.append(("rebased: base is the pushed commit, by tree", sha == p_sha and "HEAD," in how))

    # aborted: a holding commit on top of P
    (w / "c.txt").write_text("c\n"); sh(w, "add", "-A")
    sh(w, "commit", "-q", "-m", "wip: capture the working tree before rebranching")
    sha, how = base_commit(w)
    results.append(("aborted run: base is HEAD~1", sha == p_sha and "HEAD~1" in how))

    # push failed: a real commit never pushed, on top of P (rewrite the holding commit's message)
    sh(w, "commit", "-q", "--amend", "-m", "fix(x): real commit that never reached the remote")
    sha, how = base_commit(w)
    results.append(("push failed: base is HEAD~1", sha == p_sha and "HEAD~1" in how))

    # fallback: nothing on the disk shares a tree with main
    _, w = mk()
    (w / "a.txt").write_text("z\n"); sh(w, "add", "-A"); sh(w, "commit", "-q", "-m", "local only")
    sh(w, "commit", "-q", "--allow-empty", "-m", "x")
    sha, how = base_commit(w, depth=1)
    results.append(("fallback: merge-base, and it says so", sha == sh(w, "merge-base", "HEAD", "origin/main")
                    and "fallback" in how))

    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  landing base: {name}")
    n = sum(ok for _, ok in results)
    print(f"landing base selftest: {n}/{len(results)} fixtures " + ("hold" if n == len(results) else "FAILED"))
    return 0 if n == len(results) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    ap.add_argument("--depth", type=int, default=50)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.repo:
        print("landing_base: --repo is required", file=sys.stderr)
        return 1
    try:
        sha, how = base_commit(Path(a.repo), a.depth)
    except RuntimeError as exc:
        print(f"landing_base: {exc}", file=sys.stderr)
        return 1
    # Both lines to stdout: the lander merges the streams and their order is not
    # guaranteed, so it selects the line that is a 40-character sha.
    print(sha)
    print(f"landing_base: {how}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
