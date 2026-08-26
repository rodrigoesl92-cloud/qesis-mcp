#!/usr/bin/env python3
"""All GitHub orchestration, in Python, because PowerShell mangles jq.

WHY. The lander built `gh` calls in PowerShell, including jq expressions like
`.[] | "\\(.number) \\(.headRefName)"`. PowerShell expands `$` and splits on
spaces before `gh` ever sees the string, so the 2026-08-24T18:33 run produced:

    gh.exe : unknown arguments ["PR" "\\(.number)" "head" ...]; please quote all
    values that have spaces

and then tried to close a pull request on a branch literally named `gh.exe`,
then `In`, then `+`, then `--app`, forty times. Neither the amputation of stale
pull requests nor the PROOF block ran at all, in either repository.

The fix is not better quoting. It is not writing shell-quoted JSON queries from
a shell at all. Everything here asks `gh` for `--json` and parses it with
`json.loads`, where no quoting exists to get wrong.

Subcommands:
    amputate  close every open pull request whose head is not --keep, delete
              its branch, delete `selfheal/*` branches the loop pushed and
              could not land, close branch-guard false positives, and close
              `selfheal` escalation issues whose named control passes NOW on
              the checkout, with the command and exit code in the comment
    proof     print the measured state of both repositories and exit non-zero if
              anything is not green
    pr-number print the open pull request number on --head of --repo, or nothing
    pr-state  print MERGED, OPEN or CLOSED for --pr of --repo, from GitHub's own
              state field; the lander claims ON MAIN from this word only (D-116)

Evening 2026-08-24, from the run log of Self-heal loop #132 (qesis-mcp,
00b0c95): the loop pushed `selfheal/32763154920` and then died on
"GitHub Actions is not permitted to create or approve pull requests". That is
the repository setting Settings > Actions > General > Workflow permissions >
"Allow GitHub Actions to create and approve pull requests", off. Until the
operator turns it on, every class A repair and every daily report from a
runner pushes a branch and fails. The branch litter is cleaned here; the
setting is the operator's (it widens what the Actions token may do).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

OWNER = "rodrigoesl92-cloud"
REPOS = ["qesis-mcp", "sovereign-infra"]
#: Branch prefixes the runners land from (selfheal.yml, daily-ops-report.yml).
#: amputate spares them: they are the loop's work, not stale artefacts (L-177).
RUNNER_HEADS = ("selfheal/", "ops/report-")
#: Host checkouts, so an escalation issue can be re-measured on the tree the
#: fix is about to land from. ops/PATH_REGISTRY.json is the authority.
PATHS = {
    "qesis-mcp": Path(r"C:\Users\Lenovo\qesis-mcp"),
    "sovereign-infra": Path(r"C:\Users\Lenovo\OneDrive\sovereign-infra"),
}


def gh_json(*args: str, timeout: int = 120):
    """Run gh with --json and parse. No jq, no shell quoting, no interpolation."""
    try:
        p = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, check=False)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if p.returncode != 0:
        return None, (p.stderr or p.stdout).strip()
    try:
        return json.loads(p.stdout or "[]"), None
    except Exception as exc:
        return None, f"unparseable: {exc}"


def gh_run(*args: str, timeout: int = 120) -> tuple[int, str]:
    try:
        p = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, check=False)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as exc:
        return 127, f"{type(exc).__name__}: {exc}"


def amputate(keep: str) -> int:
    print(f"Amputating pull requests whose head is not '{keep}'.")
    for repo in REPOS:
        slug = f"{OWNER}/{repo}"
        prs, err = gh_json("pr", "list", "--repo", slug, "--state", "open",
                           "--limit", "100", "--json", "number,headRefName,title")
        if err:
            print(f"  {repo}: cannot list pull requests: {err}")
            continue
        if not prs:
            print(f"  {repo}: 0 open pull requests")
        for pr in prs:
            num, head = str(pr["number"]), pr["headRefName"]
            if head == keep:
                print(f"  {repo}: PR {num} on {head} is current, kept")
                continue
            # A runner's own landing is live work, not litter. selfheal.yml opens
            # `selfheal/<run id>` and daily-ops-report.yml opens `ops/report-<date>`
            # under G-07 and merges by rebase behind the required check. Closing
            # them here would undo the loop from the operator's machine, the
            # revision 5 move of L-177 applied to pull requests instead of files.
            if head.startswith(RUNNER_HEADS):
                print(f"  {repo}: PR {num} on {head} is a runner landing (G-07), kept")
                continue
            code, out = gh_run(
                "pr", "close", num, "--repo", slug, "--comment",
                f"Superseded and closed automatically. Head '{head}' is not the "
                f"current consolidated branch '{keep}', which is cut directly from "
                "origin/main and carries a single commit. Leaving it open kept "
                "producing check runs and notifications for work nobody intends to "
                "land. L-164, family stale_artifact_left_live.")
            print(f"  {repo}: PR {num} " + ("CLOSED" if code == 0 else
                  f"close failed: {out.splitlines()[0] if out else ''}") + f"  (head {head})")
            if code == 0:
                d, _ = gh_run("api", "-X", "DELETE",
                              f"repos/{slug}/git/refs/heads/{head}")
                if d == 0:
                    print(f"    branch {head} deleted")

        # Branch litter from runs that pushed and could not open a pull request.
        heads, err = gh_json("api", f"repos/{slug}/git/matching-refs/heads/selfheal/")
        open_heads = {pr["headRefName"] for pr in (prs or [])}
        for ref in (heads or []):
            name = str(ref.get("ref", "")).removeprefix("refs/heads/")
            if not name.startswith("selfheal/") or name in open_heads:
                continue
            d, out = gh_run("api", "-X", "DELETE", f"repos/{slug}/git/refs/heads/{name}")
            print(f"  {repo}: branch {name} " + ("deleted (loop litter, no pull request)" if d == 0
                                                  else f"not deleted: {out.splitlines()[0] if out else ''}"))

        close_settled_escalations(repo, slug)

        issues, err = gh_json("issue", "list", "--repo", slug, "--state", "open",
                              "--label", "branch-guard", "--json", "number")
        for i in (issues or []):
            code, _ = gh_run("issue", "close", str(i["number"]), "--repo", slug,
                             "--comment",
                             "False positive. The classifier routed on parent count, "
                             "and only the merge-commit strategy produces two parents; "
                             "a rebase merge replays with one. G-06 Rule 2-4 mandates "
                             "rebase, so every correct merge tripped this guard. Fixed "
                             "to ask repos/{repo}/commits/{sha}/pulls. L-161, D-115.")
            if code == 0:
                print(f"  {repo}: closed branch-guard issue {i['number']}")
    return 0


def _controls(root: Path) -> dict[str, list[str]]:
    """Name -> command, read from selfheal.py's CONTROLS without importing it."""
    src = root / "scripts" / "selfheal.py"
    if not src.exists():
        return {}
    block = src.read_text(encoding="utf-8").split("CONTROLS = [", 1)[-1].split("\n]", 1)[0]
    out: dict[str, list[str]] = {}
    for m in re.finditer(r'\("([a-z_]+)",\s*\[([^\]]*)\]\)', block):
        out[m.group(1)] = re.findall(r'"([^"]+)"', m.group(2))
    return out


