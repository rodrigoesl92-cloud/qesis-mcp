"""Idempotent patch set for 2026-08-15. Run AFTER the rebase recovery.

Every edit here touches a TRACKED file. `git rebase --abort` hard-resets tracked
files, and the working tree during the stalled rebase sat at c150be9, which
predates half this work. Editing tracked files before recovery would either be
discarded or would edit the wrong version. That is L-125 applied rather than
quoted: when an ordering can invalidate a step, the step moves.

Idempotent by construction. Every patch checks for its own marker first, so
running this twice is a no-op and running it after a partial failure resumes.

Usage:  python scripts/apply_20260815_patchset.py [--check]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = "--check" in sys.argv
applied: list[str] = []
skipped: list[str] = []
missing: list[str] = []


def patch(path: str, marker: str, old: str, new: str, why: str) -> None:
    p = ROOT / path
    if not p.exists():
        missing.append(f"{path}: file absent")
        return
    s = p.read_text(encoding="utf-8")
    if marker in s:
        skipped.append(f"{path}: already carries {marker!r}")
        return
    if old not in s:
        missing.append(f"{path}: anchor not found, patch NOT applied ({why})")
        return
    if not CHECK:
        p.write_text(s.replace(old, new, 1), encoding="utf-8")
    applied.append(f"{path}: {why}")


def append(path: str, marker: str, text: str, why: str) -> None:
    p = ROOT / path
    if not p.exists():
        missing.append(f"{path}: file absent")
        return
    s = p.read_text(encoding="utf-8")
    if marker in s:
        skipped.append(f"{path}: already carries {marker!r}")
        return
    if not CHECK:
        p.write_text(s + text, encoding="utf-8")
    applied.append(f"{path}: {why}")


# ── 1. G-01b in code: production is built only from main ────────────────────
patch(
    "scripts/vercel_gate.py",
    marker="PRODUCTION_BRANCH",
    old="def main() -> int:\n    print(\"QESIS+ pre-build gate. exit 1 builds, exit 0 skips (Vercel semantics).\")",
    new='''PRODUCTION_BRANCH = "main"


def branch_guard() -> bool:
    """G-01b in code. Production is replaced only by a promotion event.

    Root cause of the hourly Production probe failures, runs 221 through 229 and
    counting: this gate checked artefact quality and never checked WHICH BRANCH
    was being promoted. Any branch whose gates passed was built, and Vercel
    aliased production to it, so `deployment_commit` bound to a feature branch
    while `verify_production.py` compared it against main's HEAD. The probe was
    right every hour for nine hours and the thing it was right about was this
    function's absence.

    Preview deployments are untouched and should be: reviewing a branch on a URL
    is the point of them. Only the PRODUCTION alias is restricted.

    Returns True when the build may continue.
    """
    import os
    env = os.environ.get("VERCEL_ENV", "")
    ref = os.environ.get("VERCEL_GIT_COMMIT_REF", "")
    if env != "production":
        print(f"  branch guard: VERCEL_ENV={env or 'unset'}, not a production build, allowed")
        return True
    if ref == PRODUCTION_BRANCH:
        print(f"  branch guard: production build from {ref}, allowed")
        return True
    print(f"  branch guard: REFUSED. production build requested from {ref!r}, "
          f"and only {PRODUCTION_BRANCH!r} may bind the production alias (G-01b).")
    print("  Production keeps serving the last good deployment. That is the")
    print("  correct failure mode: an instrument that cannot verify which commit")
    print("  it is serving should keep serving the one it could.")
    return False


def main() -> int:
    print("QESIS+ pre-build gate. exit 1 builds, exit 0 skips (Vercel semantics).")
    if not branch_guard():
        return BUILD_IGNORED''',
    why="branch guard, closes the Production probe root cause",
)

# ── 2. The self-exposure artefact joins the control set ─────────────────────
patch(
    "scripts/selfheal.py",
    marker="self_exposure_check",
    old='    ("build_eval_check",       ["scripts/build_eval.py", "--check"]),',
    new='    ("self_exposure_check",    ["scripts/self_exposure.py", "--check"]),\n'
        '    ("build_eval_check",       ["scripts/build_eval.py", "--check"]),',
    why="D-113 self-exposure artefact is gated like every other derived artefact",
)
patch(
    "scripts/selfheal.py",
    marker='"self_exposure_check": {',
    old='    "build_eval_check": {',
    new='''    "self_exposure_check": {
        "class": "A",
        "why": "The instrument's own exposure is derived from a declared substrate "
               "table and recomputes nothing. A drift means the table moved and the "
               "artefact did not, which is D-113 losing its evidence.",
        "run": ["scripts/self_exposure.py"],
        "reverify": True,
    },
    "build_eval_check": {''',
    why="class A remedy for the self-exposure artefact",
)

# ── 2b. The loop lands its own repairs, from the runner, with no local machine ─
patch(
    ".github/workflows/selfheal.yml",
    marker="Land the repairs the loop made",
    old="      - name: Fail the run on escalation",
    new='''      - name: Land the repairs the loop made
        # SH-7. Nothing depends on the operator's machine. When the loop repairs a
        # derived artefact it must be able to land that repair, or the repair
        # exists for the lifetime of a runner and the next run does it again
        # forever. That is a loop that looks busy and changes nothing.
        #
        # It opens a PULL REQUEST and never pushes to main. G-06 limit 3 is
        # unchanged: direct pushes to main stay prohibited, merging a paired
        # remediation PR is delegated, and promotion is not delegated at all.
        # The branch name is derived from the run id so concurrent runs cannot
        # collide, and the guard is `git diff --quiet` rather than a trust that
        # something changed.
        if: steps.heal.outcome == 'success'
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          set -euo pipefail
          if git diff --quiet -- . ':!ops/SELFHEAL_LATEST.json'; then
            echo "no repairs to land beyond the run report"
            exit 0
          fi
          BR="selfheal/${{ github.run_id }}"
          git config user.name  "qesis-selfheal[bot]"
          git config user.email "selfheal@qesis.invalid"
          git checkout -b "$BR"
          git add -A
          git commit -m "fix(selfheal): land class A repairs from run ${{ github.run_id }}

          Derived artefacts had drifted from their sources and the declared
          remedy rebuilt them. Every change here is a rebuild, never a new
          number: class A remedies are idempotent by construction and are
          reverified before this step runs.

          See ops/SELFHEAL_LATEST.json for the control set and the verdict.
          Authority G-07. No promotion, no direct push to main."
          git push origin "$BR"
          gh pr create --base main --head "$BR" \\
            --title "selfheal: land class A repairs from run ${{ github.run_id }}" \\
            --body "Automated under G-07. Class A remedies only, each reverified before commit. Review the control set in \\`ops/SELFHEAL_LATEST.json\\`. Merge with \\`--rebase\\`, never squash (G-05)."

      - name: Fail the run on escalation''',
    why="SH-7: the loop lands its own repairs from the runner, via PR, never to main",
)

# ── 3. CLAUDE.md: lock the cloud posture and L-045 ──────────────────────────
patch(
    "CLAUDE.md",
    marker="Rule SH-7",
    old="**Rule SH-6.**",
    new='''**Rule SH-7. Nothing depends on the operator's machine.** Every recurring task
runs in GitHub Actions. A scheduled task that requires a desktop application to
be open is not a scheduled task, it is a reminder. Where a job needs to write to
the repository it commits and opens a pull request from the runner under G-07,
never from a local mount, because the analysis mount cannot complete a git write
and half-completes instead (L-122, L-123).

**Rule SH-8. The instrument declares its own substrate.** D-113 closes L-045.
The runtime is US hyperscale across four of five determined layers and one vendor
holds the source of record, the CI, the self-heal loop and the evidence mirror at
once. That is adopted deliberately, not by drift, and any change to it needs a
line in D-113 before it happens rather than an explanation afterwards. When the
product is a critique of a dependency, adopting that dependency is a decision
with a number.

**Rule SH-6.**''',
    why="SH-7 cloud-only, SH-8 declared substrate",
)

# ── 4. Ledger ───────────────────────────────────────────────────────────────
append(
    "ops/LESSONS_LEDGER.md",
    marker="**L-126",
    text='''
**L-126 · 2026-08-15 ·** The Production probe failed hourly on `main` for at least nine consecutive runs, 221 through 229, and in `sovereign-infra` the Continuous compliance verification failed alongside it. The GitHub notification inbox stood at 506 items, 452 of them on `qesis-mcp`. The probe was correct on every one of those runs. `scripts/verify_production.py` asserts `deployment_commit == github.sha`, the scheduled run supplies main's HEAD, and production was serving a commit that lived only on a feature branch, because `scripts/vercel_gate.py` gated artefact QUALITY and never gated WHICH BRANCH was promoting. Vercel aliased production to whatever last passed the gates. **Rule:** the control that decides what reaches production checks the branch before it checks anything else, because every other check answers "is this artefact good" and only this one answers "is this the artefact we promised". G-01b said the served index is replaced only by a promotion event and that sentence had no implementation for the alias path; it was enforced for the index bytes and unenforced for the deployment binding. **Second rule, and it is the expensive one:** an alarm that fires hourly and correctly for nine hours, into an inbox of 506, has been switched off by volume rather than by decision (L-063). The two-strike gate in that workflow was built to suppress transport flapping and it worked exactly as designed; what nobody built was anything that reads the certification failures, which are the ones that always page and always mean something. A notification channel with no read discipline is not a control, it is an archive.

**L-127 · 2026-08-15 ·** Asked where the runtime lives, the operator answered that he did not know. That answer is the finding, not a gap in his knowledge. The ecosystem's entire thesis is that states cannot see their own substrate dependencies, and the instrument could not see its own: four of five determined layers resolve to two US hyperscalers and a single vendor holds the source of record, the CI, the self-heal loop and the evidence mirror simultaneously. L-045 has stood open since 2026-07-29 with the remedy written into it, "adopting that dependency is a governance decision with a decision number, never an infrastructure convenience", and no decision number was ever issued. **Rule:** a lesson whose remedy is a document is not closed until that document exists and carries an id, and an open lesson older than thirty days is escalated to the operator by name rather than carried in a list. **The measurement that makes this worth keeping:** scored on its own axes under its own calibration, the instrument returns ODI 52.0, FPE 100.0 and RGD 60.0, and its composite is WITHHELD at coverage 0.25 against the same 0.75 BIG gate the 32 states face. Holding itself to a looser rule would have produced a number and destroyed the comparison, which is the choice this entry exists to record. **Correction made while writing this entry, and it belongs in it:** the first draft said the instrument fails its gate "exactly as Hong Kong, Singapore and Taiwan do", calling them states. D-111 settled that a week earlier: they are the `regions` frame, HKG and SGP because a city-territory has no resolvable catchment at Aqueduct's grid resolution and TWN because the source's territorial schema carries no separate entry, and the two frames are never pooled into one ranking because a composite over seven axes and one over six are different measures. The withholding mechanism is shared; the entity type is not. Using the wrong category in a document about ontology is the defect that document exists to prevent, and D-111 was in the repository and unread at the moment of writing. **Rule:** where the ecosystem has already ruled on an entity's type, cite the ruling rather than the intuition, and `states` and `regions` are never used interchangeably in prose any more than they are in a table.

**L-128 · 2026-08-15 ·** Three consecutive recovery blocks stalled on the same shape: a step earlier in the block invalidated a step later in it, and the block ran to the end regardless. `git rm --cached` before a rebase that replays the add (L-125); a precondition that aborted on a lock the same script had just been told how to clear; and a resume script whose `Move-Item` resolved a conflict the following `git rebase --continue` then reported as unresolved. Each was a correct command in the wrong position. **Rule:** an operator block that mutates repository state declares `$ErrorActionPreference = 'Stop'` as its first line and orders its steps so that no step can invalidate a later one, or it is not a block and its commands are handed over one at a time. The control existed in `PUSH_2026-08-15.ps1` and was absent from every block typed directly into chat, which is L-048 in an operator runbook rather than in a generator: a gate that lives in one layer and not the adjacent one has been described, not applied.
''',
    why="L-126, L-127, L-128",
)


def report() -> int:
    for line in applied:
        print(f"  {'would apply' if CHECK else 'applied  '}  {line}")
    for line in skipped:
        print(f"  skipped      {line}")
    for line in missing:
        print(f"  MISSING      {line}")
    print(f"\n{len(applied)} applied, {len(skipped)} already present, {len(missing)} missing")
    if missing:
        print("A missing anchor means the target file is not the version this patch "
              "was written against. Do not force it. Read the file and re-anchor.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(report())
