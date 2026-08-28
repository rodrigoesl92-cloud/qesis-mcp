"""Recompute the Art. 12 hash chain from the committed spine.

The served integrity endpoint reports `604 entries, 0 link breaks`. Before C-01 that
number came from the runtime that appends to the chain, so nothing a reader could reach
would ever contradict it. This is what makes it contradictable.

Reads ONLY committed artefacts: data/chain_spine.jsonl and data/chain_attestation.json.
No database, no network, no OneDrive. It recomputes every link from the spine and fails
if the attestation does not follow from it, so editing the headline numbers by hand
breaks the build instead of the truth.

The spine is exported by the verifier in sovereign-infra, which reads the live
append-only log. This side never sees that log and does not need to: a chain whose
links recompute from its own published hashes is checkable by anyone.

Usage:  python scripts/verify_chain.py [--spine PATH] [--attestation PATH] [--quiet]
Exit:   0 attestation reproduces · 1 it does not · 2 could not check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENESIS = "0" * 64

# Restated from its documented definition, exactly as on the producing side, and
# imported from neither. Two independent restatements that agree are evidence;
# one shared import that agrees with itself is not.
LINK_RULE = "sha256(prev_hash | input_hash | output_hash | timestamp)"


def link(prev: str, input_hash: str, output_hash: str, timestamp: str) -> str:
    return hashlib.sha256(
        f"{prev}|{input_hash}|{output_hash}|{timestamp}".encode("utf-8")
    ).hexdigest()


def diagnose_binding(local_sha: str, bound: set) -> tuple:
    """Which of three situations an unbound index actually is, and say which.

    D-118 rule 8: the label is part of the claim. This check's message called
    `data/qesis_v8.json` on disk "the served index" and it is nothing of the
    kind, it is a local file. On 2026-08-28 that wording sent the diagnosis
    straight at the deployment while the real cause was a working file mutated
    by a gate that proves it can fail and was killed inside its own restore
    window (L-187, and L-200 when it happened a second time). The gate was
    right and its sentence was wrong, which costs exactly as much.
    """
    if local_sha in bound:
        return "BOUND", "the index on this disk is attested in the spine"
    if not bound:
        return "NO_BINDINGS", ("the spine carries no artifact binding at all. "
                               "Bind the release with "
                               "sovereign-infra/scripts/bind_release.py.")
    return "UNBOUND", (
        f"the index ON THIS DISK, {local_sha[:12]}..., is absent from the "
        f"{len(bound)} artifact binding(s) in the spine. Before reading this as a "
        f"release defect, run `git status data/qesis_v8.json`: if it is modified, "
        f"the file is what drifted and not the deployment, and `git checkout --` "
        f"restores it (L-187, L-200). If it is clean, this is a genuinely unbound "
        f"artefact: bind it with sovereign-infra/scripts/bind_release.py, then "
        f"re-export.")


def selftest() -> int:
    """V-2 for diagnose_binding: one it must accept, and the two it must refuse,
    including the exact shape of the 2026-08-28 failure."""
    cases = [
        ("a bound index is accepted",
         diagnose_binding("8009815e4c19", {"8009815e4c19", "x"})[0] == "BOUND"),
        ("an unbound index is refused",
         diagnose_binding("bbfc66a7594f", {"8009815e4c19"})[0] == "UNBOUND"),
        ("the refusal sends the reader to git status before the deployment",
         "git status" in diagnose_binding("bbfc66a7594f", {"8009815e4c19"})[1]),
        ("the refusal does not call a local file the served index",
         "served" not in diagnose_binding("bbfc66a7594f", {"8009815e4c19"})[1]),
        ("an empty binding set is named as such",
         diagnose_binding("a", set())[0] == "NO_BINDINGS"),
    ]
    ok = sum(1 for _, good in cases if good)
    for label, good in cases:
        print(f"{'PASS' if good else 'FAIL'}  chain: {label}")
    print(f"{ok}/{len(cases)} chain diagnosis behaviours hold")
    return 0 if ok == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", type=Path, default=ROOT / "data" / "chain_spine.jsonl")
    ap.add_argument("--attestation", type=Path,
                    default=ROOT / "data" / "chain_attestation.json")
    ap.add_argument("--index", type=Path, default=ROOT / "data" / "qesis_v8.json",
                    help="the served index, which must be attested by the spine. "
                         "Point it at a copy to exercise C5 without touching the "
                         "published artifact.")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    say = (lambda *a: None) if args.quiet else print

    for p in (args.spine, args.attestation):
        if not p.exists():
            print(f"CHAIN CHECK FAILED: {p.name} is missing. The integrity endpoint "
                  f"publishes a chain figure; without this artefact it would be "
                  f"publishing it unverified.", file=sys.stderr)
            return 2

    att = json.loads(args.attestation.read_text(encoding="utf-8"))
    rows = [json.loads(l) for l in args.spine.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not rows:
        print("CHAIN CHECK FAILED: the spine is empty.", file=sys.stderr)
        return 2

    failures: list[str] = []

    # ── 1. sequence is dense and ordered ────────────────────────────────
    # A chain with a hole in it can still have every remaining link recompute.
    # Deleting an entry and repointing its neighbour is the tampering this
    # catches, and only the seq column catches it.
    expected_seq = list(range(rows[0]["seq"], rows[0]["seq"] + len(rows)))
    if [r["seq"] for r in rows] != expected_seq:
        gaps = sorted(set(expected_seq) - {r["seq"] for r in rows})
        failures.append(f"C1 spine seq is not dense and ascending: "
                        f"{len(gaps)} missing, first {gaps[:5]}")

    # ── 2. every link recomputes ────────────────────────────────────────
    breaks, prev = [], GENESIS
    for r in rows:
        if r["prev_hash"] != prev:
            breaks.append(f"seq {r['seq']} prev_hash does not match the preceding entry")
        if r["entry_hash"] != link(prev, r["input_hash"], r["output_hash"], r["timestamp"]):
            breaks.append(f"seq {r['seq']} entry_hash does not recompute from its inputs")
        prev = r["entry_hash"]
    if breaks:
        failures.append(f"C2 {len(breaks)} link breaks: {'; '.join(breaks[:4])}")

    # ── 3. the attestation follows from the spine ───────────────────────
    recomputed = {
        "entries": len(rows),
        "link_breaks": len(breaks),
        "head_sha256": rows[-1]["entry_hash"],
        "genesis_sha256": rows[0]["entry_hash"],
    }
    for k, v in recomputed.items():
        if att.get(k) != v:
            failures.append(f"C3 attestation {k}={att.get(k)!r} but the spine gives {v!r}")

    # ── 4. the attestation says who verified it and from what ───────────
    if not att.get("verifier"):
        failures.append("C4 attestation names no verifier")
    if att.get("link_rule") not in (None, LINK_RULE):
        failures.append(f"C4 attestation declares link rule {att['link_rule']!r}, "
                        f"this check implements {LINK_RULE!r}")
    if not att.get("verified_at_utc"):
        failures.append("C4 attestation carries no verification timestamp")

    # ── 5. the served index must be attested by the chain (norm N2) ─────
    # Until 2026-08-06 the chain recorded that actions happened and never which
    # bytes were published, so a release could be entirely unattested and every
    # gate would still be green. Matched as a parsed field rather than as a
    # substring of the file: a substring match would also be satisfied by the
    # hash appearing in any other position, which is a weaker claim than the one
    # being made here.
    if args.index.exists():
        served = hashlib.sha256(args.index.read_bytes()).hexdigest()
        bound = {r["artifact_sha"] for r in rows if r.get("artifact_sha")}
        verdict, sentence = diagnose_binding(served, bound)
        if verdict != "BOUND":
            failures.append(f"C5 {sentence}")
    else:
        failures.append(f"C5 cannot check attestation: {args.index.name} is missing")

    say(f"chain spine: {len(rows)} entries, {len(breaks)} link breaks")
    say(f"  genesis {recomputed['genesis_sha256'][:16]}  "
        f"head {recomputed['head_sha256'][:16]}")
    say(f"  attested {att.get('verified_at_utc')} by {att.get('verifier')}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for f in failures:
            print(f"  x {f}", file=sys.stderr)
        print("\nCHAIN CHECK FAILED. The served chain figure does not follow from "
              "the committed spine. Do not deploy.", file=sys.stderr)
        return 1
    say("\nCHAIN CHECK PASSED: the attestation reproduces from the committed spine.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:                                       # noqa: BLE001
        print(f"CHAIN CHECK FAILED: {type(exc).__name__}: {exc}. Treat the chain "
              f"as unverified.", file=sys.stderr)
        raise SystemExit(2)
