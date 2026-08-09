# Milestone record, v8.6

**v2.0 · 2026-08-09 · Repository `qesis-mcp` · Commit `39fa510`.**
**Supersedes v1.0 of the same date, which recorded two defects that do not exist.
Retracted as L-076 and L-077.**

Recorded by COUNSEL under V-1. This is not a promotion. Under G-06 promotion to
production is a human act and no amendment reaches it.

---

## 1. Measured state

### 1.1 Served bytes against committed bytes

```
$ sha256sum data/qesis_v8.json
d78f39f7964eb6f49a7be97311b772ec552c46c0b6e29050eb9b0c52ff874325
$ git cat-file -p 39fa510:data/qesis_v8.json | sha256sum
d78f39f7964eb6f49a7be97311b772ec552c46c0b6e29050eb9b0c52ff874325
```

Identical.

**Correction.** v1.0 of this document read
`provenance.plane: "working tree"` with `deployment_commit: null` as a labelling
defect. It is not. G-01b specifies exactly this: two planes, the deployment plane
carrying the promoted commit and the local stdio plane carrying the working tree
label and its warning, and the rule is that a reader is always told which of the
two they are reading. `provenance` is named in `served_contract`, so G-01a fails
the build if it ever stops being served. The block is a control, not a bug.
Registered as L-076.

### 1.2 Chain

`status VERIFIED`, 655 entries, 0 link breaks, sequence dense, head
`3fd13431c16455ce`, genesis `c53c65edf1f0dd6e`, attestation present and agreeing,
verified 2026-08-09T03:46:06Z from committed artefacts only.

**Correction.** v1.0 said the ecosystem verifies agreement rather than integrity,
because `production-integrity-probe.yml` reads `chain.status` off the endpoint.
The observation about that workflow is right and the conclusion was false.
`qesis-integrity.yml` runs `scripts/verify_chain.py`, which recomputes every link
from the committed spine and fails if the attestation does not follow, alongside
`verify_index.py`, `verify_vintage_pairing.py`, `verify_served_contract.py`,
`verify_axis_sfc.py`, `prove_axis_sfc_contract.py`, `test_routes.py`,
`test_http.py`, `coupling.py`, `build_eval --check`, `build_landing --check` and
the mutation self test `test_gate.py`. The two workflows compose: the gate proves
the committed artefact is correct by recomputation, the probe proves the served
bytes are that artefact. Registered as L-077.

### 1.3 Pairing

```
$ python scripts/verify_vintage_pairing.py
served vintage: v8.6 (2026-08-09)
register: 6 rows from vintage_lineage.json
  qesis-mcp 9c76d0bf... · sovereign-infra None · exemption: Provenance relabel
  confined to qesis-mcp.
PAIRING CHECK PASSED: the served vintage is recorded.
```

v1.0 filed the sovereign-infra lag as `PAIR-1`. It is a declared
`single_repo_reason` exemption under G-01, which the governance requires to be
stated rather than assumed by silence, and it is stated. No finding.

### 1.4 Self check

35 states, 32 ranked, 3 withheld under BIG. `composites_reproducing_from_axes:
true`, `drift: none`, contract SATISFIED with 11 declared fields.

---

## 2. What v8.6 actually delivers

Not the pipeline. The D-103 fsQCA re-run, served with its own disconfirmation
attached.

- Ten sufficient configurations. Complex solution consistency 0.9048, coverage
  0.5807.
- Per path PRI published beside raw consistency, with two paths flagged
  `DISQUALIFYING: PRI below 0.50` at 0.3032 and 0.4587. A wide consistency to PRI
  gap means the path is a subset of the outcome and of its negation at once.
  Publishing the flag is the finding.
- The necessity gate publishes four measures per condition and per negation, and
  re runs against the negated outcome. Verdict: no condition or negation is
  publishable as necessary.
- Thesis section 4.5 REE 0.916 is withdrawn on triviality, not on threshold.
  Primary anchors return 0.7033 with RoN 0.5766, and REE scores 0.7268 against the
  negated outcome, higher than against the outcome. Under sensitivity anchors
  consistency rises to 0.9672 while RoN falls to 0.195, because the condition
  becomes near constant. The rising number is the artefact. Grounding the
  withdrawal on triviality rather than on the 0.90 bar is what makes it
  irreversible by citing the flattering regime.
- No intermediate solution, because no directional expectations are declared, and
  defaulting them would publish a theoretical claim as a computed result.
- The v6.6 impossibility, intermediate 0.920 against parsimonious 0.76, is now
  caught by a standing assertion. Parsimonious 0.7032 is at or above complex
  0.5807 and it holds.
- `anticircularity` renamed `conceptual_independence_test` and marked
  `AD HOC, not to be cited as an established procedure`, with the standing
  limitation stated plainly instead of resolved by a test name.

A pipeline that turns green is maintenance. An analysis that publishes the
measure which kills its own headline result is the thing this ecosystem exists to
produce, and v8.6 is that.

---

## 3. Open, and none of it closable by an agent

`CONC-1`, `DOC-1`, `AUDIT-1`, `LOCK-1`, `ROB-1`, `PUB-1`, `D-104`, `D-105`. Full
table with owners and evidence in `CLAUDE.md` section 7. Path to v9.0 in
`ops/V9.0_PATH_AND_ROUTING.md`.

The single highest severity item is `D-104`: two thesis headline numbers with no
published method, appearing in three chapters, carrying rhetorical weight, and
uncheckable by a reader.

---

## 4. Lessons registered this cycle

Canonical: `sovereign-infra/ops/LESSONS_LEDGER.md`.

| Id | Rule |
|---|---|
| L-069 | An attestation is read back off disk after writing, never computed from the object that produced it |
| L-070 | A script that has never executed has never been tested at any level |
| L-071 | **Retracted by L-076** |
| L-072 | **Retracted by L-077** |
| L-073 | The lesson ledger is single instance. A duplicate id is a build failure |
| L-074 | A status document names the vintage it describes, or is deleted |
| L-075 | Multi agent runs validate the pipeline they write into and name the surfaces each touched |
| L-076 | Before recording a served field as a defect, find the clause that specifies it |
| L-077 | A claim that a property is unverified is only sound after enumerating the whole control set |
| L-078 | A governance lock is written from the governance documents, and a document redefining roles is written from the role definitions |
| L-079 | Run the doctrine gate over prose before claiming the work is delivered |

L-076 through L-079 are the audit of this audit. Three fabricated findings and a
role inversion, produced by reading the served payload and the ledger while
leaving `GOVERNANCE.md`, `ARTICLE_14_REGISTER.md` and twelve agent definitions
unopened. Inventing a finding to appear rigorous is the same class of failure as
suppressing one.
