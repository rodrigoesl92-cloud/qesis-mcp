# Dimensional mapping of the QESIS+ instrument

**Vintage:** v8.5 · **Written:** 2026-08-08 · **Status:** descriptive, not aspirational

This maps the instrument across four layers: what it claims exists, how it
claims to know, what its terms mean, and what its outputs signify to a reader.
Each layer is written against what the index actually declares. Where a layer
rests on an assumption that has not been discharged, the assumption is named.

---

## 1. Ontology: what the instrument asserts exists

The instrument commits to five kinds of entity.

| Entity | Cardinality | Identity condition | Where it lives |
|---|---|---|---|
| Sovereign state | 35 | ISO 3166-1 alpha-3 | `countries` |
| Axis | 7 | Named measure on a 0 to 100 stress scale | `countries[*].axes` |
| Landing city | 912 | TeleGeography city id, with coordinates | `connectivity_L1_full` |
| Cable | 343 | TeleGeography cable id | `connectivity_L1_full` |
| Configuration | 64 | A point in the 2^6 condition space | `fsqca.truth_table` |

Two commitments carry weight and are worth stating plainly.

**The state is the unit of analysis, and the network is not.** Cables land in
cities, not in countries; the country attribution is a rollup. Percolation
operates on the city graph, so its findings are about cities and become
statements about states only through that rollup. Porthcurno is a place. "The
United Kingdom" is an aggregation over 102 landing cities, of which Porthcurno
is one.

**An axis is a stress, not a capability.** Every axis runs so that a higher
number is worse. This is why CSE falls as cable density rises, and why the sign
of any correlation with an external capability measure is expected to be
negative.

**Unresolved.** The instrument treats the 35 states as a population, but they
were selected rather than sampled. No sampling frame is declared. Every
distributional statement, including the 80/50/20 calibration percentiles, is
therefore conditional on that selection.

---

## 2. Epistemology: how the instrument claims to know

Four evidence grades operate, and the instrument is unusually explicit about
the boundaries between them.

**Measured.** A quantity read from a source that measures it directly. Ember
emissions intensity is the clearest case: it is the same quantity as
`carbon_gco2_kwh`, at 35 of 35 coverage and 2024 to 2025 vintage.

**Derived.** A quantity computed from measured inputs by a declared formula.
The composite is derived: `0.3*WSE + 0.3*CSE + 0.17*ODI + 0.15*REE + 0.08*RGD`,
recomputed at build time and never carried.

**Inferred.** A quantity produced by a model whose assumptions exceed its
inputs. Every fsQCA pathway is inferred, and the intermediate solution is more
strongly inferred than the complex one because it consumes counterfactuals about
50 of 64 configurations that were never observed.

**Withheld.** A quantity a reader might expect that is deliberately absent.
Three states carry no composite under the BIG gate. CSovE is held at 21 of 35
and excluded from the composite. The v9.0 semiconductor axis is withheld at 0 of
35. Withholding is an epistemic act here, not a gap in the work.

The governing rule, D-007: coverage below 0.75 makes a finding, not a gap to
fill. Nothing is imputed to reach a threshold.

**The standing limitation.** The fsQCA outcome is calibrated from the composite,
and the composite is a weighted sum of four of the six conditions. The analysis
explains the index using the axes the index is built from. The index says so
directly rather than resolving it with a test name. Consequence: a pathway is a
combinatorial decomposition of the index, not an independently validated causal
route, and the variant-outcome probe narrows this without removing it.

---

## 3. Semantics: what the terms mean, and where meaning shifts

Three places where a term does not mean what its name suggests.

**CSE is two different measures wearing one name.** For EU states it composes
EMODnet and SubmarineMap at 0.6 and 0.4. Elsewhere it is SubmarineMap alone. A
cross-region CSE comparison therefore compares two constructs. The index
registers this and instructs that the split be stated wherever CSE is compared
across regions. As of this vintage the EMODnet half is not reproducible from the
EMODnet release, which makes the EU branch of the definition provisional.

**"Necessary" and "sufficient" are set relations, not causal claims.** A
condition is necessary when the outcome set sits inside it. That is a statement
about set containment among 32 calibrated cases, and it survives or fails on
where the anchors are placed. The index demonstrates this directly: REE reaches
necessity consistency 0.967 under fixed 75/50/25 anchors and 0.703 under the
primary anchors, and the higher figure is the artefact.

**An articulation point is a formal object, not a metaphor.** A cut vertex is a
node whose removal disconnects the graph. When the instrument says a landing
city is an articulation point, it is not gesturing at fragility; it is naming a
proved property of a specific graph.

**Semantic drift to watch.** "Sovereignty" carries a legal meaning the
instrument does not measure. What is measured is exposure to external
dependency across seven physical and institutional axes. A reader who imports
the legal sense will over-read every score.

---

## 4. Semiotics: what the outputs signify to a reader

The instrument emits signs, and signs do work that numbers do not.

**The tier label is the strongest sign and the weakest measure.** A label such
as DORM compresses a continuous composite into a category, and a reader treats
the category as a kind rather than a cut. This has already failed once: 9 of 21
published CSovE tier labels contradicted their own stated boundaries and were
recomputed. The label was believed because it looked categorical.

**Withholding signifies rigour, and can be misread as absence.** Three states
carry no composite. To a governance reader that reads as discipline; to a
commercial reader it can read as an incomplete product. The same sign carries
opposite value depending on audience, which is a reason to state the cause
wherever the blank appears.

**Rank position signifies more than it supports.** A one-place difference in a
35-state ranking sits well inside the uncertainty the index itself publishes.
Ranks invite a precision the composite does not have.

**The map signifies inevitability.** A cable route drawn on a chart reads as
permanent infrastructure. The percolation result says the opposite: 13 removals
out of 912 cut the largest connected component from 594 cities to 316.

---

## 5. Cross-layer table

| Output | Ontology | Epistemology | Semantics | Semiotics |
|---|---|---|---|---|
| Composite score | State | Derived | Weighted stress | Rank, over-read |
| Axis value | State, axis | Measured or derived | Stress, higher is worse | Comparable, sometimes wrongly |
| Tier label | State | Derived, thresholded | Boundary cut | Kind, strongest sign |
| fsQCA pathway | Configuration | Inferred, counterfactual | Set-theoretic sufficiency | Policy route, over-read |
| Articulation point | Landing city | Measured, proved | Cut vertex | Chokepoint, correctly read |
| Withheld cell | State | Withheld under D-007 | Coverage below gate | Rigour or absence, by audience |

---

## 6. What this buys, and what it costs

The mapping is exportable: each layer is separable, and the ontology and
semantics layers are reusable by anyone building a composite indicator over
sovereign states. The epistemology layer is the one with commercial value,
because the four grades and the D-007 rule are what let the instrument publish a
blank cell and defend it.

The cost is that two layers currently carry undischarged assumptions: the
selection frame in the ontology, and the circularity in the epistemology. Both
are named above. Neither is fatal, and both are the kind of thing a reviewer
finds in ninety seconds if it is not declared first.
