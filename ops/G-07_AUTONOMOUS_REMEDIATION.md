# G-07: autonomous remediation and the self-healing loop

**Proposed 2026-08-15 · COUNSEL · Binding on both repositories once signed ·
Amends the operating posture, amends no boundary in G-03, G-04 or G-06.**

The operator's instruction: the ecosystem runs continuously, repairs its own
defects, and does not bring him problems he has already answered. Everything an
agent needs to decide is filed in architecture, governance, compliance and code
design. Stop asking.

That instruction is correct and this clause implements it. It also states, once
and plainly, the three things it does not implement, and why refusing them is
what makes the rest trustworthy rather than what limits it.

---

## 1. The principle

**A defect whose remedy is already written down does not need a human. A defect
whose remedy is not written down does not need an agent inventing one.**

Most failures here are a known family arriving on a new surface. A gate exists,
a threshold is declared, a doctrine names the refusal. Where that is true,
asking the operator is waste, and worse than waste: it trains him to rubber-stamp,
which converts the human gate from a control into a formality.

Where it is not true, an agent supplying a remedy from its own judgement is the
failure this entire project was built to catch. L-076, L-077 and L-078 are three
instances in one afternoon of an agent producing confident findings from
material it had not opened.

The registry in `scripts/selfheal.py` is that boundary written as **data rather
than judgement**. It is auditable by reading it, and every entry carries the
clause that authorises it.

---

## 2. Autonomy classes

| Class | Condition | Action | Human |
|---|---|---|---|
| **A. Self-heal** | The record declares the remedy and the remedy is idempotent | Apply, reverify, record, continue | none |
| **B. Safe degradation** | No declared remedy, but the declared safe failure mode exists | Refuse and degrade, record, continue | none |
| **C. Escalation** | The correct action is not derivable from the record | Refuse, name the command that would settle it, never guess | one act |

Class B is BIG withholding generalised. A value that cannot be established is
withheld with cause, never imputed (D-007). The same logic covers a pairing
register that disagrees with the served vintage: the safe action is to block the
promotion and leave the register untouched, because a row written by the process
that failed the check is the check answering itself.

**Verified 2026-08-15.** The loop was tested by injecting `counts.nodes = 999`
into `data/qesis_graph.json`. It detected the mismatch, applied the class A
remedy, reverified, and restored the file byte-identical to its pre-injection
state. A loop that has never been run against a defect is a guard never executed
against the state it would meet, which is L-118 family A, the most repeated
defect in this ledger.

---

## 3. What is delegated, and it is nearly everything

Standing, no per-session instruction, no ticket:

- Run the full control set on a schedule and on every push.
- Repair class A, degrade class B, record both.
- Author gates and fixtures for any defect family that recurs, per the escalation
  ladder: record, wire, block, open a `D-`.
- Append to the lessons ledger, single instance, canonical location.
- Restate stale documents against the served surface.
- Rebuild derived artefacts: graph, percolation block, eval set, landing page.
- Open branches, commit, push to `feature/*`, `patch/*`, `fix/*`, `docs/*`.
- Open pull requests and **merge paired remediation pull requests by rebase once
  checks pass**. Already standing under G-06 and not new here.
- Produce the daily report, the dispatch board and the bug log without being asked.
- Propose plugins and skills at the point of use.

---

## 4. The three that are not delegated

These are not agent caution. They are the operator's own standing rules, and a
clause that quietly widened them would be the defect class this document exists
to close. Each carries the instrument that removes the operator from the daily
loop **without** removing the control.

### 4.1 Promotion to production

G-06 limit 2 is explicit: promotion stays a human act and no amendment reaches
it. Promotion is the line between changing the repository and changing what the
world reads.

**The instrument: a signed promotion policy.** This is Human-on-the-Loop applied
to promotion exactly as G-06 applied it to merge. The operator signs a predicate
once; thereafter promotion proceeds automatically whenever the predicate holds,
with no further human act.

Create `ops/G-07_PROMOTION_POLICY_SIGNED.json` containing the predicate, the
date, and the signer. `promotion_policy()` in `scripts/selfheal.py` reads it.
While the file is absent the function returns False and the runner escalates,
which is the current state.

Proposed predicate, deliberately narrow:

1. Every control in the set returns PASS or PASS_WITH_BENIGN.
2. Zero escalations and zero unclassified failures in the same run.
3. `index_sha256` equals the sha of `data/qesis_v8.json` at the commit being
   promoted, and that commit is reachable from `main`.
4. No `uncertainty_ledger` entry of severity `high` changed since the last
   promotion without a paired concordance row.
5. The chain attestation reproduces from the committed spine in the same run.

