# D-110: Knowledge Graph plus fsQCA, assessment and scoped decision

**2026-08-13 · Proposal: operator · Assessment: ANALYST with SENTINEL on the gate
limbs and COUNSEL on the Article 14 limb · Status: PARTIALLY ACCEPTED**

**Verdict in one line.** The graph limb is accepted and is worth more than the
proposal claimed. The fsQCA control-loop limb is refused on method, not on
ambition, and refusing it protects a finding the loop would have destroyed.

---

## 1. Why the fsQCA limb is refused

Seven findings. Each carries the field or command that produced it.

### F-1. Circularity is already declared and unresolved. This makes it worse.

`fsqca.conceptual_independence_test.standing_limitation`:

> "The outcome is calibrated from the published composite, so the analysis
> explains the index using the axes the index is built from. That is coherent and
> it is circular, and the chapter states it plainly rather than resolving it with
> a test name."

Graph features extracted from the same substrate do not break that loop, they
tighten it. **ODI already is a graph metric**: a Herfindahl over
`odi_continuous.provider_shares`. CABLE and HYPER already encode topology. Adding
"degree centrality" or "structural redundancy" as conditions largely means adding
ODI again under a new name, which is exactly what the independence probe exists
to catch.

### F-2. Limited diversity is already binding at n=32

The model is `WSE, CABLE, REE, HYPER, ESC_inv, GCI_inv -> HIGH_SOV_VULN`, six
conditions, n=32. That is 2^6 = **64 truth-table rows against 32 cases**: more
rows than cases before a single graph feature is added. Several published paths
already sit at `n_cases: 1` with PRI below the 0.75 working convention. The
project's own Hick rule caps the interactive playground at 2 to 4 conditions for
this reason. Adding conditions without adding cases is the most reliable known
method for manufacturing spurious sufficiency.

### F-3. Graph metrics have no calibration referent

`fsqca.calibration.declared_because`:

> "The terms are anchor-sensitive. A sensitivity run at fixed 75/50/25 reproduces
> the v6.6 trivial-driver failure through REE, so anchors are part of the result
> rather than a setting."

Anchors are Ragin direct method on sample percentiles 80/50/20. There is no
theory stating what degree of centrality constitutes full membership in a set.
Automating calibration over a new feature space with no anchor theory is D-103
replicated at machine speed. D-103 was five calibration violations and it is the
most expensive defect in this project's history.

### F-4. Step 3 is a method error, not a tuning problem

"When performance drops or costs spike, the sub-graph is fed into an fsQCA
processing engine." fsQCA is a **cross-case** method. It reports which
configurations are consistently associated with an outcome across a population. A
live sub-graph at a moment of failure is n=1. QCA does not run on one case. What
Step 3 describes needs DAG-based causal inference or rule evaluation, and neither
of those is QCA.

### F-5. Step 4 automates the ecological fallacy

`High_Cost = OverProvisioned * IdleTime + UnoptimizedRouting * MultiRegion` is a
population-level sufficiency statement. It does not license the claim that *this*
deployment's cost is caused by those conditions. Emitting a pull request from a
cross-case solution applied to an individual case ships the fallacy as code, in a
system whose own `honesty_caveat` guards against precisely that inference
elsewhere.

### F-6. Autonomous mutating pull requests collide with G-06 and Article 14

An agent may merge a **paired remediation** PR once its checks pass. It may not
push to `main` and may not promote. A system that synthesises and merges
infrastructure changes from a statistical solution is a high-risk automated
decision under the regulatory framing this project already uses against others.

### F-7. The market gap is narrower than claimed

Live infrastructure knowledge graph, policy as graph constraint, and automated
remediation PRs is an occupied space: Wiz and Orca on security graph, Lyft's
Cartography, Steampipe and CloudQuery on inventory graph, OPA/Rego and Kyverno on
policy as code, and Firefly, env0, Spacelift and Terraform Cloud on drift with
automated PRs. The genuinely unclaimed limb is configurational optimisation, and
that is the limb F-1 through F-5 disqualify in this form. "Nobody is doing it"
and "the method cannot do it" are compatible statements, and here both hold.

---

## 2. What is accepted, and why it is the larger prize

### The index is already a graph pretending to be JSON

Verified against `data/qesis_v8.json`:

| Structure | Graph reading |
|---|---|
| `coupling.global.matrix` | weighted complete graph, 6 axis nodes |
| `odi_continuous.provider_shares` | bipartite, state to hyperscaler, weighted |
| `audit.cse_components` | bipartite, state to cable source, different edge rule inside and outside the EU |
| `lineage` | directed acyclic graph over vintages |
| `chain_spine.jsonl` | linked list, 752 nodes |
| `citation_concordance.resolution_bindings` | typed edge, erratum to resolution path |

