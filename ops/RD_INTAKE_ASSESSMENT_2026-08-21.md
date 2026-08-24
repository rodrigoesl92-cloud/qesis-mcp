# R&D Pool Intake Assessment, 2026-08-21

**COUNSEL with ARCHITECT, under SH-9 and Rule DT-1. Every claim carries the file or command that produced it.**

Scope: the delta in `qesis-mcp/Digital Twin R&D/` against the inventory recorded at
`qesis-mcp/CLAUDE.md` section 4 (2026-08-09), adjudicated against the served index,
the ingestion contracts and the acquisition register.

---

## 0. Verdict in one line

Twelve new documents. **Zero admissible data records for any axis.** One genuine data
asset (WEF ETI 2026, usable as an external benchmark and not as an input), three
citable evidence sources for claims already made, one usable measurement instrument,
four vendor or marketing pieces, and one duplicate. The largest return in the batch is
defensive rather than additive: ETI 2026 added two indicators that land on ground QESIS+
claims, and knowing that before the Telecommunications Policy submission is worth more
than any record the batch could have supplied.

---

## 1. The delta, measured

`device_list_dir` on `C:\Users\Lenovo\qesis-mcp\Digital Twin R&D` returned 30 files.
Against the CLAUDE.md section 4 inventory of 2026-08-09, seventeen are new. They arrived
in two batches, by mtime:

| Batch | Count | Files |
|---|---|---|
| 2026-08-13 | 3 | OECD wafer fabrication capacity; OECD semiconductor supply chain vulnerabilities; Synergistic AI Agents with Knowledge Graphs |
| 2026-08-14 | 2 | `ISO42001_FinServ_Tracker.xlsx` and `QESIS_Ecosystem_Architecture_v1.md`, both re-touched, both already inventoried |
| 2026-08-19 15:02 to 15:09 UTC | 12 | the batch this assessment is about |

The twelve:

1. `WEF_Energy_Transition_Index_2026`
2. `WEF_Deepening_Divides_2026`
3. `WEF_From_Minerals_to_Megawatts_2025`
4. `WEF_Top_10_Emerging_Technologies_Report_2026`
5. `WEF_Chief_Economists_Outlook_May_2026`
6. `Mind The Agentic Action Gap` (Forrester reprint)
7. `ibm-ai-governance-ebook`
8. `vector-search-meets-distributed-sql` (Intellyx, sponsored)
9. `Benchmarking RabbitMQ vs Kafka vs Pulsar Performance`
10. `Connected Learning Ecosystem Infographic` (Udemy Business)
11. `STF-DLA-ENG` (Stanford Online / Global Alumni course brochure)
12. `WP-Developers_Guide_to_RAG-1` (English edition of the Spanish guide already inventoried)

Three files in the folder are hardlinked and refuse staging (`nlink > 1`): the two OECD
semiconductor papers and the Knowledge Graph paper. They were read on the device with
`pdftotext` instead. This is a mount property, not a defect, and it is recorded so the
next session does not treat it as one.

---

## 2. Triage ledger

Verdict vocabulary: **ADMIT** (may enter an artefact), **FRAME** (may inform prose,
never a measurement), **REFUSE** (does not enter the ecosystem), **CLOSED** (evidence
for a question already adjudicated).

