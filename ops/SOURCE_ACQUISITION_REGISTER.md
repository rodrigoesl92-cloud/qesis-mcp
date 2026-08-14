# Source Acquisition Register

**v1.0 · 2026-08-14 · Declared by: R. Batista Silva, ARCHITECT and operator**
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