No new data and no new method are required to express this.

### The query a scalar composite structurally cannot ask

The composite is a weighted **sum**. A sum cannot represent a **conjunction**.
ODI and CSE both enter as addends, so a state that is single-sourced on both
appears in the composite only as two moderate numbers added together. The graph
intersects them instead.

Run 2026-08-13 against the served payload:

```
States both single-provider and single-cable-source:  4 of 35
  AUT  Azure  / SubmarineMap   composite 31.2
  BHR  AWS    / SubmarineMap   composite 58.1
  FIN  GCP    / SubmarineMap   composite 38.8
  NOR  Azure  / SubmarineMap   composite 29.7

Sole-dependency sets by provider:
  Azure  present in 27 states, sole provider in 3  (AUT, DNK, NOR)
  OCI    present in 15 states, sole provider in 2  (NLD, SAU)
  AWS    present in 25 states, sole provider in 1  (BHR)
  GCP    present in 22 states, sole provider in 1  (FIN)
```

Three of the four conjunctive cases carry composites between 29.7 and 38.8, which
places them in the low-exposure half of the sample. **The index ranks them as
comparatively safe and the graph shows them as conjunctively single-sourced.**
That disagreement is the finding, and it is not visible in any view built on the
composite alone.

### REVISION B, 2026-08-13. The section below is retracted and corrected.

Rev A asserted that SubmarineMap being sole cable source for 25 of 35 states was
an unrecorded epistemic single point of failure. **Wrong, and the defect is mine.**
It was derived from `cse_components` in the served index without opening the
evidence plane. `qesis-mcp/CLAUDE.md` item `PUB-1` names both files and says they
are in the repo and not on the served surface. They were read at session start and
not opened. R-3: being right about a file you did not open is not an audit, and
here the conclusion was not even right.

What the evidence plane actually holds:

- `data/axes/cse_percolation.json`: the real submarine cable graph. 625-city giant
  component, 76 components, articulation set recomputed against published. Twelve
  targeted removals cost 31 cities between them; the thirteenth, **Porthcurno**,
  severs **278**. Random removal of 88 cities, 6.8 times more nodes, costs 14
  percent of the giant component. Robust-yet-fragile, confirmed and audited.
- `data/axes/emodnet_cse_evidence.json`: EMODnet release `20230628` with SHA-256,
  854 features, 269,019 km, unattributed share 0.6242, 12 states sourced, coverage
  **0.3429 against the 0.75 BIG gate**, verdict **NOT REPRODUCIBLE** at Spearman
  -0.467.

The non-EU SubmarineMap-only rule is therefore a **documented, audited disposition
with a stated reproduction failure behind it**, not a gap. It is in the ledger.

Second-order defect, and the more serious one: `build_graph.py` rev A typed
dataset names as infrastructure nodes, so `SOLE_CABLE_SOURCE` read as one cable
route while meaning one dataset supplied the value. A provenance edge wearing a
physical edge's clothes, in the file whose entire argument is that typed edges make
commitments explicit. Corrected in rev B: `CSE_VALUE_SOURCED_FROM` is declared a
provenance edge, and the physical plane enters as `LandingCity` and `CableNetwork`
nodes from the percolation file.

**Corrected conjunction result: 0 states.** No sole-provider state hosts a
top-betweenness landing city. Provider monoculture and cable chokepoint hosting are
**disjoint geographies** in this sample. That is a real null result and it is
reported as one rather than dressed up.

`KG-3` is rewritten accordingly: it does not add a missing ledger entry. It
promotes the percolation and EMODnet evidence onto the served surface, which is the
standing `PUB-1` item, and it is the actual publishable cable finding.

### Superseded text, retained per L-074 so the correction is explainable

`SubmarineMap` is the sole cable source for **25 of 35** states. `EMODnet`
contributes to 9, `ITU_SCM_proxy` to 1 (SAU, D-108). U-08 records that CSE is not
constructed identically inside and outside the EU. It does not record that
two-thirds of the sample's cable exposure rests on a single dataset. That is an
epistemic single point of failure in the index's own provenance and it belongs in
the uncertainty ledger.

### Scope discipline, stated so the finding is not overclaimed

`n_providers` counts hyperscalers operating a region on the state's territory,
weighted one unit per active cloud region (U-04: availability-zone counts are
missing for 27 of 35). "Single provider" therefore means **only one hyperscaler
operates a region on that territory**, which is jurisdictional single-sourcing. It
is not a claim about where that state's workloads actually run. Any view carrying
this must carry that sentence.