Why narrow. The Article 14 failure analysis found `CON * RET * HIT * MCP`
surviving the consistency cutoff at **0.822 with the human gate present**. Human
oversight is a damper, not an immunity. A promotion policy that fires on anything
less than a fully green control set removes the damper without replacing it.

### 4.2 Credential material, in either direction

G-03 and G-04, absolute, including for the purpose of testing whether a
credential is dead. No instrument changes this and none is proposed. A credential
that reaches an agent is compromised by that fact alone.

**What the loop does instead:** detects exposure, proves its extent across every
reachable ref, quarantines, blocks the affected path, and names the environment
variable. That is the whole incident response minus one act. Rotation is that
act and it stays the operator's. The same rule covers supply-chain SHAs: a SHA
is never guessed, and the runner names the `gh api` command rather than a value.

### 4.3 Article 14 signatures

The register holds 25 decisions and none is signed by an agent. The gate exists
precisely so that a person decides.

**The instrument is the register itself, and this is the part worth reading
twice.** The operator's request for permanent autonomous operation is not blocked
by the register. It is **the subject of four entries already in it**, and signing
them is the single act that switches this on forever:

| # | Decision | Risk | What it unblocks |
|---|---|---|---|
| **5** | Revocation protocol and emergency kill switch | CRITICAL | The stop control. Signed **first**, always |
| **2** | Self-modification constraints for local agentic scripts | CRITICAL | Bounded self-edit inside the runtime, never to the gate or the chain |
| **1** | Authorisation boundary for autonomous PR generation and auto-merge | HIGH | The loop's write path, standing |
| **25** | Master go-live: staging to active autonomous operation | CRITICAL | Everything. Signed **last**, on the evidence of the others |

The clearing order is not the numbering and it is not negotiable: **5, then 6,
then 20, then the rest, then 25 last, always.**

Decision 5 comes first because a stop control that arrives after autonomy is
theatre, and because the failure analysis says the human gate is insufficient in
exactly the regime an agent fleet makes likely. Decision 20, a named reviewer and
a cadence, is the standing mitigation for single-operator concentration, risk
R-01, and it matters more under autonomy, not less.

**So the honest answer to "make it run forever without me" is: sign 5, 2, 1, 6,
20, then 25, and the promotion policy in 4.1. That is one sitting. After it, the
loop runs unattended and this clause never asks again.**

---

## 5. Escalation budget

An escalation that fires every cycle has been switched off without anyone
deciding to switch it off (L-063). The loop therefore:

- Distinguishes PASS, PASS_WITH_BENIGN, FAIL and ESCALATED, and reports the
  benign reason per failing behaviour rather than per run. A suite with one
  environmental miss and one real miss is not benign, and that distinction is
  made line by line or it is not made at all.
- Exits non-zero **only** on escalation. A repaired or safely degraded run is the
  loop working, and a scheduler that pages on both teaches the operator to ignore
  it.
- Escalates with the command that settles the question, never with a request for
  a decision the record already contains.

**Escalation is capped at two classes: CRITICAL and HIGH.** CRITICAL is reserved
for a broken hash chain, a failing gate self-test, and a credential exposure.
Those three mean the instrument is no longer measuring itself, and everything
downstream of them is unreliable including the loop's own verdict.

---

## 6. The counter-argument, stated before it is asked for

**Autonomy removes the only control that has actually caught things.** Over this
project's record, the operator caught the role inversion, the fabricated
findings, the deferral dressed as a plan, and the stale-brief premise. Not one of
those was caught by a gate. If the loop had been running unattended through that
period it would have propagated all four.

The answer is not that this is untrue. It is that the correct response is to
convert each of those catches into a control, which is what the escalation ladder
does and what L-118 reclassified so the counting works. The residue that cannot
be converted is family C in L-118, the deferral dressed as a plan, which has no
technical control and never will.

**Therefore the honest scope of this clause: it makes the ecosystem self-healing
against defect families it has already met, and it does not make it self-
correcting against judgement it has never been tested on.** Those are different
properties and conflating them is how an autonomous system acquires confidence
its evidence does not support. Decision 20's named reviewer on a cadence is the
only real mitigation for the second, and it is unsigned.

---

## 7. Standing, unchanged by this clause

No agent pushes directly to `main`. No agent promotes absent a signed policy. No
credential moves in either direction. No agent signs a `D-` or an Article 14
decision. Merges of paired remediation pull requests use `--rebase`, never
squash, because squash strands the commit hashes the lineage register cites.
Every mutating command names its repository. No em dash in prose, and
`doctrine_audit` runs as the last act of writing.