| Document | Verdict | Ground |
|---|---|---|
| WEF ETI 2026 | **ADMIT, benchmark only** | 33 of 35 sample states. External to the index. Never an input: composite on composite |
| WEF Minerals to Megawatts 2025 | **ADMIT, citation** | Mechanism evidence for REE after the necessity claim was declined |
| WEF Deepening Divides 2026 | **ADMIT, citation** | External four-scenario spine for the time-evolution model |
| WEF Top 10 Emerging Technologies 2026 | **ADMIT, citation** | Three of ten bear on WSE, ESE and the attestation chain |
| Forrester Agentic Action Gap | **ADMIT, instrument** | Three measurable dimensions, directly instrumentable in `selfheal` |
| WEF Chief Economists Outlook May 2026 | **FRAME** | Sentiment survey. Converges with ETI on chokepoint framing |
| IBM AI governance ebook | **FRAME** | watsonx.governance marketing. Useful as commercial framing, never as a standard |
| Intellyx vector search white paper | **FRAME** | Sponsored vendor paper on CockroachDB. One transferable fact, no evidence |
| Kafka / RabbitMQ / Pulsar benchmark | **REFUSE** | A 2020 Confluent blog post, arrived by marketing campaign, benchmarking Confluent's own system |
| Udemy Connected Learning infographic | **REFUSE** | Marketing collateral. One line of market signal, no research content |
| Stanford Online AI leadership brochure | **REFUSE** | Course prospectus. No ecosystem relevance |
| RAG developer guide, English edition | **REFUSE, duplicate** | Spanish edition already inventoried and already applied at R1.26 |
| OECD wafer fabrication capacity | **CLOSED** | Already audited and refused 2026-08-14. See section 3 |
| OECD semiconductor vulnerabilities | **CLOSED** | Already recorded as refused, not a capacity dataset |

---

## 3. The semiconductor papers are closed evidence, not new input

`data/axes/v9_1_sdi_scaffold.json` records that SFC was **RETIRED** under D-111 on
2026-08-14 and replaced by SDI, Semiconductor Dependency Index, on UN Comtrade HS 8541
and 8542, status SPECIFIED NOT INGESTED. The OECD wafer paper appears in that file under
`sources_refused` with coverage 4 of 35, ratio 0.1143, verdict REFUSED ON COVERAGE.

Reading the paper independently corroborates the refusal rather than reopening it:

- Figure 2 note: "The figure shows data for the **nine largest economies** in terms of
  in-production capacity." Nine named economies against a 27 of 35 gate.
- Figure 3 note: "Rest of World (RoW) aggregates all economies in the dataset not
  otherwise listed in the chart." That is the `aggregate_rows_refused` clause exactly.
- Section 2: "The level of aggregation of economies presented in the paper is based on
  relevant focus on the most concentrated region. Further disaggregation is only
  possible in the case that the data agreements [permit]." The obstacle is contractual,
  so it will not resolve by looking harder.
- Annex B names "incomplete geographic coverage" as a stated data limitation.

**Nothing here is a reason to reopen SFC.** The standing decision is the procurement
question on the SEMI World Fab Forecast, refused by the operator on 2026-08-14, and this
batch does not change its terms. Do not re-litigate it.

What the paper is genuinely worth: it is CC BY 4.0, it is an OECD Digital Policy
Committee declassified paper (DSTI/DPC/CIIE(2025)1/FINAL, December 2025, No. 188), and
it fixes the canonical unit in a citable authority. WSPM in 8 inch equivalents is now
the definition QESIS+ can point at when a reviewer asks why the axis was retired rather
than estimated. It also supplies a top-five-company capacity share by economy, which is
structurally the same concentration logic as ODI and can be cited as prior art for the
construct.

---

## 4. WEF ETI 2026: the one real data asset, and its two constraints

**Authenticity confirmed.** Sixteenth edition, June 2026, with Accenture, 120 countries,
44 indicators. Ranking verified against the publisher: Sweden 1, Finland 2, Denmark 3,
Estonia 4, Norway 5. The PDF matches.

**Coverage against the QESIS+ 35-state sample: 33 of 35, ratio 0.9429.** The two absent
states are HKG and TWN, which are exactly two of the three states already withheld under
BIG. SGP is present at rank 42. This clears the 0.75 threshold by a wide margin, and it
is the only source in the batch that does.

**Use it as an external convergent-validity benchmark, not as an input.** ETI is itself a
weighted composite over 44 indicators. Feeding it into the QESIS+ composite would be a
composite on a composite and would violate the derivation doctrine that R1.24 exists to
enforce. The legitimate use is a correlation between ESE (or the composite) and the ETI
system-performance sub-index across the 33 overlapping states, published as a robustness
statement with its coefficient. That is a defensible addition to the methods section and
it costs one script.

