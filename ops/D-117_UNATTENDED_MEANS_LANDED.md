# D-117: unattended means landed, and a delegated merge is bounded by what it may carry

**Status:** decided 2026-08-26, ARCHITECT, at rung 4 of the RDL family
`claim_from_proxy_not_resource` (L-161, L-162, L-173, L-174, L-179; this
occurrence L-180).
**Authority:** CLAUDE.md Rule SH-7 (nothing depends on the operator's machine),
Rule SH-10d (G-06 stated as a duty), G-06 Rule 2-4 (an agent may merge a paired
remediation pull request by rebase once its checks pass, may not push to `main`,
may not promote), Rule SH-5 (an escalation that fires every cycle has been
switched off without anyone deciding to), D-116 rule 6 (an owned check is
asserted whether or not it is required).

## Why rung 4, and what was in the wrong layer

Nine times this family has appeared, and the move is always the same: a property
of a resource was read off a proxy for the resource. The fourth rung says the
control is one layer too low. Here it was two layers too low. SH-7 was written
as a property of the **schedule declarations**, and every fix to date has been a
fix to a declaration:

| Occurrence | Proxy that was read | Resource that was not |
|---|---|---|
| L-174 | the loop opens a pull request | no runner landing had ever completed |
| L-179 | a keyword filter over check names | the set of checks the repositories own |
| L-180 | a cron exists in Actions | whether the work the cron produces ever lands |

`daily-ops-report.yml` carries zero occurrences of `gh pr merge` in both
repositories; `selfheal.yml` carries one, and that one is `--auto`, which is
inert unless "Allow auto-merge" is ticked. SH-7 was therefore true of the
schedule and false of the outcome for as long as the clause has existed.

## Decision

1. **A recurring task is unattended only when its last act lands the work.**
   The assertion is made from a merged pull request read from GitHub, never
   from the presence of a schedule and never from the exit code of the step
   that opened the pull request. This is D-116 rule 1 applied to autonomy
   rather than to a verdict row.
2. **Landing is a sweep, not a tail step.** A workflow cannot reliably merge
   the pull request it has just opened, because that pull request's own checks
   have not reported yet, and waiting inside the job burns a runner to watch a
   clock. The loop that already runs hourly sweeps every open runner landing
   and merges the ones that are green. Latency is bounded by the sweep period
   and by nothing on anyone's desk.
3. **A delegated merge is bounded by what the branch carries, not only by who
   opened it.** Two independent conditions must both hold: the head prefix is a
   declared runner prefix AND the author is a declared runner identity. Either
   alone is forgeable by a person. On top of that, a runner landing that carries
   `.github/`, `scripts/`, `qesis_agents/`, `api/`, `server.py`, the licence,
   the authorship file, the session lock, the governance record, the Article 14
   register or the RDL baseline is REFUSED. G-06 Rule 2-4 delegates
   **remediation**. It does not delegate **authority**, and a loop that can
   merge a change to the code deciding what merges has been handed authority by
   omission.
4. **The allowlist and the denylist are not interchangeable, and the choice is
   stated.** The set of derived artefacts a class A repair may rebuild is open
   and grows with the pipeline; an allowlist over it would begin refusing
   correct repairs the week after it was written, which is D-115's failure mode
   in reverse. The set of surfaces that decide what may merge is closed and
   small. The denylist is over the closed set, deliberately.
5. **Silence is never success.** If no check the repository owns has reported on
   the head commit, the verdict is WAIT and never MERGE. Absence read as success
   is L-179 inverted, and it is the cheaper mistake to make.
6. **A check the repository does not own does not block, and says so.** D-116
   rule 3. The Cloud Build statuses that L-044 rejected are printed and never
   asserted.
7. **A refusal is a warning in the sweep, not a red run every hour.** A standing
   refusal that turns the hourly loop red until a person acts is switched off by
   exhaustion rather than by decision, which is SH-5 and L-063. The refusal is
   surfaced as a warning in the step, in the loop's issue channel and in the
   daily ops report. Only an unreadable value or a refusal exits non-zero when
   the command is run by hand, where a person is present to read it.
8. **Promotion stays human.** Nothing in this decision touches G-06 limit 2. The
   deployment plane still serves what was promoted, and promotion remains the
   operator's act. G-01b.

## The control, and where it is proven

`scripts/gh_ops.py runner-merge`, paired byte-identical in both repositories.
The decision is a pure function of values, `runner_merge_decision(pr, checks,
owned)`, so its fixtures run with no network and no credential, which is the
only form in which a gate over a merge can run in CI at all (G-03, G-04: no
credential in either direction, including for the purpose of testing one).

Twelve fixtures, `python scripts/gh_ops.py runner-merge --selftest`, exit 0 at
12 of 12. They include one refusal for a landing carrying `scripts/`, one for a
landing carrying `.github/`, one for a red owned check, one for a conflict, one
WAIT on check silence, one WAIT on workflow runs held for approval, one SKIP for
a human branch named like a runner landing, and the accept case (V-2 needs one
refuse and one accept; this carries six and six).

Wired: `scripts/test_gate.py check_runner_merge` in `qesis-mcp`, a step of the
integrity gate, 76 of 76; and a `--selftest` step delivered to
`ops/pending_workflows/qesis-integrity.yml` in `sovereign-infra`, where
`preflight.py` executes CI's own step list.

## What would falsify this decision

A runner landing that merges here and should not have. Concretely: a pull
request from a declared runner identity, on a declared runner prefix, whose
files pass the denylist and whose owned checks are green, that nonetheless
carries a change no agent should land without a person. If that occurs, rule 3
is under-specified and the remedy is to move to an allowlist over the derived
set, accepting the maintenance cost rule 4 declines today.

---
Decision holder: Rodrigo Batista Silva. Author for copyright purposes, and the
only signature on this record.
Prepared by: Claude, Cowork session of 2026-08-26, acting under CLAUDE.md and
sovereign-infra/ops/GOVERNANCE.md. Machine attribution under R-1: data, not
authorship, and not a claim of any right.
Established from: `python scripts/gh_ops.py runner-merge --selftest` exit 0 at
12 of 12; `python scripts/test_gate.py` exit 0 at 76 of 76 with the runner merge
fixtures wired, and 80 of 80 with the blueprint fixtures; `grep -c "gh pr merge"`
over both workflow files in both repositories; `python scripts/rdl.py
ci-blocking` exit 0, 6 accepted, 0 regressions.
Landed by: pending.
