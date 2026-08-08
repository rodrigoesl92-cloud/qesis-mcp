# Session report, 2026-08-08

**Shipped:** commits `560ead1` and `c092cc3` on `main`. Integrity gate green,
production serving v8.5, chain VERIFIED at 654 entries with 0 link breaks.

This report is the second half of the job: what was built, and what is still
missing. The missing list is longer than the shipped list, and that is the
honest shape of it.

---

## Part 1. What shipped and holds

| Item | Result | Evidence |
|---|---|---|
| Cable percolation | Tipping point at 13 of 912 removals | `data/axes/cse_percolation.json` |
| fsQCA 2^k engine | 64-row truth table, 3 solutions | `data/fsqca/equifinality_v85.json` |
| Variant-outcome probe | 2 of 3 pathways fail externally | same file, `variant_outcome_probe` |
| EMODnet ingest | Not reproducible, 1 unsourced value | `data/axes/emodnet_cse_evidence.json` |
| Ember ingest | 35 of 35, passes BIG gate | `data/axes/ember_ese_evidence.json` |
| EDA benchmark | +25.1% dispatch overhead, recommend against | `ops/EDA_VS_BATCH_BENCHMARK.json` |
| Dimensional mapping | Four layers, assumptions named | `docs/DIMENSIONAL_MAPPING_v8.5.md` |

**The percolation is the strongest result in the corpus.** The graph reproduced
exactly (1,255 nodes, 1,489 edges, 76 components, 88 of 88 articulation cities).
Under an adaptive betweenness attack the largest component falls from 594 cities
to 316 in a single step, at Porthcurno. Twelve prior removals cost 31 cities
between them. Random removal of 88 cities, 6.8 times more nodes, costs 14
percent. Robust-yet-fragile is now measured rather than asserted, which is what
L-056 said was missing.

---

## Part 2. What is missing

### 2.1 The index was not changed, so none of this is live

Everything above is an evidence file. No composite moved, no axis was refreshed,
and the served MCP surface returns exactly what it returned yesterday. Promotion
needs a v8.6 vintage: a decision per item, a `build_index.py` change, a reseal,
a chain append and a new attestation.

**Consequence to be aware of:** `qesis_get_pathways` is one of the 8 served
tools, and the v8.5 pathways are withdrawn. The new equifinality solutions exist
on disk but are not wired to it. That tool is currently the weakest surface in
production.

### 2.2 SAU carries an unsourced published value, right now, in production

`SAU` publishes `CSE_EMO = 94.3` with zero EMODnet geometry, and Saudi Arabia
sits outside the EMODnet geographic remit under any of its products. `POL`
publishes 96.9 on 58 km and one feature. Meanwhile `FRA` is published null while
supplying the two largest layers in the release, 28,813 attributed km across 508
features.

This is a live defect, not a backlog item. It needs a decision:

1. Correct `SAU` to null, which moves its CSE and therefore its composite; or
2. Produce the provenance that justifies 94.3.

There is no third option in which it stays as it is.

### 2.3 EMODnet cannot be promoted even if the defects are fixed

Coverage is 12 of 35, which is 0.343 against a BIG gate of 0.75. Under D-007
that is a finding, not a gap to fill. The EU-versus-non-EU split in the CSE
definition therefore stays provisional, and the instruction to state the split
wherever CSE is compared across regions stays in force.

### 2.4 The commercial claim needs rewriting

The pitch is "mathematically proven equifinal pathways". The probe does not
support that wording:

| Pathway | vs composite | vs cable betweenness | Verdict |
|---|---|---|---|
| `WSE * CABLE * ~ESC_inv` | 0.9188 | 0.6909 | fails the 0.80 bar |
| `CABLE * REE * HYPER * ~ESC_inv * GCI_inv` | 0.9156 | 0.5287 | fails the 0.80 bar |
| `WSE * REE * ~HYPER * ESC_inv * ~GCI_inv` | 0.8081 | 0.9372 | survives, and strengthens |

