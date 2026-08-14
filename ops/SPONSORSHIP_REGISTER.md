# Sponsorship Register: measurement blocked by cost, not by method

**v1.0 · 2026-08-14 · Owner: COUNSEL, commercial limb · Ratified by: R. Batista Silva**
**Authority: D-111 · Mirror: `sovereign-infra/ops/OBLIGATIONS.md`**

---

## Why this register exists

An axis that cannot ship because no method reaches it is a scientific limit and
belongs in the uncertainty ledger. An axis that cannot ship because the dataset
costs money is a **funding line**, and recording it as a limitation understates
the instrument.

The distinction is not cosmetic. QESIS+ already knows how to measure
semiconductor fabrication capacity: the ingestion contract is written, the unit
is declared, the gate is executable and it has already refused three sources
correctly. What is missing is a licence, and a licence has a price.

**Rule S-1.** Every item here states what it unlocks, what it costs, what the
sponsor receives, and what happens if it is never funded. An item without all
four is an aspiration, not an opportunity.

**Rule S-2.** A sponsored dataset never changes a finding's direction. Funding
buys **coverage**, never conclusions. Any sponsor arrangement that conditions a
result is refused at the Article 14 gate, and this sentence appears in every
sponsorship agreement or there is no agreement.

---

## SP-1. Semiconductor Fabrication Capacity (SFC), the flagship gap

| | |
|---|---|
| **Blocked item** | The SFC axis, retired to `SDI` under D-111 for lack of a free source |
| **What is already built** | Ingestion contract, canonical unit `wspm_200mm_equivalent`, executable gate (`verify_axis_sfc.py`), falsifier (`prove_axis_sfc_contract.py`), BIG threshold at 27 of 35. All of it working, all of it verified refusing three sources correctly |
| **What is missing** | A licence. Nothing else |
| **The dataset** | SEMI World Fab Forecast. Over 1,000 front-end fabs, fab-by-fab capacity, technology node, wafer size, quarterly Excel. The industry benchmark, and the source the OECD's own analysis is built on |
| **Indicative cost** | SEMI members $49, non-members $99, per the published registration page 2026-08-14. Verify at purchase; this is an order of magnitude, not a quote |
| **What it unlocks** | The eighth axis. Semiconductor capacity was named the Infrastructure Pillar in the February 2026 roadmap and is the only pillar still unmeasured. It is also the axis institutional buyers ask about first, because it is where export controls bite |
| **What the sponsor receives** | Named attribution on the axis provenance and on the method page, pre-release access to the axis at first publication, and a citable role in an openly published instrument. Not influence over the result (Rule S-2) |
| **If never funded** | The axis stays retired. `SDI` measures import dependency instead, which answers the same sovereignty question from the demand side rather than the supply side. The instrument is not broken without it, it is one dimension smaller |

**Honest counter-argument, stated before it is asked.** At this order of cost the
gap is small enough that a reader may ask why it is a sponsorship item at all.
Two reasons. The published price is for a sample or entry tier and the full
fab-level dataset used for a commercial product is licensed separately and
materially higher. And a research instrument that is public under CC-BY-NC cannot
quietly absorb a commercial redistribution licence, which is `OBL-4` below.

---

## SP-2. UN Comtrade premium tier

| | |
|---|---|
| **Blocked item** | Bulk and historical extraction for the `SDI` axis beyond the free tier |
| **Free tier** | 100,000 records per query, 500 calls per day. Sufficient for a single-year, 35-entity cut |
| **What premium unlocks** | Time series. The BAU time-evolution model runs t0 to 2030 to 2050 to 2080, and a single-year dependency reading cannot feed it |
| **Cost** | Payable, published on request from UNSD |
| **If never funded** | `SDI` ships as a single-year cross-section and the time-evolution model excludes it, stated wherever the axis appears |

---

## SP-3. Availability-zone completion (partially self-solved)

| | |
|---|---|
| **Blocked item** | U-04, capacity-weighted ODI |
| **Status** | **Largely resolved without money.** `compute_odi_bounds.py` publishes bounded intervals: 30 of 35 entities carry an ODI band the missing zone counts cannot change, 5 remain band-ambiguous (AUS, BRA, CHE, CHL, GBR) |
| **What money would buy** | A commercial cloud-infrastructure register to close the last 5 |
| **Recommendation** | **Do not fund.** The operators publish zone counts on their own region pages at no cost. This is labour, not licence, and it belongs to SCOUT |

Recorded so the register is not a wish list. An item that can be solved by work
rather than money is marked as such, and SP-3 is the control that keeps the other
two honest.

---

## New obligation raised by this register

| Id | Obligation | Owner |
|---|---|---|
| `OBL-4` | A commercially licensed dataset cannot be redistributed inside a CC-BY-NC public index. Any sponsored acquisition must be structured as **derived aggregates only**, on the TeleGeography precedent already in the licence block. Confirm the redistribution limb in writing with the licensor **before** funds move, not after | COUNSEL, then HUMAN |

**OBL-1 to OBL-3** are recorded in D-111 section 4 and cover the Comtrade
redistribution limb. `OBL-4` generalises the same constraint to every sponsored
source, so the next acquisition does not re-derive it.

---

## Standing position for the funnel

The line HERALD may publish, and no stronger:

> Two measurement gaps in QESIS+ are licence-bound rather than method-bound. The
> contracts, gates and falsifiers for both are already built and already refusing
> non-conforming sources correctly. Sponsorship buys coverage. It does not buy a
> finding, and the agreement says so.

That sentence is the instrument, and the instrument is what leads. The argument
never leads.
