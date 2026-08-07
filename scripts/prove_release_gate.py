"""Falsify the release gate: mutate one byte of a COPY and require rejection.

A gate that has only ever run against a correct artifact has not been shown to
reject anything, and an unfalsified gate is a claim rather than a check. This
runs the norms against a deliberately wrong artifact and fails the build if
either gate accepts it, or if either rejects the real one.

Two things this proof learned the hard way, both preserved here because the
first version got them wrong:

1. The mutation must leave valid JSON. Flipping a byte at the midpoint landed in
   JSON structure and verify_release.py "rejected" the copy with a
   JSONDecodeError. That is a gate exiting non-zero for the wrong reason: the
   parser caught it, not the norm. One hex character inside a quoted string is
   changed instead, and the copy is parsed here to prove it is well formed
   before either gate sees it.
2. The real artifact must still pass. A gate that rejects everything is not
   correct, it is broken in the safe direction, and only the second half of this
   proof can tell those apart.

The published index is never written to: mutating it is forbidden without a
RELEASES.json binding in the same commit. The copy is discarded either way, and
the original bytes are compared afterwards to prove it.

Usage:  python scripts/prove_release_gate.py
Exit:   0 both gates reject the mutation and accept the real artifact · 1 not
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REAL = ROOT / "data" / "qesis_v8.json"


def run(argv: list[str]) -> tuple[int, str]:
    p = subprocess.run([sys.executable] + argv, cwd=ROOT,
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    original = REAL.read_bytes()
    print(f"real index sha : {hashlib.sha256(original).hexdigest()}")

    tmpdir = Path(tempfile.mkdtemp(prefix="qesis_release_proof_"))
    copy = tmpdir / "qesis_v8.json"
    failures: list[str] = []
    try:
        text = original.decode("utf-8")
        m = (re.search(r'"sha256":\s*"([0-9a-f]{64})"', text)
             or re.search(r'"([0-9a-f]{64})"', text))
        if not m:
            print("PROOF FAILED: no hex string available to mutate safely")
            return 1
        start = m.start(1)
        old_ch = text[start]
        new_ch = "b" if old_ch != "b" else "c"
        copy.write_bytes((text[:start] + new_ch + text[start + 1:]).encode("utf-8"))

        json.loads(copy.read_text(encoding="utf-8"))   # must still parse
        mutated = copy.read_bytes()
        print(f"mutated one hex char at byte {start}: {old_ch!r} -> {new_ch!r}")
        print(f"mutated copy   : {hashlib.sha256(mutated).hexdigest()}")
        print(f"bytes differing: {sum(1 for a, b in zip(original, mutated) if a != b)}")
        print("still valid JSON: True\n")

        for name, argv in (
            ("verify_release.py", ["scripts/verify_release.py", "--index", str(copy)]),
            ("verify_chain.py",   ["scripts/verify_chain.py", "--index", str(copy)]),
        ):
            rc, out = run(argv)
            print(f"--- {name} vs mutated copy -> exit {rc}: "
                  f"{'REJECTED (correct)' if rc else 'ACCEPTED (GATE IS BLIND)'}")
            for line in out.splitlines():
                print(f"      {line}")
            print()
            if rc == 0:
                failures.append(f"{name} accepted a mutated index")
            elif "JSONDecodeError" in out or "Traceback" in out:
                failures.append(f"{name} rejected by crashing, not by the norm")

        for name, argv in (
            ("verify_release.py", ["scripts/verify_release.py"]),
            ("verify_chain.py",   ["scripts/verify_chain.py", "--quiet"]),
        ):
            rc, out = run(argv)
            print(f"--- {name} vs real index -> exit {rc}: {'PASS' if rc == 0 else 'FAIL'}")
            for line in out.splitlines():
                print(f"      {line}")
            if rc != 0:
                failures.append(f"{name} rejected the real index")
        print()
    finally:
        # Cleanup only. A `return` here would swallow any exception raised in the
        # body, including the one that would tell us why the proof aborted.
        if copy.exists():
            copy.unlink()
        if tmpdir.exists():
            tmpdir.rmdir()

    if REAL.read_bytes() != original:
        failures.append("the published index was modified by this proof")
    else:
        print("scratch copy discarded, published index unchanged: True")

    if failures:
        print("\nPROOF FAILED:")
        for f in failures:
            print(f"  x {f}")
        return 1
    print("\nPROOF PASSED: both gates reject a one-byte mutation on the norms, and "
          "accept the real artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
