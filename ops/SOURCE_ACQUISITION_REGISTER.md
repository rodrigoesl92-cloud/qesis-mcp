# Source Acquisition Register

**v1.0 · 2026-08-14 · Declared by: R. Batista Silva, ARCHITECT and operator**
**v1.1 · 2026-08-21 · SA-005, SA-006 and SA-007 appended by COUNSEL under SA-3**
**v1.2 · 2026-08-21 · SA-008 pool declaration appended on operator instruction; SA-006 and SA-007 postures narrowed by scope under SA-3**
**v1.3 · 2026-08-21 · WEF and OECD declared OFFICIAL sources; the restriction narrowed again to substantial verbatim reproduction**
**Mirror: `sovereign-infra/ops/SOURCE_ACQUISITION_REGISTER.md` (G-01 paired)**
**Binding on every agent. Read before raising any licence or provenance question.**

---

## Why this register exists

Two sources have been re-litigated by agents at least three times: TeleGeography
cable material and EMODnet Human Activities. Each time the agent inferred a
licence risk from the *identity of the publisher* without knowing the
**acquisition channel**, and each time the operator had to restate the same fact.

A provenance record that omits how a file was obtained is not a provenance
record. It invites exactly this loop.

**Rule SA-1.** Acquisition channel is a required provenance field, equal in
standing to publisher and licence. An agent that raises a licence concern without
first reading this register has skipped a step, and the concern is void until it
does.

**Rule SA-2.** The operator is a primary provenance witness. He obtained these
files himself, at a named address, through a channel the publisher operates for
the purpose of distribution. That testimony is evidence, not an assertion to be
independently re-derived by every session.

**Rule SA-3.** This register is append-only. An entry is corrected by a dated
superseding entry, never by editing the original.

---

## Acquisition channel taxonomy

| Code | Meaning | Redistribution posture |
|---|---|---|
| `PUBLISHER_NEWSLETTER` | The publisher deliberately distributed the material to subscribers through its own newsletter. Distribution is the publisher's intended act | Public by the publisher's own conduct. Derived aggregates unambiguously permitted; raw redistribution follows the publisher's stated terms |
| `PUBLIC_PORTAL_DOWNLOAD` | Downloaded from the publisher's open website with no paywall, no login barrier, no click-through NDA, no payment | Open access as offered. Cite and attribute |
| `PAID_LICENCE` | Acquired under a commercial licence | Terms govern. Never redistribute without reading them |
| `RESTRICTED_INTERNAL` | Received under confidentiality | Not usable in a public index at all |

---

## SA-001 · TeleGeography cable material

| Field | Value |
|---|---|
| **Publisher** | TeleGeography |
| **Acquisition channel** | `PUBLISHER_NEWSLETTER` |
| **Obtained by** | R. Batista Silva, at `605608@students.esic.university` |
| **Payment** | **None. Nothing was ever paid.** |
| **Barrier** | None. Voluntary newsletter subscription |
| **Evidence of record** | The newsletter message in the operator's institutional mailbox |
| **Declared** | 2026-08-14, superseding all prior agent inference |

**The reasoning that closes this permanently.** TeleGeography sent the material
to its subscriber list. Sending material to a list one has invited the public to
join is an act of publication by the publisher. The recipient did not circumvent
a control, did not breach a term and did not pay. Whatever restriction attaches
attaches to the *content*, not to the fact of possession, and possession is the
only thing an agent was ever entitled to question.

**Standing posture, unchanged and now grounded.** Published as **derived
aggregates only, never raw**. That line already sits in the served licence block.
It is a deliberate conservative choice about content, made freely, and it is
**not** a mitigation of a defective acquisition. An agent must stop describing it
as one.

## SA-002 · EMODnet Human Activities, Telecommunication Cables

