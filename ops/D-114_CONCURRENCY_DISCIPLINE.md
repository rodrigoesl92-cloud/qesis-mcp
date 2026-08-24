# D-114: concurrency discipline for the shared working tree

**Status:** APPROVED and EXECUTED
**Date opened:** 2026-08-24, by L-152 at the fourth rung
**Date approved:** 2026-08-24
**Approved by:** R. Batista Silva
**Authored by:** COUNSEL. Wired by ARCHITECT. Confirmed by SENTINEL.

---

## What happened

Two sessions wrote one working tree on 2026-08-24 and neither could see the
other. Measured from mtimes, host clock UTC+2: the scheduled sweep began at
17:23:06 with fourteen controls green; an interactive session wrote
`verify_ledger_singleton.py` at 17:26:40, `LEDGER_GAPS.json` at 17:27:15,
`daily-ops-report.yml` at 17:27:37 and `build_ops_report.py` at 17:28:30; the
sweep edited `selfheal.py` and `test_gate.py` around 17:29 to 17:30; the other
session appended L-145 to L-149 at 17:30:57, added a `CONTROLS` entry at
17:31:09, and at 17:32:22 removed the sweep's duplicate `CONTROLS` line.

That last row makes the diagnosis dispositive rather than probable. A filesystem
sync lag delivers files late; it does not perform a targeted deduplication of a
line written two minutes earlier by a different process.

Both sessions independently reached the same correct conclusion and both wrote
it, producing a `CONTROLS` list holding the same control twice. That raises no
syntax error, runs the gate twice, and double counts it in the totals the
promotion predicate reads.

## The ruling

**A loop that repairs a tree it does not exclusively hold is not idempotent,
however idempotent each individual remedy is.** Idempotence is a property of a
remedy applied to a known state, and concurrency removes the known state.

Three controls, all landed in the change set that carries this decision.

| Exposure | Control | Where |
|---|---|---|
| `CONTROLS` had no uniqueness assertion, and G-07 4.1 P1 reads "every control returns PASS", which a double-counted control satisfies twice | module-level assertion raising `SystemExit` on any duplicate control name | `scripts/selfheal.py::_assert_controls_unique` |
| Two writers appending to one ledger produce a lost update that `verify_ledger_singleton.py` cannot detect, because it compares ids and file hashes and has no record of what should be there | append via a separate artefact merged by a single process, with the singleton gate run before and after | `ops/RDL_PENDING*.md`, `scripts/rdl_append.py` |
| The scheduled sweep had no interlock, and it is the standing session-open act under SH-1 on a shared working tree | advisory lock naming the holder, pid and start time; refuses to mutate while another holder is live inside a 900 second window | `scripts/rdl.py::acquire`, `ops/.rdl.lock` |

## Scope, and what this decision does not claim

It binds any agent process that mutates the shared working tree at
`C:\Users\Lenovo\qesis-mcp` or `C:\Users\Lenovo\OneDrive\sovereign-infra`. It
does not bind the GitHub runner, where the checkout is exclusive by construction
and the lock would be pure overhead.

The advisory lock is advisory. It stops a cooperating process and cannot stop an
uncooperating one, and this document says so rather than dressing it up, in the
same register the branch guard uses about detective controls. The preventive
version of this is one repository per session, which is not available while the
scheduled sweep and interactive sessions share a machine.

## Falsifier

If two agent processes again write the same file within one minute and neither
lock is taken, this control is not applied and the decision is open again.
`ops/.rdl.lock` records the holder, so an unattributed concurrent write is
detectable after the fact.

*Status:* EXECUTED. *Approved by:* R. Batista Silva, 2026-08-24.
