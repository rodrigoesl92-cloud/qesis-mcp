#!/usr/bin/env python3
"""Extract the WEF Energy Transition Index 2026 ranking rows for the QESIS+ sample.

WHY THIS SCRIPT EXISTS AND WHY IT WRITES WHERE IT DOES
------------------------------------------------------
The WEF report reserves all rights "by any means, including photocopying and
recording, or by any information storage and retrieval system". Acquisition
register entry SA-006 therefore sets the posture to derived aggregates only,
the same posture SA-004 sets for UN Comtrade.

Consequence: the per-country ETI scores may never enter `qesis-mcp`, which is a
public repository. They are written to `var/restricted/`, which is gitignored, from a copy
of the report the operator already holds. Only the derived coefficient reaches
`data/`, and that is written by `verify_eti_convergence.py`, not by this file.

This script therefore REFUSES to write anywhere under `data/`. That refusal is
the control. A rule held only in prose has been described, not applied (L-054).

Usage
-----
    python scripts/eti_extract.py
    python scripts/eti_extract.py --pdf "Digital Twin R&D/WEF_Energy_Transition_Index_2026_260818_133013.pdf"

Requires pypdf. Prints counts only. It never prints a score.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys

# The 35 state sample, keyed by the name the ETI ranking table prints.
# Alternate spellings are listed because the publisher has used more than one
# form across editions. An unmatched sample state is reported, never guessed.
SAMPLE_BY_NAME = {
    "united arab emirates": "ARE",
    "australia": "AUS",
    "austria": "AUT",
    "belgium": "BEL",
    "bahrain": "BHR",
    "brazil": "BRA",
    "canada": "CAN",
    "switzerland": "CHE",
    "chile": "CHL",
    "germany": "DEU",
    "denmark": "DNK",
    "spain": "ESP",
    "finland": "FIN",
    "france": "FRA",
    "united kingdom": "GBR",
    "hong kong sar": "HKG",
    "hong kong sar, china": "HKG",
    "indonesia": "IDN",
    "india": "IND",
    "israel": "ISR",
    "italy": "ITA",
    "japan": "JPN",
    "south korea": "KOR",
    "korea, rep.": "KOR",
    "republic of korea": "KOR",
    "mexico": "MEX",
    "malaysia": "MYS",
    "netherlands": "NLD",
    "norway": "NOR",
    "new zealand": "NZL",
    "poland": "POL",
    "qatar": "QAT",
    "saudi arabia": "SAU",
    "singapore": "SGP",
    "sweden": "SWE",
    "taiwan, china": "TWN",
    "chinese taipei": "TWN",
    "united states": "USA",
    "south africa": "ZAF",
}

SAMPLE_ISO3 = {
    "ARE", "AUS", "AUT", "BEL", "BHR", "BRA", "CAN", "CHE", "CHL", "DEU",
    "DNK", "ESP", "FIN", "FRA", "GBR", "HKG", "IDN", "IND", "ISR", "ITA",
    "JPN", "KOR", "MEX", "MYS", "NLD", "NOR", "NZL", "POL", "QAT", "SAU",
    "SGP", "SWE", "TWN", "USA", "ZAF",
}

# rank, country, overall ETI, system performance, transition readiness.
# Trailing text is tolerated because the publisher's repeated column header runs
# into the last row of the left-hand column on the two-column page.
ROW_RE = re.compile(
    r"^\s*(\d{1,3})\s+"
    r"([A-Za-zÀ-ɏ\.\,\'’\-\(\) ]+?)\s+"
    r"(\d{1,2}\.\d)\s+(\d{1,2}\.\d)\s+(\d{1,2}\.\d)"
    r"(?:\s*$|\s*Rank\b)",
    re.M,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(REPO_ROOT, "var", "restricted", "eti_2026_scores.json")
DEFAULT_GLOB = os.path.join(REPO_ROOT, "Digital Twin R&D", "WEF_Energy_Transition_Index_2026*.pdf")


def refuse_public_plane(out_path: str) -> None:
    """SA-006 control. Restricted per-country values never enter the public artefact plane."""
    rel = os.path.relpath(os.path.abspath(out_path), REPO_ROOT)
    head = rel.replace("\\", "/").split("/")[0]
    if head in ("data", "public", "content", "docs"):
        raise SystemExit(
            "REFUSED: SA-006 restricts WEF material to derived aggregates only.\n"
            f"  requested output: {rel}\n"
            "  '%s/' is a published plane. Write to var/restricted/ instead." % head
        )


def extract_text(pdf_path: str) -> str:
    """pypdf first, pdftotext second. Neither is assumed present.

    L-139: an agent that cannot execute in the operator's environment does not
    hand the operator code to run. The two extractors cover the Windows checkout
    (pypdf, already in requirements) and the analysis mount (poppler's pdftotext,
    already installed there), so this runs in both without a setup step.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        pass
    else:
        reader = PdfReader(pdf_path)
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    import shutil
    import subprocess
    if shutil.which("pdftotext"):
        proc = subprocess.run(["pdftotext", "-layout", pdf_path, "-"],
                              capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout
        raise SystemExit(f"pdftotext failed: {proc.stderr.strip()[:200]}")

    raise SystemExit(
        "No PDF text extractor available. Settle it with one of:\n"
        "  pip install pypdf\n"
        "  apt-get install poppler-utils"
    )


def parse_rows(text: str) -> list[tuple[int, str, float, float, float]]:
    out = []
    for rank, name, eti, sp, tr in ROW_RE.findall(text):
        out.append((int(rank), name.strip(), float(eti), float(sp), float(tr)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pdf", default=None, help="path to the ETI 2026 PDF")
    ap.add_argument("--out", default=DEFAULT_OUT, help="local, gitignored output path")
    ap.add_argument("--text", default=None, help="pre-extracted text file, for testing")
    args = ap.parse_args()

    refuse_public_plane(args.out)

    if args.text:
        source_name, text = os.path.basename(args.text), open(args.text, encoding="utf-8").read()
        source_sha = hashlib.sha256(open(args.text, "rb").read()).hexdigest()
    else:
        pdf = args.pdf
        if not pdf:
            hits = sorted(glob.glob(DEFAULT_GLOB))
            if not hits:
                raise SystemExit(
                    "No ETI 2026 PDF found. Settle it with:\n"
                    '  python scripts/eti_extract.py --pdf "<path to WEF_Energy_Transition_Index_2026*.pdf>"'
                )
            pdf = hits[0]
        source_name = os.path.basename(pdf)
        source_sha = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
        text = extract_text(pdf)

    rows = parse_rows(text)
    ranks = {r[0] for r in rows}
    gaps = [i for i in range(1, 121) if i not in ranks]

    matched, unmatched_sample = {}, set(SAMPLE_ISO3)
    for rank, name, eti, sp, tr in rows:
        iso3 = SAMPLE_BY_NAME.get(name.lower())
        if iso3:
            matched[iso3] = {"rank": rank, "eti": eti, "system_performance": sp, "transition_readiness": tr}
            unmatched_sample.discard(iso3)

    payload = {
        "_warning": "RESTRICTED. WEF material under SA-006, derived aggregates only. "
                    "This file is gitignored and must never be committed or redistributed.",
        "source": {
            "publisher": "World Economic Forum",
            "work": "Energy Transition Index 2026",
            "edition": "16th, June 2026, in collaboration with Accenture",
            "file": source_name,
            "sha256": source_sha,
            "licence": "All rights reserved. Derived aggregates only (SA-006).",
        },
        "parsed_rows": len(rows),
        "rank_gaps": gaps,
        "sample_matched": sorted(matched),
        "sample_absent": sorted(unmatched_sample),
        "scores": matched,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)

    n, total = len(matched), len(SAMPLE_ISO3)
    print(f"parsed rows            {len(rows)} of 120")
    print(f"rank gaps              {gaps if gaps else 'none'}")
    print(f"sample coverage        {n} of {total}  ratio {n / total:.4f}")
    print(f"absent from the source {sorted(unmatched_sample) if unmatched_sample else 'none'}")
    print(f"written                {os.path.relpath(args.out, REPO_ROOT)}  (gitignored, restricted)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
