# D-103 status: the v8.5 fsQCA artefact

**2026-08-05. Recorded after an exhaustive search. Supersedes the account that the
artefact was lost.**

## Verdict

**The artefact exists.** It was not lost in a rebase, and it is not missing. It is
committed in the private `sovereign-infra` repository, it is reproducible from a
committed script, and its numbers are internally consistent with its own write-up.

Two things that were being conflated are separated here:

1. The **re-run** is done, committed, and verifiable.
2. The **release** of it as v8.5 has not happened. It is staged and unapplied, and
   applying it is a release decision with a human name against it.

Every fsQCA figure stays withdrawn. That conclusion is unchanged, but the reason is
not the one previously recorded. The figures are withdrawn because the re-run
**supersedes** them, not because no re-run exists.

## What was searched

Negative findings are only worth something if the search behind them is stated, so
here is the whole of it.

**Inside `qesis-mcp`:**

- Every object in the git object database, reachable **and** unreachable: 1,446
  packed plus 19 loose. Every tree object was expanded and every filename it has
  ever recorded was matched against `v85`, `v8.5`, `fsqca` and `stage`. This is
  strictly wider than the dangling-object search that was outstanding, and it
  supersedes it. `git fsck --full --dangling --unreachable` now reports nothing
  dangling, because fetching `origin/main` and tagging the prior local tip made
  those objects reachable again.
- Every blob in that database was scanned for the literal string
  `stage_v85_fsqca`. One blob matched: `data/sqlite/qesis_ops.sqlite`.
- The operational database, all 12 tables.
- `data/fsqca/`, which is empty.

**Outside `qesis-mcp`:** `sovereign-infra`, `qesis-mcp-archive`, `OneDrive`,
`OneDrive - ESIC`, `Documents`, `Desktop`, and `scripts`, recursively, by filename.

### What is not in this repository

`scripts/stage_v85_fsqca.py` has never existed here, in any commit, reachable or
not. That part of the earlier account is correct. The single trace of it in this
repository is a task title:

