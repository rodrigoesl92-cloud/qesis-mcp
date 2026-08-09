"""Reseal the v8.6 index so the attested SHA is the SHA of the bytes on disk.

Three defects in the previous version, all measured:

  1. It hashed `json.dumps(data, sort_keys=True)` and then wrote
     `json.dump(data, indent=4)`. Two different serialisations, so the printed
     attestation certified bytes that were never saved. `scripts/verify_release.py`
     hashes the index FILE, so the old seal could never have matched it. The
     figure it printed, bd4283f9..., is the hash of the sorted dump; the file it
     wrote hashes to 27f8cea4....

  2. It wrote the vintage only `if "metadata" in data`. The QESIS index has no
     `metadata` key and never has: `vintage` and `supersedes` sit at the ROOT,
     and the artifact SHA is not stored in the index at all. It lives in
     `data/RELEASES.json`, keyed by the vintage label, because a hash of a file
     cannot be stored inside that file. So the branch never fired and
     `data/qesis_v8.6.json` still declared itself v8.5.

  3. It wrote `indent=4` against a repository convention of
     `indent=1, ensure_ascii=False` with no trailing newline. That reformats
     every line and buries a three-line substantive change inside a 4,000-line
     diff.

The fix is to write first and hash second, reading the bytes back off disk so
the attestation cannot drift from the artifact by construction.

This does NOT switch production. It writes `data/qesis_v8.6.json` and prints the
binding record. Appending to the chain spine and binding in RELEASES.json are
the acts that make a vintage publishable, and they stay a human step.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "data", "qesis_v8.json")
DST = os.path.join(ROOT, "data", "qesis_v8.6.json")

NEW_VINTAGE = "v8.6 (2026-08-09)"
PRIOR_VINTAGE = "v8.5 (2026-08-01)"

# Serialisation convention of the committed index, verified against the bytes of
# data/qesis_v8.json rather than assumed.
DUMP = dict(indent=1, ensure_ascii=False)


def patch_sau(node, log):
    """Relabel the SAU CSE component from EMODnet to the ITU proxy (D-108).

    Matched on the exact numeric signature so the walk cannot catch a different
    state. Idempotent: a node already carrying ITU_SCM_proxy is left alone.
    """
    if isinstance(node, dict):
        comp = node.get("cse_components")
        if isinstance(comp, dict):
            if comp.get("EMODnet") == 94.3 and comp.get("SubmarineMap") == 19.4:
                comp["ITU_SCM_proxy"] = comp.pop("EMODnet")
                comp["rule"] = "0.6*ITU_SCM_proxy + 0.4*SubmarineMap"
                comp["provenance_note"] = (
                    "D-108. The value is sourced from the ITU Submarine Cable Map used "
                    "as a Middle East proxy, not from EMODnet: the EMODnet HA release "
                    "20230628 contains zero geometry attributable to SAU and EMODnet's "
                    "remit is European seas. Relabel only; CSE and composite unchanged.")
                log.append("SAU: EMODnet -> ITU_SCM_proxy")
            elif "ITU_SCM_proxy" in comp and comp.get("SubmarineMap") == 19.4:
                log.append("SAU: already relabelled, left unchanged")
        for v in node.values():
            patch_sau(v, log)
    elif isinstance(node, list):
        for item in node:
            patch_sau(item, log)


def main():
    with open(SRC, "rb") as fh:
        raw = fh.read()
    data = json.loads(raw)
    src_sha = hashlib.sha256(raw).hexdigest()

    before = json.loads(json.dumps(data["countries"]["SAU"]["audit"]["cse_components"]))

    log = []
    patch_sau(data, log)
    if not log:
        print("ERROR: SAU signature not found. Nothing written.")
        return 1

    # Root-level, which is where this index actually keeps them.
    data["vintage"] = NEW_VINTAGE
    data["supersedes"] = PRIOR_VINTAGE

    # Write first.
    payload = json.dumps(data, **DUMP).encode("utf-8")
    with open(DST, "wb") as fh:
        fh.write(payload)

    # Hash second, from the file, not from the object in memory.
    with open(DST, "rb") as fh:
        on_disk = fh.read()
    artifact_sha = hashlib.sha256(on_disk).hexdigest()

    # Self-check: the gate reads the file, so reproduce what the gate will do.
    if hashlib.sha256(open(DST, "rb").read()).hexdigest() != artifact_sha:
        print("ERROR: hash is not stable across reads. Aborting.")
        return 1
    if json.loads(on_disk)["vintage"] != NEW_VINTAGE:
        print("ERROR: vintage did not persist to disk. Aborting.")
        return 1

    after = json.loads(on_disk)["countries"]["SAU"]["audit"]["cse_components"]
    sau = json.loads(on_disk)["countries"]["SAU"]

    binding = {
        NEW_VINTAGE: {
            "artifact_sha": artifact_sha,
            "bound_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "provenance": (
                "Provenance relabel of the SAU CSE component from EMODnet to the ITU "
                "Submarine Cable Map proxy under D-108. No axis, composite, coverage, "
                "coupling, CSovE, fsQCA or withholding value changed."),
            "status": "candidate",
            "supersedes": [PRIOR_VINTAGE],
        }
    }

    print(f"source  {os.path.basename(SRC)}  sha256 {src_sha[:12]}...")
    print(f"written {os.path.basename(DST)}  sha256 {artifact_sha[:12]}...  "
          f"{len(on_disk)} bytes")
    print(f"changes {'; '.join(log)}")
    print(f"vintage {json.loads(on_disk)['vintage']}  supersedes "
          f"{json.loads(on_disk)['supersedes']}")
    print()
    print(f"SAU before  {json.dumps(before)}")
    print(f"SAU after   {json.dumps(after)}")
    print(f"SAU CSE {sau['axes']['CSE']}  composite {sau['composite']}  "
          f"(unchanged by a relabel)")
    print()
    print("ATTESTED SHA-256 IS THE FILE SHA-256:")
    print(f"  {artifact_sha}")
    print()
    print("RELEASES.json binding record, NOT written by this script:")
    print(json.dumps(binding, indent=2))
    print()
    print("Remaining before production switch: append this artifact_sha to "
          "data/chain_spine.jsonl, bind in data/RELEASES.json, re-attest, then "
          "verify_release passes. Human step.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
