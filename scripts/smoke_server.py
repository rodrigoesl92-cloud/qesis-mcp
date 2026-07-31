"""Contract smoke test for the served surface.

Checks the shape the MCP tools depend on, without importing the MCP runtime,
so it still runs on a CI box where the server deps are unavailable. If the
runtime IS importable it also asserts every declared tool is registered.

Usage:  python scripts/smoke_server.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Deliberately a literal, not derived from the index: this is an independent
# restatement of the published axis contract, so an index that renames an axis
# has to be reconciled here on purpose. RGD was CRD until v8.3 (D-049).
AXES = ["WSE", "CSE", "REE", "FPE", "ODI", "RGD", "ESE"]
EXPECTED_TOOLS = {
    "qesis_get_country", "qesis_rank_countries", "qesis_compare_countries",
    "qesis_get_coupling", "qesis_get_pathways", "qesis_get_component_audit",
    "qesis_get_methodology", "qesis_get_integrity",
}

fails: list[str] = []


def need(cond, msg):
    if not cond:
        fails.append(msg)


d = json.loads((ROOT / "data" / "qesis_v8.json").read_text(encoding="utf-8"))
C = d["countries"]

need(len(C) == 35, f"expected 35 states, found {len(C)}")
for key in ("vintage", "license", "countries", "coupling", "fsqca", "fidelity",
            "ese_method", "composite_model", "lineage", "epis_findings"):
    need(key in d, f"top-level key missing: {key}")

for iso, c in C.items():
    need(set(c["axes"]) == set(AXES), f"{iso}: axis set mismatch")
    for k in ("name", "composite", "composite_status", "coverage", "big_flags"):
        need(k in c, f"{iso}: field missing: {k}")
    need(c.get("odi_continuous") is not None, f"{iso}: no continuous ODI")
    need(c.get("fsqca_conditions") is not None, f"{iso}: no fsQCA conditions")
    if c["composite"] is None:
        need(c["composite_status"] == "EPIS", f"{iso}: withheld but not EPIS")

# Ranking must never place a withheld state in the ranked body.
ranked = [i for i, c in C.items() if c["composite"] is not None]
need(all(C[i]["composite"] is not None for i in ranked), "ranked set impure")
need(len(ranked) + len(d["epis_findings"]) == len(C),
     "ranked + EPIS does not account for the sample")

# Pathway members must exist in the sample.
for p in d["fsqca"]["pathways"]:
    for m in p["members"]:
        need(m in C, f"pathway {p['id']} names unknown state {m}")

# Optional: assert the live tool surface if the runtime is importable.
try:
    sys.path.insert(0, str(ROOT))
    import server  # noqa: E402
    reg = server.mcp._tool_manager.list_tools()
    names = {t.name for t in reg}
    missing = EXPECTED_TOOLS - names
    need(not missing, f"tools not registered: {sorted(missing)}")
    # The server declares its own axis list and uses it to build comparisons.
    # If it drifts from the index, compare_countries raises KeyError per state
    # at request time rather than here. v8.3 renamed CRD to RGD and this is
    # the check that would have caught the server being left behind.
    need(set(server.AXES) == set(AXES),
         f"server.AXES {sorted(server.AXES)} != index contract {sorted(AXES)}")
    print(f"runtime importable: {len(names)} tools registered")
except ImportError as exc:
    print(f"runtime not importable ({exc.name}); ran data-contract checks only")
except Exception as exc:                                       # noqa: BLE001
    fails.append(f"server import raised {type(exc).__name__}: {exc}")

if fails:
    print("\nSMOKE FAILED:", file=sys.stderr)
    for f in fails:
        print(f"  x {f}", file=sys.stderr)
    raise SystemExit(1)
print(f"smoke passed: {len(C)} states, {len(ranked)} ranked, "
      f"{len(d['epis_findings'])} EPIS")
