"""Bump the served index to a new vintage. The writer that did not exist.

WHY THIS FILE EXISTS
--------------------
GEN-1, and it is worse than the ticket said. The ticket recorded that the
citation concordance had no live generator. The truth is that the whole served
index has had none since v8.4:

  build_index.py    declares itself "the ONLY sanctioned writer of the served
                    index" and hardcodes "vintage": "v8.2 (2026-07)".
  build_v8_4.py     refuses to run against anything but v8.3.
  qesis_v8.json     carries no generated_by and no built_at.

So five vintages were carried by hand, and RELEASE.ps1 cut branches, bound the
chain and ran the gates without ever changing the artefact it named. It
certified v8.9 as publishable and labelled the branch v9.0. Production then
served v8.9 forever, correctly, because that is what the repository contained.

The failure was not Vercel, GitHub, or the merge. It was that a release script
which does not write the vintage it names will mislabel every vintage.

WHAT THIS DOES, AND WHAT IT REFUSES
------------------------------------
It changes exactly three things and asserts everything else is untouched:

    vintage      -> the new tag
    supersedes   -> the tag that was there
    change_log   -> one dated entry naming the ticket and what closed

It refuses to run if:
  · the new vintage is not strictly newer than the current one
  · the change set is empty (a vintage with no change is a lie)
  · any key other than the three above changed (asserted by diffing keys)
  · the dashboard is not updated in the same run (R1.27 would catch it later,
    which is too late: the artefact would already be committed)

It does NOT recompute scores, weights or axes. A vintage that changes an
analytical value is a different operation and must go through the axis
pipeline, not through here. This is a metadata release: it publishes work that
is already in the evidence plane.

Usage:
    python scripts/bump_vintage.py --vintage "v9.0 (2026-08-13)" \
        --ticket QT-0007 --note "provenance-complete vintage" [--apply]

Exit: 0 ok · 1 refused · 2 could not run
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "qesis_v8.json"
DASH = ROOT / "STIR_Governance_Dashboard.html"

TAG = re.compile(r"^v(\d+)\.(\d+) \((\d{4}-\d{2}-\d{2})\)$")


def parse(tag: str) -> tuple[int, int, str]:
    m = TAG.match(tag)
    if not m:
        raise ValueError(
            f"vintage must look like 'v9.0 (2026-08-13)', got {tag!r}")
    return int(m.group(1)), int(m.group(2)), m.group(3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vintage", required=True)
    ap.add_argument("--ticket", required=True)
    ap.add_argument("--note", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if not re.match(r"^QT-\d{4}$", a.ticket):
        print(f"REFUSED: --ticket must look like QT-0007, got {a.ticket!r}")
        return 1

    if not INDEX.exists():
        print(f"REFUSED: {INDEX} not found")
        return 2

    raw = INDEX.read_text(encoding="utf-8")
    idx = json.loads(raw)
    before_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    current = idx.get("vintage")

    print(f"  current vintage : {current}")
    print(f"  requested       : {a.vintage}")
    print(f"  current sha256  : {before_sha[:16]}")

    try:
        new_major, new_minor, new_date = parse(a.vintage)
        cur_major, cur_minor, _ = parse(current)
    except ValueError as exc:
        print(f"\nREFUSED: {exc}")
        return 1

    # A vintage must move forward. Re-cutting the same tag with different bytes
    # is how a published sha256 stops meaning anything.
    if (new_major, new_minor) <= (cur_major, cur_minor):
        print(f"\nREFUSED: {a.vintage} is not newer than {current}.")
        print("Re-cutting a published tag with different bytes breaks every")
        print("citation of its index_sha256.")
        return 1

    if new_date != date.today().isoformat():
        print(f"\n  note: vintage date {new_date} is not today "
              f"({date.today().isoformat()}). Permitted, but say why in the log.")

    after = copy.deepcopy(idx)
    after["vintage"] = a.vintage
    after["supersedes"] = current

    entry = {
        "vintage": a.vintage,
        "ticket": a.ticket,
        "date": new_date,
        "note": a.note,
        "supersedes": current,
        "kind": "metadata release",
        "analytical_values_changed": False,
        "statement": (
            "This vintage publishes work already recorded in the evidence "
            "plane. No score, weight or axis value was recomputed. A vintage "
            "that changes an analytical value goes through the axis pipeline, "
            "not through bump_vintage.py."),
    }
    log = after.setdefault("change_log_vintages", [])
    if any(e.get("vintage") == a.vintage for e in log):
        print(f"\nREFUSED: change_log already has an entry for {a.vintage}.")
        return 1
    log.append(entry)

    # Assert the blast radius. Anything beyond these three keys means this
    # script did something it does not claim to do, and the operator would have
    # no way to know. Fail loudly rather than publish a surprise.
    allowed = {"vintage", "supersedes", "change_log_vintages"}
    changed = {k for k in set(idx) | set(after)
               if json.dumps(idx.get(k), sort_keys=True, default=str)
               != json.dumps(after.get(k), sort_keys=True, default=str)}
    if changed - allowed:
        print(f"\nREFUSED: unexpected keys changed: {sorted(changed - allowed)}")
        return 1
    print(f"  keys changed    : {sorted(changed)}  (as declared)")

    new_raw = json.dumps(after, indent=1, ensure_ascii=False) + "\n"
    after_sha = hashlib.sha256(new_raw.encode("utf-8")).hexdigest()
    print(f"  new sha256      : {after_sha[:16]}")

    # The dashboard must move with the index. R1.27 refuses a public surface
    # that contradicts the index, and catching it after the commit is too late.
    dash_hits = 0
    dash_new = None
    if DASH.exists():
        dtext = DASH.read_text(encoding="utf-8")

        # Replacing only the exact dated string is not enough and quietly was
        # not: the dashboard carries the bare tag in the title, the citation
        # block, the footer and its own embedded data blob, and one of those
        # blobs dates v8.9 as (2026-06), which no exact-string match reaches.
        # verify_dashboard refuses ANY superseded vN.M token, so a one-hit
        # replacement leaves the gate red with the writer reporting success.
        # Two passes, widest first: any dated form of the old tag, then any
        # bare occurrence of it.
        cur_tag, new_tag = f"v{cur_major}.{cur_minor}", f"v{new_major}.{new_minor}"
        dated = re.compile(re.escape(cur_tag) + r" \(\d{4}-\d{2}(?:-\d{2})?\)")
        bare = re.compile(re.escape(cur_tag) + r"(?!\d)")

        dash_new, n_dated = dated.subn(a.vintage, dtext)
        dash_new, n_bare = bare.subn(new_tag, dash_new)
        dash_hits = n_dated + n_bare
        print(f"  dashboard       : {n_dated} dated + {n_bare} bare occurrence(s) "
              f"of {cur_tag}")
        if dash_hits == 0:
            print("\nREFUSED: the dashboard does not mention the current vintage,")
            print("so this script cannot know it was updated. Check it by hand.")
            return 1
        # Scoped to the outgoing vintage family, which is what verify_dashboard
        # scans for, and NOT to every vN.M token on the page. The page cites
        # third-party dataset versions (Climate TRACE v5.4) that are nobody's
        # vintage and must survive a bump untouched. A guard that cannot tell a
        # source version from a vintage would refuse every correct release.
        # Subtracting new_tag is load-bearing on a same-major bump. v9.0 -> v9.1
        # leaves the page full of correct v9.1 tokens that this very pattern
        # matches, so without the subtraction the guard refuses every valid
        # successor within a major. Caught by the acceptance fixture, which is
        # the half of V-2 that refusal fixtures alone would never have found.
        stale = sorted(set(re.findall(rf"v{cur_major}\.\d+(?!\d)", dash_new))
                       - {new_tag})
        if stale:
            print(f"\nREFUSED: the dashboard still names {stale} after the "
                  f"rewrite. verify_dashboard would fail after the commit.")
            return 1
    else:
        print("\nREFUSED: dashboard not found; R1.27 would fail after the commit.")
        return 1

    if not a.apply:
        print("\ndry run. Nothing written. Pass --apply.")
        print("Then run, in this order, and do not skip any:")
        print("  python scripts/verify_index.py")
        print("  python scripts/verify_dashboard.py")
        print("  python scripts/test_gate.py")
        return 0

    # newline="\n" is load-bearing, not tidiness. write_text() with the default
    # newline=None translates every \n to os.linesep, which on Windows is \r\n.
    # after_sha is computed over the LF string above, so without this the writer
    # announces a sha256 of bytes it did not write: the artefact lands as CRLF
    # and hashes to something else entirely. .gitattributes pins this repository
    # to eol=lf (L-063) and every recorded artifact hash in the lineage register
    # is the LF hash, so LF is the artefact's true form and the announcement is
    # what was wrong.
    INDEX.write_text(new_raw, encoding="utf-8", newline="\n")
    DASH.write_text(dash_new, encoding="utf-8", newline="\n")

    # Read the bytes back and prove the announced fingerprint fingerprints them.
    # A writer that publishes a hash of something other than what it wrote is the
    # defect this whole release exists to correct, one layer down: the index
    # sha256 is served as provenance.index_sha256 under G-01b and compared
    # against the promoted commit by vercel_promote.py. Assert it here, at the
    # only point where both the intent and the result are in hand.
    on_disk = hashlib.sha256(INDEX.read_bytes()).hexdigest()
    if on_disk != after_sha:
        print(f"\nREFUSED after write: announced sha256 {after_sha[:16]} but the "
              f"bytes on disk hash to {on_disk[:16]}. The artefact and its "
              f"fingerprint disagree; do not commit this tree.")
        return 1

    print(f"\nWRITTEN. {current} -> {a.vintage}")
    print(f"  index    {INDEX.relative_to(ROOT)}  sha256 {after_sha[:16]}  "
          f"(verified against the bytes on disk)")
    print(f"  dashboard {DASH.relative_to(ROOT)}  {dash_hits} occurrence(s)")
    print("\nThe gates have NOT been run. This script writes; it does not")
    print("certify. Run verify_index, verify_dashboard and test_gate now.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
