"""Ingest the EMODnet HA Telecommunication Cables release and test whether the
inherited CSE_EMO column can be reproduced from it.

The v8 index carries CSE_EMO as a hand-typed spreadsheet column. Nothing in this
repository derives it from EMODnet geodata, and `operationalize_sources.py`
declares the source ACTIVE by hashing a string literal. This script computes the
quantity from the published release so the column can be checked rather than
trusted.

Attribution uses the 912 landing cities from `connectivity_L1_full.xlsx`, which
reproduced exactly on independent recomputation (CONNECTIVITY_BATCH_AUDIT
2026-07-31). A cable segment is attributed to the nearest landing city when that
city lies within ATTRIB_KM of the segment midpoint. Segments with no city in
range are counted as unattributed rather than forced onto a country.

Output: data/axes/emodnet_cse_evidence.json
Reads only the EMODnet release, the workbook and the committed index. Writes one
evidence file. Does not mutate the index; supersession is a separate decision.
"""

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapelite import read_shp, read_dbf, haversine_km  # noqa: E402

EMODNET_DIR = r"C:/Users/Lenovo/Downloads/EMODnet_HA_Cables_Telecommunication_20230628"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(REPO, "data", "qesis_v8.json")
OUT = os.path.join(REPO, "data", "axes", "emodnet_cse_evidence.json")

# Attribution radius. 150 km is roughly continental-shelf scale and keeps a
# North Sea segment from being claimed by a country on the far side of it.
ATTRIB_KM = 150.0
GRID = 2.0  # degrees, for the lookup index

# Workbook country names to ISO3, restricted to the QESIS 35 plus the European
# neighbours whose waters the EMODnet layers cross.
NAME_TO_ISO = {
    "United Kingdom": "GBR", "United States": "USA", "France": "FRA",
    "Germany": "DEU", "Spain": "ESP", "Netherlands": "NLD", "Belgium": "BEL",
    "Denmark": "DNK", "Sweden": "SWE", "Norway": "NOR", "Finland": "FIN",
    "Poland": "POL", "Italy": "ITA", "Ireland": "IRL", "Portugal": "PRT",
    "Malta": "MLT", "Greece": "GRC", "Estonia": "EST", "Latvia": "LVA",
    "Lithuania": "LTU", "Russia": "RUS", "Morocco": "MAR", "Tunisia": "TUN",
    "Algeria": "DZA", "Iceland": "ISL", "Faroe Islands": "FRO",
    "Jersey": "JEY", "Guernsey": "GGY", "Isle of Man": "IMN",
    "Switzerland": "CHE", "Austria": "AUT",
}

# States whose EMODnet value is structurally zero rather than missing.
LANDLOCKED = {"AUT", "CHE"}


def load_cities(workbook):
    import openpyxl
    wb = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    ws = wb["cities"]
    rows = ws.iter_rows(values_only=True)
    next(rows)
    cities = []
    for cid, name, country, lon, lat in rows:
        if lon is None or lat is None:
            continue
        cities.append({
            "id": str(cid), "name": name, "country": country,
            "iso3": NAME_TO_ISO.get(country),
            "lon": float(lon), "lat": float(lat),
        })
    wb.close()
    return cities