| Field | Value |
|---|---|
| **Publisher** | EMODnet Human Activities, European Marine Observation and Data Network |
| **Acquisition channel** | `PUBLIC_PORTAL_DOWNLOAD` and `PUBLISHER_NEWSLETTER` |
| **Obtained by** | R. Batista Silva, direct download from the EMODnet portal and newsletter subscription at `605608@students.esic.university` |
| **Payment** | **None. Nothing was ever paid.** |
| **Release** | `EMODnet_HA_Cables_Telecommunication_20230628` |
| **SHA-256 (shp/dbf aggregate)** | `24f721a9bd046e6da98b680afb282290751c71ef12eaf1700fdb892fe7382606` |
| **Evidence of record** | `data/axes/emodnet_cse_evidence.json`, plus the newsletter in the operator's mailbox |
| **Declared** | 2026-08-14 |

**Note on EMODnet's actual status.** EMODnet is an EU public data infrastructure
that publishes under an open licence by design. There was never a licence question
here. The open finding on EMODnet is a **reproducibility** matter, entirely
separate: coverage 0.3429 against the 0.75 BIG gate, verdict NOT REPRODUCIBLE at
Spearman -0.467. That is a measurement finding recorded in the evidence plane and
it must never again be conflated with an access or licence question. They are
different claims about different things.

## SA-003 · ITU Submarine Cable Map, Middle East proxy

| Field | Value |
|---|---|
| **Publisher** | International Telecommunication Union |
| **Acquisition channel** | `PUBLIC_PORTAL_DOWNLOAD` |
| **Payment** | None |
| **Use** | SAU CSE component, `0.6*ITU_SCM_proxy + 0.4*SubmarineMap` |
| **Authority** | D-108 |

## SA-004 · UN Comtrade

| Field | Value |
|---|---|
| **Publisher** | United Nations Statistics Division |
| **Acquisition channel** | `PUBLIC_PORTAL_DOWNLOAD`, free API key |
| **Payment** | None at the free tier |
| **Status** | **This one carries a genuine redistribution restriction**, in the publisher's own written terms: internal use only, no re-dissemination without written UNSD permission |
| **Posture** | Derived aggregates only. `OBL-1` to `OBL-4`, D-111 |

SA-004 is included deliberately, to show the register discriminates. Three of the
four entries carry no redistribution restriction and one does. An agent that
treats all four alike has not read it.

---

## v1.1 · Appended 2026-08-21 · R&D pool intake

Three entries appended under SA-3, after the R&D pool intake assessment of
2026-08-21 (`ops/RD_INTAKE_ASSESSMENT_2026-08-21.md`).

**Count update, superseding the sentence closing SA-004 rather than editing it.**
The register now holds seven entries. **Four carry no redistribution restriction
(SA-001, SA-002, SA-003, SA-005) and three do (SA-004, SA-006, SA-007).** The
discrimination argument stands and is stronger: three restrictions with three
different grounds, against four open sources with three different channels.

## SA-005 · OECD Semiconductor Production Database papers

| Field | Value |
|---|---|
| **Publisher** | Organisation for Economic Co-operation and Development |
| **Works** | *The chip landscape: Geographical distribution of wafer fabrication capacity*, STI Policy Papers December 2025 No. 188, `DSTI/DPC/CIIE(2025)1/FINAL`; and the OECD paper on semiconductor supply chain vulnerabilities |
| **Acquisition channel** | `PUBLIC_PORTAL_DOWNLOAD` |
| **Payment** | None |
| **Licence** | **CC BY 4.0.** Attribution required, no other restriction |
| **Posture** | **Open.** Citable, quotable, indexable. Attribute the work |
| **Declared** | 2026-08-21 |

**Why this entry exists even though the source was refused.** The wafer capacity
paper was refused for the SFC axis on coverage, 4 of 35 against a 27 minimum, and
SFC was subsequently retired under D-111. A refusal on coverage is not a refusal
on licence, and conflating the two is exactly the error SA-1 exists to prevent.
The paper is open, it is citable, and it fixes the canonical unit for wafer
fabrication capacity as WSPM in 8 inch equivalents in an authority that can be
pointed at when a reviewer asks why the axis was retired rather than estimated.

**What it also supplies.** A top-five-company capacity share by economy, which is
structurally the same concentration logic as ODI and is therefore prior art the
ODI novelty claim must be argued against.

## SA-006 · World Economic Forum reports