**Constraint one, and it is the important one. ETI 2026 added two indicators:
"AI readiness" and "clean technology minerals supply chain exposure".** Both land on
ground QESIS+ claims. The second is functionally an REE stress construct. The ODI
methodology block already carries a `prior_art` clause requiring novelty claims to be
argued against published index constructions; ETI 2026 raises that bar and the paper for
Telecommunications Policy must answer it explicitly rather than by omission. The honest
narrowing survives: ETI measures readiness and exposure at the national energy-system
level, QESIS+ measures facility-level substrate concentration. That distinction has to be
written, not assumed.

**Constraint two, legal.** Every WEF report in this batch carries: "All rights reserved.
No part of this publication may be reproduced or transmitted in any form or by any means,
including photocopying and recording, **or by any information storage and retrieval
system**." That is a genuine redistribution restriction in the same class as SA-004
UN Comtrade, not the open posture of SA-001 to SA-003. Two consequences:

1. The ranking table may not be republished. A correlation coefficient computed from it
   is a derived aggregate and may.
2. A vector index built over the `Digital Twin R&D/` pool is literally an information
   storage and retrieval system. If the RAG layer is ever pointed at this folder, the
   WEF files must be excluded by rule, not by intention.

---

## 5. Six domains

### Architecture

Two refusals and one small transferable fact.

The Kafka benchmark is dated **21 August 2020** and the page footer in every extracted
page carries `https://www.confluent.io/blog/kafka-fastest-messaging-system/?utm_medium=
marketingemail&utm_campaign=tm.campaigns_cd.general-welcome`. It is therefore not a
report at all: it is a Confluent blog post, delivered through a Confluent marketing
campaign, in which the vendor of one of the three systems benchmarks that system against
the other two and titles the page "kafka-fastest-messaging-system". That is not evidence
under the D-015 and L-007 sourcing discipline. It is also six years stale on a fast-moving
stack. Beyond the
sourcing objection, the architecture does not want a broker: the runtime is FastMCP on
Vercel with GitHub Actions as the scheduler under Rule SH-7, and the ecosystem's
defining property is byte-reproducibility of an artefact from a public commit. A stateful
broker adds a component that cannot be reproduced from a commit. **REFUSE.**

The Intellyx vector paper is sponsored vendor content about CockroachDB's C-SPANN index.
One fact survives extraction and transfers: CockroachDB added pgvector-compatible vector
types in 2024. The generalisable form is that vector search now lives inside ordinary
Postgres, which means that if the graph layer ever needs embeddings, the move is pgvector
on the database already connected, not a new engine. That is one sentence of framing, not
a design input. **FRAME.**

The genuine architecture question this batch raises is neither of those. It is
`ops/EDA_VS_BATCH_BENCHMARK.json` plus Rule SH-7: the scheduler is settled and the
benchmark file is the record of that. Nothing in the batch disturbs it.

### Governance

The IBM ebook is watsonx.governance marketing. Its value is not the product and not the
standard. It is the commercial framing, "maximize AI ROI through smarter governance",
which is precisely the argument the institutional licence has to make to a buyer's
compliance function. HERALD may use the framing. It may not be cited as a governance
authority: the authority is ISO/IEC 42001 and the EU AI Act, and the mapping already
exists at `QESIS_Ecosystem_Architecture_v1.md` section 9.2.

The real governance work this batch creates is registry hygiene, and it is an ARCHITECT
task rather than a human one: two new entries in `ops/SOURCE_ACQUISITION_REGISTER.md`
under the SA-3 append-only rule.

- **SA-005, OECD Semiconductor Production Database papers.** Channel
  `PUBLIC_PORTAL_DOWNLOAD`, licence CC BY 4.0, no restriction, attribution required.
- **SA-006, World Economic Forum reports.** Channel `PUBLIC_PORTAL_DOWNLOAD`, all rights
  reserved, **derived aggregates only**, storage and retrieval expressly named in the
  reservation. Posture identical to SA-004.