> **QT-0018** `a96522ac-e85a-4a38-8135-cbb86c8eebe2`, owner RICO, priority 1,
> created 2026-08-01T13:32:30Z, due 2026-08-04, origin `D-055,
> ops/REMEDIATION_v8.4.md section 4 item 7`.
> "Release v8.5: apply the staged D-103 fsQCA re-run (`scripts/stage_v85_fsqca.py
> --apply --by`), add the lineage row, pair the commits in both repos, confirm CI"
>
> **status: open. closed_at: null.** Also recorded in the Art. 12 log at seq 624.

The task was never closed. That is the correct record of what happened: the release
was queued and not performed. It was read as evidence that the *analysis* was
missing, which it never was.

The fsQCA tables in the operational database are empty and confirm the same split:
`qesis_core_fsqca_datasets` 0 rows, `qesis_core_fsqca_truth_tables` 0 rows,
`qesis_core_findings` 0 rows. The re-run was never written back to the warehouse.

## What was found, and where

All four files below are **tracked and clean against HEAD** in `sovereign-infra`.
Their 2026-08-03 modification times are a checkout artefact; the content is
byte-identical to what is committed.

| artefact | bytes | sha256 |
|---|---|---|
| `ops/analysis/D-103_fsqca_rerun.json` | 93,086 | `731825204c076a02e794b8dae748503165262ca48167967ff488327e6474f102` |
| `ops/analysis/2026-08-01_D-103_fsqca_rerun.md` | 6,364 | the write-up |
| `scripts/rerun_fsqca_d103.py` | 12,381 | produces the JSON |
| `scripts/stage_v85_fsqca.py` | 21,081 | stages the release |

Commits, both 2026-08-01:

- `0bae1c0` 15:31:40 +0200, "D-103: re-run the fsQCA, and section 4.5's necessity
  does not survive"
- `a071952` 19:28:16 +0200, "Necessity needs four numbers, and REE does not survive
  them", 782 insertions

Reproduce with `python scripts/rerun_fsqca_d103.py` in `sovereign-infra`.

### The staged release, untracked

`sovereign-infra/var/staged/v8.5/`, written 2026-08-01 19:27:27:

- `fsqca_block.json`, 25,949 bytes, sha256
  `6a7f31703bd431f9645e7fd7cb3f8ba5366c8f8d41eeeedfedccc5270a6210ed`
- `uncertainty_U-02.json`, 1,874 bytes
- `vintage_lineage_row.md`, 308 bytes
- `RELEASE_NOTES.md`, 1,452 bytes

The staging timestamp is 49 seconds **before** `a071952` was committed, which raised
the obvious question of whether the staged block predates the final necessity work
and is therefore stale. It does not. The staged block carries `necessity_gate`,
`necessity_gate_method` and `necessity_verdict`, which are exactly the keys
`a071952` added, and its solution statistics match the committed JSON. It was built
from the working tree seconds before that tree was committed. The staged block is
current with the committed artefact.

## What the re-run says

n=32. HKG, SGP and TWN are excluded rather than imputed, because they carry no
composite under BIG. Conservative solution only.

- Ten sufficient configurations, six terms surviving one absorption pass.
- Solution consistency **0.9048**, coverage **0.5807**.
- All five D-103 violations resolved under the primary calibration, which uses
  sample percentile anchors at 80/50/20.
- **Necessity: nothing clears the bar** of consistency 0.90 with coverage 0.60.
  WSE is closest at 0.790 consistency, 0.817 coverage.
- **REE returns 0.703.** The thesis section 4.5 headline is 0.916. RoN 0.577,
  coverage_N 0.576, and it scores 0.727 against the negated outcome. It does not
  survive re-derivation.
- The sensitivity run at fixed anchors 75/50/25 **fails check C**: REE goes
  near-constant, standard deviation 0.0985, and appears in every sufficient path.
  That is the v6.6 trivial-driver failure reappearing through a different condition.
  It is reported because it fails.

On Phase 1 exit criterion 5, the re-run's own write-up states: criterion 5 was met as
written by marking the chapter withdrawn, and the re-run being done means it is now
met in substance. It does **not** restore the thesis figures.

## The live defect this search exposed

The served index is v8.4 (2026-08-01), sha256
`b8a5b5ad56129ada80421a0f952d6bb5fb8bfa8e5c35460fb95413f8fbca920c`. It contradicts
itself on fsQCA.

Its `citation_concordance` marks both section 4.5 figures `"live": "withdrawn"`,
`"status": "withdrawn pending re-run"`, erratum D-103. Its `fsqca` block, which is
what `qesis_get_pathways` returns, still serves the superseded v6.6 values as live
data:

- `necessity: {"REE": 0.916}`, the exact figure the concordance calls withdrawn
- five pathways P1 to P5 with consistency, coverage and member states, at n=35
- `solution: {consistency 0.807, coverage 0.862}`

The withdrawal lives in a key a caller of `qesis_get_pathways` has no reason to read.
`recalibration_required` carries `status: PENDING` and an instruction not to cite
pathway membership from this vintage, which is the right warning in the wrong place:
it is a sibling field, not a property of the numbers themselves.

**Nothing in this repository was changed to fix that.** `data/qesis_v8.json` is under
a do-not-touch instruction, and amending a served vintage is a release decision, not
a repair. It is recorded here as the finding it is.

## What must happen next, and by whom

These are human decisions and are deliberately left open.

1. **Decide whether to release v8.5.** The block is staged and validated. Applying it
   requires `python scripts/stage_v85_fsqca.py --apply --by "<name>"` in
   `sovereign-infra`, then the lineage row, the paired commits in both repositories,
   and CI. That is QT-0018, still open and past its 2026-08-04 due date.
2. **Until then, do not cite any fsQCA figure from either vintage.** The v6.6
   figures are withdrawn and superseded. The v8.5 figures are computed but not
   published, and a staged result is not a released one.
3. **Do not wire the frontend to `getFsQCAMatrix()`.** It would read the v8.4 block,
   which serves the superseded numbers.
4. `var/staged/v8.5/` is untracked. Four artefacts that a release depends on exist
   only in one working tree on one machine.

## Sources not used

`OneDrive\Documents\INITIUM\Master IR & GE\Final Master Thesis\_DATABASE\csv_exports\v8_fsqca_truth_tables.csv`
was found during the search. It is dated 2026-07-27 and predates the re-run. It was
not opened, not used, and must not be used to reconstruct a v8.5 result. Neither was
any figure reconstructed from memory. Every number in this document was read from the
committed artefact.
