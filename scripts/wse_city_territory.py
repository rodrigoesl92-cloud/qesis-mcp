"""Computes WSE for the three territories the Aqueduct country rollup drops, and
runs the falsifier that decides whether the result is comparable with the other 32.

WHY THIS EXISTS. v9.0 withholds a composite for HKG, SGP and TWN because WSE is
absent, and every artefact records that absence honestly: qesis.sqlite
v8_qesis_country_scores leaves the WSE column empty for all three,
v8_aqueduct_4_0_batch_35 marks all seven scenario columns N/A, and
aqueduct40_country_rankings has no row for HKG or TWN and an all-sentinel row for
SGP. The number is recorded nowhere.

That is a fact about the COUNTRY ROLLUP, not about the measurement. The rollup is
keyed on GADM gid_0, a territorial schema with no Taiwan entry that collapses
city-territories. The gridded baseline underneath it is keyed by catchment with a
gid_0, gid_1, name_0, name_1 and area_km2 on every record, and it covers the
globe. The value is unextracted, not missing.

WHAT IT DOES. Streams the grid once. Selects catchment records belonging to each
territory by GADM identity, primary on gid_0 and falling back to name_0 or
name_1, because a territory the rollup collapses may appear nested under its
parent. Takes the area-weighted mean of bws_score, which is what a catchment
rollup does, and prints the unweighted mean beside it so the reader can see how
much the weighting moved. Applies the rescale of 20, read off the published
rollup rather than invented.

THE FALSIFIER, and it is the point. The same extraction runs over states the
rollup DOES carry. If the reconstruction lands on their published
wse_bws_tot_0_100, the method reproduces Aqueduct and the three new figures are
comparable with the other 32. If it does not, they are not, and the honest place
for them is a diagnostic axis outside the composite. One run decides it.

Usage:  python scripts/wse_city_territory.py --grid PATH [--rollup PATH]
        python scripts/wse_city_territory.py --selftest
Exit:   0 computed or selftest passed - 1 refused with a named reason
"""
from __future__ import annotations
import argparse, csv, json, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

TARGETS = {
    "HKG": {"name": "Hong Kong", "names": ("hong kong", "hongkong", "xianggang")},
    "SGP": {"name": "Singapore", "names": ("singapore",)},
    "TWN": {"name": "Taiwan",    "names": ("taiwan", "taiwan province of china", "chinese taipei")},
}
# States the rollup carries, used only to falsify the method.
CONTROLS = {"ESP": {"name": "Spain", "names": ("spain", "espana")},
            "NLD": {"name": "Netherlands", "names": ("netherlands",)}}
RESCALE = 20.0
SENTINEL = {-9999.0, -9999, -9999.9}
NEEDED = ("gid_0", "name_0", "name_1", "area_km2", "bws_score")


