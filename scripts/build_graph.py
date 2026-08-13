"""KG-1. Emit the graph the served index already contains.

D-110, 2026-08-13. No new data and no new method: every node and edge below is
read from data/qesis_v8.json. The graph exists to express what a weighted sum
structurally cannot, which is a CONJUNCTION. ODI and CSE both enter the composite
as addends, so a state single-sourced on both appears there only as two moderate
numbers added together. The graph intersects them instead.

Edges are typed with a declared domain and range. That is the point of the
exercise: JSON field names are an implicit ontological commitment, typed edges
are an explicit one. This is the ontology no longer pretending to be a schema.

Scope, and it travels with every use of this file (U-04):
  `n_providers` counts hyperscalers operating a region on the state's territory,
  weighted one unit per active cloud region, because availability-zone counts are
  missing for 27 of 35 states. SOLE_PROVIDER therefore means only one hyperscaler
  operates a region on that territory. It is jurisdictional single-sourcing and
  it is NOT a claim about where that state's workloads actually run.

Usage:  python scripts/build_graph.py [--check]
        --check verifies the emitted file matches a fresh build and exits
        non-zero if it does not. Wire it into CI beside build_eval --check.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "qesis_v8.json"
OUT = ROOT / "data" / "qesis_graph.json"

#: Declared domain and range per edge type. An edge whose endpoints do not match
#: its declaration is a build failure, not a warning. This table IS the ontology.
EDGE_SCHEMA = {
    "HOSTS_REGION_OF": ("State", "Provider"),
    "SOLE_PROVIDER": ("State", "Provider"),
    # PROVENANCE edge, not a physical one. v1 of this file typed dataset names as
    # infrastructure nodes, so "single cable source" read as "one cable route"
    # while meaning "one dataset supplied the value". A provenance edge wearing a
    # physical edge's clothes. Corrected 2026-08-13, D-110 rev B.
    "CSE_VALUE_SOURCED_FROM": ("State", "CableSourceDataset"),
    # The real cable plane, from data/axes/cse_percolation.json.
    "CHOKEPOINT_IN": ("LandingCity", "CableNetwork"),
    "COUPLED_WITH": ("Axis", "Axis"),
    "WITHHELD_UNDER": ("State", "WithholdingCause"),
    "SUPERSEDES": ("Vintage", "Vintage"),
}

NON_SOURCE_KEYS = {"rule", "provenance_note"}


def cable_sources(country: dict) -> list[str]:
    comp = (country.get("audit") or {}).get("cse_components") or {}
    return sorted(k for k in comp if k not in NON_SOURCE_KEYS and comp.get(k) is not None)


def build() -> dict:
    doc = json.loads(SRC.read_text(encoding="utf-8"))
    countries = doc["countries"]

    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def node(kind: str, nid: str, **attrs) -> None:
        if (kind, nid) in seen:
            return
        seen.add((kind, nid))
        nodes.append({"kind": kind, "id": nid, **attrs})

    def edge(etype: str, src: str, dst: str, **attrs) -> None:
        edges.append({"type": etype, "source": src, "target": dst, **attrs})

    for iso, c in sorted(countries.items()):
        node("State", iso, name=c["name"], composite=c.get("composite"),
             composite_status=c.get("composite_status"), coverage=c.get("coverage"),
             big_flags=c.get("big_flags") or [],
             csove_tier=(c.get("csove") or {}).get("tier"))

        oc = c.get("odi_continuous") or {}
        shares = oc.get("provider_shares") or {}
        for p, share in sorted(shares.items()):
            node("Provider", p)
            edge("HOSTS_REGION_OF", iso, p, share=share)
        if oc.get("n_providers") == 1 and shares:
            edge("SOLE_PROVIDER", iso, next(iter(shares)),
                 odi_hhi=oc.get("odi_hhi"), n_regions=oc.get("n_regions"))

        for s in cable_sources(c):
            node("CableSourceDataset", s)
            edge("CSE_VALUE_SOURCED_FROM", iso, s)

    # Axis coupling. Upper triangle only: the matrix is symmetric, so emitting
    # both directions would double every weight in any centrality computed on it.
    cg = (doc.get("coupling") or {}).get("global") or {}
    matrix = cg.get("matrix") or {}
    axes = cg.get("axes") or sorted(matrix)
    for a in axes:
        node("Axis", a)
    for i, a in enumerate(axes):
        for b in axes[i + 1:]:
            r = (matrix.get(a) or {}).get(b)
            if r is not None:
                edge("COUPLED_WITH", a, b, r=r)

    for f in doc.get("epis_findings") or []:
        cause = f["withholding_cause"]
        node("WithholdingCause", cause,
             statement=(doc.get("withholding_causes", {}).get("codes", {}) or {}).get(cause))
        edge("WITHHELD_UNDER", f["iso3"], cause, coverage=f["coverage"])

    node("Vintage", doc["vintage"])
    if doc.get("supersedes"):
        node("Vintage", doc["supersedes"])
        edge("SUPERSEDES", doc["vintage"], doc["supersedes"])

    # The real cable plane. PUB-1: this file is in the repo and not on the served
    # surface, which is exactly why v1 of this script missed it.
    perc = json.loads((ROOT / "data" / "axes" / "cse_percolation.json").read_text(encoding="utf-8"))
    hd, gr = perc["headline"], perc["graph"]
    node("CableNetwork", "SubmarineCableNetwork", cities=gr["cities"], cables=gr["cables"],
         edges_n=gr["edges"], components=gr["components"],
         baseline_lcc_cities=hd["baseline_lcc_cities"], source="scripts/percolation_cse.py")
    for cp in perc["top_chokepoints"]:
        node("LandingCity", cp["node"], city=cp["city"], country=cp["country"])
        edge("CHOKEPOINT_IN", cp["node"], "SubmarineCableNetwork",
             betweenness=cp["betweenness"], cables=cp["cables"],
             is_articulation=cp["is_articulation"])

    # The conjunction the composite cannot express. Provider concentration
    # intersected with physical chokepoint hosting. Both limbs are now physical.
    sole_p = {e["source"]: e["target"] for e in edges if e["type"] == "SOLE_PROVIDER"}
    chokepoint_countries = {cp["country"] for cp in perc["top_chokepoints"]}
    name_to_iso = {c["name"]: iso for iso, c in countries.items()}
    hosts_chokepoint = {name_to_iso[n] for n in chokepoint_countries if n in name_to_iso}
    conjunctive = sorted(set(sole_p) & hosts_chokepoint)

    by_source: dict[str, int] = {}
    for e in edges:
        if e["type"] == "CSE_VALUE_SOURCED_FROM":
            by_source[e["target"]] = by_source.get(e["target"], 0) + 1

    return {
        "vintage": doc["vintage"],
        "derived_from": {"file": "data/qesis_v8.json", "authority": "D-110"},
        "generator": "scripts/build_graph.py",
        "note": "Generated from the served index. Never hand-edited. No value is "
                "computed here that the index does not already publish.",
        "scope_statement": (
            "SOLE_PROVIDER means only one hyperscaler operates a cloud region on "
            "that state's territory, weighted one unit per active region because "
            "availability-zone counts are missing for 27 of 35 states (U-04). It "
            "is jurisdictional single-sourcing, not a claim about where that "
            "state's workloads run. This sentence travels with every use."),
        "edge_schema": {k: {"domain": v[0], "range": v[1]} for k, v in EDGE_SCHEMA.items()},
        "counts": {"nodes": len(nodes), "edges": len(edges),
                   "by_kind": {k: sum(1 for n in nodes if n["kind"] == k)
                               for k in sorted({n["kind"] for n in nodes})},
                   "by_edge_type": {t: sum(1 for e in edges if e["type"] == t)
                                    for t in sorted({e["type"] for e in edges})}},
        "findings": {
            "sole_provider_and_chokepoint_host": {
                "states": conjunctive,
                "n": len(conjunctive),
                "detail": [{"iso3": s, "provider": sole_p[s],
                            "composite": countries[s].get("composite")} for s in conjunctive],
                "statement": (
                    "Sole hyperscaler on territory AND host of a top-betweenness "
                    "cable landing city. The composite is a weighted sum and a sum "
                    "cannot represent a conjunction, so these states appear there "
                    "only as separate moderate addends. Both limbs are physical."),
                "falsifier": (
                    "A state entering this set whose composite already places it in "
                    "the high-exposure decile would show the composite is not blind "
                    "to conjunction, only coarse about it.")},
            "network_fragility": {
                "critical_node": hd["critical_node"],
                "tipping_point_removals": hd["tipping_point_removals"],
                "cities_severed_in_one_step": hd["cities_severed_in_one_step"],
                "targeted_at_13_removals": hd["targeted_at_13_removals"],
                "random_at_88_removals": hd["random_at_88_removals"],
                "statement": (
                    "Robust-yet-fragile, already computed and already audited in "
                    "data/axes/cse_percolation.json. Twelve targeted removals cost "
                    "31 cities. The thirteenth, Porthcurno, severs 278. This is the "
                    "cable finding. It is not a gap and it was never missing."),
                "source": "data/axes/cse_percolation.json, scripts/percolation_cse.py"},
            "cse_value_provenance": {
                "by_dataset": dict(sorted(by_source.items(), key=lambda x: -x[1])),
                "statement": (
                    "A PROVENANCE count, not an infrastructure one. The non-EU "
                    "SubmarineMap-only rule is a documented and audited disposition: "
                    "data/axes/emodnet_cse_evidence.json records EMODnet release "
                    "20230628 at coverage 0.3429 against the 0.75 BIG gate with "
                    "verdict NOT REPRODUCIBLE at rho -0.467. The disposition is in "
                    "the evidence plane. It is not an unrecorded single point of "
                    "failure and must not be presented as one."),
                "source": "data/axes/emodnet_cse_evidence.json"},
        },
        "nodes": nodes,
        "edges": edges,
    }


def validate(g: dict) -> list[str]:
    """Every gate owns one fixture it must refuse and one it must accept (V-2).
    Fixtures live in scripts/test_gate.py; this is the assertion they exercise."""
    kind = {n["id"]: n["kind"] for n in g["nodes"]}
    fails = []
    for e in g["edges"]:
        decl = EDGE_SCHEMA.get(e["type"])
        if decl is None:
            fails.append(f"undeclared edge type {e['type']}")
            continue
        dom, rng = decl
        if kind.get(e["source"]) != dom:
            fails.append(f"{e['type']}: source {e['source']} is "
                         f"{kind.get(e['source'])}, declared domain {dom}")
        if kind.get(e["target"]) != rng:
            fails.append(f"{e['type']}: target {e['target']} is "
                         f"{kind.get(e['target'])}, declared range {rng}")
    return fails


def main() -> int:
    g = build()
    fails = validate(g)
    if fails:
        print("GRAPH SCHEMA VIOLATIONS")
        for f in fails[:20]:
            print("  FAIL", f)
        return 1

    payload = json.dumps(g, indent=1, ensure_ascii=False) + "\n"

    if "--check" in sys.argv:
        if not OUT.exists():
            print("FAIL data/qesis_graph.json missing. Run without --check.")
            return 1
        if OUT.read_text(encoding="utf-8") != payload:
            print("FAIL data/qesis_graph.json does not match a fresh build.")
            return 1
        print(f"OK   graph matches a fresh build at {g['vintage']}")
        return 0

    OUT.write_text(payload, encoding="utf-8")
    c = g["counts"]
    print(f"OK   {OUT.relative_to(ROOT)}  {g['vintage']}")
    print(f"     {c['nodes']} nodes {c['by_kind']}")
    print(f"     {c['edges']} edges {c['by_edge_type']}")
    cj = g["findings"]["sole_provider_and_chokepoint_host"]
    nf = g["findings"]["network_fragility"]
    print(f"     sole-provider AND chokepoint host: {cj['n']} states {cj['states']}")
    print(f"     network tipping point: {nf['critical_node']} severs "
          f"{nf['cities_severed_in_one_step']} cities at removal "
          f"{nf['tipping_point_removals']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
