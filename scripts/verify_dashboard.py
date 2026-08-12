"""The public dashboard may not contradict the index it claims to present.

L-090. STIR_Governance_Dashboard.html is hand maintained: no script writes it and
no gate read it. On 2026-08-12 it was serving three claims the served payload
denies at the same moment:

  1. "QESIS+ v8.6 canonical" while data/qesis_v8.json served v8.9.
  2. "States cannot simultaneously achieve algorithmic independence, hyperscale
     efficiency, and ecological sustainability. This limitation constitutes the
     Infrastructural Trilemma." The payload's own agent_reading_contract sets
     trilemma_status to interpretive_overlay_only and binds that no result may
     be presented as a trilemma corner. The dashboard presented it as measured.
  3. "4 of 35 states pass their own sovereignty test (USA, FRA, DEU, NLD)".
     No sovereignty_test field exists in the payload, and only 32 states carry a
     composite at all. A named-states finding with no published rule is D-104
     with a country list attached.

A surface nobody gates will say whatever it said last.

Usage:  python scripts/verify_dashboard.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = json.loads((ROOT / "data" / "qesis_v8.json").read_text(encoding="utf-8"))
PAGES = [p for p in (ROOT / "STIR_Governance_Dashboard.html",
                     ROOT / "public" / "STIR_Governance_Dashboard.html") if p.exists()]

VINTAGE = DOC["vintage"]
ARC = (DOC.get("agent_reading_contract") or {}).get("flags") or {}
TRILEMMA = (ARC.get("trilemma_status") or {}).get("value")

# Language that asserts the trilemma as a measured structural result rather than
# an interpretive claim. Matched on the assertion, not on the word "trilemma":
# naming it is fine, presenting it as a finding is not.
#: Affirmative structural assertions only. A negated mention is the demotion
#: being published, which is required, not forbidden: "no pathway term on this
#: page is a trilemma corner" must be sayable. The negator window is 60
#: characters, which covers the sentence forms actually used on the page.
STRUCTURAL = re.compile(
    r"(?<!\bnot )(cannot simultaneously achieve|this limitation constitutes|"
    r"the trilemma (?:is|shows|demonstrates|proves) )", re.I)
NEGATOR = re.compile(r"\b(no|not|never|rather than|is not)\b", re.I)

# A bare "N of 35" claim on a public page needs a rule behind it.
COUNT_CLAIM = re.compile(r"\b(\d{1,2})\s+of\s+35\b", re.I)
#: A block explicitly marked as a withdrawal, which may quote the figure it
#: withdraws. Anything outside such a block is a live claim.
WITHDRAWN = re.compile(r"<(\w+)[^>]*data-withdrawn=\"[^\"]*\"[^>]*>.*?</\1>", re.S)
DECLARED_COUNTS = {
    str(sum(1 for c in DOC["countries"].values() if c.get("composite") is not None)),
    str(len(DOC["countries"])),
    str(len(DOC.get("epis_findings") or [])),
}


def main() -> int:
    if not PAGES:
        print("no dashboard on disk, nothing to check")
        return 0
    fails: list[str] = []
    for p in PAGES:
        t = p.read_text(encoding="utf-8", errors="ignore")
        name = p.relative_to(ROOT)

        served = [v for v in set(re.findall(r"v8\.\d+", t)) if v != VINTAGE.split()[0]]
        ok = VINTAGE.split()[0] in t
        print(f"  {'OK  ' if ok else 'FAIL'}  {name}: declares {VINTAGE.split()[0]}"
              + (f", also carries {sorted(served)}" if served else ""))
        if not ok:
            fails.append(f"{name} does not name the served vintage {VINTAGE}")
        if served:
            fails.append(f"{name} names superseded vintages {sorted(served)}")

        if TRILEMMA == "interpretive_overlay_only":
            hits = [m.group(0) for m in STRUCTURAL.finditer(t)
                    if not NEGATOR.search(t[max(0, m.start() - 60):m.start()])]
            ok = not hits
            print(f"  {'OK  ' if ok else 'FAIL'}  {name}: trilemma presented as "
                  f"{'overlay' if ok else 'a measured limitation'}")
            if not ok:
                fails.append(
                    f"{name} asserts the trilemma structurally ({hits[0]!r}) while "
                    f"agent_reading_contract.trilemma_status is "
                    f"interpretive_overlay_only")

        # A retraction must be free to name what it retracts. The exemption is
        # declared in the markup as data-withdrawn="<erratum>" and stripped
        # before scanning, so it is auditable rather than inferred from tone.
        # An undeclared figure elsewhere on the page is still a claim.
        scanned = WITHDRAWN.sub(" ", t)
        for m in WITHDRAWN.finditer(t):
            if not re.search(r'data-withdrawn="[A-Z]+-\d+"', m.group(0)):
                fails.append(f"{name} withdraws a figure without naming the erratum")
        claims = {m for m in COUNT_CLAIM.findall(scanned)} - DECLARED_COUNTS
        ok = not claims
        print(f"  {'OK  ' if ok else 'FAIL'}  {name}: 'N of 35' claims resolve to "
              f"published counts {sorted(DECLARED_COUNTS)}")
        if not ok:
            fails.append(
                f"{name} publishes {sorted(claims)} of 35 with no matching count in "
                f"the index. Publish the rule or withdraw the figure. This is the "
                f"D-104 disposition and there is no third option")

    if fails:
        print("\nDASHBOARD CHECK FAILED:")
        for f in fails:
            print(f"  x {f}")
        return 1
    print("\nDASHBOARD CHECK PASSED: the public surface agrees with the index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