def clean(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f in SENTINEL or math.isnan(f) or f < 0:
        return None
    return f


def aggregate(cells: list[dict]) -> dict:
    """Pure over [{score, area}]. Area-weighted and unweighted means."""
    vals = [c for c in cells if c.get("score") is not None]
    if not vals:
        return {"n_cells": 0, "score_0_5": None, "wse_0_100": None,
                "unweighted_0_100": None, "area_km2": 0.0}
    tot_a = sum((c.get("area") or 0.0) for c in vals)
    if tot_a > 0:
        wm = sum(c["score"] * (c.get("area") or 0.0) for c in vals) / tot_a
    else:
        wm = sum(c["score"] for c in vals) / len(vals)
    um = sum(c["score"] for c in vals) / len(vals)
    return {"n_cells": len(vals), "score_0_5": round(wm, 6),
            "wse_0_100": round(wm * RESCALE, 2),
            "unweighted_0_100": round(um * RESCALE, 2),
            "area_km2": round(tot_a, 1),
            "min_score": round(min(c["score"] for c in vals), 4),
            "max_score": round(max(c["score"] for c in vals), 4)}


def selftest() -> int:
    ok = True
    # 1 must compute, and area weighting must actually bite.
    cells = [{"score": 5.0, "area": 900.0}, {"score": 1.0, "area": 100.0}]
    r = aggregate(cells)
    if r["n_cells"] != 2 or r["wse_0_100"] != 92.0 or r["unweighted_0_100"] != 60.0:
        print(f"  x FIXTURE 1 FAILED: expected weighted 92.0 and unweighted 60.0, got {r}"); ok = False
    # 2 must refuse: every cell a sentinel.
    r = aggregate([{"score": clean(-9999.0), "area": 10.0}, {"score": clean("NoData"), "area": 10.0}])
    if r["n_cells"] != 0 or r["wse_0_100"] is not None:
        print(f"  x FIXTURE 2 FAILED: sentinel-only input must yield nothing, got {r}"); ok = False
    # 3 the rescale is the published one, verified against the rollup's own pair.
    if round(3.369185991 * RESCALE, 5) != round(67.38371982, 5):
        print("  x FIXTURE 3 FAILED: rescale does not reproduce the published AFG pair"); ok = False
    # 4 zero total area must fall back to unweighted rather than divide by zero.
    r = aggregate([{"score": 2.0, "area": 0.0}, {"score": 4.0, "area": 0.0}])
    if r["wse_0_100"] != 60.0:
        print(f"  x FIXTURE 4 FAILED: zero-area fallback wrong, got {r}"); ok = False
    # 5 the falsifier must NOT pass when a control produced nothing. This fixture
    # exists because that exact defect shipped on 2026-08-28 and printed
    # "METHOD REPRODUCES THE ROLLUP" over two null reconstructions. L-211.
    rows = [{"iso3": "ESP", "reconstructed": None, "published": 78.8, "delta": None},
            {"iso3": "NLD", "reconstructed": None, "published": 31.6, "delta": None}]
    deltas = [abs(r["delta"]) for r in rows if r["delta"] is not None]
    unmeasured = [r["iso3"] for r in rows if r["delta"] is None]
    verdict = "FALSIFIER DID NOT RUN" if (unmeasured or not deltas) else "METHOD REPRODUCES THE ROLLUP"
    if verdict != "FALSIFIER DID NOT RUN":
        print("  x FIXTURE 5 FAILED: a falsifier with no measurement reported a pass"); ok = False
    print(f"WSE CITY-TERRITORY SELFTEST: {'PASSED, 5 fixtures' if ok else 'FAILED'}")
    return 0 if ok else 1


ap = argparse.ArgumentParser()
ap.add_argument("--grid", type=pathlib.Path)
ap.add_argument("--rollup", type=pathlib.Path, default=None,
                help="aqueduct40_country_rankings.csv, used to falsify the method")
ap.add_argument("--out", type=pathlib.Path,
                default=ROOT / "data" / "axes" / "wse_city_territory_evidence.json")
ap.add_argument("--selftest", action="store_true")
args = ap.parse_args()
if args.selftest:
    raise SystemExit(selftest())
if not args.grid or not args.grid.exists():
    print("REFUSED: --grid must name the gridded Aqueduct baseline present on this machine.")
    raise SystemExit(1)

ALL = dict(TARGETS, **CONTROLS)
buckets = {k: [] for k in ALL}
matched_on = {k: set() for k in ALL}
scanned = 0
seen_gid0: dict[str, int] = {}
seen_name0: dict[str, int] = {}

with args.grid.open("r", encoding="utf-8", errors="replace", newline="") as fh:
    rdr = csv.DictReader(fh)
    missing = [c for c in NEEDED if c not in (rdr.fieldnames or [])]
    if missing:
        print(f"REFUSED: the grid lacks {missing}.")
        print(f"  columns present ({len(rdr.fieldnames or [])}): {(rdr.fieldnames or [])[:40]}")
        print("  Name the right columns and this refusal becomes a computation. It does not guess.")
        raise SystemExit(1)
    print(f"grid columns bound: gid_0, name_0, name_1, area_km2, bws_score  "
          f"(of {len(rdr.fieldnames)} present)")
    for row in rdr:
        scanned += 1
        g0 = (row.get("gid_0") or "").strip().upper()
        n0 = (row.get("name_0") or "").strip().lower()
        n1 = (row.get("name_1") or "").strip().lower()
        if g0:
            seen_gid0[g0] = seen_gid0.get(g0, 0) + 1
        if n0:
            seen_name0[n0] = seen_name0.get(n0, 0) + 1
        for iso, spec in ALL.items():
            hit = None
            if g0 == iso:
                hit = "gid_0"
            elif n0 in spec["names"]:
                hit = "name_0"
            elif n1 in spec["names"]:
                hit = "name_1"
            if hit:
                matched_on[iso].add(f"{hit}={g0 or n0 or n1}")
                buckets[iso].append({"score": clean(row.get("bws_score")),
                                     "area": clean(row.get("area_km2")) or 0.0})
                break

print(f"scanned {scanned} catchment record(s)\n")
result = {}
for iso, spec in ALL.items():
    r = aggregate(buckets[iso])
    r["name"] = spec["name"]
    r["matched_on"] = sorted(matched_on[iso])
    r["role"] = "target, withheld by the rollup" if iso in TARGETS else "control, carried by the rollup"
    result[iso] = r
    v = f"WSE {r['wse_0_100']}" if r["wse_0_100"] is not None else "NO RECORD MATCHED"
    print(f"  {iso}  {spec['name']:<12} cells {r['n_cells']:>6}  {v:<14} "
          f"(unweighted {r['unweighted_0_100']})  via {r['matched_on'] or 'nothing'}")

empty = [iso for iso in ALL if result[iso]["n_cells"] == 0]
if empty:
    print("\n  KEY DIAGNOSTIC. Nothing matched for: " + ", ".join(empty))
    print("  This is a key-format problem, not an absence. What the grid actually contains:")
    g = sorted(seen_gid0.items(), key=lambda kv: -kv[1])
    n = sorted(seen_name0.items(), key=lambda kv: -kv[1])
    print(f"    distinct gid_0 values : {len(g)}   sample: {[k for k, _ in g[:12]]}")
    print(f"    distinct name_0 values: {len(n)}   sample: {[k for k, _ in n[:12]]}")
    for iso, spec in ALL.items():
        if iso in empty:
            near = [k for k, _ in g if iso in k] or [k for k, _ in n if any(w in k for w in spec["names"])]
            print(f"    {iso} ({spec['name']}): candidate keys containing it -> {near[:6] or 'none'}")
    print("  Give the extractor the key it actually uses and this becomes a computation.")

falsifier = {"ran": False, "verdict": "FALSIFIER DID NOT RUN",
             "meaning": "No rollup was supplied, so nothing was compared and nothing is claimed."}
if args.rollup and args.rollup.exists():
    published = {}
    with args.rollup.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh):
            iso = (row.get("gid_0") or "").strip().upper()
            if iso in CONTROLS:
                published[iso] = clean(row.get("wse_bws_tot_0_100"))
    rows, deltas = [], []
    for iso in CONTROLS:
        rec = result[iso]["wse_0_100"]; pub = published.get(iso)
        d = None if (rec is None or pub is None) else round(rec - pub, 2)
        if d is not None:
            deltas.append(abs(d))
        rows.append({"iso3": iso, "reconstructed": rec, "published": pub, "delta": d})

    # L-211 applied, not quoted. An empty denominator is null, never a pass.
    unmeasured = [r["iso3"] for r in rows if r["delta"] is None]
    if unmeasured or not deltas:
        worst = None
        verdict = "FALSIFIER DID NOT RUN"
        meaning = ("No verdict. " + ", ".join(unmeasured) + " produced no reconstruction, so "
                   "nothing was compared. A control that yields nothing is not a control that "
                   "agreed. Until every control reconstructs, the three target figures have no "
                   "standing and must not be proposed for the composite.")
    else:
        worst = max(deltas)
        passed = worst <= 5.0
        verdict = ("METHOD REPRODUCES THE ROLLUP" if passed else
                   "METHOD DOES NOT REPRODUCE THE ROLLUP")
        meaning = ("The three target figures are comparable with the other 32 and may be "
                   "proposed for the composite." if passed else
                   "The three target figures are NOT comparable with the other 32. Publish them "
                   "as a diagnostic axis outside the composite, or not at all.")
    print("\n  FALSIFIER")
    for r in rows:
        print(f"    {r['iso3']}  reconstructed {r['reconstructed']}  published {r['published']}  "
              f"delta {r['delta']}")
    print(f"    worst absolute delta {worst} against a threshold of 5.0"
          if worst is not None else "    worst absolute delta: NOT COMPUTED, a control returned nothing")
    print(f"    {verdict}")
    print(f"    {meaning}")
