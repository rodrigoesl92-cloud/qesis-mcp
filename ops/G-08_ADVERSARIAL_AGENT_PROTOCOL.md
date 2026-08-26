# G-08: the agents work against the system, not for it

**Status:** ACTIVE
**Date:** 2026-08-24
**Opened by:** the operator, after four rounds in which every fix produced a new failure.
**Authored by:** COUNSEL. Wired by ARCHITECT. Adversarially reviewed by SENTINEL.

---

## The diagnosis this protocol answers

Sixteen defects were recorded on 2026-08-24. They are not sixteen problems. They
are **one epistemic move**, arriving on sixteen surfaces:

> A property was asserted without executing the check that would falsify it.

- A local gate pass asserted a CI pass. It was a different environment. (L-166)
- A parent count asserted merge provenance. It was a side effect. (L-161)
- An empty folder asserted an unreachable repository. It was one path. (L-143)
- A file tail asserted the next free id. The file is not sorted. (L-151)
- `git add` returning nothing asserted a clean tree. The add had failed. (L-153)
- A banner asserted a merge. Auto-merge had refused. (L-155, L-160)

**More knowledge does not close this.** The information was available in every
case: the documentation, the log, the directory listing. What was missing was a
mechanism that made skipping the check impossible. This protocol is that
mechanism, distributed across the six agents.

---

## The rule

> **No agent may report a state it has not executed a command to establish, in
> the environment where that state matters.**

Two halves, and the second is the one that failed all day. Running a gate on the
analysis mount and reporting on CI satisfies the first half and violates the
second.

---

## Standing adversarial duties

Each agent's job is to try to **falsify** the ecosystem's claims about itself,
in its own domain. Popper, applied to operations.

| Agent | Attacks | Instrument | Refuses when |
|---|---|---|---|
| **SENTINEL** | the gates themselves | `test_gate.py`, mutation self-test | a gate passes a fixture it must refuse |
| **ARCHITECT** | the pipeline's prediction of itself | `preflight.py` | the local prediction and CI disagree |
| **ANALYST** | every published number | `verify_index.py`, `coupling.py` | a prose number is not computed from the rows beside it |
| **SCOUT** | provenance | acquisition register | a source is cited without a channel |
| **HERALD** | the served surface | `build_landing.py --check`, `verify_dashboard.py` | a surface states a number the index no longer holds |
| **COUNSEL** | the agents' own claims | this document, `rdl.py` | a report asserts a state no command established |

## The execution order, and it is not negotiable

Nothing reaches the operator until all four have run and passed.

```
1  python scripts/verify_ledger_singleton.py     the memory is one thing
2  python scripts/rdl.py ci-blocking             no NEW escalation
3  python scripts/preflight.py                   CI's own steps, on this tree
4  python scripts/gh_ops.py proof                the forge's own answer
```

**Step 3 is the load-bearing one.** It parses `qesis-integrity.yml` and executes
every `run:` step in order. It does not simulate CI and it does not approximate
it: a step added to the workflow is picked up automatically, so the predictor
cannot drift from the thing it predicts. A dependency missing locally is reported
as `ENV`, never as a pass and never as a defect, because conflating those two is
the same fault one level down.

`LAND_EVERYTHING_FINAL.ps1` runs 1, 2 and 3 **before** it stages anything, and
aborts without pushing if any fails. A red gate now costs zero operator time
instead of one round trip.

## What each agent does when it finds something

`scripts/rdl.py` and nothing else. Occurrences 1 to 3 never reach the operator:
record an `L-`, wire a gate with two fixtures, make that gate a release blocker.
Routing is the table in `rdl.py`, not a judgement. The release gate measures the
**delta** against `ops/RDL_BASELINE.json`, because a gate that fails on its own
history is a deadlock and that has now been built twice (L-158, L-166).

## The falsifier for this protocol

If a defect reaches the operator that any of the four steps above could have
caught, G-08 is not applied and this document is wrong. That is the test, it is
cheap to run, and it is the only claim here worth making.

## The honest limit, stated so it is not discovered later

This makes the ecosystem self-healing against **defect families it has already
met**, and it now predicts CI instead of guessing at it. It does not make it
self-correcting against judgement it has never been tested on. SH-6 said that
before today. Sixteen entries later it is still true, and two of today's defects
were introduced by the fixes for the others, which is R-2 working exactly as
designed: the moment of highest risk is immediately after a correction.

*Approved by:* R. Batista Silva, 2026-08-24.
