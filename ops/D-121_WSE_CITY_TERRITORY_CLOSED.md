# D-121: the three withheld states stay withheld, and the question is closed

**Status:** DECIDED by ARCHITECT and ANALYST 2026-08-28 under the operator's standing
instruction to test it and decide it. **Closes:** the reopening of U-01 attempted
this evening. **Records:** L-213.

---

## 1. What was claimed, and by whom

The operator was told this evening that the absence of a water stress value for
Hong Kong, Singapore and Taiwan is an artefact of the Aqueduct country rollup,
which is keyed on GADM `gid_0`, and that the gridded baseline underneath it covers
those coordinates, so the value was unextracted rather than missing.

That claim was made by the agent, in prose, before the file had been opened. It is
false in both halves.

## 2. What the measurement returned

`Aqueduct40_baseline_annual_y2023.csv`, 202 MB, run in full.

| Quantity | Measured |
|---|---|
| Basin records in the file | 68,510 |
| Records carrying any country attribution | 9,850, which is 14.4 per cent |
| Records for Spain | 13, totalling 4.1 km² |
| Records for the Netherlands | 17, totalling 2,318 km² |
| Records for Hong Kong, Singapore, Taiwan | 2, 3 and 7 |
| Usable `bws_score` in any of those records | **zero. Every value is the -9999 sentinel** |

Spain's national area is roughly 500,000 km². The file attributes 4.1 of them.
The country attribution in this product is a sparse boundary-sliver overlay, not a
country rollup, and the slivers carry no data. **The file cannot produce a
country-level water stress figure for anybody, Spain included.**

## 3. Why this was caught before anything was published

The falsifier. It ran the identical extraction over two states whose published
values are known, both returned nothing, and it refused to render a verdict:

> No verdict. ESP, NLD produced no reconstruction, so nothing was compared. A
> control that yields nothing is not a control that agreed.

An earlier revision of that same falsifier computed the maximum of an empty list
as zero and printed a pass. Had that revision survived one more hour, three
imputed values would have entered a published composite on the strength of a
control that measured nothing. The repair is D-120 and the fixture that pins it.

## 4. The decision

**The three states stay withheld. The question is closed against Aqueduct 4.0.**

The instrument's original statement was correct: no WSE value exists at source for
these three. `U-01` already scoped it as permanent against the current source and
already named the only route that could reopen it, which is a different
water-stress source with city-territory resolution and its own territorial schema.
That would be a new axis input, not a gap fill.

**And that route is not taken, on L-044 grounds.** Price the service against the
failure it removes. It buys three small city-territories entering a ranking. It
costs a new source, a SCOUT intake, a SENTINEL gate, a new axis definition, and a
method asymmetry across the sample that a reviewer would attack anyway. The
absence is currently published with a per-state cause, distinguishing a
measurement limit from a territorial-schema one, and that publication is worth
more to the instrument than three imputed numbers would be.

## 5. What would reopen it

One thing only, and it is written down so the answer is testable rather than
merely preferred: an institutional client whose scope requires those three states
ranked, at which point the cost is charged to that engagement and the new axis is
declared as its own input with its own vintage. Nothing else reopens this, and in
particular no further attempt to mine Aqueduct 4.0 for a value it does not hold.

## 6. What is kept

`scripts/wse_city_territory.py` stays in the tree even though its hypothesis
failed. It is now the instrument that proves the absence rather than one that
argued about it: it reads the source, reports the attribution rate, separates a
missing key from a source with no value, and refuses a verdict without a
reproducing control. `data/axes/wse_city_territory_evidence.json` carries the run.
The next session that wonders whether the gap is real runs one command instead of
reasoning about it.