SA-006 matters because the register's own closing argument is that it discriminates.
It currently reads three open entries against one restricted. Adding a second restricted
entry with a different reason strengthens that argument rather than weakening it.

### fsQCA

**The batch does not close KG-4, and KG-4 is the only fsQCA blocker that matters.**

`ops/D-110_KG_FSQCA_ASSESSMENT.md` states the condition plainly: the outcome must be
calibrated from a source outside the index, observed outage or incident history is the
candidate, and if it is unsourced by the next vintage D-110 is recorded as declined
rather than pending. Nothing in these twelve documents supplies event-level outage or
incident history for 32 states.

The tempting substitution must be refused explicitly, because it will occur to someone.
ETI's system-performance sub-index is external to QESIS+ and covers 33 of 35 states, so it
looks like an outcome. It is not one. It is another weighted composite, and swapping the
declared circularity for an outcome that is itself an opinion-weighted index trades a
known problem for an unknown one. Worse, ESE already consumes World Bank SAIDI, which is
outage duration, so any energy-security outcome shares inputs with the conditions.
**Use ETI as a robustness check beside the result. Never as the outcome.**

One thing the batch does give fsQCA: the ETI security dimension decomposes into three
named indicators, diversification of import partners, diversity of the energy mix, and
net energy imports. Those are the closest published analogue to the QESIS+ conditions and
they are useful for defending the condition set against a reviewer who asks why these
six and not others.

### Methodology

The strongest methodological input in the batch is `WEF_Deepening_Divides_2026`.

The time-evolution BAU model runs t0 to 2030 to 2050 to 2080 and currently carries no
external scenario anchor. Deepening Divides supplies a published, sourced, four-scenario
fragmentation model with named mechanisms (East-West goods trade, sensitive technology
trade, intra-West measures, retaliation rates, extraterritorial enforcement) and costed
outcomes: roughly 300 billion USD for current fragmentation, above 6 trillion USD in the
severed-blocs case. The methodology gain is that the QESIS+ scenarios stop being author
choices and become a mapping onto a citable external scenario set, with the mapping
published. That is the difference between a projection an examiner accepts and one he
asks you to justify.

Second input, and it is a falsification input rather than a supporting one.
`WEF_Top_10_Emerging_Technologies_2026` lists passive radiative cooling materials at
number 3. WSE's long-horizon projection rests on an implicit assumption that data centre
cooling stays water-intensive. A named, tracked substitution pathway is exactly the sort
of thing that should appear in the uncertainty ledger against the 2050 and 2080 values.
Under the Popper standing order, this is the falsifier for the WSE trajectory and it
should be written as one.

### Data indexes

Net new admissible records to any axis: **zero**. That is the gate working, not a bad
batch, but it must be said plainly rather than softened.

What did change is the comparative landscape. ETI 2026 is now a 120-country, 44-indicator
composite that includes an AI readiness indicator and a minerals supply chain exposure
indicator. QESIS+ measures 35 states on seven axes with five in the composite. On breadth
QESIS+ loses and will keep losing. The defensible ground is the one the ecosystem already
occupies and no rival occupies: attestation. ETI publishes scores. It does not publish a
hash chain that lets a third party reproduce the artefact byte for byte from a public
commit. That is the differentiator to lead with, and this batch is the evidence that
leading with coverage or breadth would be a losing argument.

`WEF_From_Minerals_to_Megawatts_2025` is the citation the REE axis needs after the
necessity claim was declined. It states that by 2035 data centres are projected to
account for about 6 percent of global gallium use and some 2.4 percent of germanium
demand, and it decomposes the facility into compute, networking, cooling, electrical and
backup layers with the material dependency of each. **Report both directions.** The
mechanism is real and now citable, which supports REE remaining as a sufficiency-side
condition. The shares are small, which cuts against any claim that REE is central. A
reviewer will find the second reading whether or not the paper states it, so the paper
states it.

### MCP

Nothing in the batch changes the MCP surface, which stands at eight registered tools on
FastMCP with two transports.

