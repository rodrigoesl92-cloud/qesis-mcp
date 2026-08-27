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
    runner-merge
              merge by rebase every open pull request that is a runner landing
              (head prefix AND bot author) and whose owned checks are all green
              on its head commit; --selftest runs the decision over fixtures
              with no network and no credential
    owned     print the check-run names this repository's own workflows produce
              (each job's name, or its id), the set proof and the audit assert

2026-08-26, after the 01:08Z landing (L-179): proof and the audit judged main
by a keyword filter over check names ("integrity", "heal", "binding"), so the
evidence plane's `verify` job (compliance.yml: doctrine gate, credential scans)
was invisible to both, red on main under a GREEN verdict. The set of checks the
ecosystem owns is read from the workflow files, never from a list of words.

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

#: The identities the runners land under. Two independent conditions must BOTH
#: hold before anything merges with nobody in the loop: the head prefix and the
#: author. Either alone is forgeable. A person can name a branch
#: `ops/report-2026-08-26`; a bot label can sit on work a person pushed. The
#: pair cannot be aimed at human work by naming a branch after a runner.
RUNNER_AUTHORS = ("github-actions", "github-actions[bot]",
                  "qesis-ops[bot]", "qesis-selfheal[bot]")

#: Paths a runner landing may not carry. A denylist, deliberately, and the
#: asymmetry is the argument: the set of derived artefacts a class A repair may
#: rebuild is open and grows with the pipeline, so an allowlist over it would
#: start refusing correct repairs the week after it was written. The set of
#: surfaces that decide what is allowed to merge is closed and small. This
#: refuses exactly the thing that must never happen, which is a loop widening
#: its own authority with no person present. `.github/` is listed even though
#: the Actions token already cannot push a workflow change: a control that
#: rests on a platform default holding is one settings change from absent.
RUNNER_REFUSED_PREFIXES = (
    ".github/", "scripts/", "qesis_agents/", "api/", "server.py",
    "LICENSE", "AUTHORS.md", "CLAUDE.md", "SESSION_START.md",
    "ops/GOVERNANCE.md", "ops/ARTICLE_14_REGISTER.md", "ops/RDL_BASELINE.json",
    "ops/pending_workflows/",
)
#: Verdicts that stop the loop and are counted as escalation on exit (SH-5).
REFUSING = ("REFUSE",)
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


def owned_check_names(root: Path) -> set[str]:
    """Check-run names GitHub produces for this repository's own workflows.

    A check run is named after the job's `name:` when one is set, else after the
    job id. Both are included so a name that GitHub renders differently still
    matches something; an owned name with no run on a commit is reported, not
    failed, because schedule-only and path-filtered workflows do not run on
    every push. Parsed by indentation from the YAML, no yaml module needed on
    the host (the same reading preflight.py does).
    """
    names: set[str] = set()
    wdir = root / ".github" / "workflows"
    if not wdir.is_dir():
        return names
    for wf in sorted(wdir.glob("*.yml")):
        in_jobs, job_id, job_name = False, None, None
        for line in wf.read_text(encoding="utf-8", errors="replace").splitlines():
            if re.match(r"^jobs:\s*$", line):
                in_jobs = True
                continue
            if in_jobs and line and not line[0].isspace():
                in_jobs = False
            if not in_jobs:
                continue
            m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
            if m:
                if job_id:
                    names.update({job_id, job_name} - {None})
                job_id, job_name = m.group(1), None
                continue
            m = re.match(r"^    name:\s*(.+?)\s*$", line)
            if m and job_id and job_name is None and "${{" not in m.group(1):
                job_name = m.group(1).strip("\"'")
        if job_id:
            names.update({job_id, job_name} - {None})
    return names


def foreign_checks(check_runs: list, owned: set) -> list:
    """Checks present on a commit that this ecosystem does not own.

    D-116 rule 3 says a check the repository does not own must not block. That
    was correct and it was quietly read as "must not be mentioned", which is a
    different claim. The consequence, measured on main at e7647fb: two Cloud Run
    triggers in a Google Cloud project had been red on every commit, the proof
    block listed six owned checks and named neither, and the audit printed GREEN.
    Nothing was wrong with the verdict. Everything was wrong with the silence,
    because an integration nobody in this ecosystem declared was writing to the
    repository's own commit status and no artefact here said so. That is L-179
    inverted: silence read as absence rather than as success.

    Reported, never asserted. The verdict still turns on owned checks only.
    Newest run per name decides, as GitHub lists newest first.
    """
    seen: dict = {}
    for cr in (check_runs or []):
        name = str(cr.get("name") or "")
        if not name or name in owned:
            continue
        seen.setdefault(name, (str(cr.get("status") or ""),
                               str(cr.get("conclusion") or "")))
    return sorted((n, st, cc) for n, (st, cc) in seen.items())


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

            runs, err = gh_json("api", f"repos/{slug}/commits/main/check-runs?per_page=100")
            owned = owned_check_names(PATHS[repo]) if PATHS[repo].exists() else set()
            if not owned:
                # No checkout to read the workflows from: fall back to the old
                # keyword filter and SAY so, rather than silently asserting less.
                print("    (workflow files not readable here; asserting integrity, heal and binding only)")
            seen: dict[str, tuple[str, str]] = {}
            for cr in ((runs or {}).get("check_runs") or []):
                name = cr.get("name", "")
                keep = (name in owned) if owned else any(
                    k in name.lower() for k in ("integrity", "heal", "binding"))
                if keep:
                    # The newest run per name decides; GitHub lists newest first.
                    seen.setdefault(name, (cr.get("status") or "", cr.get("conclusion") or ""))
            if not seen:
                print("    main checks: none reported yet")
            for name, (status, concl) in sorted(seen.items()):
                if status != "completed":
                    print(f"    main check  {name}: {status} (not finished at read time)")
                    continue
                print(f"    main check  {name}: {concl}")
                if concl != "success":
                    clean = False
            for name in sorted(owned - set(seen)):
                print(f"    main check  {name}: no run on this commit (schedule- or path-triggered)")
            foreign = foreign_checks((runs or {}).get("check_runs") or [], owned)
            if foreign:
                red = [f for f in foreign if f[2] not in ("success", "neutral", "skipped", "")]
                print(f"    not owned by this ecosystem, reported and never asserted "
                      f"({len(foreign)} present, {len(red)} not passing):")
                for name, status, concl in foreign:
                    print(f"      {name}: {concl or status or 'no state'}")
                if red:
                    print("      An integration this ecosystem did not declare is writing to")
                    print("      this repository's commit status. It does not block, and it is")
                    print("      not evidence about this ecosystem. Declare it or disconnect it.")

        issues, _ = gh_json("issue", "list", "--repo", slug, "--state", "open",
                            "--json", "number")
        n = len(issues or [])
        print(f"    open issues: {n}")
        print()

    print("  VERDICT: " + (
        "every completed check the ecosystem owns reports success on main in "
        "both repositories." if clean else
        "at least one owned check on main is not success, or a value could not be read. "
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



def runner_merge_decision(pr: dict, checks: list, owned: set) -> tuple[str, str]:
    """Decide, from values alone, what happens to one open pull request.

    Pure by construction: no network, no clock, no filesystem. That is what
    makes the fixtures below a test of the decision rather than a test of what
    GitHub happened to answer on the day the test ran (V-2, and the whole point
    of L-179: a judgement is only as good as the set it is taken over).

    Returns (verdict, reason), verdict in:
      SKIP    not a runner landing. This command has no opinion about it.
      WAIT    it may merge later. Nothing green has been established yet.
      REFUSE  it must not merge here, and the reason names the act that settles it.
      MERGE   every check the repository owns is completed and green on this head.

    A check the repository does not own (a Cloud Build status, a third party
    app) is reported and never asserted: D-116 rule 3, and L-044 already
    rejected Cloud Build, so its red is noise rather than a finding. A check
    the repository DOES own is asserted whether or not the branch protection
    rules require it: D-116 rule 6, which is L-179 stated as a rule.
    """
    head = str(pr.get("headRefName") or "")
    login = str(((pr.get("author") or {}).get("login")) or "")
    base = str(pr.get("baseRefName") or "")

    if base != "main":
        return "SKIP", f"base is {base!r}, not main"
    if not head.startswith(RUNNER_HEADS):
        return "SKIP", f"head {head!r} carries no runner landing prefix"
    if login not in RUNNER_AUTHORS:
        return "SKIP", (f"head {head!r} reads as a runner landing but the author is "
                        f"{login!r}. Both conditions are required and only one holds.")
    if pr.get("isDraft"):
        return "WAIT", "draft"

    carried = [str(f.get("path") or "") for f in (pr.get("files") or [])]
    if not carried:
        return "WAIT", ("the file list came back empty. A landing is judged on what it "
                        "carries, and an unread list is not an empty one.")
    forbidden = sorted({p for p in carried if p.startswith(RUNNER_REFUSED_PREFIXES)})
    if forbidden:
        return "REFUSE", ("carries " + ", ".join(forbidden[:4])
                          + (" and more" if len(forbidden) > 4 else "")
                          + ". A runner may land derived artefacts, never the surfaces "
                            "that decide what is allowed to land. This one is a human "
                            "review, G-06 Rule 2-4 delegates remediation and not authority.")

    if (str(pr.get("mergeStateStatus") or "").upper() == "DIRTY"
            or str(pr.get("mergeable") or "").upper() == "CONFLICTING"):
        return "REFUSE", ("conflicts with main. Auto-merge cannot resolve a conflict, so "
                          "the remedy is to close it and let the next run cut it again "
                          "from origin/main. L-165.")

    seen: dict[str, tuple[str, str]] = {}
    for cr in (checks or []):
        name = str(cr.get("name") or "")
        if name in owned:
            # Newest run per name decides; GitHub lists newest first.
            seen.setdefault(name, (str(cr.get("status") or ""),
                                   str(cr.get("conclusion") or "")))
    if not seen:
        return "WAIT", ("no check this repository owns has reported on this head. Merging "
                        "on silence is L-179 inverted: absence read as success.")
    for name, (status, concl) in sorted(seen.items()):
        if status != "completed":
            return "WAIT", f"owned check {name} is {status or 'unreported'}"
        if concl == "action_required":
            return "WAIT", (f"owned check {name} is held for workflow approval, which is "
                            "GitHub's default for a first pull request from an identity. "
                            "Approving it is a repository act and not a merge.")
        if concl not in ("success", "neutral", "skipped"):
            return "REFUSE", f"owned check {name} concluded {concl}"

    ignored = sorted({str(cr.get("name") or "") for cr in (checks or [])} - set(owned))
    note = (" Not owned, reported and not asserted: " + ", ".join(ignored[:4]) + "."
            if ignored else "")
    return "MERGE", (f"{len(seen)} owned check(s) green on "
                     f"{str(pr.get('headRefOid') or '')[:12]}: "
                     + ", ".join(sorted(seen)) + "." + note)



def _root_for(repo: str, explicit: str | None = None) -> "Path | None":
    """Where this repository's workflow files can be read from.

    Three cases, and they are not interchangeable. On the operator's machine the
    host checkouts named in PATHS are the tree. On a GitHub runner PATHS does
    not exist at all, and the checkout the job is running inside IS the
    repository, which is knowable from the directory name rather than assumed
    (`/home/runner/work/<repo>/<repo>`). Anywhere else the set of checks this
    repository owns is unknown, and the caller is told that rather than handed
    an empty set, which would read like a clean bill. L-179 is exactly the cost
    of asserting over a set nobody established.
    """
    if explicit:
        p = Path(explicit).resolve()
        return p if p.is_dir() else None
    host = PATHS.get(repo)
    if host and host.exists():
        return host
    here = Path(__file__).resolve().parent.parent
    if here.name == repo and (here / ".github" / "workflows").is_dir():
        return here
    return None


def runner_merge(only_repo: str | None = None, dry_run: bool = False,
                 root_override: str | None = None) -> int:
    """Merge, by rebase, every runner landing whose owned checks are green.

    WHY. SH-7 says nothing depends on the operator's machine. `selfheal.yml`
    already arms `--auto` on its own pull request, which needs the repository
    setting Settings > General > Pull Requests > "Allow auto-merge" and stalls
    silently where that is off. `daily-ops-report.yml` had no landing step at
    all, so PR 43 of 2026-08-26, the first runner landing this ecosystem has
    ever produced, waited for a person. A recurring task that ends by asking
    for a click is a reminder, which is what SH-7 says it is not.

    This merges directly once the checks are ALREADY green, so it needs no
    repository setting, and falls back to arming `--auto` when the direct merge
    is refused, which is the SH-10g order: the mechanism before the compliance.
    Rebase, never squash: squash strands the commit hashes the lineage register
    cites (G-05, G-06 Rule 2-4). It does not promote. Promotion is G-06 limit 2
    and stays human.
    """
    want = only_repo.split("/")[-1] if only_repo else None
    print("Runner landings, read from GitHub just now. Not a claim.")
    print("G-06 Rule 2-4 delegates the merge of a remediation pull request to an")
    print("agent once its checks pass. Promotion is not delegated and is not")
    print("attempted here (G-06 limit 2).")
    print()
    escalate = False
    for repo in REPOS:
        if want and repo != want:
            continue
        slug = f"{OWNER}/{repo}"
        print(f"  {slug}")
        prs, err = gh_json("pr", "list", "--repo", slug, "--state", "open", "--limit", "50",
                           "--json", "number,headRefName,baseRefName,author,isDraft,"
                                     "mergeable,mergeStateStatus,files,headRefOid")
        if err:
            print(f"    cannot list pull requests: {err}")
            escalate = True
            continue
        root = _root_for(repo, root_override)
        owned = owned_check_names(root) if root else set()
        if not owned:
            print("    the workflow files are not readable from here, so the set of checks "
                  "this repository owns is unknown. Nothing merges on an unknown set (L-179).")
            continue
        if not prs:
            print("    0 open pull requests")
        for pr in (prs or []):
            num = str(pr.get("number"))
            oid = str(pr.get("headRefOid") or "")
            checks = []
            if oid:
                runs, e2 = gh_json("api", f"repos/{slug}/commits/{oid}/check-runs?per_page=100")
                if e2:
                    print(f"    PR {num}: check runs unreadable, {e2}")
                    escalate = True
                    continue
                checks = (runs or {}).get("check_runs") or []
            verdict, why = runner_merge_decision(pr, checks, owned)
            print(f"    PR {num}  {pr.get('headRefName')}  {verdict}: {why}")
            if verdict in REFUSING:
                escalate = True
                continue
            if verdict != "MERGE":
                continue
            if dry_run:
                print("      --dry-run, not merged")
                continue
            code, out = gh_run("pr", "merge", num, "--repo", slug, "--rebase", "--delete-branch")
            if code == 0:
                print(f"      PR {num} MERGED by rebase, branch deleted.")
                continue
            first = (out.splitlines() or [""])[0]
            code2, out2 = gh_run("pr", "merge", num, "--repo", slug, "--rebase", "--auto")
            if code2 == 0:
                print(f"      direct merge refused ({first}). Auto-merge ARMED; it fires "
                      "when the branch becomes mergeable.")
                continue
            print(f"      NOT MERGED. direct: {first}; auto: {(out2.splitlines() or [''])[0]}")
            print("      If auto-merge is unavailable the repository setting is "
                  "Settings > General > Pull Requests, 'Allow auto-merge'. That is the "
                  "operator's act, G-03 and G-04 by analogy: it widens what the Actions "
                  "token may do.")
            escalate = True
        print()
    print("  VERDICT: " + (
        "every runner landing read here is merged, waiting on its own checks, or not a "
        "runner landing." if not escalate else
        "at least one runner landing was refused or could not be read. The lines above "
        "name it. Not glossed."))
    # SH-5: a benign WAIT must not fire an escalation every cycle. Only a refusal
    # or an unreadable value exits non-zero.
    return 1 if escalate else 0


def _rm_pr(**kw) -> dict:
    base = {
        "number": 43,
        "headRefName": "ops/report-2026-08-26",
        "baseRefName": "main",
        "author": {"login": "github-actions[bot]"},
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "files": [{"path": "ops/reports/2026-08-26.md"}],
        "headRefOid": "0123456789abcdef0123456789abcdef01234567",
    }
    base.update(kw)
    return base


def _rm_ck(name: str, status: str = "completed", conclusion: str = "success") -> dict:
    return {"name": name, "status": status, "conclusion": conclusion}


def runner_merge_selftest() -> int:
    """One fixture the decision must refuse and one it must accept, and then
    some (V-2). The cases are values, so this runs with no network and no
    credential, which is the only way a gate over a merge can run in CI at all
    (G-03, G-04: no credential in either direction, including to test one)."""
    owned = {"qesis-integrity", "verify", "heal"}
    green = [_rm_ck("qesis-integrity"), _rm_ck("verify"), _rm_ck("heal"),
             _rm_ck("cloudrun-qesis-europe-west1", conclusion="failure")]
    cases = [
        ("a runner report with every owned check green merges", "MERGE",
         _rm_pr(), green),
        ("a failing check the repository does not own does not block", "MERGE",
         _rm_pr(), [_rm_ck("qesis-integrity"), _rm_ck("verify"), _rm_ck("heal"),
                    _rm_ck("cloudrun-qesis-europe-west1", conclusion="failure")]),
        ("a runner branch carrying scripts/ is refused", "REFUSE",
         _rm_pr(files=[{"path": "ops/reports/2026-08-26.md"},
                       {"path": "scripts/gh_ops.py"}]), green),
        ("a runner branch carrying .github/ is refused", "REFUSE",
         _rm_pr(files=[{"path": ".github/workflows/selfheal.yml"}]), green),
        ("a red owned check is refused", "REFUSE",
         _rm_pr(), [_rm_ck("qesis-integrity", conclusion="failure"), _rm_ck("verify")]),
        ("a conflicting runner landing is refused, close and re-cut", "REFUSE",
         _rm_pr(mergeStateStatus="DIRTY"), green),
        ("an unfinished owned check waits", "WAIT",
         _rm_pr(), [_rm_ck("qesis-integrity", status="in_progress", conclusion="")]),
        ("no owned check on the head waits, never merges on silence", "WAIT",
         _rm_pr(), [_rm_ck("cloudrun-qesis-europe-west1", conclusion="failure")]),
        ("workflow runs held for approval wait", "WAIT",
         _rm_pr(), [_rm_ck("qesis-integrity", conclusion="action_required")]),
        ("a human branch named like a runner landing is skipped", "SKIP",
         _rm_pr(author={"login": "rodrigoesl92-cloud"}), green),
        ("an ordinary human branch is skipped", "SKIP",
         _rm_pr(headRefName="fix/land-20260826-runner-merge"), green),
        ("a runner landing aimed at a base that is not main is skipped", "SKIP",
         _rm_pr(baseRefName="release/v9.0"), green),
    ]
    ok = 0
    for label, expect, pr, checks in cases:
        got, why = runner_merge_decision(pr, checks, owned)
        good = got == expect
        ok += good
        print(f"{'PASS' if good else 'FAIL'}  runner-merge: {label}")
        if not good:
            print(f"        expected {expect}, got {got}: {why}")
    print(f"{ok}/{len(cases)} runner-merge decisions behave as declared")
    return (0 if ok == len(cases) else 1) | foreign_check_selftest()


def foreign_check_selftest() -> int:
    """The inventory reports what the verdict must ignore (V-2).

    One fixture it must list and one it must not: a foreign check appears
    whatever its conclusion, and an owned check never appears in the inventory
    no matter how it concluded. Without the second case the function would pass
    by listing everything, which is not the claim being made.
    """
    owned = {"qesis-integrity", "verify", "heal"}
    runs = [_rm_ck("qesis-integrity"), _rm_ck("verify", conclusion="failure"),
            _rm_ck("cloudrun-qesis-mcp-git-europe-west1", conclusion="failure"),
            _rm_ck("rmgpgab-qesis-mcp-europe-west1", conclusion="failure"),
            _rm_ck("some-app", status="in_progress", conclusion="")]
    got = foreign_checks(runs, owned)
    names = [n for n, _, _ in got]
    cases = [
        ("a foreign failing check is reported rather than hidden",
         "cloudrun-qesis-mcp-git-europe-west1" in names),
        ("every foreign check is reported, not just the first",
         "rmgpgab-qesis-mcp-europe-west1" in names and "some-app" in names),
        ("an owned check never appears in the foreign inventory",
         "qesis-integrity" not in names and "verify" not in names),
        ("a foreign check still carries its own state",
         ("some-app", "in_progress", "") in got),
        ("no foreign check, no inventory", foreign_checks(
            [_rm_ck("qesis-integrity"), _rm_ck("heal")], owned) == []),
    ]
    ok = 0
    for label, good in cases:
        ok += bool(good)
        print(f"{'PASS' if good else 'FAIL'}  foreign-checks: {label}")
    print(f"{ok}/{len(cases)} foreign-check behaviours hold")
    return 0 if ok == len(cases) else 1


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
    a5 = sub.add_parser("owned")
    a5.add_argument("--root", default=".")
    a6 = sub.add_parser("runner-merge")
    a6.add_argument("--repo", default=None,
                    help="limit to one repository; owner/name or name")
    a6.add_argument("--dry-run", action="store_true")
    a6.add_argument("--selftest", action="store_true",
                    help="run the decision over fixtures; no network, no credential")
    a6.add_argument("--root", default=None,
                    help="checkout to read the owned check names from; defaults to "
                         "the host path, then to this script's own checkout")
    a = ap.parse_args()
    if a.cmd == "pr-number":
        return pr_number(a.repo, a.head)
    if a.cmd == "pr-state":
        return pr_state(a.repo, a.pr)
    if a.cmd == "runner-merge":
        return (runner_merge_selftest() if a.selftest
                else runner_merge(a.repo, a.dry_run, a.root))
    if a.cmd == "owned":
        for n in sorted(owned_check_names(Path(a.root))):
            print(n)
        return 0
    return amputate(a.keep) if a.cmd == "amputate" else proof()


if __name__ == "__main__":
    sys.exit(main())