---

## 3. The ontology and epistemology correction, accepted and extended

The operator is right that v2.0 of `MODELING_LAYERS_MDA.md` under-committed by
treating ontology and epistemology as analytic columns only. In a reflexive twin
the ontology **is** the schema and the epistemology **is** the chain: not
questions asked about the system but artefacts running inside it.

The extension the correction implies: they are columns **and** reified carriers,
and the reification is what distinguishes a twin from a model. MOF's own move is
that M3 describes itself. Keeping only the reification loses the ability to ask
ontological questions at rungs where no schema answers them, for example whether
the Article 14 register commits to "a held decision" as an entity that persists
across vintages. Keeping only the columns loses the reflexivity. Both, and the
carrier is named per rung.

**This is the strongest argument for the graph limb, and it is semiotic rather
than technical.** JSON field names are an *implicit* ontological commitment.
Typed edges with declared domain and range are an *explicit* one. Moving to a
graph is the ontology stopping pretending to be a schema. It is an upgrade at the
semantic rung, and it is the reason the graph limb survives while the loop does
not.

---

## 4. The version of KG plus fsQCA that would pass

Not a control loop. A second study, and it would be the first thing in this
project to break the declared circularity.

| Element | Requirement |
|---|---|
| Cases | the 32 ranked states, already held |
| Conditions | at most 5, and **none may be reconstructible from the composite**. Conjunctive single-sourcing qualifies. Any restatement of ODI does not |
| Outcome | calibrated from a source **outside the index**. Observed outage or incident history is the candidate |
| Calibration | anchors declared before the run, with the sensitivity run published beside the result |
| Claim | reported beside the six-condition baseline, superseding nothing |

If the outcome cannot be sourced externally, the study does not run. That
constraint is the whole point: it is what F-1 has been asking for since v8.3.

---

## 5. Roadmap and agent tasks

| Id | Task | Agent | Gate |
|---|---|---|---|
| `KG-1` | Emit `data/qesis_graph.json` from the served index. Nodes: state, provider, cable source, axis, vintage. Typed edges with declared domain and range. Generated only, never hand-edited | ARCHITECT | new `verify_graph.py`, two fixtures, one refuse and one accept (V-2) |
| `KG-2` | Add conjunctive single-sourcing to views V4 and V5 of the visualisation spec. Carries the U-04 scope sentence wherever it appears | ARCHITECT | `verify_dashboard.py` |
| `KG-3` | **Rewritten rev B.** Promote `cse_percolation.json` and `emodnet_cse_evidence.json` to the served surface. This is standing item `PUB-1` and it carries the publishable cable finding: Porthcurno severs 278 cities at removal 13. Do NOT file a ledger gap; the disposition is already audited | ANALYST, SENTINEL to confirm | `verify_index.py`, `verify_served_contract.py` |
| `KG-5` | **New rev B.** Extend `verify_graph.py` to fail the build if any node kind is a dataset name reachable by an edge type declared physical. The rev A defect was a provenance edge typed as physical, and a rule held only in prose has been described, not applied (L-054) | ARCHITECT | two fixtures |
| `AUDIT-1` | Now evidenced. `ops/v9.0_FINAL_AUDIT.md` certifies EMODnet ACTIVE while `emodnet_cse_evidence.json` returns coverage 0.3429 and NOT REPRODUCIBLE. ACTIVE is a property of a connection, not of a result (L-055) | SENTINEL | both artefacts |
| `KG-4` | Source external outage or incident history for 32 states. **Blocks any fsQCA extension.** If unsourced by the next vintage, record `D-110` as declined rather than pending | SCOUT | none until sourced |
| `MDA-1` | Wire the gate for the `effective_weights.finding` versus `necessity_verdict` contradiction on REE 0.916 | ARCHITECT, SENTINEL | two fixtures |
| `SEC-1` | Pin all ten GitHub Actions `uses:` lines to full-length commit SHAs and correct the false closure claim retracted in `MODELING_LAYERS_MDA.md` section 5(b) | ARCHITECT | credential and pinning scan in the pre-commit gate |

**Refused and recorded as refused, not deferred:** autonomous mutating pull
requests (F-6), per-instance fsQCA diagnosis (F-4, F-5), and automated fuzzy
calibration of graph metrics (F-3). Recording a refusal is cheaper than
rediscovering it.

**Sequence.** `SEC-1` first, because it is an open supply-chain exposure recorded
as closed. Then `MDA-1`, because a served contradiction is visible the moment the
visualisation renders both blocks. Then `KG-1` to `KG-3`. `KG-4` runs in parallel
and gates nothing else.
