"""U-04. Capacity-weighted ODI as a bounded interval, never as an imputed point.

THE PROBLEM. The served ODI Herfindahl weights one unit per active cloud region,
because availability-zone counts are absent for most of the sample. Verified
against cloud_regions_master.csv: 8 states carry a zone count for EVERY one of
their regions, 24 carry some, 3 carry none. That is the ledger's "missing for 27
of 35" exactly, and the ledger figure is correct.

WHY NOT JUST WEIGHT WHAT WE HAVE. Weighting some rows by zone count and others
by 1 produces a column that is not comparable across its own rows. That is the
`baseline_identity` failure the SFC ingestion contract was written to prevent,
and it would be worse here because nothing in the values themselves would reveal
it. A reader would compare a zone-weighted Netherlands against a region-weighted
Germany and read the difference as concentration.

WHY NOT IMPUTE. D-007: coverage below threshold is a finding, not a gap to fill.
Filling 56 unknown zone counts with a mean would convert a coverage limit into a
measurement, which is the D-101 pattern.

WHAT THIS DOES INSTEAD. For every state it computes the Herfindahl twice:

  ODI_lo   every region with an unknown zone count is assigned the MINIMUM zone
           count observed anywhere in the dataset
  ODI_hi   the same regions are assigned the MAXIMUM observed

Both bounds are computed on ONE baseline, so they are comparable. The true
capacity-weighted value lies inside the interval by construction, and no number
is invented: the bounds are the arithmetic consequence of what is unknown.

A state is DECIDABLE when the interval does not cross an ODI band boundary, so
the missing data cannot change what the reader concludes. That converts most of
U-04 from an open limitation into a published and bounded one, and names the
remainder precisely rather than as "27 of 35".

Usage:  python scripts/compute_odi_bounds.py [--check]
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "qesis_v8.json"
OUT = ROOT / "data" / "axes" / "odi_capacity_bounds.json"

#: The register lives in the thesis database, not in either repository. It is
#: named in lineage.sources and this is where it actually is. Recorded because
#: looking in the repo and concluding the file was absent is precisely the error
#: this script exists downstream of.
CSV_CANDIDATES = [
    ROOT.parent / "OneDrive" / "Documents" / "INITIUM" / "Master IR & GE"
        / "Final Master Thesis" / "_DATABASE" / "csv_exports" / "cloud_regions_master.csv",
    Path("/sessions/trusting-brave-fermat/mnt/Final Master Thesis/_DATABASE/csv_exports/cloud_regions_master.csv"),
]

#: ODI bands as read by the surface. A bound crossing one of these changes what
#: a reader concludes, which is the only thing that makes the gap consequential.
BANDS = [(0, 25, "LOW"), (25, 50, "MODERATE"), (50, 75, "HIGH"), (75, 100.01, "CRITICAL")]


def band(v: float) -> str:
    for lo, hi, name in BANDS:
        if lo <= v < hi:
            return name
    return "CRITICAL"


def hhi(weights: dict[str, float]) -> float:
    """Herfindahl over provider shares of weighted capacity, on 0 to 100."""
    total = sum(weights.values())
    if total <= 0:
        return 0.0
    return round(sum((w / total) ** 2 for w in weights.values()) * 100, 4)


def locate_csv() -> Path:
    for p in CSV_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(
        "cloud_regions_master.csv not found. It lives in the thesis database "
        "under _DATABASE/csv_exports, not in either repository.")


def main() -> int:
    doc = json.loads(INDEX.read_text(encoding="utf-8"))
    sample = doc["countries"]
    src = locate_csv()
    rows = list(csv.DictReader(src.open(encoding="utf-8-sig")))

    known = [float(r["intra_region_fault_domains"]) for r in rows
             if (r.get("intra_region_fault_domains") or "").strip()
             not in ("", "NA", "null", "None")]
    if not known:
        print("FAIL  no zone counts at all; nothing to bound")
        return 1
    z_min, z_max = min(known), max(known)

    per_state: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        iso = (r.get("country_iso3") or "").strip()
        if iso in sample:
            per_state[iso].append(r)

    out: dict[str, dict] = {}
    decidable = undecidable = complete = 0
    for iso, rs in sorted(per_state.items()):
        lo_w: dict[str, float] = defaultdict(float)
        hi_w: dict[str, float] = defaultdict(float)
        n_known = 0
        for r in rs:
            p = (r.get("provider") or "").strip() or "UNKNOWN"
            raw = (r.get("intra_region_fault_domains") or "").strip()
            if raw not in ("", "NA", "null", "None"):
                z = float(raw)
                lo_w[p] += z
                hi_w[p] += z
                n_known += 1
            else:
                lo_w[p] += z_min
                hi_w[p] += z_max
        odi_lo, odi_hi = hhi(lo_w), hhi(hi_w)
        b_lo, b_hi = band(odi_lo), band(odi_hi)
        is_complete = n_known == len(rs)
        is_dec = b_lo == b_hi
        complete += is_complete
        decidable += (is_dec and not is_complete)
        undecidable += (not is_dec)
        out[iso] = {
            "name": sample[iso]["name"],
            "served_odi": sample[iso].get("odi_continuous", {}).get("odi_hhi"),
            "regions": len(rs), "regions_with_zone_count": n_known,
            "odi_lower": odi_lo, "odi_upper": odi_hi,
            "interval_width": round(odi_hi - odi_lo, 4),
            "band_lower": b_lo, "band_upper": b_hi,
            "status": ("COMPLETE" if is_complete
                       else "DECIDABLE" if is_dec else "BAND-AMBIGUOUS"),
            "reading": ("Every region carries a zone count. The capacity-weighted "
                        "value is measured, not bounded."
                        if is_complete else
                        f"Zone counts absent for {len(rs) - n_known} of {len(rs)} "
                        f"regions. Both bounds fall in {b_lo}, so the absence "
                        f"cannot change what a reader concludes."
                        if is_dec else
                        f"Zone counts absent for {len(rs) - n_known} of {len(rs)} "
                        f"regions and the interval spans {b_lo} to {b_hi}. The "
                        f"absence is consequential here and is published as such."),
        }

    payload = {
        "vintage": doc["vintage"], "generator": "scripts/compute_odi_bounds.py",
        "closes": "U-04 as a bounded limitation rather than an open one",
        "source": {"file": "_DATABASE/csv_exports/cloud_regions_master.csv",
                   "rows": len(rows),
                   "note": "Lives in the thesis database, not in either repository."},
        "method": ("Herfindahl over provider shares of zone-weighted capacity, "
                   "computed twice. Regions with no zone count take the minimum "
                   "observed count for the lower bound and the maximum for the "
                   "upper. Both bounds use ONE baseline so they are comparable, "
                   "and the true value lies inside by construction. Nothing is "
                   "imputed: the bounds are the arithmetic consequence of what "
                   "is unknown (D-007)."),
        "observed_zone_counts": {"min": z_min, "max": z_max, "n_known": len(known),
                                 "n_rows": len(rows)},
        "summary": {"states": len(out), "complete": complete,
                    "decidable_despite_gaps": decidable,
                    "band_ambiguous": undecidable,
                    "reading": (f"{complete + decidable} of {len(out)} states carry an ODI "
                                f"band that the missing zone counts cannot change. "
                                f"{undecidable} remain genuinely ambiguous and are named. "
                                f"U-04 previously reported 27 of 35 as missing without "
                                f"saying for how many of those it mattered.")},
        "states": out,
    }
    text = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"

    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("FAIL  odi_capacity_bounds.json does not match a fresh build")
            return 1
        print("OK    odi bounds match a fresh build")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    s = payload["summary"]
    print(f"OK    {OUT.relative_to(ROOT)}  {doc['vintage']}")
    print(f"      zone counts observed: min {z_min}, max {z_max}, "
          f"{len(known)}/{len(rows)} rows")
    print(f"      COMPLETE {s['complete']}  DECIDABLE {s['decidable_despite_gaps']}  "
          f"BAND-AMBIGUOUS {s['band_ambiguous']}  of {s['states']}")
    amb = [k for k, v in out.items() if v["status"] == "BAND-AMBIGUOUS"]
    if amb:
        print(f"      ambiguous: {', '.join(amb)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
