# D-108: SAU CSE_EMO provenance, ITU Submarine Cable Map proxy

**Raised:** 2026-08-08 · **Status:** RESOLVED IN PRINCIPLE, NOT YET APPLIED

## The finding

`SAU` publishes `CSE_EMO = 94.3`. The EMODnet HA Telecommunication Cables
release (`20230628`, SHA-256 aggregate `24f721a9bd04...`) contains zero geometry
attributable to Saudi Arabia, and EMODnet's geographic remit is European seas
under every product it publishes. Verified in
`data/axes/emodnet_cse_evidence.json`.

## The resolution Rico gave

The value derives from the **ITU Submarine Cable Map, used as a Middle East
proxy**, not from EMODnet. Declared in `operationalize_sources.py` on 2026-08-08
as source `"ITU Submarine Cable Map (Middle East Proxy)"`, method
`"verified_geospatial_api_pull"`.

This is a coherent resolution. Saudi Arabia is covered by ITU and TeleGeography
cable cartography, so a value is obtainable; the defect was never that 94.3 is
impossible, it was that the cell was labelled EMODnet when EMODnet cannot have
produced it.

## What remains, precisely

The resolution is a **relabelling**, and the label lives in the index, not in
the source-declaration script. As of this commit `data/qesis_v8.json` still
reads:

```json
"cse_components": {"EMODnet": 94.3, "SubmarineMap": 19.4,
                   "rule": "0.6*EMO + 0.4*SCM; non-EU = SCM"}
```

Two things follow and neither is closed by declaring the source active:

1. **The key is still `EMODnet`.** It must become a distinct key, for example
   `ITU_SCM_proxy`, with the composition rule amended to name which states use
   the proxy branch. Until then the index asserts an EMODnet provenance that the
   EMODnet release contradicts.

2. **The rule string contradicts itself for SAU.** It says `non-EU = SCM`, and
   Saudi Arabia is non-EU, so the declared rule returns `CSE = 19.4`. The
   published `CSE` is 64.3, which is `0.6*94.3 + 0.4*19.4`. The rule as written
   does not generate the published value.

Applying the relabel changes `data/qesis_v8.json`, therefore its SHA-256,
therefore the release attestation `f2a29747d6f2...` and the served contract. It
requires a v8.6 vintage: reseal, chain append, re-attest, redeploy. That is a
ten-minute operation done properly and a broken production surface done in
three, so it is recorded here rather than rushed.

**Numeric impact when applied:** none. Relabelling the provenance key does not
move `CSE = 64.3` or `composite = 75.6`. The rule-string correction is
presentational. No composite in the index changes, and no ranking moves.

## Note on `operationalize_sources.py`

The script declares four sources ACTIVE and performs no validation of any of
them. It builds a fixed dictionary and hashes a string literal. The EMODnet
entry now reads `strict_iso3_spatial_join_validation`; no spatial join is
executed anywhere in the file. The independent check that *did* run is
`scripts/ingest_emodnet.py`, and it returned NOT REPRODUCIBLE.

A declaration file is a useful register of intent. It is not evidence, and it
should not carry method names that describe procedures the code does not run,
because the next reader will believe them. Recommend either deleting it or
reducing it to a plain source register with the validating script named beside
each entry.

## Decision required

Apply the relabel and the rule-string correction as part of v8.6, alongside the
Ember promotion and the equifinality publication. Tracked in
`ops/SESSION_REPORT_2026-08-08.md` Part 3.