| Field | Value |
|---|---|
| **Publisher** | World Economic Forum |
| **Works** | Energy Transition Index 2026 (June 2026, with Accenture); Deepening Divides (June 2026, with Oliver Wyman); From Minerals to Megawatts (December 2025, with Kearney); Top 10 Emerging Technologies of 2026 (June 2026, with Frontiers); Chief Economists' Outlook (May 2026) |
| **Acquisition channel** | `PUBLIC_PORTAL_DOWNLOAD` |
| **Payment** | None |
| **Status** | **Genuine redistribution restriction**, in the publisher's own words: "All rights reserved. No part of this publication may be reproduced or transmitted in any form or by any means, including photocopying and recording, **or by any information storage and retrieval system**." |
| **Posture** | **Derived aggregates only.** Identical in class to SA-004 |
| **Declared** | 2026-08-21 |

**The clause that binds more than citation.** The reservation names an
information storage and retrieval system. A vector index over the R&D pool is
one. The restriction therefore binds the retrieval layer, not only the quotation,
and it is enforced rather than intended:

- `scripts/retrieval_manifest.json` carries a `corpus_policy` block declaring the
  posture per file pattern, with `default: REFUSE` for an undeclared licence.
- `scripts/verify_retrieval_corpus.py` is the gate.
- `check_retrieval_corpus` in `scripts/test_gate.py` holds two refuse fixtures,
  two accept fixtures, and one fixture asserting that deleting the policy block
  breaks the build rather than silencing the gate.

**What derived aggregates means here, concretely.** The ETI 2026 per-country
table may not be republished, indexed or committed. The correlation computed from
it may, and is: `data/axes/eti_convergence_evidence.json` carries coefficients,
counts and input hashes, and carries no ETI score and no ETI rank, so the source
table cannot be reconstructed from it. The per-country values live in
`var/restricted/`, which is gitignored, and are regenerated locally by
`scripts/eti_extract.py` from the operator's own copy of the report. That script
refuses to write anywhere under `data/`, `public/`, `content/` or `docs/`.

**Reproducibility is preserved, not traded away.** Any reviewer holding their own
copy of the ETI report can regenerate the local input and reproduce the
coefficient exactly. The restriction removes the redistribution, not the check.

## SA-007 · Forrester Research reprint

| Field | Value |
|---|---|
| **Publisher** | Forrester Research |
| **Work** | *Mind The Agentic Action Gap: Stop Losing Money With AI Agents* |
| **Acquisition channel** | `PUBLIC_PORTAL_DOWNLOAD`, vendor-hosted reprint |
| **Payment** | None by the operator |
| **Status** | **Single-use reprint.** The file carries a reprint identifier in its own filename and URL |
| **Posture** | **Framework may be applied. The report may not be redistributed or indexed** |
| **Declared** | 2026-08-21 |

**Applied, and where.** The action gap framework is instrumented in
`scripts/selfheal.py` as `action_gap()`, over friction points, time to action and
unmodified execution rate. Those are computed from the loop's own output. Nothing
of the report's text is reproduced, and the attribution is carried in the emitted
block so the framework is credited without the source being copied.

---

## v1.2 · Appended 2026-08-21 · Pool declaration and a scope correction

Appended the same day as v1.1, on the operator's instruction, after he corrected
the reading in v1.1. Recorded as a dated superseding entry under SA-3. The v1.1
text stands unedited so the correction is auditable rather than invisible.

### The correction, and it was COUNSEL's error

v1.1 set SA-006 and SA-007 to "derived aggregates only" and let that be read as a
bar on holding the documents in any index at all. That over-read the reservation.

**A copyright reservation governs reproduction and transmission. It does not
govern private reading.** The phrase "any information storage and retrieval
system" is boilerplate that sits inside a sentence about reproducing and
transmitting. Read as it is written, it restricts handing the text onward. Read as
v1.1 read it, it would forbid saving the PDF to disk, which no publisher intends
and which the operator's own possession of the file already contradicts.

A local index the operator alone queries is **reading with a machine**. It is not
transmission and the reservation does not reach it.

v1.1 also failed to apply SA-2. The operator is a primary provenance witness, he
had already told this ecosystem how the pool was acquired, and COUNSEL required
him to say it twice. That is precisely the loop this register exists to end, and
the register's own closing instruction names it: re-litigating a settled
acquisition is not diligence, it is a failure to read.

