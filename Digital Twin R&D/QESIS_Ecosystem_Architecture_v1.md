# QESIS+ Ecosystem Architecture

**Document status:** Official · Version 1.0 · 2026-08-07
**Scope:** Technical structure of the QESIS+ ecosystem as measured at close of Phase 2
**Audience:** Principal, agents operating on the ecosystem, and external reviewers
**Rule of this document:** every state claim is traceable to a measurement. No line asserts a
condition that was not observed at the public surface.

---

## 1. What this system is

QESIS+ is a **substrate-sovereignty index served as an MCP tool surface**, whose distinguishing
property is not the data but the *attestation*: any third party can reproduce the served artifact
byte-for-byte from a public commit and independently verify the hash chain behind it.

That property is the product. Everything in this architecture exists to protect it.

The corollary determines every design decision below: **a system whose value is attestation may
never be permitted to assert its own health.** It must measure, and it must be able to fail.

---

## 2. Ontology — five entities

These are the primitives. Conflating any two of them produced a documented failure during Phase 2.

| Entity | Definition | Identified by |
|---|---|---|
| **ARTIFACT** | Immutable bytes. Has no version. | `sha256` only |
| **RELEASE** | An immutable binding of a label to an artifact, with timestamp and provenance. A label binds exactly once, forever. | `(label → artifact_sha)` |
| **ATTESTATION** | A chain entry containing the artifact's `sha256`. The chain is invalid if it does not cover the artifact it stands for. | chain sequence + link hash |
| **DEPLOYMENT** | `(git_commit, artifact_sha, host, observed_at)` — always measured at the public host, never read from a build record. | measurement, not record |
| **CLAIM** | Any statement of state, carrying evidence ∈ {measured, asserted}. An asserted claim is not a status. | its evidence class |

**Why this matters concretely.** In Phase 2 the label `v8.4 (2026-08-01)` came to denote two
different byte-streams because the label was treated as an identity rather than a binding. The
chain passed both, because the chain attested only its own linkage and never the artifact. Both
defects are structural consequences of a missing ontology, not coding errors.

---

## 3. Physical architecture

### 3.1 Repositories

| Repo | Visibility | Role |
|---|---|---|
| `rodrigoesl92-cloud/qesis-mcp` | public | Served surface, published index, exported chain spine, gates, CI |
| `rodrigoesl92-cloud/sovereign-infra` | private | Source of record: compliance log, fsQCA analysis, staging, citation concordance |

**Governance rule G-01:** any change to index vintage, axis definition, provenance or citation
metadata must land in *both* repositories in the same operation. A file written to a local disk
has not landed.

**Push control:** `sovereign-infra` carries a pre-push hook requiring `QESIS_HUMAN_PUSH=1`. An
agent that sets this variable to bypass the guard defeats its purpose; agents must refuse and
hand the push to the principal. This was tested in production on 2026-08-07 and held.

### 3.2 Runtime

Python is canonical. This is documented in `requirements.txt` itself, which names the two
transports:

- `server.py` — FastMCP, eight registered tools, `stdio` transport for local use
- `api/index.py` — the same FastMCP instance exposed via `streamable_http_app()` on Vercel

There is no Node application. A `dummy.ts`, `tsconfig.json` and a trimmed `package.json` exist
only to satisfy platform expectations and to support one genuine Node function
(`api/pack/download.ts`, which needs `jszip`).

**Historical note that must not be relitigated:** a Next.js build was declared in `package.json`
for a repository containing no `app/`, `pages/` or `src/` directory. No Next build ever succeeded.
Three incompatible runtimes (FastAPI, Flask, Next.js) coexisted for two days. The repository now
declares one.

### 3.3 Hosting and routing

- Vercel project `qesis`, single project, team `rodrigoesl92s-projects`
- `qesis.eu` → 308 → `www.qesis.eu`; both `www.qesis.eu` and `qesis-mcp.vercel.app` assigned to Production
- Production branch is named `fix/python-canonical-runtime`; `main` is content-identical and is
  force-synced to it by `mirror-production-ref.yml` on every push

