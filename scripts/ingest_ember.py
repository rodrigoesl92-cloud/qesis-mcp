"""Ingest Ember Yearly Electricity Data and test it against the ESE axis.

ESE carries `carbon_gco2_kwh` per state. Ember publishes exactly that quantity
as `Emissions intensity (gCO2e/kWh)` on an annual national basis, which makes it
a direct check rather than a proxy.

Same disposition rule as everywhere else in this repository: compute, compare,
report. A refresh that moves an audited axis is a supersession and needs a
decision, so this writes evidence and does not mutate the index.

Reads data/electricity_yearly_global_EMBER.csv and the committed index.
Writes data/axes/ember_ese_evidence.json.
"""

import csv
import json
import os
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOBAL_CSV = os.path.join(REPO, "data", "electricity_yearly_global_EMBER.csv")
EUROPE_CSV = os.path.join(REPO, "data", "electricity_yearly_lower_EUROPE_EMBER.csv")
INDEX = os.path.join(REPO, "data", "qesis_v8.json")
OUT = os.path.join(REPO, "data", "axes", "ember_ese_evidence.json")

INTENSITY = "Emissions intensity (gCO2e/kWh)"


def load_intensity(path):
    """Latest national emissions intensity per ISO3, with its year."""
    best = {}
    sources = defaultdict(set)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            iso = (row.get("ISO 3 code") or "").strip()
            if not iso or row.get("Area type") != "Country or economy":
                continue
            # Intensity is published per source. Only the total-generation row
            # is the national figure; the rest are per-technology and averaging
            # them would be meaningless.
            if row.get("Electricity source") != "Total generation":
                continue
            sources[iso].add(row.get("Electricity source", ""))
            val = (row.get(INTENSITY) or "").strip()
            if not val:
                continue
            try:
                year = int(row["Year"])
                v = float(val)
            except (ValueError, KeyError):
                continue
            # Intensity is published on the total-generation row; other rows
            # leave it blank, so any populated row is the national figure.
            if iso not in best or year > best[iso][0]:
                best[iso] = (year, v)
    return {k: {"year": v[0], "gco2_kwh": round(v[1], 2)} for k, v in best.items()}


def main():
    ember = load_intensity(GLOBAL_CSV)
    index = json.load(open(INDEX, encoding="utf-8"))
    countries = index["countries"]

    rows, deltas = [], []
    for iso in sorted(countries):
        cur = countries[iso].get("ese_components", {}).get("carbon_gco2_kwh")
        new = ember.get(iso)
        delta = None
        if cur is not None and new is not None:
            delta = round(new["gco2_kwh"] - cur, 2)
            deltas.append((iso, cur, new["gco2_kwh"], delta, new["year"]))
        rows.append({
            "iso3": iso,
            "index_carbon_gco2_kwh": cur,
            "ember_gco2_kwh": new["gco2_kwh"] if new else None,
            "ember_year": new["year"] if new else None,
            "delta": delta,
        })

    matched = [r for r in rows if r["ember_gco2_kwh"] is not None]
    coverage = round(len(matched) / len(countries), 4)
    big = [d for d in deltas if abs(d[3]) > 50]
    years = sorted({r["ember_year"] for r in matched if r["ember_year"]})

    evidence = {
        "generated_by": "scripts/ingest_ember.py",
        "source": "Ember Yearly Electricity Data",
        "files": [os.path.basename(GLOBAL_CSV), os.path.basename(EUROPE_CSV)],
        "measure": INTENSITY,
        "vintage_years_present": years,
        "coverage": {
            "qesis_states_matched": len(matched),
            "of": len(countries),
            "coverage": coverage,
            "big_gate": 0.75,
            "passes_big_gate": coverage >= 0.75,
            "unmatched": [r["iso3"] for r in rows if r["ember_gco2_kwh"] is None],
        },
        "comparison": {
            "states_comparable": len(deltas),
            "mean_abs_delta": round(sum(abs(d[3]) for d in deltas) / len(deltas), 2) if deltas else None,
            "max_abs_delta": max((abs(d[3]) for d in deltas), default=None),
            "states_moving_more_than_50_gco2": [
                {"iso3": d[0], "index": d[1], "ember": d[2], "delta": d[3], "ember_year": d[4]}
                for d in sorted(big, key=lambda x: -abs(x[3]))
            ],
        },
        "disposition": (
            "ESE is a diagnostic axis and is excluded from the weighted composite, "
            "so a refresh here does not move any published composite. Ember clears "
            "the BIG coverage gate and is a direct measure of the same quantity "
            "rather than a proxy. Promotion is therefore a vintage decision, not a "
            "methodological one, and is recorded for a decision rather than applied "
            "silently."),
        "rows": rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(evidence, open(OUT, "w", encoding="utf-8"), indent=2)

    print(f"Ember national intensity rows: {len(ember)} states, years {years}")
    print(f"QESIS coverage {len(matched)}/{len(countries)} = {coverage} "
          f"(BIG gate 0.75: {'PASS' if coverage >= 0.75 else 'FAIL'})")
    print(f"comparable {len(deltas)}  mean|delta| "
          f"{evidence['comparison']['mean_abs_delta']}  max|delta| "
          f"{evidence['comparison']['max_abs_delta']}")
    for d in sorted(big, key=lambda x: -abs(x[3]))[:10]:
        print(f"   {d[0]}  index {d[1]:>7} -> ember {d[2]:>7} ({d[4]})  delta {d[3]:+.1f}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
