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

**Note, unchanged by this patch:** the file still asserts
`ALL_SOURCES_OPERATIONAL` over a hardcoded dictionary and hashes a string
literal. It reads no data and performs no spatial join. It now runs; it does not
validate. Item 18 of the brief stands, and this file remains its only instance
in the repository.

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

## Not done, and deliberately

**Production still serves v8.5.** Per instruction, the pointer was not moved.

**v8.6 does not yet pass `verify_release`, and cannot.** That gate has two
conditions:

1. **N1** a `RELEASES.json` entry for the label whose `artifact_sha` equals the
   file hash. The binding record is printed by the reseal script and is not
   written by it.
2. **N2** the same SHA present as an `artifact_sha` in `data/chain_spine.jsonl`.

N2 is a chain append, which is an attestation act against the compliance chain
and re-dates `data/chain_attestation.json`. It is the step that makes a vintage
publishable, so it stays a human decision rather than something a fix-forward
branch does on its own authority.

**Sequence to switch production, when authorised:**

1. Append `d78f39f7964e...` to `data/chain_spine.jsonl`, re-run
   `scripts/verify_chain.py`, refresh `data/chain_attestation.json`.
2. Bind `v8.6 (2026-08-09)` in `data/RELEASES.json`, status `published`, and
   mark v8.5 superseded.
3. Promote `data/qesis_v8.6.json` to `data/qesis_v8.json`.
4. Re-run all four gates plus `verify_served_contract` and
   `verify_vintage_pairing`, then deploy.

**Also outstanding from the merge of PR #33:** the branch was named for a
`production-integrity-probe.yml` workflow that it never contained. That file is
still absent from `.github/workflows/`.
