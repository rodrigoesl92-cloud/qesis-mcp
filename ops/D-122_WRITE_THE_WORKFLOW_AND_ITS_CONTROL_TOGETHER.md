# D-122: a workflow and its control-set entry are one change, not two

**Status:** PROPOSED by ARCHITECT 2026-08-29. **Signs:** HUMAN. No agent signs a `D-`.
**Opened by:** the fourth rung of `paired_what_is_not_pairable`, reached at occurrence 4 (L-216).
**Prior evidence:** L-163, L-171, L-175.

---

## 1. What happened, and what did not

A workflow was written that runs two scripts in CI. The self-heal control set was
not updated in the same change. `verify_workflow_contract.py` refused at step 1 of
23 of the operator's own landing, named both scripts, and the lander stopped
before it committed, pushed or opened anything.

**The control worked.** It caught the defect at the earliest possible moment and
cost one aborted run rather than a red `main` or a broken required check. Nothing
about the gate needs strengthening.

## 2. Why the rung still climbed, and why that is right

The ladder escalates on the family, never on the outcome of any single instance.
Four times now a change has added an obligation on one side of a pair and left the
other side alone: a workflow without its control, a lesson without its gate, a
ledger without its gaps file. The gate catches each one **after** the author has
finished and the operator has clicked. That is a good place to catch it and a bad
place to be told about it.

Rung 4 says the control sits in the wrong layer. Here the diagnosis is precise:
the **detecting** control is in exactly the right layer, and there is no
**preventing** control at all. Nothing exists at authoring time that knows a
workflow step implies a control-set entry. The knowledge lives in a document and
in the memory of whoever is writing.

## 3. The decision

**Move the pairing from detection to authoring.**

`scripts/new_workflow.py` scaffolds a workflow and, in the same run, writes the
matching `CONTROLS` entries into `scripts/selfheal.py` or refuses and prints the
exact lines to add. It reads the step list it just generated, so the pair cannot
diverge at the moment of creation. `verify_workflow_contract.py` stays exactly as
it is: the scaffold prevents, the gate still catches, and neither replaces the
other.

Two fixtures, per V-2. One workflow that adds a script must produce its control
entry. One workflow whose scripts are all already controls must add nothing and
say so.

## 4. What this costs, and the honest alternative

It costs one script and a habit. The alternative is to accept that the gate
catches it every time and pay one aborted landing per new workflow, which is
cheap in isolation and has now happened four times.

The prediction, so the alternative is testable rather than merely preferred: with
no authoring-time control, a fifth instance appears the next time a workflow or a
paired artefact is added, and it will again be found by a gate rather than
prevented.

## 5. Baseline

`ops/RDL_BASELINE.json` moves this family from rung 3 to rung 4 with this document
as its reason. Accepting a baseline without a stated reason is a silent amnesty,
which is why the accessor refuses one.
