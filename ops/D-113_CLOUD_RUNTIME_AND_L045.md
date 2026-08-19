# D-113: the cloud runtime, and the decision L-045 has been waiting for

**Status:** Proposed. **Date:** 2026-08-15. **Author:** COUNSEL.
**Signs:** HUMAN. No agent signs a `D-`.
**Closes:** L-045, open since 2026-07-29.
**Supersedes nothing. Amends no boundary in G-03, G-04, G-06 or G-07.**

---

## 0. Why this document exists, in one paragraph

L-045 says: "when the product is a critique of a dependency, adopting that
dependency is a governance decision with a decision number, never an
infrastructure convenience. State it before, not when a reviewer asks."

The operator was asked today where the runtime lives and answered, accurately,
that he does not know. That answer **is** the finding. An ecosystem whose entire
thesis is that states cannot see their own substrate dependencies could not see
its own. The reviewer's question was never going to be "why did you use AWS". It
was always going to be "did you notice".

This document is the noticing, and the decision number.

---

## 1. The measured footprint

Determined 2026-08-15 by inspection, not by recollection. Where a value sits
behind a credential, COUNSEL names the file and does not open it (G-03).

| Layer | Provider | Ultimate substrate | Jurisdiction | Evidence |
|---|---|---|---|---|
| Served endpoint | Vercel | AWS | US | `qesis-mcp.vercel.app`, `vercel.json`, `VERCEL_OIDC_TOKEN` in `.env.local` |
| CI, gates, self-heal loop | GitHub Actions | Microsoft Azure | US | `.github/workflows/*`, `ubuntu-latest` hosted runners |
| Source of record, both repos | GitHub | Microsoft Azure | US | `origin` remotes |
| Evidence-plane mirror | OneDrive | Microsoft | US | operator-supplied share link, 2026-08-15 |
| Agent runtime, this session | Anthropic | AWS | US | Claude |
| Database | **UNDETERMINED** | unknown | unknown | `database_string.txt`, deliberately unopened |
| Signing key custody | local `.env` | operator machine | ES | `FSQCA_ED25519_PRIV_B64`, name read, value never |

**Concentration, stated plainly.** Four of the six determined layers resolve to
**two** US hyperscalers, and one vendor, Microsoft, holds the source of record,
the CI, the self-heal loop and the evidence mirror simultaneously. That is not a
diversified posture. It is a single-vendor dependency across every plane except
the served endpoint, and the served endpoint's provider runs on the other one.

**The undetermined row is a finding, not a gap in this document.** An index that
publishes source SHA-256 hashes for every axis cannot say "unknown" about where
its own database lives. `ACT-1` below closes it, and it is a human act because
the answer sits behind a credential.

---

## 2. The decision

**Adopt the current posture explicitly, and instrument it.** Do not migrate.

Three options were considered and the reasoning matters more than the verdict.

### Option A: migrate the runtime to an EU-jurisdiction provider

| Dimension | Assessment |
|---|---|
| Reduces the contradiction | Materially, on jurisdiction. Not on hyperscale concentration, since Hetzner and OVH are still concentrated substrate |
| Cost | Recurring, plus a migration during a live release cycle |
| Removes the specific failure | **No.** The failure L-045 names is an *undeclared* dependency, not a US one |

**Refused, and this is the load-bearing argument.** L-044 requires each service
to be priced against the specific failure it removes. The failure here is that
the exposure was never stated. Migration does not state it, it relocates it, and
an EU provider adopted without a decision number reproduces L-045 in a different
jurisdiction. Migration may still be right later, on cost or on latency or on a
client requirement. It is not the remedy for this lesson.

### Option B: self-hosted always-on machine

| Dimension | Assessment |
|---|---|
| Preserves the sovereignty claim | Most fully of the three |
| Removes the specific failure | No, for the same reason as A |
| Cost | The operator becomes the SRE for a public endpoint, and R-01 already records single-operator concentration as the standing red risk |

**Refused.** It converts a vendor dependency into a person dependency, and the
person is already the sole approver on twenty-five Article 14 decisions and the
named risk in R-01. It also contradicts the operator's own instruction that no
task depend on his machine.