else:
    print("\n  FALSIFIER NOT RUN: pass --rollup aqueduct40_country_rankings.csv to settle "
          "whether these figures are comparable with the other 32.")

payload = {
    "_doc": "WSE for the three territories the Aqueduct 4.0 country rollup does not carry, "
            "computed from the gridded baseline that does. Evidence only. Nothing here changes "
            "a composite until the methodology decision is signed.",
    "generator": "scripts/wse_city_territory.py",
    "source_grid": str(args.grid),
    "method": "Area-weighted mean of bws_score over the catchment records belonging to each "
              "territory by GADM identity (gid_0, falling back to name_0 or name_1 because a "
              "territory the rollup collapses may sit nested under its parent), rescaled by 20. "
              "The rescale is read off the published rollup, where wse_bws_tot_0_100 equals "
              "score_bws_tot times 20, verified against AFG 3.369185991 to 67.38371982.",
    "rescale": RESCALE,
    "records_scanned": scanned,
    "territories": result,
    "falsifier": falsifier,
    "uncertainty": "A catchment crossing a border is counted whole to whichever territory its "
                   "GADM identity names. For a small territory that is a material share of the "
                   "total area, so the figure carries more spread than a large state's.",
    "confounder": "If Aqueduct weights its country rollup by population or by withdrawal rather "
                  "than by area, the reconstruction will diverge systematically. The falsifier "
                  "detects exactly that, which is why it is not optional.",
    "decision_required": "Admitting a value derived this way beside 32 derived from the rollup "
                         "creates a method asymmetry. The falsifier verdict decides which of the "
                         "two publishable routes is honest, and the human signs it.",
}
args.out.parent.mkdir(parents=True, exist_ok=True)
args.out.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"\nwrote {args.out}")
print("Nothing in the index changed.")
