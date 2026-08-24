# Prior art: WEF Energy Transition Index 2026

**2026-08-21 · COUNSEL with ANALYST · Written to answer the `prior_art` clause in
`odi_method`, which requires any novelty claim to be argued against published
index constructions rather than asserted around them.**

Target venue: *Telecommunications Policy*. This file holds the passage to paste
and the reasoning behind it. No manuscript file exists in either repository at
the time of writing, which is why the passage lives here rather than in a draft.

---

## 1. Why this is now a submission risk and not a background note

The ODI methodology block already carries this:

> "HHI-based cloud sovereignty measurement is not novel. Published Cloud Adoption
> Index constructions weight HHI supplier diversification at 40 percent; published
> EU cloud HHI estimates run 2500 to 3450. Any novelty claim must be narrowed to
> substrate-linked facility-level concentration and argued against this prior art."

ETI 2026 raises that bar in a specific, checkable way. The sixteenth edition,
published June 2026 in collaboration with Accenture, evaluates 120 countries on
44 indicators, and **the 2026 edition added two indicators: "AI readiness" and
"clean technology minerals supply chain exposure"**. The second is functionally a
critical minerals stress construct. The first puts compute into an energy index.

Both land on ground QESIS+ claims. A reviewer who knows the ETI will ask the
question, and answering it in the response letter rather than in the paper is a
worse position than answering it in the paper.

---

## 2. The passage

> **Relation to existing composite indices.** Substrate exposure is not an unmeasured
> field. The World Economic Forum's Energy Transition Index, in its sixteenth
> edition (2026), scores 120 economies on 44 indicators and in that edition added
> two that bear directly on the constructs used here: an AI readiness indicator and
> a clean technology minerals supply chain exposure indicator. Published Cloud
> Adoption Index constructions already weight Herfindahl supplier diversification at
> 40 percent, and published estimates of EU cloud market concentration run between
> 2500 and 3450 HHI points. Any claim of novelty must therefore be narrowed rather
> than asserted, and we narrow it on three grounds.
>
> First, unit of analysis. The ETI measures a national energy system and its
> enabling conditions; the indicators are country-level policy, investment,
> infrastructure and innovation conditions. QESIS+ measures concentration at the
> level of the facility and the physical route: operator shares of active cloud
> regions per territory, submarine cable landing exposure, and water catchment
> stress at the sites where compute is actually placed. A country can score well on
> transition readiness while hosting a single hyperscaler and terminating on a
> single cable dataset, and four states in this sample do.
>
> Second, direction of measurement. The ETI is a performance and readiness
> instrument: high is good. QESIS+ axes are stress and exposure measures: high is
> vulnerable. These are not two names for one quantity. Where they overlap, they
> should correlate negatively and moderately, and they do. Across the 33 sample
> states the ETI covers, the QESIS+ Electricity Stress Exposure axis correlates with
> the ETI system performance sub-index at Spearman rho = -0.49 (n = 33, p = 0.003;
> Pearson r = -0.55, p = 0.001). The sign is the predicted one and the magnitude is
> the informative part: a coefficient near -0.95 would show the axis to be a
> restatement of an existing index, and a coefficient near zero would show it to be
> measuring nothing recognisable. A moderate negative association is what
> convergent validity without redundancy looks like.
>
> Third, and this is the claim we would defend hardest, the contribution is
> epistemic rather than metrical. The ETI publishes scores. It does not publish an
> artefact a third party can reproduce byte for byte from a public commit, nor a
> hash chain binding each published figure to the inputs that produced it, nor a
> coverage rule that withholds a composite with a stated cause rather than imputing
> it. Three states in this sample carry no composite for that reason, and the cause
> is published per state and distinguishes a measurement limit from a political one.
> What is offered here is not a better score for substrate exposure. It is a
> substrate exposure measure that can be checked, and that declines to report where
> it cannot measure.

---

## 3. Three things the passage does not do, deliberately

**It does not claim the correlation validates the composite.** ESE is a
diagnostic axis excluded from the composite under D-044, recorded at U-05. The
correlation corroborates ESE. Any sentence extending it to the headline number is
a claim the evidence does not carry, and a reviewer familiar with the exclusion
will notice the gap before anyone else does.

**It does not use the ETI as an input.** ETI is itself a weighted composite over
44 indicators. Feeding it into the QESIS+ composite would be a composite on a
composite and would defeat the derivation doctrine under which the composite is
computed from published axes at build time and never carried.

**It does not use the ETI as the fsQCA outcome.** The temptation is real: the ETI
system performance sub-index is external to the index and covers 33 of 35 states,
which is exactly the shape D-110 KG-4 has been asking for. It is still the wrong
instrument. Substituting one opinion-weighted composite for a declared
circularity trades a known problem for an unknown one, and ESE already consumes
World Bank SAIDI outage duration, so an energy security outcome would share
inputs with the conditions. KG-4 remains open and is not closed by this material.

---

## 4. Reproducibility and licence

The coefficient is regenerated by:

```
python scripts/eti_extract.py            # reads the operator's own copy of the report
python scripts/verify_eti_convergence.py # writes data/axes/eti_convergence_evidence.json
```

The evidence file carries coefficients, counts and input hashes. It carries no
ETI score and no ETI rank, so the source table cannot be reconstructed from it,
and the per-country values live in `var/restricted/`, which is gitignored. This
is the SA-006 posture: derived aggregates only, the same posture SA-004 sets for
UN Comtrade.

**Reproducibility is preserved rather than traded away.** Any reviewer holding
their own copy of the ETI report regenerates the local input and reproduces the
coefficient exactly. The restriction removes the redistribution, not the check.
That sentence belongs in the data availability statement.

**Data availability wording:**

> World Economic Forum, *Energy Transition Index 2026*, obtained by the author from
> the publisher's public website at no cost. The report reserves redistribution, so
> per-country scores are not republished here; the reported coefficients are derived
> aggregates from which the source table cannot be reconstructed. The extraction and
> correlation scripts are published, so a reader holding their own copy of the report
> reproduces the coefficients exactly.

---

## 5. What would change this passage

If a later ETI edition publishes a facility-level or operator-level concentration
indicator, the second ground above weakens and the narrowing has to move. Check
the indicator list at each edition rather than assuming the 2026 boundary holds.
The 2026 edition already moved it once.
