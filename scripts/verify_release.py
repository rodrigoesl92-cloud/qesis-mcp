"""Refuses to let a published label point at new bytes, or a release go out
unattested. Run in CI on any diff touching data/.

N1  a published label is immutable. If the index changes under a label already
    bound in RELEASES.json, that is drift, and the fix is a new label or an
    erratum, never a repointed one.
N2  a released index must be attested. Its hash has to appear as an artifact
    binding in the committed chain spine, so a release cannot go out unbound to
    the record. Closed 2026-08-06 at chain seq 652; before that the chain
    recorded that actions happened and never which bytes were published.

The paths are arguments so the norms can be exercised against a copy. A gate
that can only ever be run against the real artifact cannot be shown to reject
anything, and an unfalsified gate is a claim rather than a check. Mutating the
published index to test it is not an option: it is forbidden without a
RELEASES.json binding in the same commit.

Usage:  python scripts/verify_release.py [--index PATH] [--releases PATH]
                                         [--spine PATH]
Exit:   0 release is bound and attested · 1 a norm is violated
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser()
ap.add_argument("--index", type=pathlib.Path, default=ROOT / "data" / "qesis_v8.json")
ap.add_argument("--releases", type=pathlib.Path, default=ROOT / "data" / "RELEASES.json")
ap.add_argument("--spine", type=pathlib.Path, default=ROOT / "data" / "chain_spine.jsonl")
args = ap.parse_args()

idx = args.index.read_bytes()
sha = hashlib.sha256(idx).hexdigest()
label = json.loads(idx)["vintage"]
lock = json.loads(args.releases.read_text(encoding="utf-8"))

# Parsed as fields, not searched as text. A substring hit anywhere in the file
# would satisfy a weaker claim than the one being made.
bindings = set()
for line in args.spine.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    a = json.loads(line).get("artifact_sha")
    if a:
        bindings.add(a)

fail = []
bound = lock.get(label)
if bound is None:
    fail.append(f"N1: label {label!r} has no RELEASES.json binding")
elif bound["artifact_sha"] != sha:
    fail.append(
        f"N1 VIOLATION: {label!r} is already bound to {bound['artifact_sha'][:12]}...\n"
        f"  index now hashes {sha[:12]}...\n"
        f"  A published label is immutable. Bump the label or file an erratum.")
if sha not in bindings:
    fail.append(
        f"N2 VIOLATION: {sha[:12]}... is absent from the {len(bindings)} artifact "
        f"binding(s) in the attestation chain")

for f in fail:
    print("FAIL  " + f)
if fail:
    sys.exit(1)
print(f"PASS  release {label} -> {sha[:12]}..., attested")
