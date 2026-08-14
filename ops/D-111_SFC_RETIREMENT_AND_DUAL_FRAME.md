# D-111: SFC retired, semiconductor dependency adopted, and the sample split into two frames

**Raised:** 2026-08-14 · **Status:** DECIDED, BUILD PENDING PROMOTION
**Decided by:** R. Batista Silva (operator, sole Article 14 approver)
**Drafted by:** ARCHITECT · **Licence limb:** COUNSEL · **Gate:** SENTINEL
**Supersedes:** `data/axes/v9_sfc_scaffold.json` status WITHHELD, ledger entry U-06

---

## 1. The operator decision, in the operator's terms

> "Physical capacity cannot be robustly measured without violating unit rules
> (ETO refusal). Dependency maps directly to sovereignty exposure. SFC retired."
> R. Batista Silva, 2026-08-14

---

## 2. Why SFC could not ship, evidenced

Three sources were retrieved and read against the ingestion contract. This closes
the standing caveat that no lead had been opened by this repository.

| Source | Unit | Verdict |
|---|---|---|
| OECD, Geographical Distribution of Wafer Fabrication Capacity | WSPM 8-inch equivalent, which **is** the canonical `wspm_200mm_equivalent` | **REFUSED on coverage.** 4 of 35 sample states carry a figure. Ratio 0.1143 against the required 0.75 |
| OECD, Vulnerabilities in the Semiconductor Supply Chain | none | **REFUSED.** Two occurrences of "capacity" and no WSPM figures. A risk paper, not a dataset |
| CSET / ETO Advanced Semiconductor Supply Chain Dataset | `market_share_pct` | **REFUSED TWICE.** The unit is in `refused_units`. And its own documentation lists "Assessing the physical location of chip production" under uses **not** recommended, because country data is keyed to **headquarters of the ultimate parent** |

SEMI World Fab Forecast is the only source that clears the contract. It is paid,
and the student concession no longer applies. Procurement was refused by the
operator. There is no free source that measures fabrication located in the state.

**The closed-world escape was tested and refused by the source itself.** If the
underlying fab database were a census, a state absent from it would carry a
measured zero and the axis would unlock at full coverage. The OECD paper states
"incomplete geographic coverage", "data coverage is uneven across economies" and
"neither of the datasets are fully complete, correct and accurate". Absence from
an admittedly uneven dataset is not a measured zero, and treating it as one would
convert a coverage bias into a stress score of 100 for every unlisted state. That
is imputation wearing a measurement's clothes, refused by D-007.

**The gate worked.** A source in the correct unit covering 4 of 35 was refused on
coverage rather than admitted on unit.

---

## 3. The ontological shift, stated as a shift

This is not a substitution of source. It is a change in what the model commits to
existing, and it is recorded as such per Rule O-1.

| | Retired | Adopted |
|---|---|---|
| Construct | installed fabrication capacity **located in** the state | **net import dependency** on semiconductors |
| Ontological commitment | wafers can physically be made here | this state cannot obtain chips without someone else |
| Unit | `wspm_200mm_equivalent` | normalised 0 to 100 from HS 8541 and 8542 trade balance |
| Source | SEMI World Fab Forecast (paid) | UN Comtrade (free, official) |
| Coverage | 4 of 35 | expected 35 of 35, to be measured not assumed |

**Why the shift is defensible rather than a retreat.** The axis existed to measure
substrate dependency. Fabrication capacity was a *proxy* for it: a state with fabs
is less dependent. Import dependency measures the dependency directly. The proxy
was unobtainable and the target is obtainable, so the model moves closer to what
it always meant.

**What is lost, stated plainly.** Import dependency cannot distinguish a state
that imports because it chooses to from one that imports because it cannot
fabricate. Fabrication capacity could. Any state hosting foreign-owned fabs that
export output will read as low dependency for a reason the axis does not see.
That limitation ships with the axis in the uncertainty ledger, not in a footnote.

---

## 4. COUNSEL: licence posture on UN Comtrade

**Finding, and it is blocking as stated.** UN Comtrade data is copyright of the
United Nations and is made available **for internal use only, and may not be
re-disseminated in any form without written permission of the United Nations
Statistics Division**. Free API access is capped at 100,000 records per query and
500 calls per day.

QESIS+ publishes a public index under CC-BY-NC. Serving Comtrade values in that
index is redistribution, and the licence forbids it without written permission.

**Mitigation, with in-house precedent.** The licence block on this repository
already reads: *"TeleGeography-derived cable material is published only as derived
aggregates, never raw."* The same treatment resolves Comtrade:

1. Raw Comtrade records are **never** written to `data/qesis_v9_1.json`, never
   served by any MCP tool, and never included in a data pack.
