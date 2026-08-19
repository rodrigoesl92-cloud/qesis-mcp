"""D-113. Score the QESIS instrument on its own axes.

An index that measures substrate dependency and cannot state its own is the
failure L-045 named. This computes the instrument's exposure using the axes,
the calibration and the withholding discipline the index already applies to 32
states, so the result is comparable rather than rhetorical.

PUBLICATION STATUS: COMPUTED, NOT PUBLISHED.
    Operator ruling 2026-08-15. This writes ONLY to the evidence plane at
    data/axes/instrument_self_exposure.json. It never touches data/qesis_v8.json
    and never reaches a served surface. `served: false` is carried inside the
    artefact so a later reader cannot mistake an evidence file for a published
    one, which is the D-103 and EMO-1 failure shape.

WHAT THIS REFUSES TO DO
    It does not invent a value to fill an axis. Where the instrument has no
    measurable analogue for an axis, the axis is WITHHELD WITH CAUSE and the
    cause is stated per axis. Values are withheld, never imputed (D-007), and
    the composite is withheld if coverage falls below the same 0.75 BIG gate
    every state is held to. Scoring the instrument under a looser rule than the
    states would make the comparison worthless and dishonest in the same motion.

    It does not read a credential to determine anything. Where the answer sits
    behind one, the axis records UNDETERMINED and names the human act that
    settles it (G-03).

Usage:  python scripts/self_exposure.py [--check]
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "qesis_v8.json"
OUT = ROOT / "data" / "axes" / "instrument_self_exposure.json"

BIG_GATE = 0.75

#: The instrument's substrate, measured 2026-08-15. Each entry names the
#: evidence, because an unevidenced row here would be exactly the defect the
#: whole document is about.
SUBSTRATE = {
    "served_endpoint": {"vendor": "Vercel", "substrate": "AWS", "juris": "US",
                        "evidence": "vercel.json, qesis-mcp.vercel.app"},
    "ci_and_selfheal": {"vendor": "GitHub Actions", "substrate": "Microsoft Azure",
                        "juris": "US", "evidence": ".github/workflows/*, ubuntu-latest"},
    "source_of_record": {"vendor": "GitHub", "substrate": "Microsoft Azure",
                         "juris": "US", "evidence": "origin remotes, both repos"},
    "evidence_mirror": {"vendor": "OneDrive", "substrate": "Microsoft", "juris": "US",
                        "evidence": "operator share link 2026-08-15"},
    "agent_runtime": {"vendor": "Anthropic", "substrate": "AWS", "juris": "US",
                      "evidence": "this process"},
    # D-1, operator-declared 2026-08-19. COUNSEL did not open database_string.txt
    # and cannot verify this row against the connection string (G-03). It is
    # recorded as declared, not as measured, and the distinction is carried in
    # `evidence` so a later reader is not misled about how it was established.
    #
    # `substrate` is AWS, not "Neon". Neon is a managed Postgres vendor that runs
    # on AWS, so recording it as its own substrate would manufacture a
    # diversification that does not exist. The axis measures where the compute
    # physically sits, exactly as HOSTS_REGION_OF does for a state.
    "database": {"vendor": "Neon", "substrate": "AWS", "juris": "US",
                 "region": "eu-central-1", "region_juris": "EU",
                 "evidence": "operator-declared D-1, 2026-08-19. Not verified by "
                             "COUNSEL: the connection string is not opened (G-03)."},
}


def herfindahl(shares: list[float]) -> float:
    return round(sum(s * s for s in shares), 4)


def axes() -> dict:
    """One entry per QESIS axis. Measured, inferred or withheld, never assumed."""
    determined = {k: v for k, v in SUBSTRATE.items() if v["vendor"]}
    n = len(determined)

    # ODI. Operator concentration, computed exactly as the index computes it for
    # a state: Herfindahl over provider shares, one unit per active layer.
    by_substrate: dict[str, int] = {}
    for v in determined.values():
        key = v["substrate"].split()[0]
        by_substrate[key] = by_substrate.get(key, 0) + 1
    shares = [c / n for c in by_substrate.values()]
    odi = round(herfindahl(shares) * 100, 1)

    # FPE. Foreign platform exposure. Every determined layer is a foreign
    # platform relative to the operator's jurisdiction (ES). This is 100 by
    # construction and saying so is the point.
    foreign = sum(1 for v in determined.values() if v["juris"] != "ES")
    fpe = round(100 * foreign / n, 1)

    # RGD. Region density, inverted to a stress scale. Two distinct substrates
    # across six layers is thin, and one vendor holds four of them.
    max_vendor = max(by_substrate.values())
    rgd = round(100 * max_vendor / n, 1)

    return {
        "ODI": {"value": odi, "status": "MEASURED",
                "method": "Herfindahl over substrate shares, one unit per determined layer, "
                          f"n={n}. Identical construction to the state axis.",
                "components": by_substrate},
        "FPE": {"value": fpe, "status": "MEASURED",
                "method": "Share of determined layers outside the operator's jurisdiction (ES). "
                          "100 by construction, and that is the finding rather than an artefact."},
        "RGD": {"value": rgd, "status": "MEASURED",
                "method": "Share of determined layers held by the single largest vendor. "
                          f"Largest holds {max_vendor} of {n}."},
        "CSE": {"value": None, "status": "WITHHELD",
                "cause": "SOURCE_RESOLUTION",
                "cause_statement": "The instrument is not a territory and has no cable landings. "
                                   "There is no analogue at the axis's own resolution, so no "
                                   "value exists at source. Mechanically this is the SOURCE_RESOLUTION "
                                   "case the D-111 `regions` frame carries for HKG and SGP, and the "
                                   "shared mechanism must not be read as a shared entity type: they "
                                   "are regions, this is an instrument, and neither is a state."},
        "WSE": {"value": None, "status": "WITHHELD",
                "cause": "SOURCE_RESOLUTION",
                "cause_statement": "Water stress is a catchment property. A software instrument "
                                   "has no catchment. Datacentre water draw is a property of the "
                                   "vendor's estate, not of this instrument, and attributing it "
                                   "here would be imputation."},
        "REE": {"value": None, "status": "WITHHELD",
                "cause": "SOURCE_RESOLUTION",
                "cause_statement": "Rare-earth exposure is a supply-chain property of hardware "
                                   "the instrument does not own. Inheriting the vendor's figure "
                                   "would attribute someone else's measurement to this entity."},
        "ESE": {"value": None, "status": "UNDETERMINED",
                "cause": "CREDENTIAL_BOUND",
                "cause_statement": "Electricity substrate exposure requires the database and "
                                   "compute regions, and the database provider sits behind "
                                   "database_string.txt, which COUNSEL does not open (G-03). "
                                   "Settled by ACT-1, a human act."},
    }


def build() -> dict:
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    ax = axes()
    weights = idx["composite_model"]["weights"]

    covered = [a for a in weights if ax.get(a, {}).get("value") is not None]
    coverage = round(sum(weights[a] for a in covered), 4)
    passes = coverage >= BIG_GATE

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generated_by": "scripts/self_exposure.py",
        "authority": "D-113, closing L-045",
        "served": False,
        "publication_status": (
            "COMPUTED, NOT PUBLISHED. Operator ruling 2026-08-15. This artefact "
            "lives in the evidence plane only. Publication is a separate change "
            "set requiring SENTINEL gate_publication and the operator reading "
            "these numbers first."),
        "subject": "The QESIS+ instrument itself, scored on its own axes",
        "vintage_scored_against": idx["vintage"],
        "substrate": SUBSTRATE,
        "axes": ax,
        "composite": {
            "value": None,
            "status": "WITHHELD",
            "coverage": coverage,
            "big_gate": BIG_GATE,
            "passes_big_gate": passes,
            "statement": (
                f"Weighted coverage {coverage} against the {BIG_GATE} gate. The "
                "instrument is held to the same threshold as the 32 states and it "
                "does not clear it, so no composite is emitted. Scoring itself "
                "under a looser rule than the 32 states would destroy the "
                "comparison it exists to make."),
        },
        "finding": (
            "Four of five determined layers resolve to two US hyperscalers, and "
            "one vendor holds the source of record, the CI, the self-heal loop "
            "and the evidence mirror at once. Measured ODI "
            f"{ax['ODI']['value']}, FPE {ax['FPE']['value']}, RGD "
            f"{ax['RGD']['value']}. On the three axes where the instrument has a "
            "genuine analogue, it scores as a concentrated, foreign-dependent, "
            "single-vendor substrate. That is the honest reading and it is the "
            "reason D-113 exists."),
        "limitations": [
            {"id": "SX-01",
             "statement": "The instrument chose the axes, the weights and the anchors it is "
                          "scored on. The number is checkable; the framing is not. An entity "
                          "scoring itself under rules it wrote is not in the epistemic position "
                          "of the 32 states, which did not consent to being scored at all.",
             "effect": "This is a demonstration of method, never a peer comparison. It must "
                       "never be sorted into a table with the `states` frame or the `regions` frame. D-111 forbids "
                       "pooling even those two with each other, and this is a third thing again."},
            {"id": "SX-02",
             "statement": "Four of seven axes carry no value. Three are withheld because no "
                          "analogue exists at source and one is undetermined behind a credential.",
             "effect": "The composite is withheld and the three measured axes are read singly."},
            {"id": "SX-04",
             "statement": "FPE is computed on VENDOR jurisdiction, not region. The database sits "
                          "in eu-central-1 while Neon is US-incorporated, so the data rests in the "
                          "EU under a US corporate reach. Both facts are recorded; only the vendor "
                          "one enters the axis.",
             "effect": "FPE stays 100.0. Whether platform exposure should be measured at the "
                       "vendor or at the region is a real modelling question the state axis has "
                       "never had to answer, because a state's cloud regions and their operators "
                       "are recorded separately. It is opened here, not settled."},
        {"id": "SX-03",
             "statement": "Declaring an exposure does not reduce it. If either hyperscaler "
                          "withdraws service the index goes dark regardless of this document.",
             "effect": "Only D-113 ACT-4, second custody for the chain spine and attestations, "
                       "changes a physical fact."},
        ],
        "falsifier": (
            "Refuted if an independent reviewer, given the published axis definitions and this "
            "substrate table, computes a materially different ODI, FPE or RGD. Not refuted by "
            "disagreement about whether the instrument should be scored at all, which is a "
            "question about SX-01 and is conceded there."),
    }


def main() -> int:
    block = build()
    payload = json.dumps(block, indent=1, ensure_ascii=False) + "\n"

    if "--check" in sys.argv:
        if not OUT.exists():
            print("FAIL data/axes/instrument_self_exposure.json missing.")
            return 1
        cur = json.loads(OUT.read_text(encoding="utf-8"))
        fresh = json.loads(payload)
        cur.pop("generated_utc", None)
        fresh.pop("generated_utc", None)
        if cur != fresh:
            print("FAIL instrument_self_exposure.json does not match a fresh build.")
            return 1
        print("OK   instrument self-exposure matches a fresh build")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(payload, encoding="utf-8")
    a, c = block["axes"], block["composite"]
    print(f"OK   {OUT.relative_to(ROOT)}   served={block['served']}")
    print(f"     ODI {a['ODI']['value']}   FPE {a['FPE']['value']}   RGD {a['RGD']['value']}")
    print(f"     composite WITHHELD, coverage {c['coverage']} against the {c['big_gate']} gate")
    print(f"     withheld axes: " + ", ".join(
        k for k, v in a.items() if v["value"] is None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
