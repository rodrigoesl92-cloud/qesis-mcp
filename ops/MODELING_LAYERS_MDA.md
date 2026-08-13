# Modelling Layers: MDA crossed with the semiotic ladder

**v2.0 · 2026-08-13 · Supersedes v1.0, which is retracted on three counts recorded
in section 5. Authority: `sovereign-infra/ops/GOVERNANCE.md` G-02, which makes the
served index authoritative on any disagreement with this file.**

---

## 0. Why v1.0 was wrong to be a list

v1.0 stacked three layers and hung a mixed vocabulary on them: epistemology under
Layer 1, semantics under Layer 2, pragmatics under Layer 3. That reads well and it
does not survive use, because the terms it mixes are not siblings.

Two corrections are structural, not cosmetic.

**Semiotics is not a rung.** Syntactics, semantics and pragmatics are the three
branches *of* semiotics (Morris 1938, carried into Stamper's MEASUR). Listing
"semiotics" beside "syntax" and "semantics" lists a container next to its own
contents. The request that prompted this revision named all four; only three of
them are layers, and the fourth is the name of the ladder they sit on.

**Ontology and epistemology are not rungs either.** They are orthogonal. Ontology
asks what the model commits to existing. Epistemology asks what earns a claim the
right to be asserted. Both questions apply at *every* rung, so they are columns
across the table rather than rows inside it.

The correct object is therefore a matrix, not a stack.

---

## 1. The matrix

Rows are Stamper's semiotic ladder. Columns are the MDA abstraction and the
artefact in this repository that carries the layer. A layer with no artefact is a
layer nobody is checking.

| Rung | MDA / MOF | What it governs here | Carrier on disk |
|---|---|---|---|
| **Social world** | outside CIM | Licence split, EU AI Act obligations, the SSRN deposit, institutional acceptance | `CITATION_CONCORDANCE.md`, `ARTICLE_14_REGISTER.md`, obligations register |
| **Pragmatics** | PSM, M0 | Who may assert what, to whom, with what force. Agent routing, the Article 14 gate, the four HERALD registers | `agents/*.md`, `agent_reading_contract` in the served index |
| **Semantics** | PIM, M1 | Axis definitions, the composite expression, calibration anchors, severity bands | `composite_model`, `fsqca.calibration`, `qesis_get_methodology` |
| **Syntactics** | PIM, M2 | Form without meaning: index schema, the hash chain link rule, gate contracts | `served_contract`, `chain_spine.jsonl`, `scripts/verify_*.py` |
| **Empirics** | PSM, M0 | Signal against noise: coverage, sample size, bootstrap width, what the data cannot resolve | `uncertainty_ledger`, `effective_weights.honesty_caveat` |
| **Physical world** | instance | The substrate: catchments, landing stations, cloud regions, grid | `cloud_regions_master.csv`, Aqueduct 4.0, EMODnet, ITU SCM |

**Reading rule M-1.** A claim is only as strong as the *lowest* rung that supports
it. A statement that is syntactically valid and empirically unsupported is a
well-formed sentence about nothing. U-01 is the worked example: three states carry
a schema-valid record and no water-stress measurement, so they carry no composite.

**Reading rule M-2.** Rungs do not collapse upward. A pragmatic act cannot repair
a semantic defect. Approving a figure at the Article 14 gate does not make it
reproducible, which is why D-104 stays open despite having an owner.

---

## 2. Ontology, the first orthogonal column

What this system commits to existing, stated so it can be attacked.

| Commitment | Status | Debt |
|---|---|---|
| The **state** is the unit of exposure | Held | City-territories break it. HKG and SGP carry no catchment at source resolution, which is an ontological limit dressed as missing data (U-01, SOURCE_RESOLUTION) |
| **Seven axes** name seven distinguishable stressors | Held with a known violation | FPE and ODI correlate at 0.783 in the global coupling matrix. Two names, one construct, and FPE is the diagnostic descendant of the retired CRD (D-106) |
| **Exposure is a scalar** | Held for 32 of 35 | Contested by the coupling matrix: dominant eigenmode 0.40 means the seven axes do not reduce to one direction cleanly |
| **Trilemma corners are entities** | **REJECTED** | `agent_reading_contract.trilemma_status` = `interpretive_overlay_only`. The trilemma does not decompose the condition set. HYPER carried two of its three limbs at once and CABLE and REE mapped to no limb at all. No pathway term, necessity verdict or solution statistic may be described as a corner |
| **Territory is politically neutral in the source** | **REJECTED** | TWN carries SOURCE_POLITICAL_COVERAGE. The source's territorial schema is itself an ontological act, and recording it as missing data would have hidden that |

**Rule O-1.** An axis is an ontological commitment before it is a column. Renaming
one is a substitution of construct, not a relabel. CRD to RGD in the same 0.08
slot changed what the model says exists, which is why D-106 is RECORDED rather
than silently applied.

---

## 3. Epistemology, the second orthogonal column

What earns a claim the right to be asserted. Three warrants, never blended.

| Warrant | Test | Instrument |
|---|---|---|
| **Measured** | A source publishes the value and the ingest carries its hash | `lineage.sources`, SHA-256 per input file |
| **Inferred** | Derived from measured values by a published rule that a third party can re-run | `derivation: "Computed from published axes at build time. Never carried."` |
| **Assumed** | Neither. Carries a stated falsifier or it does not ship | Popper standing order, ANALYST mandate |

**Rule E-1.** The chain is the epistemic instrument, not a security feature. Its
function is that a claim's ancestry is recomputable by a process other than the
one that wrote it. `verify_chain.py` reimplements the link rule from its
documented definition rather than importing it from the writer, which is what
makes the attestation independent rather than self-certifying.

**Rule E-2.** Sample size is an epistemic boundary and it binds the headline. At
n=32 with 4000 bootstrap resamples, only WSE's inflation is distinguishable from
its nominal weight at 95%. The defensible claim is that **nominal weights are not
identified at this sample size**, not that ODI, RGD and REE are weightless. Any
visual that draws the point estimates without the intervals asserts more than the
data warrants.

**Rule E-3.** A withdrawn figure may be quoted only inside a block marked as a
withdrawal. See section 5, defect (d).

---

## 4. Verified system state, 2026-08-13

Every row carries the command that produced it (V-1).

| Property | Value | Command |
|---|---|---|
| Vintage | `v9.0 (2026-08-13)` | `qesis_get_integrity` |
| Index SHA-256 | `8009815e4c19132048bf285cf6622cc864e7bc090fc31627b09ce0145463647d` | `qesis_get_integrity` |
| Chain entries | **752**, 0 link breaks, sequence dense | `wc -l data/chain_spine.jsonl`, `qesis_get_integrity` |
| States | 35 total, 32 ranked, 3 EPIS | `lineage.n_countries` |
| Served contract | SATISFIED, **11** fields declared | `qesis_get_integrity.contract` |
| Composite | `0.3*WSE + 0.3*CSE + 0.17*ODI + 0.08*RGD + 0.15*REE` | `composite_model.expression` |
| Plane | `working tree`, `deployment_commit: null` | `qesis_get_integrity.provenance` |

The plane warning is G-01b working as designed and is not a defect (L-076). It
does mean the deployed surface is **unverified from this process**. Confirming
production requires `scripts/verify_production.py` or `probe_remote.py` against
the Vercel origin, and no claim about the deployed bytes is made here.

---

## 5. What v1.0 asserted and disk denies

Retracted in full. Each line was a claim about system state carried without the
command that would have produced it.

| Id | v1.0 said | Disk says | Command |
|---|---|---|---|
| **(a)** | `QESIS_THEORY = 0.30*WSE + 0.30*CSE + 0.17*ODI + 0.08*CRD + 0.15*REE` | The slot carries **RGD**, not CRD. CRD was retired at v8.3 and D-106 records the substitution as a different construct in the same slot | `composite_model.expression` |
| **(b)** | "100% of GitHub Actions pinned to full-length commit SHAs per DevSecOps 2026 standards" | **Zero are pinned.** All ten `uses:` lines carry mutable tags: `actions/checkout@v4`, `actions/setup-python@v5`, `actions/github-script@v7` | `grep -h "uses:" .github/workflows/*.yml` |
| **(c)** | "erify_chain.py (655 spine entries)" | 752 entries. The figure was stale by 97 and the script name had lost its leading character in three places | `wc -l data/chain_spine.jsonl` |
| **(d)** | Layer 2 carried the density fidelity formula as a live equation | `fidelity.method` is **Bhattacharyya** between trace-normalised stress distributions, computed for **3 of 35** states (DEU, ESP, GBR). U-03, severity medium. For diagonal rho the two forms coincide, so the formula is not wrong, but presenting it without its three-state scope overstates coverage by an order of magnitude | `fidelity`, `uncertainty_ledger` U-03 |
| **(e)** | "HERALD: UI rendering and public artifact ladder" | HERALD owns `draft`, `artifact_ladder`, `lead_scan`, `seo_page_plan`. Rendering doctrine belongs to the design system under ARCHITECT. The artifact ladder limb is correct; the UI rendering limb is a mandate drift of the L-078 family | `agents/*.md`, CLAUDE.md section 1 |

Defect (b) is the serious one. It is a supply-chain exposure recorded as already
remediated, which is worse than an unrecorded one: a reviewer reading this file
would have marked the control closed. It escalates to a `D-` decision under the
fourth rung of the RDL ladder, because a canonical document asserting a control
that no gate checks is the control sitting in the wrong layer.

---

## 6. Standing item opened by this revision

| Id | Item | Owner | Evidence |
|---|---|---|---|
| `MDA-1` | `effective_weights.finding` states REE is "quasi-necessary under fsQCA (consistency 0.916)" in the present tense. `fsqca.necessity_verdict` returns REE at 0.7033 with RoN 0.5766 and records 0.916 as the withdrawn thesis figure under D-103. One served block cites as live a number another served block withdraws. This is the CONC-1 family in a field R1.23 does not reach, since R1.23 reads `citation_concordance.resolution_bindings` and this contradiction sits in `effective_weights` | ARCHITECT to wire, SENTINEL to gate | `effective_weights.finding` against `fsqca.necessity_verdict` |

Wire the control in the same change set or it has been described, not applied
(L-054). The gate owes one fixture it must refuse and one it must accept (V-2).
