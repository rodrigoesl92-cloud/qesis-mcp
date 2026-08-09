# v8.6 integrity patch: measured verification record

**Branch:** `fix/v86-integrity-patch` · **Base:** `6e46a5f` (merged PR #33) ·
**Date:** 2026-08-09

Fix-forward on three defects carried into `main` by PR #33. Production was not
touched and still serves v8.5. This is the measured record the standing rule
requires; it is a VERIFIER artifact, not a claim of done.

---

## Item 1: the crash

`scripts/operationalize_sources.py` was committed with
`datetime.now(datetime.UTC)` under `from datetime import datetime`, which binds
the class, not the module. It raised `AttributeError` and exited 1, so the
committed version had never been run.

Resolved to `from datetime import datetime, timezone` and
`datetime.now(timezone.utc)`.

```
$ python scripts/operationalize_sources.py
EXIT=0
"timestamp": "2026-08-09T03:31:14.008290+00:00"
```

**Superseded later in this branch:** fixing the crash made the file honest about
executing, not about validating. It still asserted `ALL_SOURCES_OPERATIONAL`
over a hardcoded dictionary and hashed a string literal, reading no data and
performing no spatial join. On Rico's instruction it was deleted outright rather
than repaired. See "Also in this branch" below.

## Item 2: the seal

The previous `v86_reseal.py` hashed `json.dumps(data, sort_keys=True)` and wrote
`json.dump(data, indent=4)`. `scripts/verify_release.py` hashes the index
**file**, so that seal could never have matched. Measured:

| Quantity | Value |
|---|---|
| Old printed attestation | `bd4283f97df4c5d3...` (hash of the sorted dump) |
| Old file as written | `27f8cea443c6d609...` |

Rewritten to write first and hash second, reading the bytes back off disk so the
attestation cannot drift from the artifact by construction.

```
attested   : d78f39f7964eb6f49a7be97311b772ec552c46c0b6e29050eb9b0c52ff874325
file sha256: d78f39f7964eb6f49a7be97311b772ec552c46c0b6e29050eb9b0c52ff874325
```

The second line was computed independently of the reseal script.

## Item 3: the metadata path

The brief asked for the correct nested path. There is no nested path: the QESIS
index has **no `metadata` key** and never has. `vintage` and `supersedes` sit at
the **root**, and the artifact SHA is not stored in the index at all, because a
hash of a file cannot live inside that file. It belongs in `data/RELEASES.json`,
keyed by the vintage label, which is what `verify_release.py` reads.

That is why the old `if "metadata" in data:` branch never fired and
`data/qesis_v8.6.json` shipped still declaring `"vintage": "v8.5 (2026-08-01)"`.

Now written at the root, and confirmed to have persisted to disk:

```
vintage v8.6 (2026-08-09)  supersedes v8.5 (2026-08-01)
```

A third defect was corrected while here: the file was written `indent=4` against
a repository convention of `indent=1, ensure_ascii=False` with no trailing
newline, verified against the bytes of `data/qesis_v8.json`. That reformatting
turned a three-line change into a 4,014-line diff.

| | old v8.6 | this v8.6 |
|---|---|---|
| Changed lines vs v8.5 | 4,014 | **9** |

## Item 4: gates, before any production switch

```
verify_index --json data/qesis_v8.6.json    21 checks, 0 failed, 0 warnings, GATE PASSED
                                            reports "v8.6 (2026-08-09), 35 states"
verify_chain                                654 entries, 0 link breaks, CHAIN CHECK PASSED
verify_index          (production v8.5)     21 checks, 0 failed, 0 warnings, GATE PASSED
verify_release        (production v8.5)     PASS  v8.5 (2026-08-01) -> f2a29747d6f2..., attested
```

Substantive check across all 35 states:

```
axis/composite changes: 0
fsqca block identical:  True
coupling identical:     True
withholding identical:  True
```

SAU, the only changed cell:

```
before  {"EMODnet": 94.3, "SubmarineMap": 19.4, "rule": "0.6*EMO + 0.4*SCM; non-EU = SCM"}
after   {"SubmarineMap": 19.4, "ITU_SCM_proxy": 94.3,
         "rule": "0.6*ITU_SCM_proxy + 0.4*SubmarineMap", "provenance_note": "D-108 ..."}
CSE 64.3   composite 75.6   unchanged
```

---

## Attestation act, authorised 2026-08-09

Rico authorised binding the v8.6 artifact. Executed via
`scripts/append_chain_entry.py`, which restates the link rule from its
documented definition rather than importing it from `verify_chain.py`, on the
same reasoning `verify_chain` gives for restating it: two independent
restatements that agree are evidence, one shared import that agrees with itself
is not.

```
prev  seq 654  entry_hash 6552ba782217dbb4
new   seq 655  entry_hash 3fd13431c16455ce
      artifact d78f39f7964eb6f4  at 2026-08-09T03:46:06Z
```

`input_hash` is the v8.5 artifact and `output_hash` the v8.6 artifact, which is
the reseal expressed as a transformation. The script refuses a duplicate
artifact binding and refuses any digest that is not lowercase sha256 hex.

Gates after the append:

```
verify_chain                                655 entries, 0 link breaks, PASSED
                                            head 3fd13431c16455ce
verify_release  --index data/qesis_v8.6.json  PASS  v8.6 (2026-08-09) -> d78f39f7964e..., attested
verify_release  (production v8.5)             PASS  v8.5 (2026-08-01) -> f2a29747d6f2..., attested
verify_chain    --index data/qesis_v8.6.json  RC=0  (C5 satisfied)
```

`data/RELEASES.json` binds v8.6 with **status `candidate`**, not `published`.
v8.5 remains `published`. Attested and bound is not the same as served, and the
pointer has not moved.

### One thing to reconcile

`verify_chain.py` documents the spine as an export of the live append-only log
in sovereign-infra, and C5's own failure text names
`sovereign-infra/scripts/bind_release.py` as the binding path. Appending here
makes the export lead its source by one entry. `data/chain_attestation.json`
now records this explicitly under `appended_outside_sovereign_infra`, with the
sequence number and the reconciliation instruction. **Replay seq 655 into the
sovereign-infra log before the next export**, or that export will overwrite the
spine and the chain will regress by one entry.

## Also in this branch

**`scripts/operationalize_sources.py` deleted.** It asserted
`ALL_SOURCES_OPERATIONAL` over a hardcoded dictionary, hashed a string literal,
read no data and performed no spatial join, while this session measured EMODnet
as not reproducible. Nothing in the codebase imported it; the only references
were prose in `ops/` and one entry in `.claude/settings.local.json`. Item 18 is
closed by removal.

**`.github/workflows/production-integrity-probe.yml` created.** The workflow
PR #33 was named for and never carried. It is not a stub that exits 0: it runs
the four committed-artifact gates, gates every candidate vintage in `data/`,
and compares the served endpoint's vintage, index hash and chain status against
the committed index. An unreachable endpoint warns and passes; a disagreeing one
fails. Those are different findings and the workflow treats them differently.

## Still not done

**Production still serves v8.5.** The pointer was not moved. To switch:
promote `data/qesis_v8.6.json` to `data/qesis_v8.json`, flip the RELEASES
statuses, re-run all gates plus `verify_served_contract`, deploy.