**Three measured platform properties** (established empirically, not from documentation):

1. Vercel's filesystem router owns the `/api/*` namespace and **preempts** `vercel.json` rewrites.
   A request to `/api/health` looks for `api/health.py`, fails to find it, and 404s before any
   rewrite is evaluated. The health surface therefore lives at `/health`, `/diag`, `/mcp/_diag`.
2. Vercel forwards the **original** path to the function, not the rewritten one. A public path
   requires both a rewrite *and* a route matching the original path.
3. Every file under `api/` becomes a deployed function. A test file once shipped as a live endpoint.

**Alias assignment is separate from build success.** A deployment can be `READY`, build cleanly in
22 seconds, and never receive a production domain, because project-level checks marked as blocking
withhold the alias. Two such checks (`Typecheck`, `Microfrontends Config Present`) silently blocked
every good build for two days. Both validated surfaces this project does not have; both were removed
on 2026-08-07.

---

## 4. Control plane — six executable norms

Documentation is not a control. Each norm below is enforced by code, and each has been falsified
against a deliberate violation.

| Norm | Rule | Enforced by |
|---|---|---|
| **N1** | Index bytes change under an unchanged label → publication forbidden | `verify_release.py` against `data/RELEASES.json` |
| **N2** | A release whose `artifact_sha` is absent from the chain is invalid | `verify_release.py` against `chain_spine.jsonl` |
| **N3** | A completion claim without a measured deployment record closes nothing | `verify_production.py`, measured at `www.qesis.eu` |
| **N4** | A verifier identical to the author voids the verification | role separation (§6) |
| **N5** | A file matching a credential pattern may not be committed | GitHub secret scanning with push protection, server-side |
| **N6** | A reference to a label rather than a `sha256` is not citable | `RELEASES.json` as the label→hash register |

**On falsification.** A gate that rejects everything is broken in the safe direction, not correct.
Every proof must therefore include an acceptance case. During Phase 2 the N1/N2 falsification test
initially passed *for the wrong reason* — the mutation corrupted JSON structure and the parser
rejected the copy before the norm ever ran. The proof now mutates a hex character inside a string,
asserts the copy is well-formed first, and **fails the build if a gate rejects by crashing**.

---

## 5. Data plane

```
sovereign-infra/  qesis_audit_compliance_log   (SQLite)   ← SOURCE OF RECORD
        │  written only via ComplianceGate.record
        ▼
qesis-mcp/        data/chain_spine.jsonl       (export)   ← DERIVED, NEVER HAND-EDITED
qesis-mcp/        data/qesis_v8.json           (artifact)
qesis-mcp/        data/RELEASES.json           (label → artifact_sha, append-only)
```

**The spine is an export, not a source.** Appending a line to the published spine writes a green
tick that the next export erases, and asserts an entry that does not exist at the source. Bindings
are written through `ComplianceGate.record` in `sovereign-infra`, then exported. Before any export
overwrites the published file, the existing rows must be proven byte-identical.

**Measured state as of 2026-08-07:**

```
vintage        v8.5 (2026-08-01)
index_sha256   f2a29747d6f269844b38369ae96120e2eb2bc5ba1441ef8b1022512a32693850
chain          654 entries, 0 link breaks
tools          8
deployment     bb05144d2ca2b70bd47e761ec88a141ecfeb7bde
```

The index hash reproduces exactly from the public repository at that commit. This is the
verification any external reviewer can perform without access to any private system.

### 5.1 The v8.5 erratum

`fsqca.necessity.REE` carries `necessity_consistency 0.7033` and `necessity_coverage 0.5763`,
with an **embedded erratum block** naming `withdrawn_value 0.916` and listing every artifact that
carried it — the index through v8.4, the thesis section, the vintage lineage.

The erratum lives *inside* the data node, not only in a side document. A consumer reading
`fsqca.necessity.REE` directly sees the correction. This is the correct pattern: a withdrawal
recorded only in a concordance is invisible to the machine consumers that matter most.

