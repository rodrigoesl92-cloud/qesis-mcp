#!/usr/bin/env python3
"""Retrieval corpus licence gate. Scope decides, not the filename alone.

WHY THIS IS SCOPED AND NOT A FLAT REFUSE LIST
---------------------------------------------
Version 1.0 of this gate refused a file outright whenever its publisher restricted
redistribution, and refused anything whose licence was not enumerated. Both were
wrong and the error was COUNSEL's.

A copyright reservation governs reproduction and transmission. It does not govern
private reading. A local index that only the operator queries is reading with a
machine, not transmitting, and refusing it would forbid him from using material
publishers deliberately sent him through their own newsletters. That channel is
`PUBLISHER_NEWSLETTER` in the acquisition register, and SA-001 already settled the
reasoning for TeleGeography: distributing to a list one invited the public to join
is an act of publication by the publisher.

What the reservation does still govern is handing the text onward. So:

    academic_citation  default ADMIT    citing a figure, publishing a derived statistic
    private_analysis   default ADMIT    the operator's own corpus, nothing leaves
    served_verbatim    default REFUSE   handing substantial source text to a third party

Only the last one restricts anything, because it is the only act a redistribution
reservation actually reaches. Citing a published figure with attribution, and
reporting statistics derived from it, is accepted and expected academic use and
needs no permission from anyone.

Usage
-----
    python scripts/verify_retrieval_corpus.py --scope academic_citation
    python scripts/verify_retrieval_corpus.py --scope private_analysis
    python scripts/verify_retrieval_corpus.py --scope served_verbatim --files a.pdf

Exit 0 every candidate is admissible in that scope. Exit 1 at least one is not.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO_ROOT, "scripts", "retrieval_manifest.json")
DEFAULT_CORPUS = os.path.join(REPO_ROOT, "Digital Twin R&D")
SCOPES = ("academic_citation", "private_analysis", "served_verbatim")


def classify(name: str, policy: dict, scope: str) -> tuple[str, dict | None]:
    """Quarantine wins outright. Otherwise first matching entry, then the scope default."""
    for entry in policy.get("sources", []):
        if fnmatch.fnmatch(name, entry["pattern"]):
            return entry.get(scope, "REFUSE"), entry
    return policy["scopes"][scope]["default"], None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scope", choices=SCOPES, default="served_verbatim",
                    help="which index is being built. Defaults to the strict one.")
    ap.add_argument("--corpus", default=None, help="directory of candidate files")
    ap.add_argument("--files", nargs="*", default=None, help="explicit candidate list")
    ap.add_argument("--manifest", default=MANIFEST)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    try:
        manifest = json.load(open(args.manifest, encoding="utf-8"))
    except FileNotFoundError:
        print(f"REFUSE: retrieval manifest absent at {args.manifest}", file=sys.stderr)
        return 1

    policy = manifest.get("corpus_policy")
    if not policy:
        print("REFUSE: the manifest declares no corpus_policy. An index whose corpus "
              "licence posture is undeclared may not be built.", file=sys.stderr)
        return 1
    if args.scope not in policy.get("scopes", {}):
        print(f"REFUSE: the manifest declares no scope '{args.scope}'. A scope that "
              "is not defined has no default and may not be assumed.", file=sys.stderr)
        return 1

    if args.files is not None:
        names = [os.path.basename(f) for f in args.files]
    else:
        corpus = args.corpus or DEFAULT_CORPUS
        if not os.path.isdir(corpus):
            print(f"REFUSE: corpus directory absent at {corpus}", file=sys.stderr)
            return 1
        names = sorted(f for f in os.listdir(corpus)
                       if os.path.isfile(os.path.join(corpus, f)))

    admitted, refused = [], []
    for name in names:
        verdict, entry = classify(name, policy, args.scope)
        (admitted if verdict == "ADMIT" else refused).append((name, verdict, entry))

    if not args.quiet:
        print(f"  scope: {args.scope}  "
              f"(default {policy['scopes'][args.scope]['default']})\n")
        for name, _verdict, entry in admitted:
            tag = f"[{entry['register_entry']}] " if entry else "[SA-008 pool] "
            lic = (entry or {}).get("licence", "")
            print(f"  ADMIT   {name}   {tag}{lic}")
        for name, _verdict, entry in refused:
            why = (entry.get("reason") if entry else
                   "no source entry, and this scope defaults to REFUSE")
            tag = f"[{entry['register_entry']}] " if entry else ""
            print(f"  REFUSE  {name}   {tag}{why}")
        print(f"\n  admitted {len(admitted)}   refused {len(refused)}   "
              f"of {len(names)} candidates")

    if refused:
        print(f"RETRIEVAL CORPUS GATE FAILED for scope '{args.scope}': a source whose "
              "verbatim text may not be handed onward was proposed for it.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