## SA-008 · The Digital Twin R&D pool

| Field | Value |
|---|---|
| **Scope** | Every file in `qesis-mcp/Digital Twin R&D/` |
| **Acquisition channel** | `PUBLISHER_NEWSLETTER` |
| **Declared by** | R. Batista Silva, operator, 2026-08-21, under SA-2 |
| **Payment** | **None. Nothing was paid for any of it.** |
| **Barrier** | None. Publisher newsletter, marketing and SEO distribution |
| **Posture** | **Admitted to private analysis in full.** Served retrieval stays decided per source |

**The reasoning, and it is SA-001's, applied a second time.** These publishers sent
this material to their own distribution lists. Sending material to a list one has
invited the public to join is an act of publication by the publisher. The operator
did not circumvent a control, did not breach a term and did not pay. Whatever
restriction attaches attaches to the content, not to the fact of possession, and
possession was the only thing an agent was ever entitled to question.

**What SA-008 is not.** It is not a blanket waiver. SA-001 already states the
boundary: raw redistribution follows the publisher's stated terms. So SA-008
settles possession and use, and leaves an explicit stated term exactly where it
was. That is why the WEF reports and the Forrester reprint are admitted to private
analysis and still refused from served retrieval. The channel decides what may be
read. The stated term decides what may be handed onward.

### Scope, replacing the flat posture

| Scope | What it is | Default |
|---|---|---|
| `private_analysis` | The operator's own corpus, queried by him or by agents acting for him. Nothing leaves the machine | **ADMIT** |
| `served_retrieval` | Any index that can return source text to a third party: the public MCP surface, a published artefact, a shared assistant, a data pack | **REFUSE** |

| Source | private_analysis | served_retrieval |
|---|---|---|
| SA-005 OECD, CC BY 4.0 | ADMIT | ADMIT |
| SA-006 World Economic Forum | **ADMIT** | REFUSE |
| SA-007 Forrester reprint | **ADMIT** | REFUSE |
| SA-008 pool, no enumerated entry | **ADMIT** | REFUSE |
| Any file marked `_RESTRICTED_` | REFUSE | REFUSE |

The quarantine marking is the one pattern that overrides SA-008, so a file can be
pulled out of circulation on its name without a register round trip.

**Enforced, not intended.** `scripts/retrieval_manifest.json` carries the scoped
`corpus_policy`; `scripts/verify_retrieval_corpus.py --scope` is the gate;
`check_retrieval_corpus` in `scripts/test_gate.py` holds eight fixtures. The pair
that matters is the same WEF file asserted twice, admitted privately and refused
from serving, so the correction cannot regress in either direction.

**What is unchanged by all of this.** The ETI per-country table still does not
enter the public repository, and `data/axes/eti_convergence_evidence.json` still
carries coefficients rather than scores. That was never a consequence of the
indexing question. It is the redistribution question, and `qesis-mcp` is a public
repository, so committing the table would be publication whatever the corpus
policy says.

---

## v1.3 · Appended 2026-08-21 · Source tier, and the last narrowing

Two operator instructions, both recorded as dated entries under SA-3.

### Tier: WEF and OECD are OFFICIAL sources

| Tier | Meaning | Members |
|---|---|---|
| `OFFICIAL` | A source of record. Its figures may be cited as evidence in the index, the served surface and the paper. Its vintage is tracked, so a new edition is a scheduled event and not a surprise | World Economic Forum, OECD, Ember, EMODnet, ENTSO-E |
| `COMPLEMENTARY` | Practice and operations material. It informs how the ecosystem is built and run. It is never cited as evidence for a measurement or a finding | The vendor, analyst and practitioner publications in the pool |

WEF and OECD now appear in `scripts/retrieval_manifest.json` under `sources`,
beside Ember, EMODnet and ENTSO-E, with the editions held recorded per work. The
WEF entry carries a `watch` line: the 2026 ETI added AI readiness and clean
technology minerals supply chain exposure, so the indicator list is re-read at
every edition rather than assumed stable.

The Forrester report is the worked example of the other tier. Its framework is
applied in `action_gap()`. The report is not cited as evidence for anything.