2. What is served is a **derived aggregate**: one normalised 0 to 100 score per
   state, from which the underlying trade values cannot be reconstructed.
3. The ingest keeps raw records outside the repository, under `.gitignore`, and
   records only the query parameters, the retrieval date and a SHA-256 of the
   payload so the derivation is reproducible without republishing the input.
4. Attribution appears wherever the axis appears: "Derived from UN Comtrade,
   United Nations Statistics Division."

**New risk gates introduced by the shift: three.**

| Id | Gate | Owner |
|---|---|---|
| `OBL-1` | No raw Comtrade record may reach any served surface or any repository. Enforced by a scan in the pre-commit gate, not by prose | SENTINEL |
| `OBL-2` | The 500 calls per day free-tier limit binds the ingest. A refresh loop without rate limiting breaches the terms of service, which is a licence matter and not merely an engineering one | ARCHITECT |
| `OBL-3` | Written permission from UNSD is required **only if** derived aggregates are later judged to be re-dissemination. Seek confirmation before any institutional-tier licence is sold that includes this axis | COUNSEL, then HUMAN |

**Recorded to the obligations register 2026-08-14. COUNSEL is not a lawyer.**
`OBL-3` in particular should be put to a qualified professional before the axis
enters a paid tier. The draft above exists so that conversation is short.

---

## 5. The dual frame, and why it is the stronger design

The operator refused the removal of HKG, SGP and TWN, and was right to. They are
essential to the rare-earth and production-supply-chain ontology, which is
precisely where semiconductor dependency lives.

The sample is therefore not reduced. It is **split into two frames that are
published side by side and test each other.**

| Frame | Members | Comparable on | Not comparable on |
|---|---|---|---|
| `states` | 32 | the full substrate composite, all seven axes | nothing withheld |
| `regions` | HKG, SGP, TWN | REE, CSE, ODI, FPE, ESE, RGD, and the new dependency axis | WSE, which has no resolvable catchment at source (HKG, SGP) or no separate territorial entry (TWN) |

**Why this is not a workaround.** The three were never failing a measurement.
Two are city-territories whose catchment does not resolve at Aqueduct's grid
resolution, and one is absent from the source's territorial schema for political
reasons. Those are properties of the *entity type*, not of the data collection.
A frame is the correct place to record a property of the entity type.

**The stress test this unlocks.** The two frames share five axes and one
calibration. Any finding that holds in `states` and inverts in `regions` is a
finding about the frame rather than about the world, and the ecosystem can now
detect that about itself. Taiwan carrying the highest semiconductor
concentration on earth while sitting outside the substrate composite is exactly
the case that should be visible rather than hidden.

**Constraint that binds every use:** the two frames are never pooled into one
ranking. A composite computed over seven axes and one computed over six are
different measures, and a table that sorts them together is a category error.
Gate this, do not request it.

---

## 6. Vintage and propagation

`v9.1 (2026-08-14)`, superseding `v9.0 (2026-08-13)`.

**G-01, cross-repo atomicity.** Paired change set. `qesis-mcp` carries the served
index, the scaffold, the build script and the surfaces. `sovereign-infra` carries
the lineage register, the lessons ledger and the obligations register. Neither
lands alone and `single_repo_reason` stays null.

**G-01a, data last.** Commit, push, deploy, restart, then confirm the contract
against the served payload. The index is not published ahead of the code that
computes it.

**G-01b, plane identification.** `data/qesis_v9_1.json` is written under its own
name so the two vintages are distinguishable on disk rather than by inspection of
a field. `ops/VINTAGE_LINEAGE.md` and its JSON mirror carry the pair of commit
hashes.

**Surfaces that must move in the same change set:** `data/qesis_v9_1.json`,
`STIR_Governance_Dashboard.html`, `index.html`, `overview.html`, `method.html`,
`console.html`, `served_contract`, `data/domains.json` if the axis adds a source
host, and the eval set.

---

## 7. Open, and honestly open

| Id | Item | Owner |
|---|---|---|
| `D-111-a` | The Comtrade ingest is specified here and **not yet built**. No trade record has been retrieved. Coverage of 35 of 35 is expected, not measured, and it is stated as expected | SCOUT, then ANALYST |
| `D-111-b` | The axis has no calibration anchors until real values exist. Anchors are part of the result, never a setting | ANALYST |
| `D-111-c` | Weight in the composite is undecided. Adding an axis changes every composite in the index, so it does not enter the weighted sum until D-111-a and D-111-b close | HUMAN |
| `OBL-3` | UNSD confirmation on derived aggregates before any paid tier includes this axis | COUNSEL, then HUMAN |

**Rule V-1 applies to this document.** Section 2 carries commands and values.
Section 7 carries none, because nothing in it has been run.
