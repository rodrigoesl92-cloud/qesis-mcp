# Decision dossier, 2026-08-19

**For: Rico, sole approver. Prepared by COUNSEL under CLAUDE.md rule SH-9.**
**Six decisions. Each carries a recommendation. You decide, I implement.**

State at the top of this document, measured: PR #64 merged, production deployed
from `main` at `8b12760`, self-heal `verdict GREEN`, `test_gate` 49/49, promotion
`HELD` pending signature. Issue #63 is open with 67 comments and closes itself on
the next probe run.

---

## D-1. Name the database provider (D-113 ACT-1)

**What it is.** `data/axes/instrument_self_exposure.json` carries `ESE:
UNDETERMINED, cause CREDENTIAL_BOUND`. The instrument scores its own substrate on
three axes and cannot score the fourth, because the database provider sits in
`database_string.txt`.

**Why it is yours.** G-03. An agent does not open a file that holds a connection
string, and reading one to learn a hostname is still reading one. There is no
version of this I can do.

**The options.**

| | What it buys | What it costs |
|---|---|---|
| Tell me the provider and region | ESE becomes MEASURED. Self-exposure coverage rises from 0.25 toward the 0.75 gate | Two minutes |
| Leave it UNDETERMINED | Nothing | The index publishes source SHA-256 for every axis and says "unknown" about its own database |

**COUNSEL recommends: name it.** Standard: G-02 provenance precedence and the
BIG discipline. The whole instrument rests on the claim that an unmeasured thing
is declared rather than guessed. `UNDETERMINED` is an honest label and it is also
the only row in the substrate table with no evidence beside it. Every other row
names its file.

**Reply with just the provider and region**, for example `Neon, eu-central-1` or
`Supabase, us-east-1`. Never the connection string, never a fragment of it. If
you paste one by accident, that is an INC and rotation follows, so send the two
words only.

**If you decide otherwise:** `ESE` stays UNDETERMINED, D-113 §1 keeps its
UNDETERMINED row, and the self-exposure artefact remains at coverage 0.25. It
still works. It is just quieter than it should be about the one layer you can
actually change.

**On your decision I:** update `SUBSTRATE` in `scripts/self_exposure.py`, rerun
it, update D-113 §1, and recompute ODI, FPE and RGD, which will move because n
rises from 5 to 6.

---

## D-2. Rotate the signing key out of plaintext (D-113 ACT-5)

**What it is.** `.env` holds `FSQCA_ED25519_PRIV_B64`. I read the variable name
and never the value. It is the key that signs fsQCA artefacts.

**Why it is yours.** G-03 and G-04. Rotation is never an agent action, and the
incident record already carries four credential exposures, three of them caused
by remedies for the previous one.

**The options.**

| | What it buys | What it costs |
|---|---|---|
| Move to GitHub Actions secret + Vercel env var, rotate on move | Key leaves the disk. Cloud-only, consistent with SH-7 | Twenty minutes and one re-sign of existing artefacts |
| Move without rotating | Key leaves the disk | The old value has sat in a plaintext file on a machine that syncs to OneDrive. Provider-side version history survives local deletion |
| Leave as is | Nothing | A signing key in plaintext on a synced machine |

**COUNSEL recommends: move AND rotate.** Standard: G-03's sync-folder clause
verbatim, "cloud sync retains provider-side version history that survives local
deletion, so a secret written there is not removed by deleting it. Rotation is
the only remedy." The file is on a machine with OneDrive. Treat the current value
as disclosed, because under your own rule it is.

**If you decide otherwise:** the key stays reachable by anything that reads the
disk or the sync history, and the signature on every fsQCA artefact means less
than it appears to, because a signature whose key may be held elsewhere certifies
nothing.

**On your decision I:** write the runbook, add a `verify_no_plaintext_secrets.py`
gate with a refuse fixture and an accept fixture, wire it into
`qesis-integrity.yml`, and register the lesson. I will name the environment
variables and never see a value.

---

## D-3. Confirm the OneDrive mirror is read-only export (D-113 ACT-6)

**What it is.** You shared a OneDrive link for `sovereign-infra`. I do not know
whether that is an export of published material or the writable evidence plane.

**Why it is yours.** Only you know how that folder is used, and I will not infer
it from a link.

**The options.**

| | What it buys | What it costs |
|---|---|---|
| Read-only export of published material | A shareable map, and D-027 is satisfied | Nothing |
| Writable evidence plane on OneDrive | Convenience | D-027 and G-03 both forbid it. SQLite locking semantics break on sync mounts, and INC-20260731-01 is the case where a folder built for safe artefacts became a credential location by accident |

**COUNSEL recommends: read-only export, and the authoritative plane stays in
git.** Standard: D-027, plus L-042, a gate scans sources and never copies, and
any control that can modify a backup can corrupt a restore. Git already gives you
history, hashes and reproducibility. OneDrive gives you a folder that looks like
the same thing and is not.

**If you decide otherwise:** the pairing register cites commit hashes that a
synced folder cannot reproduce, and `verify_vintage_pairing.py` would be checking
a plane that is no longer authoritative.

**On your decision I:** if export, add a one-line note to D-113 §1 and nothing
changes. If writable, that is a `D-` decision of its own and I will draft it with
the objection stated, because a rule you overrule deliberately is fine and one
overruled silently is not.

