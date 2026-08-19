# ADR D-112: classify RDL defects by epistemic move, not by artefact

**Status:** Proposed
**Date:** 2026-08-15
**Deciders:** HUMAN (Rico) signs. SENTINEL confirms the control. ARCHITECT wires it.
**Opened by:** L-118, fourth-rung condition. Authored by COUNSEL.

---

## Context

The escalation ladder climbs on the failure family: first occurrence records,
second wires a gate, third makes it a release blocker, fourth is evidence the
control sits in the wrong layer. It has worked for every family it could name.

L-118 measured what it could not name. Ten of the thirteen lessons L-104 to
L-117 were agent defects incurred in one session, and they were not ten
mistakes. They were three, and the ladder never fired because each instance
presented on a different surface: a PowerShell block, a Python guard, a lock
file, a git claim, a ledger id.

| Family | Instances | What actually happened |
|---|---|---|
| A. The unverified guard | L-108, L-109, L-114, L-115 | A guard was written and never executed once against the state it would meet |
| B. The generalised probe | L-104, L-105, L-111 | A claim about a resource was made from a proxy for that resource |
| C. The deferral dressed as a plan | L-112 | An agent context budget presented as a property of the work |

Family A ran four times without escalating past rung one, because a duplicate
pull request, an inverted precondition, an untracked-file miscount and a partial
lock clear look like four unrelated bugs. They are one: **a property asserted
without executing the check that would falsify it.**

Two forces pull against each other. Classifying by artefact keeps the ladder
concrete and its rungs cheap to apply, and it under-counts. Classifying by
epistemic move counts correctly, and it risks a category so abstract that
everything falls in it, which disables the ladder from the other direction.

Today's session produced a fifth instance of family B before this ADR was
written. `data/DATA_MAP.json`, the control built specifically to remedy L-104
and L-105, records absolute roots under `/sessions/trusting-brave-fermat/mnt/`.
That path resolves in exactly one session. The map is declared `read_before`
any statement containing the words missing, absent or unreachable, and it
cannot support those statements from any other session. The remedy for family B
has the family B defect.

---

## Decision

Register RDL defects under the **epistemic move by which the claim was reached**,
not under the artefact the move was made in. Keep the artefact as a secondary
field so a reader hitting the same symptom from a different direction can still
find the entry.

Admit a defect to a reasoning family only under the **availability test**: a
check that would have falsified the claim was available and was not run. A
defect arising from a check that does not exist is a gap in the control set and
escalates on a separate track.

---

## Options considered

### Option A: keep artefact classification, add cross-references by hand

| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Cost | Zero to build, unbounded to maintain |
| Enforceability | None. It is a habit |
| Failure mode | The one already observed |

**Pros.** No change to the ledger, no migration, no new field. Cross-references
are already used and read well.

**Cons.** It is the status quo that produced four uncounted instances of family
A. A cross-reference is written by whoever notices the connection, and the whole
point is that nobody noticed across five surfaces. It puts the control in the
same layer as the defect: human attention at the moment of writing.

### Option B: classify by epistemic move, with the availability test as the boundary

| Dimension | Assessment |
|---|---|
| Complexity | Medium. One required field, one boundary rule, one migration pass |
| Cost | A schema field and a lint gate |
| Enforceability | Gateable at append time |
| Failure mode | Over-broad families if the boundary is not held |

**Pros.** Counts correctly. Four instances escalate as four and reach rung two,
where a gate gets wired, rather than sitting at rung one four times. Directly
addresses the measured failure. The availability test is checkable in review:
name the command that was available, or the entry does not belong to the family.

**Cons.** Requires judgement at append time, and judgement drifts. Retro-fitting
119 entries is real work, and half-migrating is worse than not migrating,
because a partially populated field reads as evidence of absence.

### Option C: dual classification, both fields required

| Dimension | Assessment |
|---|---|
| Complexity | High |
| Cost | Two fields, two taxonomies, two ways to be wrong |
| Enforceability | Gateable, and twice the surface |
| Failure mode | The two taxonomies disagree and nothing says which wins |

**Pros.** Loses nothing. Preserves artefact retrieval exactly as it is today.

**Cons.** This project has a documented and recurring defect class of exactly
this shape: one fact in two places with no precedence rule. D-103 violation D,
CONC-1, R1.28 and EMO-1 are all instances. Adding a second authoritative
taxonomy without a precedence rule is that pattern volunteered rather than
inherited.

---

## Trade-off analysis

The real choice is A against B. C is B plus the failure mode this ecosystem
already knows how to produce.

A is cheaper and has been measured failing. B costs a field and a gate and
addresses the measured cause. The decisive argument is not that B is elegant, it
is that A's control lives in the layer that failed: noticing. The fourth rung
exists to say precisely that, and this is a fourth-rung condition.

The honest objection to B is the abstraction risk, and it is not hypothetical.
"Asserting without checking" describes most defects if the boundary is loose.
The availability test is what makes it narrow: the entry must name the specific
command that was available and not run. `git rev-parse origin/<branch>` for
L-080. `ls sovereign-infra` for L-104. `grep -c graph scripts/test_gate.py` for
KG-1. If no such command can be named, the entry is a control gap, not a
reasoning defect, and it goes on the other track. That test is falsifiable by a
reviewer, which is the property the taxonomy needs and the reason to prefer it
over a definition.

**What this ADR does not claim.** It does not claim the reclassification would
have prevented L-104 through L-117. Family A's four instances happened inside
one session and the ladder cannot escalate faster than entries are written.
What it claims is narrower: at the end of that session the ledger would have
shown four instances of one family standing at rung three, requiring a release
blocker, instead of four unrelated entries at rung one.

---

## Consequences

**Easier.** Counting. A family reaching rung two triggers a gate while the
instances are still fresh. Retrieval by symptom survives through the retained
artefact field.

**Harder.** Appending. Every entry now answers "which check was available and
not run", and entries that cannot answer it move track. That is friction on
purpose and it is the cost being accepted.

**To revisit.** Whether three families are the right number. Three is what one
session's evidence supports and it is almost certainly incomplete. The taxonomy
is expected to grow and the ADR should be reopened at the first family that does
not fit, rather than that family being forced into one that nearly fits.

**Adjacent finding this ADR does not resolve.** The `D-` namespace has drifted.
`citation_concordance.id_namespace` declares D-001 to D-099 as ecosystem
decisions and D-101 upward as defects found in the v6.6 lineage, while D-108,
D-109, D-110 and D-111 are all decisions living in the defect range. This ADR is
numbered D-112 to follow observed practice rather than the declared rule, which
is the wrong resolution and is recorded here so it is not mistaken for
agreement. One of the two must be corrected.

---

## Action items

1. [ ] HUMAN signs or refuses. No agent signs a `D-` decision.
2. [ ] ARCHITECT adds `epistemic_family` and retains `artefact` on the ledger
       entry schema, with the availability test written into the field
       description rather than into prose elsewhere (L-054).
3. [ ] ARCHITECT wires the append-time gate: an entry claiming a reasoning
       family must name the command that was available and not run. Two
       fixtures, one it must refuse and one it must accept (V-2).
4. [ ] SENTINEL migrates L-001 to L-118 in one pass, never partially, and
       records the count of entries that could not be classified rather than
       forcing them.
5. [ ] ARCHITECT fixes `build_data_map.py` to store repository-relative paths
       and resolve the root at read time, and asserts that no recorded path
       contains a session identifier. Family B's only control currently has
       family B's defect.
6. [ ] HUMAN rules on the `D-` namespace drift recorded above.