Two observations worth one line each. First, the Udemy infographic is marketing, but it
is market evidence: Udemy, Glean, Workday and Cornerstone are shipping MCP connections
today. "Index served as an MCP tool surface" is therefore a distribution channel with
enterprise adoption behind it, not a bet. That belongs in the HERALD funnel argument,
sourced honestly as vendor collateral.

Second, and this is the one that binds: the WEF reservation names information storage and
retrieval systems. Any future MCP resource or RAG index over `Digital Twin R&D/` must
exclude the WEF files by an executable rule. A rule held only in prose has been described,
not applied, per L-054. If that layer is ever built, the exclusion ships as a fixture in
the same change set.

---

## 6. The one instrument worth wiring

The Forrester reprint defines an agentic action gap over three measurable dimensions:

- **Friction.** The number of distinct unintegrated systems or humans needed to execute
  an agent-generated insight.
- **Time to action.** The interval between insight and value delivery.
- **Adoption and compliance.** The percentage of agent recommendations accepted and
  executed without modification.

The ecosystem already emits most of this and does not aggregate it.
`selfheal --dry-run` on 2026-08-19 returned repaired 0 and escalations 0, which is the
adoption and compliance numerator and denominator in his terms. `ops/DORA_ROI_BASELINE.md`
already exists for delivery metrics. The gap between them is the action gap.

**Recommendation: add three fields to the self-heal step summary rather than write a new
document.** `friction_points` (count of class C refusals, which are by definition the
cases needing a human), `time_to_action` (interval from detection to repair for class A
and B), `unmodified_execution_rate` (repaired divided by detected). This is the cheapest
ROI instrumentation available and it is measured rather than asserted, which is the only
kind this ecosystem accepts.

Note the licence: the file is a Forrester reprint carrying a reprint identifier. The
framework may be applied. The report may not be redistributed.

---

## 7. Escalations, under SH-9

**One item, and it is a scope decision rather than a defect.**

1. **What it is.** The `Digital Twin R&D/` pool now contains five World Economic Forum
   publications whose copyright reservation expressly names information storage and
   retrieval systems. There is a standing interest in an agentic RAG layer over this pool.
2. **Why it is yours.** It is a scope and licence-posture commitment on a public,
   commercially licensed instrument, which is a COUNSEL preparation and a human signature.
3. **The options.** (a) Exclude WEF files from any retrieval index by an executable rule,
   keeping them as human-read framing only. (b) Seek written WEF permission, which is slow
   and unlikely to be granted for an index sold commercially. (c) Index them and accept
   the exposure.
4. **COUNSEL recommends (a).** Ground: it is the same posture already ratified for
   SA-004 UN Comtrade under D-111, so it introduces no new doctrine, and the register's
   own argument is that it discriminates by source rather than applying one rule to all.
5. **What changes if you decide otherwise.** Option (c) puts a redistribution exposure
   inside the artefact whose entire product is attestation, which is the one place the
   ecosystem cannot afford an unverifiable claim. Option (b) costs weeks and blocks
   nothing that (a) does not unblock immediately.
6. **On your decision.** COUNSEL drafts SA-005 and SA-006 for the acquisition register and
   ARCHITECT wires the exclusion fixture in the same change set as the first retrieval
   index, whenever that is built.

---

## 8. Ranked next actions

1. **Write the ETI 2026 prior-art paragraph into the Telecommunications Policy draft.**
   Highest value, lowest cost, and it is time-sensitive because it is a submission risk
   rather than an engineering one. The ODI `prior_art` clause already requires it and ETI
   2026 makes the requirement concrete.
2. **Run the ESE against ETI system-performance correlation over the 33 overlapping
   states.** One script, one coefficient, one robustness sentence. Publish the coefficient,
   never the table.
3. **Append SA-005 and SA-006 to the acquisition register.** Registry hygiene, ARCHITECT,
   no human decision required.
4. **Add the three action-gap fields to the self-heal summary.** Cheap, measured, and it
   converts an ROI claim from assertion to instrument.
