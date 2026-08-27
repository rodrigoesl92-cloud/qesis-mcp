# D-113: the cloud runtime, and the decision L-045 has been waiting for

**Status:** ACCEPTED, signed by the operator 2026-08-19. **Date:** 2026-08-15. **Author:** COUNSEL.
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
| Database | Neon (`eu-central-1`) | AWS | US vendor, EU region | Operator-declared D-1, 2026-08-19. Not verified by COUNSEL: the connection string is not opened (G-03) |
| Signing key custody | local `.env` | operator machine | ES | `FSQCA_ED25519_PRIV_B64`, name read, value never |
| **Continuous deployment triggers, UNDECLARED** | **Google Cloud** | **Google** | **europe-west1** | **Found 2026-08-27. Two Cloud Build triggers in project `5c4e8a9a-723a-453e-80d` write check runs onto every `qesis-mcp` commit and have been failing. Nothing in either repository produces them. See ACT-7** |

**Concentration, stated plainly, recomputed at n=6 on 2026-08-19.** ODI 50.0, FPE 100.0, RGD 50.0. Adding the database changed the concentration barely at all, and the reason is the finding: Neon is managed Postgres running on AWS, so it is not a sixth vendor, it is a third AWS layer. Recording it as its own substrate would have manufactured a diversification that does not exist. Five of the six determined layers resolve to
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

**Re-tested 2026-08-27 against a live request to deploy a container backend to
Cloud Run in europe-west1.** The refusal stands, for the reason it was written.
L-044 requires each service to be priced against the specific failure it
removes. The failure presented was two red checks on a commit page. A container
backend does not remove that failure, it supplies a build for triggers nobody
declared, starts a bill, and creates a second surface serving the same index
while the chain binds exactly one artefact. Disconnecting the triggers removes
the failure completely and costs nothing. Option A remains available and remains
a decision, not a configuration: a client or institutional licence requiring EU
data residency reopens this page, and the database already rests in
`eu-central-1` under `ACT-1`.

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
| `ACT-1` | **CLOSED 2026-08-19.** Operator declared Neon, `eu-central-1`. Recorded as declared rather than measured. Opens SX-04: FPE is computed on vendor jurisdiction while the data rests in the EU, and whether platform exposure belongs at the vendor or at the region is a real question the state axis never had to answer | closed |
| `ACT-2` | Sign or refuse this decision | **HUMAN** |
| `ACT-3` | Run `scripts/self_exposure.py`, read the numbers, then rule on publication | HUMAN, then SENTINEL |
| `ACT-4` | Move the chain spine and the release attestations to a second, independent custody. Narrow diversification: these are the unrecoverable artefacts | ARCHITECT proposes, HUMAN approves |
| `ACT-5` | **Gate shipped 2026-08-19**, `scripts/verify_no_plaintext_secrets.py`, wired into CI and the Vercel pre-build gate with four fixtures. The gate proves `.env` stays untracked and covered; it cannot move the key. Injecting it into GitHub Actions and Vercel and rotating it remains a human act (G-03) | **HUMAN** |
| `ACT-6` | Confirm the OneDrive mirror is read-only export and not the writable evidence plane. D-027 and G-03 forbid a writable plane on a sync target, because provider-side version history survives local deletion | **HUMAN** |

| `ACT-7` | **Opened 2026-08-27.** Two Cloud Run triggers in Google Cloud project `5c4e8a9a-723a-453e-80d` write to `qesis-mcp` commit status and fail on every commit. Nothing in either repository can build a container: no Dockerfile, no `cloudbuild.yaml`, no Procfile, no `main.py`. They deploy nothing and they are not declared here. **Neither identifier is canonical:** `qesis_agents/cloud.py` fixes the project at `qesis-sovereign-infra` and the region at `europe-west3`, and the checks name a different project and `europe-west1`, so this is a second undeclared connection rather than a misconfiguration of the declared one. **Rule on them: disconnect, or declare with a row above and a container this ecosystem actually builds.** Runnable procedure at `sovereign-infra/ops/GCP_DISCONNECT_TRIGGERS.md`. The account is credentialed, so the act is human under G-03; the visibility is not, and `gh_ops.py foreign_checks` shipped in the same change set that opened this item | **HUMAN** |

| `ACT-8` | **Opened 2026-08-27.** `qesis.eu`, the EU-registered public address, redirects 308 to `www.qesis.eu`, which is NXDOMAIN at the zone's own authoritative nameserver. The registrar counted 768 errors in 1377 queries over 24 hours. The application is healthy: `qesis.qesis.eu` returns 200 with the landed commit and a verified chain. Fix by making `qesis.eu` the primary domain on the Vercel project, which needs no zone edit, or by creating the `www` CNAME to the target Vercel shows for that domain. Credentialed, so human under G-03. The domain also belongs in the footprint table above once it is serving, because a `.eu` registration is the only EU-jurisdiction layer this ecosystem holds | **HUMAN** |

`ACT-5` and `ACT-6` are the two items on this page that are security findings
rather than governance ones, and they would be true regardless of which cloud the
runtime sits in.