**Methodological note.** At a conventional necessity threshold of 0.90, a drop from 0.916 to 0.7033
does not weaken the claim — it falsifies it. REE is not a necessary condition. The necessity
battery is consistency(N), coverage of necessity (covN), Relevance of Necessity (RoN), and the
negated-outcome counterproof. PRI is a *sufficiency* measure and belongs with solution consistency
(0.9048) and coverage (0.5807), never in a necessity validation.

`recalibration_required` reads `RESOLVED_DECLINED`. The finding was declined rather than rescued.

### 5.2 Withheld axes

Coverage below the BIG threshold produces a **withheld axis with stated cause**, not an estimate.
This applies today to HKG, SGP, TWN on existing axes, and to the entire v9.0 semiconductor
fabrication-capacity axis.

The v9.0 gate: **27 of 35 states**, from one source, on one consistent definition.
(0.75 × 35 = 26.25, so 26 states = 0.7429 and fails; the minimum integer is 27.) The ingestion
contract is executable and rejects twelve falsification cases — revenue passed off as capacity,
fab counts as a measure, market share, announced capacity, aggregate rows, aggregator publishers,
missing provenance, non-numeric or negative values — while admitting exactly one conforming record.

---

## 6. Agent architecture — separation of duties

| Role | Permission | Owns |
|---|---|---|
| **SCOUT** | read-only everywhere | diagnosis; "what is true right now" |
| **BUILDER** | writes code; forbidden `data/` and `chain_spine.jsonl` | runtime, API, CI |
| **CUSTODIAN** | sole writer of data and chain | release ceremony; N1, N2 |
| **VERIFIER** | read-only; never the author (N4) | the only role that may close a task |
| **SECRETARY** | appends to the incident and decision ledger | record-keeping |

**Core rule: BUILDER may never report "done."** Only VERIFIER may, and only with a measured
production record attached.

---

## 7. Failure modes retired during Phase 2

Each of these was observed, diagnosed and structurally closed.

| Failure | Mechanism | Closure |
|---|---|---|
| Fabricated attestation | `api/index.py` returned a hardcoded `"status": "intact"` | Handler deleted; real chain verification or HTTP 501, never a synthetic pass |
| Green build, dark service | build success read as service delivery | `/health` contract with runtime-computed hash and bound `deployment_commit` |
| Silent index mutation | label treated as identity | N1 + `RELEASES.json` |
| Chain not binding the artifact | attestation covered only its own linkage | N2; artifact hash written into the chain at source |
| Stale export mistaken for source | published spine 47 entries behind live log | bindings written via `ComplianceGate.record`, then exported with byte-identity proof |
| Credential in a public repo | `.gitignore` treated as a security control | server-side secret scanning with push protection |
| Threshold stated below its own gate | 26 states asserted against a 0.75 ratio | count derived from the ratio; proof fails if they diverge |
| Alias silently withheld | blocking project checks on absent surfaces | checks removed; probe now measures the public domain |

**The single generalisation:** every one of these was a state *asserted* rather than *measured*.
The architecture's defining property is now that it can catch itself — it declined its own
headline finding, rejected its own falsification proof for passing on the wrong grounds, and caught
an arithmetic error in its own operating brief.

---

## 8. Residual risks

1. **No continuous observation.** Until the hourly probe is installed, nothing detects a dark
   service between pushes. This is the exact condition that hid a two-day outage.
2. **Orphaned credential blobs.** `.env2` remains retrievable by direct SHA from three
   `refs/pull/*/head` refs. Only GitHub can remove pull refs. The token is rotated, so this is
   hygiene, not exposure.
3. **Single-machine dependency.** 5.8 GB RAM prevents the full stack running locally; verification
   depends on the public surface, which is correct, but local reproduction is constrained.
4. **v9.0 has no data.** The axis is complete as *contract and gate*; it has zero admitted records.

---

## 9. Next level — Phase 3, tailored

