"""Refuses a tracked configuration file that names a path ops/PATH_REGISTRY.json
declares a decoy.

L-209. The registry has recorded the empty sovereign-infra stub as a decoy since
L-143, and nothing read the registry back against the files that carry paths. A
registry consulted only by readers is documentation; a registry consulted by a
gate is a control.

The assessment is a pure function over (decoys, config text) so it can be shown
to refuse and to accept without touching the real tree. An unfalsified gate is a
claim rather than a check (V-2).

Usage:  python scripts/verify_config_paths.py [--selftest]
Exit:   0 no tracked config names a decoy - 1 at least one does
"""
from __future__ import annotations
import argparse, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIGS = [".mcp.json", "vercel.json", "docker-compose.yml", ".claude/launch.json"]


def decoy_paths(registry: dict) -> list[str]:
    out = []
    for entry in (registry.get("canonical") or {}).values():
        for d in entry.get("decoys") or []:
            if d.get("path"):
                out.append(d["path"])
    return out


def normalise(p: str) -> str:
    return re.sub(r"[\\/]+", "/", p).rstrip("/").lower()


def assess(decoys: list[str], texts: dict[str, str]) -> list[str]:
    """Return one finding per (file, decoy) hit. Pure, so it is testable."""
    findings = []
    norm = {normalise(d): d for d in decoys}
    for name, text in texts.items():
        flat = normalise(text.replace("\\\\", "\\"))
        for nd, original in norm.items():
            if nd and nd in flat:
                findings.append(
                    f"{name} names {original}, which ops/PATH_REGISTRY.json "
                    f"declares a decoy. The canonical path is in the registry."
                )
    return findings


def selftest() -> int:
    decoys = ["C:\\Users\\Lenovo\\sovereign-infra"]
    must_refuse = {"bad.json": '{"cwd": "C:\\\\Users\\\\Lenovo\\\\sovereign-infra"}'}
    must_accept = {"good.json": '{"cwd": "C:\\\\Users\\\\Lenovo\\\\OneDrive\\\\sovereign-infra"}'}
    ok = True
    if not assess(decoys, must_refuse):
        print("  x FIXTURE 1 FAILED: a config naming the decoy was accepted"); ok = False
    if assess(decoys, must_accept):
        print("  x FIXTURE 2 FAILED: the canonical path was refused"); ok = False
    print(f"CONFIG PATH SELFTEST: {'PASSED, 2 fixtures' if ok else 'FAILED'}")
    return 0 if ok else 1


ap = argparse.ArgumentParser()
ap.add_argument("--selftest", action="store_true")
args = ap.parse_args()
if args.selftest:
    raise SystemExit(selftest())

reg = json.loads((ROOT / "ops" / "PATH_REGISTRY.json").read_text(encoding="utf-8"))
decoys = decoy_paths(reg)
texts = {}
for c in CONFIGS:
    f = ROOT / c
    if f.exists():
        texts[c] = f.read_text(encoding="utf-8", errors="replace")

print(f"{len(decoys)} declared decoy(s), {len(texts)} tracked config file(s) read")
findings = assess(decoys, texts)
for name in texts:
    hit = any(name in f for f in findings)
    print(f"  {'DECOY' if hit else 'OK   '} {name}")
if findings:
    print("\nCONFIG PATH CHECK FAILED")
    for f in findings:
        print(f"  x {f}")
    raise SystemExit(1)
print("\nCONFIG PATH CHECK PASSED: no tracked config names a declared decoy.")