### Option C: declare, instrument, and diversify only where it buys something

**Adopted.** Three limbs:

1. **Declare.** This document, plus a served `instrument_exposure` block once
   SENTINEL gates it, so a reader of the index can see the index's own posture
   without asking.
2. **Instrument.** `scripts/self_exposure.py` scores the instrument on its own
   seven axes. Computed now, published later, per the operator's ruling of
   2026-08-15.
3. **Diversify narrowly.** Only where a second provider removes a named failure.
   The one that qualifies today is custody of the signing key and the chain
   spine, because those are the artefacts whose loss is unrecoverable, and both
   currently sit in one vendor's estate plus one laptop.

---

## 3. Why this is the stronger position, and the counter-argument

**The strong form.** An index measuring substrate dependency, which publishes its
own substrate dependency on the same axes, using the same calibration, is making
a claim no competitor can make. Every sovereignty index in existence runs on
someone's cloud. This is the only one that says so in its own units. The
contradiction, once measured, stops being a vulnerability and becomes the
worked example: here is what the method looks like applied to something you can
verify independently, because you are looking at it.

**The counter-argument, stated before it is asked for.** A self-assessment
produced by the instrument on itself is not independent, and no amount of
methodological care makes it so. The score can be checked but the framing cannot:
QESIS chose the axes, the weights and the anchors, and an entity scoring itself
under rules it wrote is in a different epistemic position from the 32 states that
did not consent to being scored at all. This asymmetry is not resolved by this
document and should not be presented as resolved. It is disclosed, and the
disclosure travels with the block. Publication remains held under §5.

**The second counter-argument.** Declaring an exposure does not reduce it. If
AWS or Azure withdraws service, the served index goes dark regardless of how
elegantly the dependency was documented. `ACT-4` is the only limb of this
decision that changes the physical facts, and it is deliberately narrow.

---

## 4. Consequences

**Easier.** The reviewer's obvious question is answered in the artefact rather
than in a defensive reply. The `states` and `regions` dual frame of D-111 gains a
third comparator that is neither: the instrument itself.

**Harder.** Every future infrastructure choice now needs a line in this document.
That friction is the control, and it is the whole content of L-045.

**To revisit.** Reopen on any of: a client or institutional licence requiring EU
data residency, a second vendor entering any plane, the database provider being
determined under `ACT-1`, or the `instrument_exposure` block reaching the served
surface.

---

## 5. Publication status: COMPUTED, NOT PUBLISHED

Ruled by the operator, 2026-08-15: compute the self-assessment into the evidence
plane, hold publication.

`scripts/self_exposure.py` writes `data/axes/instrument_self_exposure.json` and
writes **nothing** to `data/qesis_v8.json` or any served surface. `served: false`
is carried inside the artefact so a later reader cannot mistake an evidence file
for a published one. Publication is a separate change set requiring SENTINEL
`gate_publication`, and the operator reading the numbers first.

---

## 6. Action items

| Id | Action | Owner |
|---|---|---|
| `ACT-1` | Determine the database provider and jurisdiction from `database_string.txt` and record it in §1. COUNSEL will not open the file (G-03) | **HUMAN** |
| `ACT-2` | Sign or refuse this decision | **HUMAN** |
| `ACT-3` | Run `scripts/self_exposure.py`, read the numbers, then rule on publication | HUMAN, then SENTINEL |
| `ACT-4` | Move the chain spine and the release attestations to a second, independent custody. Narrow diversification: these are the unrecoverable artefacts | ARCHITECT proposes, HUMAN approves |
| `ACT-5` | Rotate `FSQCA_ED25519_PRIV_B64` out of a plaintext `.env` into the platform secret store. Rotation is never an agent action (G-03) | **HUMAN** |
| `ACT-6` | Confirm the OneDrive mirror is read-only export and not the writable evidence plane. D-027 and G-03 forbid a writable plane on a sync target, because provider-side version history survives local deletion | **HUMAN** |

`ACT-5` and `ACT-6` are the two items on this page that are security findings
rather than governance ones, and they would be true regardless of which cloud the
runtime sits in.