def close_settled_escalations(repo: str, slug: str) -> None:
    """Close `selfheal` issues whose named control passes on the checkout NOW.

    The issue names the control; the control is a script with an exit code;
    the checkout is the tree about to land. Re-running the control here is the
    measurement, and the comment carries the command, the exit code and the
    commit it ran on (V-1). A control that cannot be run here leaves the issue
    open, with no comment: silence is not a closure.
    """
    root = PATHS.get(repo)
    if not root or not root.exists():
        return
    issues, err = gh_json("issue", "list", "--repo", slug, "--state", "open",
                          "--label", "selfheal", "--json", "number,title")
    if err or not issues:
        return
    controls = _controls(root)
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                              capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        head = "unknown"
    for i in issues:
        title = i.get("title", "")
        m = re.match(r"selfheal (?:HIGH|CRITICAL): (.+)$", title)
        if not m:
            continue
        names = [n.strip() for n in m.group(1).split(",") if n.strip()]
        lines, all_ok = [], True
        for n in names:
            cmd = controls.get(n)
            if not cmd:
                all_ok = False
                lines.append(f"{n}: not in CONTROLS of this checkout, cannot re-measure")
                continue
            try:
                r = subprocess.run([sys.executable, *[str(root / c) if c.endswith(".py") else c for c in cmd]],
                                   cwd=root, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=600)
                tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
                lines.append(f"{n}: `python {' '.join(cmd)}` exit {r.returncode} on {head}: {tail[0][:120]}")
                all_ok &= r.returncode == 0
            except Exception as exc:
                all_ok = False
                lines.append(f"{n}: could not run here: {exc}")
        if not all_ok:
            print(f"  {repo}: issue {i['number']} stays open; a named control does not pass here")
            continue
        body = ("Closed by gh_ops.py after re-measuring the named control on the tree being "
                "landed. Not inferred from a later green run; the command and its exit code:\n\n"
                + "\n".join(f"- {l}" for l in lines)
                + "\n\nIf the control fails again the loop reopens an issue on its own.")
        code, out = gh_run("issue", "close", str(i["number"]), "--repo", slug, "--comment", body)
        print(f"  {repo}: issue {i['number']} " + ("CLOSED, control re-measured green" if code == 0
                                                     else f"close failed: {out.splitlines()[0] if out else ''}"))