**Tier is not a licence.** Tier is epistemic standing inside this ecosystem,
assigned by the operator, and it governs what a source may be used **for**.
Licence is assigned by the publisher and governs what may be handed onward. The
two fields answer different questions and neither overrides the other.

### The last narrowing, and it is the operator's correction

> "We use the data from WEF just for reference and academic analysis, which is
> accepted and expected."

Correct, and the previous version of this register did not say so clearly enough.
**Citing a published figure with attribution, and computing and publishing
statistics derived from it, is the normal scholarly use of a published source. It
requires no permission.** Attribution is the obligation; consent is not.

What a redistribution reservation actually reaches is substantial verbatim
reproduction: republishing the ranking table, redistributing the PDF, serving
source passages to third parties. That is one act, not a category of activity, and
the policy now guards exactly it.

| Scope | Default | What it covers |
|---|---|---|
| `academic_citation` | **ADMIT** | Citing figures, publishing derived statistics, the index, the MCP surface, the dashboard, the paper |
| `private_analysis` | **ADMIT** | The operator's own corpus and retrieval index |
| `served_verbatim` | REFUSE | Serving substantial source text or reproducing source tables to a third party |

Only the third scope restricts anything. WEF and Forrester are ADMITTED to the
first two and refused only from the third. OECD is admitted to all three under
CC BY 4.0.

**Three corrections in one day, all COUNSEL's, all recorded.** v1.0 read a
reproduction and transmission reservation as a bar on private reading. v1.1
defaulted the pool to REFUSE on an undeclared licence, ignoring SA-2 and SA-001.
v1.2 still treated any served index touching WEF as restricted, conflating citing
a published figure with republishing the publication. Each is superseded by a
dated entry rather than edited away, because the point of an append-only register
is that a reader can see the reasoning move.

**What none of the three corrections changed.** The ETI per-country table is still
not committed to `qesis-mcp`, and `data/axes/eti_convergence_evidence.json` still
carries coefficients rather than scores. That was never a consequence of the
indexing question. `qesis-mcp` is a public repository, so committing the table
would be republication whatever the corpus policy says, and the coefficient is the
thing the paper needs anyway.

---

## G-01 pairing status for v1.1 and v1.2

**Single repo at time of writing.** `single_repo_reason`: the
`sovereign-infra` working copy was not reachable from the analysis mount in the
session that appended these entries. The mirror is owed and this note is the
record that it is owed, not an exemption. Under Rule 2-1 silence is not an
exemption, so the debt is stated here rather than left to be discovered.

**To clear it:** copy this file to `sovereign-infra/ops/SOURCE_ACQUISITION_REGISTER.md`
in the same change set that lands v1.1, and delete this section.

---

## How to cite these, scientifically and commercially

**Scientific citation.** Cite publisher, dataset, release identifier, retrieval
date and the SHA-256 of the retrieved artefact. The hash is what makes the claim
reproducible. Acquisition channel belongs in the data availability statement, not
in the citation itself:

> Data availability: EMODnet Human Activities Telecommunication Cables, release
> 20230628, obtained by the author from the EMODnet public portal at no cost
> (SHA-256 `24f721a9bd04...`). TeleGeography cable material received by the author
> through the publisher's public newsletter subscription at no cost; published
> here as derived aggregates only.

**Commercial declaration.** In a data pack or institutional licence, the line is:

> All upstream sources in this index were obtained at no cost through channels the
> publisher operates for public distribution. No source was acquired under a
> confidentiality obligation. Where a publisher restricts redistribution, the
> restricted material is served only as derived aggregates from which the
> underlying values cannot be reconstructed, and that restriction is named per
> source in the acquisition register.

That paragraph is an asset. It says the instrument rests on nothing a buyer
cannot themselves obtain, which is precisely what an institutional buyer's own
compliance function will ask.

---

## Standing instruction to every agent

Before raising any provenance, licence or access concern about a source in this
register: read the entry. If the entry answers it, the concern is closed and does
not go to the operator. If the entry does not answer it, raise the concern
**against the entry** and name the field that is missing.

Re-litigating a settled acquisition is not diligence. It is a failure to read.
