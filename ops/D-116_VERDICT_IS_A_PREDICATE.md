# D-116: a verdict is a predicate over a parsed value, never the exit status of the fetch

**Status:** decided 2026-08-24, ARCHITECT, at rung 4 of the RDL family
`success_literal_not_measured` (L-155, L-160, L-172; prior L-100).
**Authority:** CLAUDE.md Rule V-5 (`success` is a status of the operation, not
of the result), Rule V-1 (a claim carries the command and the value), D-115 (a
control queries the thing it asserts).

## The defect family, and why rung 4 means the control was in the wrong layer

Four times in twelve days a surface reported success from the status of an
operation while the value the operation returned said otherwise:

| Occurrence | Surface | What was read as success | What the value said |
|---|---|---|---|
| L-100 | release script | a gate ran to completion | the vintage on the same line was the old one |
| L-155 | lander summary | `gh pr merge --auto` exited 0 | arming is not merging; the merge had not happened |
| L-160 | ops report | a step returned | the count it should have asserted was zero |
| L-172 | ecosystem audit | `gh api` exited 0 | `qesis-integrity: failure`, `PR 71 DIRTY` |

Each was fixed where it was found. The fourth occurrence shows the fix was
applied one layer too low every time: the reader of a report was expected to
notice that a green row carried a red value. A reader is not a control.

## Decision

1. **Every audited row is one of two kinds, and the kind is stated on the row.**
   A **gate** is a script built so that its exit code IS its contract; exit 0
   means the property holds, and that script owns V-2 fixtures proving it. A
   **measurement** is a value fetched from a resource; its verdict is an
   explicit predicate evaluated over the PARSED value, beside the fetch, in the
   generator. The fetch's exit code decides nothing about a measurement.
2. **Unparseable is FAIL.** A measurement whose value cannot be parsed is red,
   never green by default and never silently skipped.
3. **No predicate, no colour.** A row that carries a value but no predicate is
   INFO. It is shown, it is recorded, and it cannot make the verdict green or
   red. The verdict is computed from PASS and FAIL rows and from nothing else.
4. **The predicate lives in the layer that produces the report**, next to the
   fetch, and is printed on the row as its basis. A downstream reader, human or
   agent, never has to infer the rule that coloured a row.
5. **Required means required.** Whether a status check gates `main` is read
   from the branch ruleset, never from a name filter. A required check with no
   run is FAIL (L-092: a required check that never reports blocks forever and
   shows nothing red). A check that is not required is INFO by rule 3.

## Where it is applied

- `scripts/audit_ecosystem.py`: `gate()` and `measure()` are the only two row
  constructors. Section C reads `repos/{slug}/rules/branches/main` for the
  required contexts and evaluates each against the latest check run; a DIRTY
  pull request fails the row (L-165); section D evaluates `/health` field by
  field and fails when `deployment_commit` is not `main`.
- `LAND_EVERYTHING_FINAL.ps1`: the closing summary is built from measured
  results and ends by running the audit, so the lander's last word is the
  audit's verdict, not its own.
- `scripts/gh_ops.py proof`: unchanged in shape, and it is the audit that is
  authoritative when the two disagree.

## What this does not decide

It does not turn every INFO row into a gate. Open, non-conflicting pull requests
are unlanded work and not a defect; informational check runs from integrations
this ecosystem does not own (the Cloud Build triggers, L-044) are recorded and
not asserted. Widening the predicate set is a change to this decision, made
here, with a number.
