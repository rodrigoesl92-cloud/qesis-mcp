"""Mutation test for the integrity gate.

A gate is only worth its exit code if it fails when it should. This injects one
defect at a time into a copy of the served index and asserts the gate catches
it. The Singapore case is the v8.0 defect itself, replayed.

Usage:  python scripts/test_gate.py
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts" / "verify_index.py"
BASE = json.loads((ROOT / "data" / "qesis_v8.json").read_text(encoding="utf-8"))


def run_gate(doc) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
        p = fh.name
    try:
        r = subprocess.run([sys.executable, str(GATE), "--json", p, "--quiet"],
                           capture_output=True, text=True)
        return r.returncode, (r.stdout + r.stderr)
    finally:
        Path(p).unlink(missing_ok=True)


# ── mutations: (name, mutator, expected substring in failure output) ────────
def m_drift(d):
    """A composite silently disagrees with its own axes."""
    d["countries"]["DEU"]["composite"] = 99.9
    return d


def m_singapore(d):
    """The v8.0 defect: emit a number over a BIG-flagged axis."""
    sgp = d["countries"]["SGP"]
    sgp["composite"] = 1.7
    sgp["composite_status"] = "DORM"
    d["epis_findings"] = [e for e in d["epis_findings"] if e["iso3"] != "SGP"]
    return d


def m_inversion(d):
    """Dominance inverted without breaking arithmetic elsewhere."""
    # Axes come from the declared model, never a hardcoded list: v8.3 renamed
    # CRD to RGD and a literal list silently crashed this case instead of
    # exercising it. A self-test that cannot run proves less than no self-test.
    W = d["composite_model"]["weights"]
    for a in W:
        d["countries"]["GBR"]["axes"][a] = max(
            d["countries"]["GBR"]["axes"][a], d["countries"]["CHE"]["axes"][a])
    d["countries"]["GBR"]["composite"] = round(
        sum(W[a] * d["countries"]["GBR"]["axes"][a] for a in W), 1)
    d["countries"]["CHE"]["composite"] = d["countries"]["GBR"]["composite"] + 5.0
    return d


def m_weights(d):
    """Weights quietly stop summing to 1."""
    d["composite_model"]["weights"]["WSE"] = 0.40
    return d


def m_lineage(d):
    """Served rows can no longer be traced to a generation."""
    d["lineage"].pop("sources", None)
    return d


def m_silent_exclusion(d):
    """Coupling drops states without naming them."""
    d["coupling"].pop("excluded_from_global", None)
    return d


def m_citation(d):
    """A superseded citation returns to a public surface."""
    d["fidelity"]["citation"] = "Ontological Blind-Spots: Hybrid War..."
    return d


CASES = [
    ("composite drift (DEU)",        m_drift,            "R1.4"),
    ("Singapore: number over gap",   m_singapore,        "R1.5"),
    ("dominance inversion",          m_inversion,        "R1.7"),
    ("weights stop summing to 1",    m_weights,          "R1.3"),
    ("lineage sources removed",      m_lineage,          "R1.8"),
    ("unnamed coupling exclusions",  m_silent_exclusion, "R1.12"),
    ("superseded citation returns",  m_citation,         "R1.16"),
]


def check_idempotent() -> bool | None:
    """Two builds from the same sources must agree, timestamp aside.

    Guards a defect this build already had once: it read its carried-forward
    values from the file it writes, so the second run recorded v8.1 numbers as
    the superseded ones and erased the provenance of the defect it fixed.
    Returns None when the canonical sources are unreachable, as in CI.
    """
    builder = ROOT / "scripts" / "build_index.py"
    if not builder.exists():
        return None          # operator-only tool, absent from the public repo
    outs = []
    for _ in range(2):
        p = Path(tempfile.mktemp(suffix=".json"))
        r = subprocess.run([sys.executable, str(builder), "--out", str(p)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            if "required input missing" in (r.stdout + r.stderr):
                return None
            print(f"  build failed: {r.stdout[-300:]}{r.stderr[-300:]}")
            return False
        outs.append(json.loads(p.read_text(encoding="utf-8")))
        p.unlink(missing_ok=True)
    for o in outs:
        o.get("lineage", {}).pop("generated_at_utc", None)
    return outs[0] == outs[1]


def main() -> int:
    print("mutation test: the gate must FAIL on each injected defect\n")
    rc, out = run_gate(BASE)
    baseline = rc == 0
    print(f"  {'ok ' if baseline else 'X  '} baseline (unmutated) passes    "
          f"exit={rc}")
    passed = int(baseline)
    if not baseline:
        print(out)

    for name, mut, expect in CASES:
        rc, out = run_gate(mut(copy.deepcopy(BASE)))
        caught = rc != 0 and expect in out
        passed += caught
        status = "ok " if caught else "X  "
        why = "" if caught else (
            f"  <-- expected {expect}, exit={rc}"
            f"{' (gate passed!)' if rc == 0 else ''}")
        print(f"  {status} caught: {name:<30} [{expect}]{why}")

    idem = check_idempotent()
    total = len(CASES) + 1
    if idem is None:
        print("  ..  skipped: build idempotence "
              "(canonical sources unreachable from here)")
    else:
        total += 1
        passed += idem
        print(f"  {'ok ' if idem else 'X  '} build is idempotent "
              f"(two builds agree, timestamp aside)")

    print(f"\n{passed}/{total} gate behaviours verified")
    if passed != total:
        print("GATE IS NOT TRUSTWORTHY: it missed a defect it must catch.",
              file=sys.stderr)
        return 1
    print("Gate is trustworthy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