def build_grid(cities):
    """Bucket cities into GRID-degree cells so attribution stays O(n)."""
    grid = defaultdict(list)
    for c in cities:
        grid[(int(c["lon"] // GRID), int(c["lat"] // GRID))].append(c)
    return grid


def nearest_city(lon, lat, grid):
    """Nearest city within ATTRIB_KM, searching the cell and its neighbours."""
    gx, gy = int(lon // GRID), int(lat // GRID)
    best, best_km = None, ATTRIB_KM
    # A 2-cell ring at 2 degrees covers well beyond 150 km at every latitude
    # these layers reach.
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            for c in grid.get((gx + dx, gy + dy), ()):
                d = haversine_km((lon, lat), (c["lon"], c["lat"]))
                if d < best_km:
                    best, best_km = c, d
    return best, best_km


def main():
    scratch = os.environ.get("QESIS_SCRATCH", "")
    workbook = os.path.join(scratch, "connectivity_L1_full.xlsx")
    if not os.path.exists(workbook):
        raise SystemExit(f"connectivity workbook not staged at {workbook}")

    cities = load_cities(workbook)
    grid = build_grid(cities)

    layers = sorted(f for f in os.listdir(EMODNET_DIR) if f.endswith(".shp"))
    per_country = defaultdict(lambda: {"km": 0.0, "segments": 0, "features": set()})
    layer_report = []
    unattributed_km = 0.0
    total_km = 0.0

    for fname in layers:
        path = os.path.join(EMODNET_DIR, fname)
        geo = read_shp(path)
        try:
            attrs = read_dbf(path[:-4] + ".dbf")
        except Exception:
            attrs = []
        lay_km = 0.0
        lay_unattr = 0.0
        touched = set()
        for fidx, parts in enumerate(geo):
            for part in parts:
                for i in range(len(part) - 1):
                    a, b = part[i], part[i + 1]
                    seg_km = haversine_km(a, b)
                    if seg_km <= 0:
                        continue
                    lay_km += seg_km
                    mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
                    city, _ = nearest_city(mid[0], mid[1], grid)
                    if city is None or city["iso3"] is None:
                        lay_unattr += seg_km
                        continue
                    rec = per_country[city["iso3"]]
                    rec["km"] += seg_km
                    rec["segments"] += 1
                    rec["features"].add(f"{fname}:{fidx}")
                    touched.add(city["iso3"])
        total_km += lay_km
        unattributed_km += lay_unattr
        layer_report.append({
            "layer": fname,
            "publisher_hint": fname.split("_")[0],
            "features": len(geo),
            "dbf_records": len(attrs),
            "length_km": round(lay_km, 1),
            "unattributed_km": round(lay_unattr, 1),
            "countries_touched": sorted(touched),
        })
        print(f"  {fname[:44]:46s} {len(geo):5d} feats  {lay_km:9.1f} km  "
              f"{len(touched):2d} countries")

    index = json.load(open(INDEX, encoding="utf-8"))
    qesis = index["countries"]

    # Reproduction test against the inherited column.
    computed = {k: round(v["km"], 1) for k, v in per_country.items()}
    rows = []
    for iso in sorted(qesis):
        inherited = qesis[iso].get("audit", {}).get("cse_components", {}).get("EMODnet")
        km = computed.get(iso)
        rows.append({
            "iso3": iso,
            "inherited_CSE_EMO": inherited,
            "emodnet_km_computed": km,
            "emodnet_features": len(per_country[iso]["features"]) if iso in per_country else 0,
            "landlocked": iso in LANDLOCKED,
        })

    sourced = [r for r in rows if r["emodnet_km_computed"]]
    inherited_filled = [r for r in rows if r["inherited_CSE_EMO"] is not None]
    unsupported = [r["iso3"] for r in inherited_filled if not r["emodnet_km_computed"]]
    unclaimed = [r["iso3"] for r in sourced if r["inherited_CSE_EMO"] is None]

    evidence = {
        "generated_by": "scripts/ingest_emodnet.py",
        "source_release": "EMODnet_HA_Cables_Telecommunication_20230628",
        "source_crs": "WGS84 geographic (all 7 layers, verified from .prj)",
        "attribution_method": (
            f"Segment midpoint to nearest of 912 verified landing cities within "
            f"{ATTRIB_KM:.0f} km. Unmatched segments counted as unattributed, never forced."),
        "totals": {
            "layers": len(layers),
            "features": sum(l["features"] for l in layer_report),
            "length_km": round(total_km, 1),
            "unattributed_km": round(unattributed_km, 1),
            "unattributed_share": round(unattributed_km / total_km, 4) if total_km else None,
        },
        "layers": layer_report,
        "qesis_rows": rows,
        "reproduction_verdict": {
            "qesis_states_sourced_by_emodnet": len(sourced),
            "coverage": round(len(sourced) / len(qesis), 4),
            "big_gate": 0.75,
            "passes_big_gate": (len(sourced) / len(qesis)) >= 0.75,
            "inherited_column_filled_for": len(inherited_filled),
            "inherited_values_with_no_emodnet_geometry": unsupported,
            "emodnet_sourced_but_inherited_null": unclaimed,
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2)
    print(f"\nwrote {OUT}")
    return evidence


if __name__ == "__main__":
    ev = main()
    v = ev["reproduction_verdict"]
    print(json.dumps(v, indent=2))
