# D-120: a null is not a pass, and the control belongs at the writer

**Status:** PROPOSED by ARCHITECT 2026-08-28. **Signs:** HUMAN. No agent signs a `D-`.
**Opened by:** the fourth rung of `success_literal_not_measured`, reached at occurrence 5 (L-211).
**Prior evidence:** L-155, L-160, L-172, L-201, L-211.

---

## 1. Why this document exists

The ladder opens a `D-` at rung 4 because a family that recurs five times is not a
run of unlucky bugs. It is a control sitting in the wrong layer. This family has
now been remediated four separate times, each time by fixing the reader that
misread a value, and it came back on the fifth occurrence in a script written the
same evening by the agent that had just recorded the fourth.

The occurrences, stated as one sentence each.

| Id | The literal that was read | What should have been measured |
|---|---|---|
| L-155 | `success` in a tool response | the row count the operation returned |
| L-160 | an exit code | the predicate the gate claims to assert |
| L-172 | a status string | the state it was standing in for |
| L-201 | `7/7` written into a banner | the number of fixtures actually present |
| L-211 | `hitl_approved != 1` | whether a decision exists at all |

And the one that opened this document, hours after L-211 was written:
`scripts/wse_city_territory.py` computed the worst absolute delta of an empty list
as `0.0`, compared `0.0 <= 5.0`, and printed **METHOD REPRODUCES THE ROLLUP** over
two null reconstructions. A falsifier reported that it had falsified nothing, and
it reported it as a pass.

## 2. The finding

Every remediation so far has been applied **at the reader**. Fix the query, fix
the banner, fix the predicate. That is why the family survives: the reader is
wherever the next author happens to be writing, so each fix is local and the next
author repeats the mistake in a new place.

The invariant these five all violate is one line: **an aggregate over an empty set
is null, and null is never a verdict.** `max([])` is not zero. `mean([])` is not
zero. `all([])` is not true in any sense a reviewer will accept. Python and SQL
both make the wrong answer the ergonomic one, and no control in this ecosystem
asserts the invariant.

## 3. The decision

**Put the invariant in a shared module and make every verdict route through it,
rather than fixing the fifth reader and waiting for the sixth.**

`qesis_agents/verdict.py` exposes one type. A verdict carries the count of
observations behind it. A verdict built on zero observations renders as
`NOT MEASURED` and can never render as a pass, and asking it whether it passed
raises rather than returning False, because False is a claim too. Every gate,
every falsifier and every counter that reports to the operator constructs its
result through that type.

The control that makes it stick is not a rule in prose. `scripts/test_gate.py`
gains a fixture applied to every registered gate: run it against an input that
matches nothing, and require the word `NOT MEASURED` or a non-zero exit. A gate
that returns a pass over an empty input fails the build.

## 4. What this costs

Every gate is touched once. That is the price of a rung-4 remediation and it is
the reason the ladder makes the fourth occurrence expensive: four cheap local
fixes cost more in total than one structural one, and they buy nothing, because
the family kept recurring through all four.

## 5. What changes if the operator decides otherwise

If the decision is to keep fixing readers, the prediction is falsifiable and
short: a sixth occurrence in a new file within a fortnight. That prediction is
recorded here so the alternative is testable rather than merely preferred.

## 6. Applied ahead of signature, because it was already shipped broken

The falsifier is repaired in `scripts/wse_city_territory.py` and a fifth fixture
pins it: a control set with two null reconstructions must render
`FALSIFIER DID NOT RUN`, never a pass. The held counter in
`scripts/apply_operator_decisions.py` is repaired at three predicate sites and now
distinguishes undecided from rejected. That repair also closes a latent hazard
nobody had noticed: as written, a standing ruling would have swept the operator's
own REJECTED decision into APPROVED, because it selected on `hitl_approved=0`
without asking whether a human had already answered.

Those two are the instances. This document is about the family.
