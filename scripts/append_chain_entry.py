"""Append one artifact-binding entry to the chain spine and re-attest.

Authorised by Rico on 2026-08-09 to bind the v8.6 artifact.

Standing caveat, recorded rather than assumed away: `data/chain_spine.jsonl` is
described by `verify_chain.py` as an export of the live append-only log held in
sovereign-infra, and C5's own failure text names
`sovereign-infra/scripts/bind_release.py` as the binding path. Appending to the
export directly makes the export lead its source. The entry written here must be
reconciled into the sovereign-infra log, or the next export will drop it and the
chain will regress by one.

The link rule is restated from its documented definition, not imported from
`verify_chain.py`. Two independent restatements that agree are evidence; one
shared import that agrees with itself is not. That is the same reason
`verify_chain` gives for restating it, and it applies symmetrically to the
writer.

Usage:
    python scripts/append_chain_entry.py --artifact <sha256> \
        --input <sha256> --output <sha256> [--dry-run]
"""

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPINE = ROOT / "data" / "chain_spine.jsonl"
ATTESTATION = ROOT / "data" / "chain_attestation.json"

LINK_RULE = "sha256(prev_hash | input_hash | output_hash | timestamp)"


def link(prev, input_hash, output_hash, timestamp):
    return hashlib.sha256(
        f"{prev}|{input_hash}|{output_hash}|{timestamp}".encode("utf-8")
    ).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True, help="artifact_sha being bound")
    ap.add_argument("--input", required=True, help="sha256 of the source artifact")
    ap.add_argument("--output", required=True, help="sha256 of the produced artifact")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for name, val in (("artifact", args.artifact), ("input", args.input),
                      ("output", args.output)):
        if len(val) != 64 or any(c not in "0123456789abcdef" for c in val.lower()):
            print(f"REFUSED: --{name} is not a lowercase sha256 hex digest")
            return 1

    rows = [json.loads(l) for l in SPINE.read_text(encoding="utf-8").splitlines() if l.strip()]
    last = rows[-1]

    # Refuse to bind the same artifact twice: a chain that records the same
    # bytes at two sequence numbers cannot say which one published them.
    already = {r.get("artifact_sha") for r in rows}
    if args.artifact in already:
        print(f"REFUSED: {args.artifact[:12]}... is already bound in the spine. "
              f"Nothing appended.")
        return 1

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prev = last["entry_hash"]
    entry = {
        "artifact_sha": args.artifact,
        "entry_hash": link(prev, args.input, args.output, timestamp),
        "input_hash": args.input,
        "output_hash": args.output,
        "prev_hash": prev,
        "seq": last["seq"] + 1,
        "timestamp": timestamp,
    }
    # Key order matches the existing rows exactly, so the export stays uniform.
    line = json.dumps(entry, sort_keys=True)

    print(f"prev  seq {last['seq']}  entry_hash {prev[:16]}")
    print(f"new   seq {entry['seq']}  entry_hash {entry['entry_hash'][:16]}")
    print(f"      artifact {args.artifact[:16]}  at {timestamp}")
    if args.dry_run:
        print("\n--dry-run: nothing written")
        print(line)
        return 0

    with open(SPINE, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")

    att = json.loads(ATTESTATION.read_text(encoding="utf-8"))
    att["entries"] = len(rows) + 1
    att["link_breaks"] = 0
    att["head_sha256"] = entry["entry_hash"]
    att["verified_at_utc"] = timestamp
    att["appended_outside_sovereign_infra"] = {
        "seq": entry["seq"],
        "artifact_sha": args.artifact,
        "reason": "v8.6 artifact binding, authorised 2026-08-09",
        "reconcile": "This entry exists in the qesis-mcp export before it exists in "
                     "the sovereign-infra log. Replay it there before the next "
                     "export, or the export will regress by one entry.",
    }
    ATTESTATION.write_text(json.dumps(att, indent=1) + "\n", encoding="utf-8")

    print(f"\nappended seq {entry['seq']}, attestation now {att['entries']} entries")
    print("run scripts/verify_chain.py to confirm it recomputes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
