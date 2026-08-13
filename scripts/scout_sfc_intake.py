"""SCOUT: retrieve a candidate SFC source, count admissible states, refuse or clear.

Authorised 2026-08-13 under QT-0007 as the official intake for the SFC axis.

WHAT THIS DOES, AND THE ONE THING IT WILL NOT DO
------------------------------------------------
It retrieves a candidate source, records its provenance, runs every candidate
record through the REAL ingestion gate, and reports how many of the 35 sample
states are admissible. It writes nothing into the served index. Admission of an
axis into the composite is a publication act and stays with SENTINEL and the
human, per the Article 14 register.

The gate is imported from verify_axis_sfc, never reimplemented. A gate pasted
into a second caller is a gate that drifts (L-048), and this file exists
precisely to feed that gate rather than to duplicate its judgement.

TWO PHASES, BECAUSE A MACHINE CANNOT HONESTLY PARSE AN UNKNOWN TABLE
---------------------------------------------------------------------
    --fetch    retrieve the URL, hash it, save it with provenance, and dump
               anything table-shaped for a human to read. It does NOT guess
               which column is capacity. A scraper that infers a schema it has
               never seen is how a revenue column becomes a capacity column.

    --admit    take a structured JSON file of candidate records, run each one
               through admit(), and report the count with every refusal reason.

The split is the point. Phase one produces evidence with provenance. A human
reads the table once and writes the mapping. Phase two is deterministic and
repeatable forever after. The alternative, one script that fetches and infers,
would produce a number nobody derived, which is D-104.

EXIT CODES
----------
    0   27 or more states admitted: the axis is ADMISSIBLE, v9.0 unblocked
    1   fewer than 27 admitted: REFUSED, the axis stays WITHHELD with cause
    2   could not run: the source did not answer, or the input is malformed

Usage:
    python scripts/scout_sfc_intake.py --fetch <url>
    python scripts/scout_sfc_intake.py --admit data/axes/sfc_candidate.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from verify_axis_sfc import admit  # noqa: E402  the real gate, never a copy

SCAFFOLD = json.loads(
    (ROOT / "data" / "axes" / "v9_sfc_scaffold.json").read_text(encoding="utf-8"))
MINIMUM = SCAFFOLD["big_gate"]["minimum_states"]
INTAKE_DIR = ROOT / "data" / "axes" / "intake"


def sample() -> set[str]:
    """The 35 states, read from the served index rather than a literal list."""
    idx = json.loads((ROOT / "data" / "qesis_v8.json").read_text(encoding="utf-8"))
    return set(idx["countries"])


# ── phase one: retrieve, with provenance ────────────────────────────────────
def fetch(url: str) -> int:
    import urllib.request

    print(f"SCOUT intake, phase 1: retrieve\n  url: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "QESIS-SCOUT/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            final_url = r.geturl()
            ctype = r.headers.get("Content-Type", "")
    except Exception as exc:
        print(f"\nREFUSED: could not retrieve. {exc.__class__.__name__}: {exc}")
        print("A source that does not answer is not a source. Nothing recorded.")
        return 2

    sha = hashlib.sha256(raw).hexdigest()
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^a-z0-9]+", "-", url.lower())[:60].strip("-")
    body = INTAKE_DIR / f"{stem}.body"
    body.write_bytes(raw)

    prov = {
        "origin_url": url,
        "resolved_url": final_url,
        "content_type": ctype,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sha256": sha,
        "bytes": len(raw),
        "retrieved_by": "scripts/scout_sfc_intake.py --fetch",
        "publisher": "UNSET, a human writes this after reading the page",
        "license": "UNSET, a human writes this after reading the terms",
        "note": ("publisher and license are deliberately UNSET. admit() refuses a "
                 "record whose provenance is incomplete, so an unread licence "
                 "cannot reach the index by accident."),
    }
    (INTAKE_DIR / f"{stem}.provenance.json").write_text(
        json.dumps(prov, indent=1), encoding="utf-8")

    text = raw.decode("utf-8", errors="ignore")
    tables = re.findall(r"<table.*?</table>", text, re.S | re.I)
    print(f"  sha256: {sha[:16]}  bytes: {len(raw)}")
    print(f"  saved:  {body.relative_to(ROOT)}")
    print(f"  tables found: {len(tables)}")

    if tables:
        dump = INTAKE_DIR / f"{stem}.tables.txt"
        with dump.open("w", encoding="utf-8") as fh:
            for i, tb in enumerate(tables):
                cells = re.sub(r"<[^>]+>", "\t", tb)
                cells = re.sub(r"[ \t]+", "\t", cells)
                fh.write(f"\n===== table {i} =====\n")
                fh.write("\n".join(l.strip() for l in cells.splitlines() if l.strip()))
        print(f"  dumped: {dump.relative_to(ROOT)}")

    print("\nRETRIEVED. Nothing has been admitted and nothing was inferred.")
    print("Read the dumped tables, then write data/axes/sfc_candidate.json as")
    print('  {"DEU": {"iso3": "DEU", "installed_capacity_wspm": <number>,')
    print('           "capacity_unit": "wspm_200mm_equivalent",')
    print('           "reference_year": <year>, "process_nodes_covered": "...",')
    print('           "origin_url": "...", "publisher": "...",')
    print('           "license": "...", "retrieved_at": "..."}, ...}')
    print("then re-run with --admit. The gate decides, not this script.")
    return 0


# ── phase two: admit, or refuse with the clause ─────────────────────────────
def admit_file(path: Path) -> int:
    try:
        # utf-8-sig, not utf-8. A human on Windows writing this file in Notepad,
        # VS Code or PowerShell's Set-Content gets a UTF-8 BOM by default, and
        # strict utf-8 rejects it with "Unexpected UTF-8 BOM" and exit 2. The
        # operator then sees the intake refuse perfectly good capacity data for
        # a reason that has nothing to do with capacity. Postel, and the third
        # Windows encoding defect in one day after the .gitignore UTF-16 rule
        # (L-081) and the cp1252 read (L-083). (L-095.)
        #
        # This liberality is for INPUT a human writes. Everything this project
        # GENERATES stays strict UTF-8 without a BOM, because a BOM in a served
        # artifact changes its hash.
        cand = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        print(f"REFUSED: {path} is not readable JSON. {exc}")
        return 2
    if not isinstance(cand, dict):
        print("REFUSED: expected a JSON object mapping iso3 -> record")
        return 2

    states = sample()
    try:
        label = path.relative_to(ROOT)
    except ValueError:
        label = path  # a candidate staged outside the repo is legitimate
    print(f"SCOUT intake, phase 2: admit\n  candidate: {label}")
    print(f"  sample: {len(states)} states | bar: {MINIMUM} "
          f"({MINIMUM}/{len(states)} = {MINIMUM/len(states):.4f})\n")

    ok, refused = [], []
    for iso in sorted(cand):
        passed, why = admit(iso, cand[iso], states)
        (ok if passed else refused).append((iso, why))

    for iso, _ in ok:
        print(f"  ADMIT   {iso}")
    for iso, why in refused:
        print(f"  REFUSE  {iso}: {why}")

    missing = sorted(states - {i for i, _ in ok})
    print(f"\nadmitted: {len(ok)} of {len(states)}")
    if missing:
        print(f"absent or refused: {', '.join(missing)}")

    if len(ok) >= MINIMUM:
        print(f"\nADMISSIBLE: {len(ok)} clears the {MINIMUM}-state bar.")
        print("The SFC axis can be built and v9.0 is unblocked.")
        print("Publication remains an Article 14 act: SENTINEL gates it and a")
        print("named human signs. This script does not write the index.")
        return 0

    print(f"\nREFUSED: {len(ok)} does not clear the {MINIMUM}-state bar.")
    print("The axis stays WITHHELD WITH CAUSE. Coverage below the threshold is a")
    print("finding, never a gap to fill: D-007 forbids imputation and the")
    print("outcome_rule forbids stitching partial sources onto one definition.")
    print("The refusal reasons above distinguish a state absent from the source")
    print("from a state thrown out for measuring the wrong thing.")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", metavar="URL")
    ap.add_argument("--admit", metavar="JSON", type=Path)
    a = ap.parse_args()
    if a.fetch:
        return fetch(a.fetch)
    if a.admit:
        return admit_file(a.admit)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