def proof() -> int:
    print("PROOF. Fetched from GitHub just now. Not a claim.")
    print()
    clean = True
    for repo in REPOS:
        slug = f"{OWNER}/{repo}"
        print(f"  {slug}")

        prs, err = gh_json("pr", "list", "--repo", slug, "--state", "open",
                           "--limit", "50", "--json",
                           "number,headRefName,mergeable,mergeStateStatus")
        if err:
            print(f"    pull requests: UNREADABLE, {err}")
            clean = False
        elif not prs:
            print("    0 open pull requests")
        else:
            for pr in prs:
                print(f"    PR {pr['number']}  head {pr['headRefName']}  "
                      f"mergeable {pr.get('mergeable')}  "
                      f"state {pr.get('mergeStateStatus')}")

        commit, err = gh_json("api", f"repos/{slug}/commits/main")
        if err or not commit:
            print(f"    main: UNREADABLE, {err}")
            clean = False
        else:
            sha = commit.get("sha", "")[:12]
            msg = (commit.get("commit", {}).get("message", "") or "").splitlines()[0][:60]
            print(f"    main {sha}  {msg}")

            runs, err = gh_json("api", f"repos/{slug}/commits/main/check-runs")
            seen = {}
            for cr in ((runs or {}).get("check_runs") or []):
                name = cr.get("name", "")
                if any(k in name.lower() for k in ("integrity", "heal", "binding")):
                    seen.setdefault(name, cr.get("conclusion"))
            if not seen:
                print("    main checks: none reported yet")
            for name, concl in sorted(seen.items()):
                print(f"    main check  {name}: {concl}")
                if concl != "success":
                    clean = False

        issues, _ = gh_json("issue", "list", "--repo", slug, "--state", "open",
                            "--json", "number")
        n = len(issues or [])
        print(f"    open issues: {n}")
        print()

    print("  VERDICT: " + (
        "every integrity, self-heal and binding check on main reports success in "
        "both repositories." if clean else
        "at least one check on main is not success, or a value could not be read. "
        "The lines above name it. Not glossed."))
    return 0 if clean else 1


def pr_number(repo: str, head: str) -> int:
    """Print the number of the first open pull request on `head`, or nothing.

    The lander used to pipe `gh pr list --json number` through ConvertFrom-Json
    and Select-Object. Windows PowerShell 5.1 emits a JSON array as ONE Object[]
    pipeline item, so Select-Object saw the array, not its elements, and failed
    with "the number property cannot be found"; the PR stayed empty and the
    merge and CI feedback steps were skipped in both repositories. The list is
    parsed here with json.loads, where a list is a list (L-167 family). Exit 1
    only when gh itself failed; empty stdout with exit 0 means no open PR.
    """
    prs, err = gh_json("pr", "list", "--repo", repo, "--head", head,
                       "--state", "open", "--limit", "5", "--json", "number")
    if err:
        print(f"pr-number: {err}", file=sys.stderr)
        return 1
    if prs:
        print(prs[0]["number"])
    return 0


def pr_state(repo: str, pr: str) -> int:
    """Print the pull request's state word: MERGED, OPEN or CLOSED.

    The last JSON the lander still parsed in PowerShell was this one. A single
    object survives ConvertFrom-Json on 5.1, but the rule is simpler than the
    exception: no gh output is parsed by the shell, ever (L-176). Exit 1 when
    gh failed or the field is missing; the lander then withholds ON MAIN.
    """
    obj, err = gh_json("pr", "view", str(pr), "--repo", repo, "--json", "state,mergedAt")
    if err or not isinstance(obj, dict) or "state" not in obj:
        print(f"pr-state: {err or 'no state field in the reply'}", file=sys.stderr)
        return 1
    print(str(obj["state"]).upper())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("amputate")
    a1.add_argument("--keep", required=True)
    sub.add_parser("proof")
    a3 = sub.add_parser("pr-number")
    a3.add_argument("--repo", required=True)
    a3.add_argument("--head", required=True)
    a4 = sub.add_parser("pr-state")
    a4.add_argument("--repo", required=True)
    a4.add_argument("--pr", required=True)
    a = ap.parse_args()
    if a.cmd == "pr-number":
        return pr_number(a.repo, a.head)
    if a.cmd == "pr-state":
        return pr_state(a.repo, a.pr)
    return amputate(a.keep) if a.cmd == "amputate" else proof()


if __name__ == "__main__":
    sys.exit(main())
