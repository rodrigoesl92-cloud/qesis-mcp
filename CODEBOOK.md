# QESIS+ v8.0 Codebook
**Axes (0–100 stress):** WSE Aqueduct 4.0 baseline/SSP3 · CSE 0.6·EMODnet density + 0.4·cable
registry · REE USGS/CRMA · FPE foreign platform market share · ODI hyperscaler concentration ·
CRD foreign-cloud AI workload share · ESE = 0.40·Grid(log SAIDI 0.05–250h) + 0.30·Carbon
(20–700 gCO2/kWh) + 0.30·Cost (0.03–0.30 USD/kWh ex-tax).
**BIG:** coverage ≥0.75 → DORM (rankable); <0.75 → EPIS (published gap, never imputed); INFR
under data opacity. **Coupling:** ρ=C/6 trace-normalised; CR = 1−S(ρ)/ln 6. **Fidelity:**
Bhattacharyya between trace-normalised stress distributions vs anchors (WSE 10, CSE 10, REE 40,
FPE 30, ODI/ESE P10). **fsQCA:** 6 conditions → HIGH_SOV_VULN, n=35, freq≥1, incl≥0.80,
conservative solution, Quine–McCluskey; outcome anchors 80/55/30 with anti-circularity test.

## fsQCA condition source variables (added 2026-08-27, D-118 rule 8)

Two of the six conditions are derived rather than taken from an axis, and until
this entry neither source variable carried a served definition. Both are stated
here from the resource that produces them, not from the field name.

**`GCI_2024`** is the **ITU Global Cybersecurity Index 2024**, fifth edition. It
scores state level legal, technical and organisational cybersecurity commitments
out of 100. The condition is `GCI_inv = 100 - GCI_2024`, the remaining
commitment gap. Read the values before reading the label: a large tier of states
sits at exactly 100.0, including Indonesia, Qatar and the United Arab Emirates,
while Switzerland is 91.3, Austria 89.1, New Zealand 82.6 and Chile 70.2. That
ordering is a cybersecurity commitment index and is not any connectivity index.
Coverage 33 of 35.

**`EFF_SOV_EXT`** is **Effective Sovereignty, Extended**, a jurisdictional and
key sovereignty measure over cloud infrastructure, on a 0 to 1 scale. Source:
`v8_key_eff_sovereignty_35` in `_DATABASE/qesis.sqlite`, exported to
`v8_qesis_country_scores.csv` column `eff_sov_ext` and read by
`scripts/build_index.py`. Reproduces the served value for all 35 states with
zero mismatches.

```
EFF_SOVEREIGNTY_EXT = mean(KEY_SOVEREIGNTY_norm, SC_INTEGRITY,
                           RESOURCE_SOV, RESTORATION_SOV, CP_JX_AVG)
KEY_SOVEREIGNTY_norm = mean(SC_INTEGRITY, RESOURCE_SOV, RESTORATION_SOV)
CP_JX_AVG            = mean(CP_CONTRACT, CP_DATA_RES, CP_LE_REQ,
                            CP_INFRA_PM, CP_PRIV_ACC)
```

Method: jurisdictional tier approach over eight tiers, A-EU (GDPR and NIS2 full
compliance), B-5E (Five Eyes, CLOUD Act extraterritorial risk), B-NA (NATO
aligned, non-EU and non-5E), C-HY (hybrid and emerging democracies), D-BR and
D-EM (BRICS and developing), D-AS (advanced city state), E-AU (autocratic, state
controlled), E-SI (special status, sovereignty in question). Internal gate PASS
at 0.85 or above, which 4 of 35 states reach.

**Evidence status is part of the definition.** 5 of 35 are COLLECTED from the
pilot audit (DEU, ESP, USA, BRA, SGP); the other 30 are INFERRED via regulatory
framework assessment and contract proxies. Any claim resting on this condition
carries that split.

The condition is `ESC_inv = 100 * (1 - EFF_SOV_EXT)`, the share of effective
sovereignty a state does not hold.

**Consequence for the trilemma mapping.** The served `trilemma_status` statement
records that dropping `ESC_inv` emptied the second condition under Ecological
Sustainability. `EFF_SOV_EXT` measures jurisdictional control over cloud
infrastructure, not an ecological quantity, so that corner assignment was wrong
on its own terms. The decomposition failed for a reason the definition now makes
plain, which strengthens rather than weakens the finding that the constraint is
an interpretive overlay and takes no part in the model.

**Not an aggregate of the axes, tested.** A least squares fit of `EFF_SOV_EXT`
on WSE and REE over 32 complete states returns R squared 0.5104 with a largest
residual of 0.2011 on a variable whose whole range is 0.35 to 0.87. Hong Kong,
Singapore and Taiwan carry no WSE and share one REE value of 63.1, yet carry
0.35333, 0.75267 and 0.62467. The correlation with WSE is a development level
artefact, not a construction.
