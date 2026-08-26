#!/usr/bin/env python3
"""Close the loop: read what CI actually said, and write it where the agent reads.

THE CORE DEFECT THIS EXISTS TO REMOVE, stated plainly because it cost three
rounds of the operator's time and money.

The agent runs the gates locally, sees them pass, and asserts that CI will pass.
It cannot see a GitHub Actions log: there is no connector, and the analysis mount
has no credential. So every claim about CI has been made from a PROXY, a local
run in a different environment, rather than from THE RESOURCE, the run log.
D-115 rules exactly this out, and the agent was breaking its own decision.

The consequence was a blind loop: push, discover from the operator that CI is
red, guess at the cause, fix, push again. Three iterations, each one a fresh
CI-only failure that a local run could not have shown, because CI installs
requirements.txt, checks out only one repository, and runs steps the loop does
not.

This script runs on the host, where `gh` is authenticated as the operator, waits
for the run to conclude, and writes the failure into the repository:

    ops/CI_LAST_FAILURE.md     the failing job, the failing steps, the log tail

That file is committed, so the NEXT session reads the real reason from the
repository instead of inferring it. The loop is closed without any new credential
and without the operator transcribing anything.

Usage:
    python scripts/ci_feedback.py --repo owner/name --branch feat/x --sha <pushed commit>
    python scripts/ci_feedback.py --repo owner/name --branch feat/x --sha <sha> --root <repo path>

`--sha` pins the run to the commit that was pushed. Without it the newest run on
the branch is a PROXY: immediately after a push the newest run is the PREVIOUS
one, already completed, and its conclusion would be reported for a commit it
never saw (claim_from_proxy_not_resource, D-115). `--root` places
CI_LAST_FAILURE.md in the repository the run belongs to.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ops" / "CI_LAST_FAILURE.md"  # re-pointed by --root in main()

#: The check the branch ruleset requires. A run of anything else concluding does
#: not tell us whether the merge can proceed.
REQUIRED = "QESIS+ integrity gate"


def gh(*args: str, timeout: int = 120) -> tuple[int, str]:
    try:
        p = subprocess.run(["gh", *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=timeout, check=False, cwd=ROOT)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as exc:
        return 127, f"{type(exc).__name__}: {exc}"


def runs(repo: str, branch: str, sha: str | None) -> list[dict]:
    args = ["run", "list", "--repo", repo, "--branch", branch, "--limit", "20",
            "--json", "databaseId,status,conclusion,workflowName,createdAt,headSha"]
    if sha:
        args += ["--commit", sha]
    code, out = gh(*args)
    if code != 0:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--workflow", default=REQUIRED)
    ap.add_argument("--sha", default=None, help="the pushed commit; the run must be for it")
    ap.add_argument("--root", default=None, help="repository to write CI_LAST_FAILURE.md into")
    a = ap.parse_args()
    global OUT
    if a.root:
        OUT = Path(a.root) / "ops" / "CI_LAST_FAILURE.md"

    print(f"CI FEEDBACK: waiting for '{a.workflow}' on {a.repo} @ {a.branch}"
          + (f" commit {a.sha[:12]}" if a.sha else " (no --sha given: newest run on the branch, a proxy)"))
    deadline = time.time() + a.timeout
    target = None

    while time.time() < deadline:
        rs = [r for r in runs(a.repo, a.branch, a.sha) if r.get("workflowName") == a.workflow
              and (not a.sha or str(r.get("headSha", "")).startswith(a.sha))]
        if not rs:
            print("  no run yet for that workflow, waiting")
        else:
            target = rs[0]
            if target.get("status") == "completed":
                break
            print(f"  run {target['databaseId']} is {target.get('status')}, waiting")
        time.sleep(20)

    if target is None:
        print(f"  TIMEOUT after {a.timeout}s with no run of '{a.workflow}'.")
        print("  Reported, not imputed: absence of a run is not evidence of a pass.")
        return 2

    concl = target.get("conclusion")
    rid = target["databaseId"]
    print(f"  run {rid} concluded: {concl}")

    if concl == "success":
        # Do not leave a stale failure file claiming a red build on a green one.
        if OUT.exists():
            OUT.write_text(
                f"# CI last failure\n\nNone. Run {rid} on `{a.branch}` concluded "
                f"**success** at {datetime.now(timezone.utc).isoformat(timespec='seconds')}.\n",
                encoding="utf-8", newline="\n")
        print("  CI IS GREEN. Auto-merge will proceed.")
        return 0

    # Failed. Get the actual reason, from the resource.
    code, failed = gh("run", "view", str(rid), "--repo", a.repo, "--log-failed", timeout=180)
    if code != 0 or not failed.strip():
        code, failed = gh("run", "view", str(rid), "--repo", a.repo, timeout=180)

    lines = [l for l in failed.splitlines() if l.strip()]
    tail = lines[-120:] if len(lines) > 120 else lines

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "# CI last failure\n\n"
        f"**Repository:** `{a.repo}`  \n"
        f"**Branch:** `{a.branch}`  \n"
        f"**Commit:** `{a.sha or 'not pinned'}`  \n"
        f"**Workflow:** {a.workflow}  \n"
        f"**Run:** {rid}, concluded **{concl}**  \n"
        f"**Captured:** {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n\n"
        "This file is written by `scripts/ci_feedback.py` and committed, so the next "
        "session reads the real reason from the repository instead of inferring it "
        "from a local run in a different environment. D-115: query the resource, "
        "never a proxy for it.\n\n"
        "## Failing log\n\n```\n" + "\n".join(tail) + "\n```\n",
        encoding="utf-8", newline="\n")

    print(f"  CI IS RED. Wrote {OUT}")
    print("  ---- failing output, first 40 lines ----")
    for l in tail[:40]:
        print("  " + l)
    return 1


if __name__ == "__main__":
    sys.exit(main())