5. **Record the passive radiative cooling substitution pathway in the uncertainty ledger
   against WSE 2050 and 2080.** It is a declared falsifier and the Popper standing order
   requires it to be stated.

Not on this list, deliberately: reopening SFC, adopting a message broker, adding a vector
database, and treating ETI as an index input. Each was considered and each is refused
above with its ground.

---

## 8bis. APPLIED, 2026-08-21. Operator approved all points.

All five ranked actions executed and the escalation decided as option (a). Thirteen
files written into the `qesis-mcp` working tree, six new and six modified plus the
commit message. Landing is three git commands in `ops/LAND_2026-08-21.md`.

**Verified on the operator's own machine, not only in the analysis container:**

```
6/6 scripts parse clean
eti_extract.py     120 of 120 rows, 0 rank gaps, 33 of 35 coverage, absent [HKG, TWN]
verify_eti_convergence.py   rho -0.4946 p 0.003437 | r -0.5494 p 0.000927 | CORROBORATED
verify_retrieval_corpus.py  admitted 3, refused 27, of 30 real pool files
test_gate check_retrieval_corpus   5/5 fixtures verified
selfheal --report-only  verdict DEGRADED, escalations 0, test_gate PASS_WITH_BENIGN
  action gap: friction 0, time to action 0.0s over 0 repairs, unmodified execution n/a
git check-ignore -v var/restricted/eti_2026_scores.json  -> .gitignore:140:var/restricted/
.gitignore  ASCII text
```

The extractor ran under pypdf in the container and under `pdftotext` on the operator
machine, parsed the same 120 rows both times, and produced identical coefficients.
The correlation implementation is stdlib and was cross-checked against scipy, which
agrees to every printed digit. The ignore rule was **probed** with `git check-ignore`
rather than read, per the encoding defect that once left `.env*` matching nothing.

**The result, stated with its prediction.** ESE is a stress axis and ETI system
performance is a performance score, so convergent validity predicted a negative rank
correlation, declared before the run, with the gate exiting non-zero if rho were
non-negative or under 0.30 in magnitude. Spearman rho is -0.4946 at n=33, p=0.0034.
The sign is the predicted one. The magnitude is the informative half: near -0.95
would have shown ESE to be a restatement of an existing index, near zero would have
shown it measuring nothing recognisable, and moderate negative is convergent validity
without redundancy. It corroborates **ESE**, a diagnostic axis excluded from the
composite under D-044, and not the headline number.

**What was deliberately not done, named rather than left to be found.**

1. The index was not rebuilt or republished. U-09 sits in the writer, not the payload.
   N1 forbids index bytes changing under an unchanged label, so it lands at the next
   vintage bump, and promotion stays a human act under G-06.
2. GEN-1 could not be closed and U-09 inherits it. The served ledger carries enriched
   text only `build_v8_4.py` produces, and that script aborts past v8.3, so the block
   has been hand carried since v8.4. U-09 will not reach the served ledger until GEN-1
   is settled. Filing it anywhere else would have made it look shipped when it is not.
3. Not paired to `sovereign-infra`. That working copy was unreachable from the analysis
   mount. The register carries a `single_repo_reason` section naming the debt, because
   under Rule 2-1 silence is not an exemption.

---

## 9. What this assessment did not do

It did not open the three hardlinked PDFs through the staging path, reading them on the
device instead. It did not verify the WEF ETI table row by row against the publisher's
own site; it verified the top five, the country count, the indicator count and the edition,
and treated the rest of the table as consistent with those. It did not compute the
ESE-to-ETI correlation, which is recommendation 2 rather than a finding. And it did not
open `WP-Developers_Guide_to_RAG-1` beyond confirming it is the English edition of the
Spanish guide already applied at R1.26.

*Prepared 2026-08-21. Rule DT-1 satisfied: the pool was consulted before the conclusions
were written, and it changed two of them. Reading the OECD paper directly prevented this
assessment from presenting a closed refusal as a new discovery, and reading the WEF
copyright line converted a framing document into a binding constraint on the retrieval
layer.*
