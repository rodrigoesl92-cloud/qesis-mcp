# QESIS+, sovereign substrate intelligence (MCP server)

**An auditable index of digital-sovereignty substrate risk.** 35 states, 7 measured axes
(water, submarine cable, rare earths, foreign platform, hyperscale operator, cloud risk
density, electricity). Vintage **v8.2 (2026-07)**.

Headline finding: **substrate entanglement is geopolitical, not universal.** The von
Neumann coupling ratio is **0.124** at planetary scale (n=32) and rises to **0.176**
inside the import-dependent core (n=26). Energy-rich states decouple through cheap,
reliable, carbon-heavy power. For states that import their energy, their minerals and
their hyperscalers, every axis is bound to every other.

## Why an MCP server

Analysts already work inside AI clients. `qesis_mcp` makes the index a first-class tool
those clients can call: country profiles, rankings, comparisons, two-tier coupling,
fsQCA pathways, methodology, and on the institutional tier the full component audit.

## Connect

Remote, no install:

```
https://qesis-mcp.vercel.app/mcp
```

Local, over stdio:

```bash
pip install -r requirements.txt
python server.py
```

Claude Desktop:

```json
{"mcpServers":{"qesis":{"command":"python","args":["/path/to/qesis-mcp/server.py"],
 "env":{"QESIS_LICENSE_KEY":"<institutional key>"}}}}
```

Without a key the server runs in **demo tier**: rounded scores, limited ranking depth,
component audit locked. That is the product working as designed.

## Tools

| tool | what it answers |
|---|---|
| `qesis_get_country` | 7-axis profile, composite, coverage, BIG status, fsQCA conditions, pathways |
| `qesis_rank_countries` | who is most exposed, by composite or any axis |
| `qesis_compare_countries` | side by side with deltas and binding constraints |
| `qesis_get_coupling` | the two-tier entanglement finding, derived at build time |
| `qesis_get_pathways` | fsQCA pathways, solution stats, anti-circularity test |
| `qesis_get_component_audit` | institutional: per-axis provenance, composite recomputed term by term |
| `qesis_get_methodology` | axes, BIG protocol, composite model, sources, citation |
| `qesis_get_integrity` | which generation you are reading, and whether it reproduces |

## Integrity by construction

**The composite is derived, never carried.** It is recomputed from the published axes on
every build, and the deploy fails on drift.

That rule exists because v8.0 broke it. It served a composite column computed against an
earlier axis vintage, which no weighting could reproduce from the axes published beside
it: the United Kingdom scored at or above Switzerland on all seven axes yet carried a
lower composite (28.1 against 46.2), and weights are non-negative. Every composite
changed when it was rebuilt.

**The Binary Integrity Guard never imputes,** and from v8.1 it binds the composite too.
A state missing a weighted axis is not ranked and not silently zeroed. Singapore, Hong
Kong and Taiwan sit at coverage 0.70 against the declared 0.75 threshold and return a
published gap. Singapore previously appeared as the least exposed state in the sample at
composite 1.7, which was a zero standing in for an absent water-stress reading.

**The coupling matrix is derived too,** and `scripts/coupling.py` reproduces the
published v8.0 values before the build trusts it on changed inputs.

Verify any of this yourself:

```bash
python scripts/verify_index.py     # 16 checks, exit 0 means publishable
python scripts/test_gate.py        # injects each defect the gate must catch
python scripts/coupling.py         # coupling reproduces the published values
python scripts/test_http.py        # the remote endpoint answers MCP over HTTP
```

## The ODI axis

ODI is the **continuous Herfindahl index** over hyperscale operator shares of active
cloud regions, covering 35 of 35 states. It replaced a four-level count proxy in v8.2
(decision D-045), because a macro polycrisis model runs time evolution over these axes
and a step function cannot express a partial operator withdrawal. The ordinal value stays
published per country under `audit.ODI_ordinal_value`.

The measures do not share a zero: four evenly split operators give ordinal 0 but HHI 25,
because four hyperscalers is concentration rather than its absence.

**Open:** the fsQCA `HYPER` condition was calibrated on the ordinal axis and is flagged
`recalibration_required` in the served payload. Do not cite a pathway membership from
this vintage until it is re-derived.

## Codebook

See [CODEBOOK.md](CODEBOOK.md) for axis construction, BIG thresholds, coupling and fsQCA
specification.

## Licence

Engine MIT, index CC-BY-NC 4.0, upstream sources keep their own terms. See
[LICENSE](LICENSE). TeleGeography material appears only as derived aggregates and must
not be reconstructed from this repository.

## Citation

Batista Silva, R. (2026). *Liquid Sovereignty.* ESIC/LSE.
Dataset: Sovereign_Infra_Intelligence v8.2.

Institutional licensing: open an issue, or contact via LinkedIn
(rodrigo-batista-silva-initium).