Phase 3 is not more features. It is **converting a system that can catch itself into one that
watches itself**, and then binding that capability to an external standard.

### 9.1 Immediate (this week)

**Continuous verification.** Hourly probe against `www.qesis.eu`, raising and auto-closing a
GitHub issue on state change. This is the highest-value remaining automation and the smallest.

**The boundary that must hold:** the *delivery* plane may self-heal; the *data* plane alerts and
stops. A system that automatically mutates its index or appends its chain to make a check pass has
rebuilt the `"status": "intact"` failure with better engineering. Never automate across that line.

### 9.2 Near term (this month)

**Anchor governance to ISO/IEC 42001.** The one artifact currently in `Digital Twin R&D/` is an
ISO 42001 tracker, and that instinct is correct: 42001 is the AI management system standard, and
QESIS+ already implements more of it than most certified organisations — documented risk treatment,
traceable data provenance, an immutable audit trail, and a defined human-oversight boundary.

The mapping is nearly one-to-one:

| ISO 42001 clause | Existing QESIS+ control |
|---|---|
| 6.1 Risks and opportunities | Decision log, risk register, D-numbered errata |
| 7.5 Documented information | `RELEASES.json`, citation concordance, chain spine |
| 8.3 AI system impact assessment | BIG coverage discipline, withheld axes with cause |
| 9.1 Monitoring and measurement | `verify_production.py`, hourly probe, integrity gate |
| 10.2 Nonconformity and corrective action | Incident ledger, embedded errata, RESOLVED_DECLINED |

**EU AI Act Article 12** (record-keeping) is already satisfied by the chain and is now genuinely
bound to the artifact. Article 15 (accuracy, robustness) is where the withheld-axis discipline and
the falsification proofs belong. These should be documented as a conformity argument, not left
implicit in code.

**Auto-rollback.** On two consecutive failed probes, revert the production alias to the last
certified deployment. Vercel's instant rollback makes this mechanical.

### 9.3 Medium term (this quarter)

**v9.0 source acquisition.** This is a research task, not an engineering one. The gate is built and
proven; nothing further can be coded until a dataset covering 27 states on one consistent definition
of fabrication capacity exists. Candidate definitions must be fixed *before* the search, otherwise
the search will find a source that fits whichever definition is convenient.

**Reproducibility package.** A single command that lets an external reviewer clone the public repo,
recompute the index hash, verify 654 chain entries, and probe production — with no private access.
Most of the components exist; they are not yet one entry point.

**Retire the disjoint-history debt.** Roughly twenty remote branches sit on the pre-`filter-repo`
history and can never merge into `main`. They are dead weight and a source of future confusion.

---

## 10. Reading path

Suggested, in priority order for the decisions ahead:

1. **ISO/IEC 42001:2023**, clauses 6, 8 and 9 — the management-system frame that already fits this
   architecture. Start with the tracker already in `Digital Twin R&D/`.
2. **EU AI Act, Articles 12 and 15** — record-keeping and accuracy/robustness. Article 12 is met;
   Article 15 is where the withheld-axis argument must be written down.
3. **Schneider & Wagemann, *Set-Theoretic Methods for the Social Sciences*** — chapters on
   necessity, particularly Relevance of Necessity and trivial necessity. This is the methodological
   ground under the REE withdrawal.
4. **Ragin, *Redesigning Social Inquiry*** — calibration and consistency thresholds; the source of
   the 0.90 necessity convention that decided the REE ruling.
5. **Google SRE Book**, chapters on service level objectives and on postmortem culture — the
   discipline of measuring the served surface rather than the build, which was this phase's most
   expensive lesson.

---

## 11. Change control for this document

This document is versioned with the ecosystem. Any change to §5 (data plane) or §4 (norms) requires
a paired update in both repositories under G-01. State claims in §5 must be re-measured, not copied
forward, at each revision.

*Prepared as an architecture record at the close of Phase 2. Every measurement herein was taken at
the public surface on 2026-08-07.*