The two most persuasive pathways are largely artefacts of the composite's own
construction. The one that survives rests on a single case, Italy, with PRI
0.5882, below the 0.75 working convention. This is L-057 repeating: the result
that reads best is the one that most deserves attack.

What can honestly be sold today is the combinatorial *structure*, plus the
percolation, which is externally grounded. What cannot be sold is "proven
pathways to sovereignty".

### 2.5 Limited diversity and circularity are undischarged

50 of 64 configurations are never observed, so limited diversity is 0.78. The
parsimonious and intermediate solutions consume counterfactuals about
configurations that do not exist in the data. Separately, the outcome is
calibrated from the composite, and the composite is a weighted sum of four of
the six conditions. Both are declared, neither is fixed.

### 2.6 The percolation is not connected to any axis

The result is city-level. No state-level fragility score was derived, and
nothing was wired into CSE or into a new axis. The country rollup exists only
inside the variant probe. This is the single highest-value piece of remaining
work, because it is the one externally grounded quantity in the corpus.

### 2.7 The EDA test is a floor, not a broker

Kafka and Confluent are JVM services and were not installable under the
available RAM. What was measured is the in-process dispatch floor, +25.1 percent
over a direct call, plus the arrival rates, which are the decisive term. A real
broker adds network, serialisation, partitioning and consumer-group
coordination on top. Since the recommendation is against adoption, the missing
broker test does not change the conclusion; if the answer had been marginal it
would.

### 2.8 The agentic compliance loop was not exercised

SCOUT, SENTINEL and COUNSEL were not run. `SENTINEL doctrine_audit` was not run
over the new documents, and the acceptance battery was not run. Four repository
gates passed (`verify_index`, `verify_chain`, `verify_release`,
`verify_vintage_pairing`), which is not the same thing. The operating guideline
asks for the agent battery before closing a session and it was skipped under
time pressure.

### 2.9 Repository hygiene was requested and not done

Asked for: clean GitHub, Vercel and the dashboard. Delivered: one security fix.
Still present in the working tree or the repo:

- `operationalize_sources.py` declares EMODnet, Ember and ENTSO-E ACTIVE with
  `spatial_checksum_validation`, and validates nothing. It hashes the string
  literal `b"v9.0_sources_operationalized"` and returns a fixed ledger. This is
  compliance theatre and should be deleted or made real. Given this session
  proved EMODnet is *not* reproducible, a file asserting it is operational is
  actively misleading.
- `dummy.ts`, `horizon_endpoint = http127.0.0.1800.txt`, `mcp_payload.json`,
  `locate_db.py`, `locate_json.py` and six one-off `agent_*.py` scripts.
- `scripts/fsqca_runner.py` is an 8-line pytest wrapper whose name implies it
  runs fsQCA. It does not. `scripts/fsqca_equifinality.py` is the real one now.
- The dashboard reflects none of this session's results.

### 2.10 Security note

`database_string.txt` was untracked and unignored, 113 bytes, carrying a
connection-string pattern. Nothing leaked: it appears in no commit. It is
ignored as of `c092cc3`. **The credential in it should still be rotated**, on
the principle that a secret which has sat unignored in a working tree is a
secret of unknown exposure.

---

## Part 3. Recommended order for the next session

1. Rotate the credential in `database_string.txt`.
2. Decide `SAU`, then `FRA`, `NOR`, `USA` on CSE_EMO. This is the live defect.
3. Delete or rewrite `operationalize_sources.py`.
4. Derive a state-level fragility score from the percolation and wire it in.
   Highest analytical value, and externally grounded.
5. Cut v8.6: promote Ember, publish the equifinality solutions with the probe
   attached, reseal, append the chain, re-attest.
6. Run the agent battery and `SENTINEL doctrine_audit` over everything new.
7. Repository hygiene and the dashboard.

Phase 3 and the ROG automation are not blocked by any of this, but they should
not start before item 2 is closed. Building a digital twin on top of a published
value that has no source is how the v8.0 composite failure happened.