---

## D-4. Sign or refuse D-112, and rule on the namespace drift

**What it is.** Two decisions inside one document. First, classify RDL defects by
**epistemic move** under an availability test rather than by artefact. Second,
`citation_concordance.id_namespace` declares D-001 to D-099 as decisions and D-101
upward as v6.6-lineage defects, while D-108 through D-113 are decisions living in
the defect range.

**Why it is yours.** No agent signs a `D-`.

**COUNSEL recommends: sign D-112 as Option B**, classify by epistemic move.
Standard: the escalation ladder itself, and L-118's measurement that ten of
thirteen lessons were three families the ladder could not name. It earned itself
again this week: L-124, L-125 and L-128 are all family A, "a guard authored and
then bypassed by the command meant to respect it", and under artefact
classification they read as three unrelated bugs. Under D-112 they are rung three,
which requires a release blocker.

**COUNSEL recommends: amend the namespace rule rather than renumber.** Renumbering
breaks live citations in the served payload. The amendment should say why the
ranges stopped meaning what they said, rather than quietly widening.

**If you decide otherwise:** the ladder keeps under-counting, and the next four
instances of family A will arrive as four rung-one entries exactly as these did.

**On your decision I:** add `epistemic_family` to the ledger entry schema with
the availability test in the field description rather than in prose elsewhere,
wire the append-time gate with two fixtures, and migrate L-001 to L-128 in one
pass, recording the count that could not be classified rather than forcing them.

---

## D-5. Sign or refuse D-113

**What it is.** Adopt the current cloud posture explicitly rather than migrating,
and instrument it. Measured: four of five determined layers on two US
hyperscalers, one vendor holding source of record, CI, self-heal loop and
evidence mirror simultaneously.

**Why it is yours.** L-045's own rule: adopting a dependency your product
critiques is a governance decision with a number, never an infrastructure
convenience.

**COUNSEL recommends: sign it as written, Option C.** Standard: L-044, price each
service against the failure it removes. The failure L-045 names is an *undeclared*
dependency. Migration relocates the dependency and does not declare it, so an EU
host adopted without a decision number reproduces L-045 in a different
jurisdiction. Migration may be right later on cost, latency or a client's data
residency requirement. It is not the remedy for this lesson.

**The counter-argument I owe you.** Declaring an exposure does not reduce it. If
either hyperscaler withdraws service the index goes dark regardless of how well
documented the dependency is. Only ACT-4, second custody for the chain spine and
the release attestations, changes a physical fact, and it is deliberately narrow
because those are the artefacts whose loss is unrecoverable.

**If you decide otherwise and migrate:** budget a recurring cost and a migration
during a live release cycle, and D-113 gets rewritten to argue the new posture.
The self-exposure numbers will improve on FPE and barely move on ODI, because
Hetzner and OVH are still concentrated substrate.

**On your decision I:** mark D-113 Accepted, and open ACT-4 as a scoped proposal
with two custody options priced.

---

## D-6. Article 14, in order: 5, 2, 1, 6, 20, then 25

**What it is.** Six of the twenty-five held decisions. Signing them is what makes
the loop autonomous rather than merely scheduled.

**Why it is yours.** "Nothing in this register is signed by an agent. The gate
exists precisely so that a person decides."

**COUNSEL recommends: sign 5 first, alone, and read the others after.**
Standard: the register's own clearing order and its failure analysis. The term
`CON * RET * HIT * MCP` survives the consistency cutoff at **0.822 with the human
gate present**. Human oversight is a damper, not an immunity. A kill switch that
arrives after autonomy is theatre, and the loop is already running hourly.

Then 2, self-modification bounds, because the loop now writes to the repository
and the boundary of what it may edit should be signed before it widens by
accident. Then 1, which is already de facto in force through G-06 and should be
made explicit. Then 6, licence resolution, because it is the only thing between
this ecosystem and its first euro. Then 20, a named reviewer and a cadence,
because single-operator concentration is standing risk R-01 and it matters more
under autonomy, not less. Then 25 last, always, on the evidence of the others.

**The honest scope, and I will not overstate it.** Signing all six makes the
ecosystem self-healing against defect families it has already met. It does not
make it self-correcting against judgement it has never been tested on. Every
defect you caught personally this week, the role inversion, the fabricated
findings, the wrong entity type for HKG, SGP and TWN, was caught by a person and
not by a gate. D-112 converts what can be converted. Decision 20 is the only
mitigation for the rest.

**If you decide otherwise:** the loop keeps running, keeps repairing class A and
degrading class B, and keeps holding promotion. That is a perfectly defensible
steady state. What it does not do is promote without you, which is the one thing
that still requires you to be reachable.

**On your decision I:** write `ops/G-07_PROMOTION_POLICY_SIGNED.json` from the
predicate in G-07 §4.1, and `promotion_policy()` starts returning True on a fully
green control set. Nothing else in the loop changes.

---

## How to reply

One line each is enough. For example:

```
D-1  Neon, eu-central-1
D-2  agreed, move and rotate
D-3  read-only export
D-4  sign, and amend the namespace rule
D-5  sign
D-6  signing 5 and 2 now, holding 1, 6, 20, 25
```

Anything you refuse, refuse without a reason if you like. The reason is my job to
ask for only when it changes what I build.
