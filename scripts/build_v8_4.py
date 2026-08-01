"""Derive v8.4 from the committed v8.3 index. Provenance only, no value changes.

v8.4 answers the remediation spec of 2026-08-01. It changes no axis, no composite and
no coverage figure: every number a reader has already cited from v8.3 survives it
byte-identical. What it adds is the apparatus that lets a reader tell which numbers are
citable and which are superseded, which is the thing v8.3 could not do.

  C-02  BIG withholdings carry a cause, so a reviewer is not told that Singapore and
        Taiwan are missing for the same reason. They are not.
  C-04  A citation concordance, so a reader reproducing a thesis figure against the
        live index is told the vintages differ before concluding the numbers are wrong.
  C-05  The semiconductor roadmap item carries a date and a contingency instead of an
        open-ended promise.
  D-101 to D-106, recorded as errata against the v6.6 dataset of record.

Unlike build_index.py this reads only committed artefacts, so it runs anywhere and is
part of the public repository. It is idempotent: every field is assigned outright rather
than appended to, and running it on its own output reproduces that output exactly.

Usage:  python scripts/build_v8_4.py [--in PATH] [--out PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VINTAGE = "v8.4 (2026-08-01)"
SUPERSEDES = "v8.3 (2026-07-31)"

# ── C-02. Two causes, not one ───────────────────────────────────────────────
# The instruction was to record all three as geopolitical data-accessibility
# exclusions. That is true of Taiwan and false of Hong Kong and Singapore, and a
# reviewer who checks one case against Aqueduct will reject the label for all
# three. The coverage arithmetic stays the trigger; the cause explains why the
# coverage is missing and is not itself the trigger.
WITHHOLDING = {
    "HKG": ("SOURCE_RESOLUTION",
            "Aqueduct 4.0 catchment resolution does not resolve a city-territory of "
            "this extent; no WSE value exists at source."),
    "SGP": ("SOURCE_RESOLUTION",
            "As with Hong Kong: a city-state with no resolvable catchment at the "
            "source's grid resolution; no WSE value exists at source."),
    "TWN": ("SOURCE_POLITICAL_COVERAGE",
            "Aqueduct 4.0 does not publish a separate entry for Taiwan owing to its "
            "contested status in the source's territorial schema."),
}

CAUSE_CODES = {
    "SOURCE_RESOLUTION": (
        "The source measures at a resolution that does not resolve this territory. "
        "The value is absent for a measurement reason, and no amount of access "
        "would produce it."),
    "SOURCE_POLITICAL_COVERAGE": (
        "The source's territorial schema does not carry this entity as a separate "
        "entry. The value is absent for a coverage reason that is political in "
        "origin, not measurement error and not missing data."),
}

# ── C-05. The dated scope ───────────────────────────────────────────────────
U06 = {
    "id": "U-06", "severity": "medium", "domain": "scope",
    "statement": ("No semiconductor axis exists. The February 2026 roadmap named "
                  "semiconductor capacity as the Infrastructure Pillar. Scoped as a "
                  "declared roadmap item, target vintage v9.0, 2026-12-31, contingent "
                  "on identifying a 35-state fabrication-capacity source. Until that "
                  "date the roadmap claim is stated as pending, not delivered."),
    "effect": ("Compute-fabrication dependency is unmeasured. The roadmap claim is "
               "scoped rather than unsupported: it carries a target vintage, a date "
               "and the condition that would let it ship."),
    "remedy": ("Identify a 35-state fabrication-capacity source before 2026-12-31 and "
               "derive a weight, or record the item as retired on that date. An "
               "undated roadmap item is indistinguishable from an abandoned one."),
    "target_vintage": "v9.0",
    "target_date": "2026-12-31",
    "status": "PENDING",
    "contingent_on": "a 35-state fabrication-capacity source",
    "authority": "C-05, remediation spec 2026-08-01",
}

# ── G-01, code/data atomicity: what this vintage promises to serve ──────────
# v8.4 shipped its data ahead of its code. `_refresh()` watches the index file
# and reloads it; server.py is read once at process start. The resident
# connector therefore advanced to v8.4 and served it without `chain` or
# `citation_concordance`, which are the two things v8.4 exists to add. It
# announced a vintage whose contract it half-implemented, publicly.
#
# The contract is declared in the data so the claim and the check cannot drift
# apart. verify_served_contract.py calls each tool in a fresh process and fails
# when a declared field is absent, which catches data-ahead-of-code before a
# deploy. The runtime self-report in server.py catches a stale long-lived
# process, and only from v8.4 forward: code that predates the contract cannot
# report that it is failing one.
SERVED_CONTRACT = {
    "note": ("Fields each tool must return at this vintage. Declared here so a "
             "vintage cannot be announced by a process that implements only part "
             "of it. Enforced by scripts/verify_served_contract.py in CI and "
             "self-reported under `contract` on qesis_get_integrity."),
    "authority": "G-01 code/data atomicity clause, 2026-08-01",
    "tools": {
        "qesis_get_integrity": [
            "vintage", "composite_model", "lineage", "self_check", "chain",
            "epis_findings", "withholding_causes", "uncertainty_ledger",
            "citation_concordance", "coupling_exclusions",
        ],
        "qesis_get_country": ["iso3", "vintage", "axes", "composite_exposure",
                              "coverage", "big_flags"],
        "qesis_get_methodology": ["framework", "axes", "big_protocol",
                                  "composite_model", "vintage", "citation"],
    },
    # Fields that appear only on a state whose composite is withheld. Checking
    # them against a fully covered state would fail for the right reason at the
    # wrong time, so the probe state is named rather than assumed.
    "conditional": {
        "qesis_get_country": {
            "when": "composite is withheld under BIG",
            "probe_iso3": "TWN",
            "fields": ["epis_finding", "withholding_cause", "cause_statement"],
        },
    },
}


# ── U-01 scoped rather than left as an open sourcing task ───────────────────
# Phase 1 exit criterion 6 asks for this to be sourced or permanently scoped as
# out-of-coverage with C-02's causes attached. It cannot be sourced: for two of
# the three the value does not exist at source at any resolution Aqueduct
# publishes, and for the third the source does not carry the entity. Leaving the
# remedy as "source a reading" would keep a permanent limit on a list of things
# somebody means to get to.
U01 = {
    "id": "U-01", "severity": "high", "domain": "coverage",
    "statement": ("3 of 35 states carry no composite: HKG, SGP, TWN. Water stress "
                  "is absent and coverage falls to 0.70 against the declared 0.75 "
                  "threshold. The absence has two distinct causes, published per "
                  "state as withholding_cause."),
    "effect": "Those states cannot be ranked or compared on composite.",
    "remedy": ("Scoped as permanently out of coverage against Aqueduct 4.0 rather "
               "than pending. HKG and SGP carry SOURCE_RESOLUTION: no WSE value "
               "exists at source for a catchment of that extent, so no amount of "
               "access produces one. TWN carries SOURCE_POLITICAL_COVERAGE: the "
               "source's territorial schema does not publish a separate entry. "
               "Reopening this requires a different water-stress source with "
               "city-territory resolution and its own territorial schema, which "
               "would be a new axis input and not a gap-fill."),
    "scope_status": "PERMANENT against the current source",
    "causes": {iso: code for iso, (code, _) in WITHHOLDING.items()},
    "authority": "C-02 and Phase 1 exit criterion 6, remediation spec 2026-08-01",
}

# ── D-103 supersedes U-02, which understated it ─────────────────────────────
U02 = {
    "id": "U-02", "severity": "high", "domain": "configurational",
    "statement": ("The published fsQCA is not a calibration of the published axes. "
                  "Five independent violations are recorded as D-103: identical raw "
                  "values with divergent fuzzy membership, an inverted order between "
                  "GBR and DEU on WSE, a near-constant condition present in every "
                  "sufficient path, solution statistics that are internally "
                  "inconsistent, and an outcome variable that contradicts the index "
                  "it is meant to explain."),
    "effect": ("Pathway memberships, solution statistics and necessity results in "
               "this vintage are not derived from the axes published beside them. "
               "The reported consistency of 1.000 on all three paths is an artefact "
               "of the near-constant condition, not a result."),
    "remedy": ("Re-run the fsQCA pipeline against the published axes and re-derive "
               "every anchor, or mark the chapter withdrawn pending re-run. This is "
               "not citable as it stands."),
    "supersedes_note": ("Through v8.3 this entry read as affecting only the HYPER "
                        "condition's calibration against the ordinal ODI. That "
                        "understated it: HYPER is one of five violations and not the "
                        "most serious. See errata D-103."),
    "authority": "D-103, remediation spec 2026-08-01",
}


def concordance() -> dict:
    """The v6.6 to v8.4 citation bridge, and the errata behind it."""
    return {
        "why": ("Thesis figures and the served index now differ. A reader "
                "reproducing a published figure against this endpoint is told which "
                "vintage each number belongs to before concluding that the numbers "
                "are wrong. Under G-02 the served index is authoritative on any "
                "disagreement, and the published artefact is never silently "
                "retro-fitted."),
        "mirror": "sovereign-infra/ops/CITATION_CONCORDANCE.md",
        "publication_lineage": [
            {"year": 2017, "work": "Bachelor research (PIBIC)",
             "id": "doi:10.19146/pibic-2017-77921"},
            {"year": 2026, "work": "Master's thesis, “Ontological Blind Spots”, "
                                   "MIRGE/ESIC, June 2026", "id": None},
            {"year": 2026, "work": "SSRN working paper",
             "id": "doi:10.2139/ssrn.6277938"},
            {"year": 2026, "work": "Sovereign_Infra_Intelligence v6.6, thesis dataset "
                                   "of record", "id": None},
            {"year": 2026, "work": "v8.0 to v8.1 to v8.2 to v8.3 to v8.4", "id": None},
        ],
        "framing": ("The post-thesis vintages are the methodological improvement "
                    "following from the thesis's own stated limitations at §8.6. "
                    "The SSRN deposit is the copyright instrument of record for the "
                    "STIR ecosystem."),
        "title_note": ("The deposited thesis record is the authority for the thesis "
                       "title. What v8.0 metadata withdrew was the hyphenated form of "
                       "that title used as a DATASET citation; the dataset is cited "
                       "as Sovereign_Infra_Intelligence at its vintage, and the work "
                       "as Batista Silva, R. (2026). The withdrawal was never a "
                       "statement about the thesis."),
        "rows": [
            {"figure": "§4.2 DEU composite 17.5", "thesis_value": "17.5",
             "vintage": "v6.6", "live": "recomputed",
             "status": "superseded", "erratum": "D-101"},
            {"figure": "§4.2 Δ(REE) = 74.0", "thesis_value": "74.0",
             "vintage": "v6.6", "live": "invalid",
             "status": "superseded, depends on 17.5", "erratum": "D-101"},
            {"figure": "§4.3 ODI EU 54.6 / global 44.8", "thesis_value": None,
             "vintage": "v6.6 ordinal", "live": "continuous",
             "status": "superseded", "erratum": "D-045"},
            {"figure": "§4.5 necessity REE 0.916", "thesis_value": "0.916",
             "vintage": "v6.6 fsQCA", "live": "withdrawn",
             "status": "withdrawn pending re-run", "erratum": "D-103"},
            {"figure": "§4.5 consistency 1.000 / coverage 0.920",
             "thesis_value": None, "vintage": "v6.6 fsQCA", "live": "withdrawn",
             "status": "withdrawn pending re-run", "erratum": "D-103",
             "violations": ["C", "D"]},
            {"figure": "§4.4 “27% substrate-adjusted compliance”",
             "thesis_value": "27%", "vintage": "v6.6", "live": "method unspecified",
             "status": "not reproducible", "erratum": "D-104"},
            {"figure": "§4.4 “36% of states face collapse”",
             "thesis_value": "36%", "vintage": "v6.6", "live": "threshold unspecified",
             "status": "not reproducible", "erratum": "D-104"},
            {"figure": "§4.2 ESP WSE 78.8 to 91.2 by 2050", "thesis_value": "78.8",
             "vintage": "v6.6", "live": "carried", "status": "stands", "erratum": None},
            {"figure": "§4.1 CSovE gap DEU 30% / GBR 26%", "thesis_value": "30/26",
             "vintage": "v6.6", "live": "carried", "status": "stands", "erratum": None},
            {"figure": "§3.2 cable source attributed to TeleGeography",
             "thesis_value": None, "vintage": "v6.6",
             "live": "EMODnet + SubmarineMap, 0.6/0.4 for EU states",
             "status": "thesis text is the outlier; correct the paper, not the index",
             "erratum": "U-08"},
            {"figure": "§3.3 six axes: WSE, ESE, CSE, REE, CRD, ODI",
             "thesis_value": "6", "vintage": "v6.6",
             "live": "seven: WSE, CSE, REE, FPE, ODI, RGD, ESE",
             "status": "renamed and re-slotted", "erratum": "D-106"},
        ],
        "errata": errata(),
        "id_namespace": ("D-001 to D-099 are ecosystem decisions. D-101 upward are "
                         "defects found in the v6.6 to v8.0 lineage. The ranges are "
                         "kept apart so a citation is unambiguous about whether it "
                         "names something that was decided or something that was "
                         "found."),
    }


def errata() -> list[dict]:
    """The defects behind the concordance, stated so a reviewer can check them."""
    return [
        {
            "id": "D-101", "severity": "blocking", "scope": "v6.6 and v8.0 composite",
            "title": "The QESIS Theory column is not the declared formula",
            "finding": ("The v6.6 sheet header declares WSE 0.30, CSE 0.30, ODI 0.17, "
                        "CRD 0.08, REE 0.15. Recomputing that formula from the axis "
                        "columns in the same sheet disagrees with the published "
                        "column on 30 of 32 rows by more than 2 points. The deviation "
                        "is sign-ordered: high-composite states inflated, "
                        "low-composite states deflated. The column behaves as a "
                        "rank-stretched transform, not a weighted sum."),
            "evidence": [
                {"iso3": "BHR", "published": 90.0, "recomputed": 59.2, "delta": 30.8},
                {"iso3": "KOR", "published": 65.6, "recomputed": 33.0, "delta": 32.6},
                {"iso3": "CHE", "published": 46.2, "recomputed": 20.0, "delta": 26.2},
                {"iso3": "ESP", "published": 62.8, "recomputed": 61.5, "delta": 1.3},
                {"iso3": "USA", "published": 69.9, "recomputed": 68.7, "delta": 1.2},
                {"iso3": "GBR", "published": 28.1, "recomputed": 42.6, "delta": -14.5},
                {"iso3": "ITA", "published": 25.1, "recomputed": 39.9, "delta": -14.8},
                {"iso3": "DEU", "published": 17.5, "recomputed": 29.9, "delta": -12.4},
            ],
            "consequence": ("Every composite figure in the thesis derived from QESIS "
                            "Theory is unciteable as a weighted index, including "
                            "Germany at 17.5 and its rank of 34 of 35."),
            "action": ("The v6.6 and v8.0 composite is retired. Already done in the "
                       "served index: v8.1 onward recomputes at build time. This "
                       "record exists so the thesis figures stay explainable rather "
                       "than mysterious."),
            "status": "RECORDED, index already corrected",
        },
        {
            "id": "D-102", "severity": "blocking", "scope": "v6.6 missing-data handling",
            "title": "Missing WSE handled two contradictory ways",
            "finding": ("WSE is blank for HKG, SGP and TWN in v6.6. The resulting "
                        "composites are HKG 75.2 at rank 6, TWN 75.2 at rank 6, and "
                        "SGP 1.7 at rank 35. Identical missingness produced both the "
                        "sixth-most-vulnerable and the least-vulnerable position in "
                        "the sample. HKG and TWN additionally share a byte-identical "
                        "composite and rank, which is a fill value rather than a "
                        "computation."),
            "consequence": ("Any ranking of those three states in the thesis is an "
                            "artefact of how the blank was filled, not a measurement."),
            "action": ("None needed in the served index: BIG withholds all three from "
                       "v8.1 onward. This record justifies the withholding to a "
                       "reviewer who asks why three states carry no composite."),
            "status": "RECORDED, index already correct",
        },
        {
            "id": "D-103", "severity": "blocking", "scope": "v6.6 fsQCA chapter",
            "title": "The fsQCA condition set is not a calibration of the published axes",
            "finding": ("Direct calibration is a monotonic transform of the raw value. "
                        "Five results in the published set are impossible under it."),
            "violations": [
                {"id": "A", "kind": "identical raw, divergent fuzzy",
                 "detail": "DEU and ESP both carry REE Stress 2026 of 91.5; fuzzy REE "
                           "is 0.95 for DEU and 0.30 for ESP."},
                {"id": "B", "kind": "inverted order",
                 "detail": "GBR carries WSE 26.0 with fuzzy 0.40; DEU carries WSE 40.8 "
                           "with fuzzy 0.20. The UK has lower water stress than Germany "
                           "and higher fuzzy membership."},
                {"id": "C", "kind": "near-constant condition in every path",
                 "detail": "ESC_inv across the sample: DEU 0.95, ESP 0.95, GBR 0.96, "
                           "FRA 0.90, JPN 0.94, IND 0.942, POL 0.90, ITA 0.85. It "
                           "appears in all three sufficient paths. A condition that is "
                           "high almost everywhere and present in every path yields "
                           "consistency 1.000 trivially. That is the mechanism behind "
                           "the reported Consistency 1.000 and PRI 1.000 on all three "
                           "paths: an artefact, not a result."},
                {"id": "D", "kind": "solution statistics inverted",
                 "detail": "Reported intermediate coverage 0.920 against parsimonious "
                           "coverage 0.76. The parsimonious solution uses all logical "
                           "remainders and its raw coverage is normally at or above the "
                           "intermediate. As reported the pair is internally "
                           "inconsistent."},
                {"id": "E", "kind": "outcome contradicts the index",
                 "detail": "HIGH_SOV_VULN is 0.99 for DEU, ESP and GBR, identically. "
                           "Germany's own composite ranks it 34 of 35, among the least "
                           "vulnerable. The outcome variable is not derived from the "
                           "index it is meant to explain, and the three narrative cases "
                           "share one value."},
            ],
            "consequence": ("The fsQCA chapter must be re-run, not re-cited. Every "
                            "necessity result, solution statistic and pathway "
                            "membership in it is withdrawn pending that re-run."),
            "action": ("Supersedes uncertainty ledger entry U-02, which recorded this "
                       "as affecting only the HYPER condition. U-02 is rewritten in "
                       "this vintage to carry the full scope."),
            "status": "OPEN, blocks the Phase 1 gate",
        },
        {
            "id": "D-104", "severity": "blocking", "scope": "thesis chapters IV, V, VII",
            "title": "Two headline numbers have no published method",
            "finding": ("The 27% figure is stated as EU AI Act compliance re-scored "
                        "against three QESIS+ substrate axes, and which three is never "
                        "specified. The claim that 36% of states face the risk of "
                        "infrastructure collapse carries no threshold, no axis and no "
                        "rule. Neither is reproducible."),
            "consequence": ("Both appear in three chapters and both carry rhetorical "
                            "weight. A reader cannot check either one."),
            "action": ("Publish the rule, or withdraw the figures from the SSRN "
                       "version. There is no third option that survives review."),
            "status": "OPEN, author action on the SSRN deposit",
        },
        {
            "id": "D-105", "severity": "medium", "scope": "thesis Figure 4.1",
            "title": "Figure 4.1 does not match its own caption",
            "finding": ("The caption states composite 17.5 and REE 91.5. The plotted "
                        "bars are 86 and 12. Inverting on 100 minus x gives 82.5 and "
                        "8.5, not 86 and 12. The bars preserve the delta of 74 in the "
                        "label while misstating both endpoints."),
            "action": "Redraw or relabel.",
            "status": "OPEN, author action on the SSRN deposit",
        },
        {
            "id": "D-106", "severity": "medium", "scope": "axis naming across artefacts",
            "title": "Axis count and naming drift between thesis and index",
            "finding": ("Thesis §3.3 declares six axes: WSE, ESE, CSE, REE, CRD, "
                        "ODI. The live index declares seven: WSE, CSE, REE, FPE, ODI, "
                        "RGD, ESE. CRD at weight 0.08 in v6.6 was replaced by RGD at "
                        "weight 0.08 in v8.3, the same slot carrying a different "
                        "construct. FPE is the diagnostic descendant of CRD. Thesis "
                        "Figure 4.4's caption reads Concentration of Resource "
                        "Dependency while its own axis label reads Foreign Platform "
                        "Exposure (FPE), so the published figure is already "
                        "self-contradictory."),
            "action": ("The rename and the slot substitution are recorded here "
                       "explicitly rather than left to be inferred from two documents "
                       "that disagree."),
            "status": "RECORDED",
        },
    ]


def transform(d: dict, stamp: str) -> dict:
    d = copy.deepcopy(d)
    src_vintage = d.get("vintage", "")

    # ── C-02 ────────────────────────────────────────────────────────────
    for e in d.get("epis_findings", []):
        cause = WITHHOLDING.get(e["iso3"])
        if not cause:
            raise SystemExit(f"FATAL: {e['iso3']} is withheld under BIG and C-02 "
                             f"declares no cause for it. A withholding without a "
                             f"stated cause is the string this vintage exists to "
                             f"remove.")
        e["withholding_cause"], e["cause_statement"] = cause
    d["withholding_causes"] = {
        "note": ("The coverage arithmetic is what triggers the withholding. The cause "
                 "explains why the coverage is missing and is not itself the trigger. "
                 "Both are published because a reviewer told only the arithmetic "
                 "cannot tell a measurement limit from a political one."),
        "codes": CAUSE_CODES,
        "why_not_one_label": ("Recording all three as geopolitical data-accessibility "
                              "exclusions would be accurate for Taiwan and wrong for "
                              "Hong Kong and Singapore, whose absence is a catchment "
                              "resolution limit that no access would resolve. One "
                              "label over three different causes is the kind of claim "
                              "a reviewer checks once and then distrusts throughout."),
        "authority": "C-02, remediation spec 2026-08-01",
    }

    # ── C-05 and the U-02 rewrite ───────────────────────────────────────
    entries = d["uncertainty_ledger"]["entries"]
    replacements = {"U-01": U01, "U-02": U02, "U-06": U06}
    for i, u in enumerate(entries):
        if u["id"] in replacements:
            entries[i] = replacements[u["id"]]
    d["uncertainty_ledger"]["by_severity"] = {
        s: sum(1 for u in entries if u["severity"] == s)
        for s in ("high", "medium", "low")}

    # ── C-04 ────────────────────────────────────────────────────────────
    d["citation_concordance"] = concordance()

    # ── vintage ─────────────────────────────────────────────────────────
    # `generated_at_utc` is regenerated rather than carried. The first cut of
    # this transform inherited v8.3's stamp, so v8.4 published a build time of
    # 2026-07-30T23:57Z: a day before its own vintage date and earlier than the
    # parent it derives from. On the one release whose entire subject is
    # provenance, that is the wrong field to leave carried.
    parent = d["lineage"]
    if src_vintage.startswith("v8.3"):
        # Capture the parent's own lineage rather than replacing it. The first
        # cut wrote a fresh `derived_from` over v8.3's, which erased v8.2's
        # sha256 and build stamp from the chain. A provenance transform that
        # shortens the provenance chain is working against itself.
        derived_from = {
            "vintage": SUPERSEDES,
            "generated_at_utc": parent.get("generated_at_utc"),
            "generator": parent.get("generator"),
            "derived_from": parent.get("derived_from"),
            "note": ("Provenance transform. No axis value, composite or coverage "
                     "figure changed, so the source hashes carried here remain the "
                     "provenance of every number served in v8.4."),
            "sources": parent.get("sources"),
        }
    else:
        derived_from = parent.get("derived_from")

    d["vintage"] = VINTAGE
    d["supersedes"] = SUPERSEDES
    d["lineage"]["generated_at_utc"] = stamp
    d["lineage"]["generator"] = ("scripts/build_v8_4.py applied to v8.3; see "
                                 "sovereign-infra/ops/CITATION_CONCORDANCE.md")
    d["lineage"]["derived_from"] = derived_from
    d["served_contract"] = SERVED_CONTRACT
    d["change_log_v8_4"] = [
        {"id": "C-01", "change": "Hash chain exposed on the integrity endpoint from an "
                                 "independent verifier run, with the spine committed so "
                                 "the figure is reproducible by a reader. Artefacts: "
                                 "data/chain_attestation.json, data/chain_spine.jsonl."},
        {"id": "C-02", "change": "BIG withholdings carry withholding_cause and "
                                 "cause_statement. SOURCE_RESOLUTION for HKG and SGP, "
                                 "SOURCE_POLITICAL_COVERAGE for TWN."},
        {"id": "C-04", "change": "citation_concordance added: publication lineage, 11 "
                                 "concordance rows, errata D-101 to D-106."},
        {"id": "C-05", "change": "U-06 carries target vintage v9.0, date 2026-12-31 and "
                                 "the contingency, replacing an open-ended claim."},
        {"id": "D-103", "change": "U-02 rewritten to the full scope of the fsQCA "
                                  "calibration defect. It previously recorded only the "
                                  "HYPER condition."},
        {"id": "U-01", "change": "Scoped as permanently out of coverage against "
                                 "Aqueduct 4.0 with the C-02 causes attached, replacing "
                                 "a remedy that read as a pending sourcing task."},
        {"id": "G-01", "change": "served_contract declares the fields each tool must "
                                 "return at this vintage. v8.4 shipped its data ahead "
                                 "of its code and served a vintage it half-implemented; "
                                 "this is what makes that fail a build instead."},
        {"id": "lineage", "change": "generated_at_utc is regenerated rather than carried "
                                    "from the parent, and derived_from now nests v8.3's "
                                    "own lineage instead of replacing it."},
        {"id": "scope", "change": "No axis, composite, coverage, coupling or fsQCA "
                                  "value changed. Every v8.3 number survives "
                                  "byte-identical."},
    ]
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=str(ROOT / "data" / "qesis_v8.json"))
    ap.add_argument("--out", default=str(ROOT / "data" / "qesis_v8.json"))
    ap.add_argument("--stamp", default=None,
                    help="override the build time, ISO8601 Z. For reproducing a "
                         "past build, not for routine use.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = json.loads(Path(args.src).read_text(encoding="utf-8"))
    v = src.get("vintage", "")
    if not v.startswith(("v8.3", "v8.4")):
        sys.exit(f"FATAL: input vintage is {v!r}. This transform derives v8.4 from "
                 f"v8.3, and applying it to anything else would produce a document "
                 f"whose lineage does not describe it.")

    stamp = args.stamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = transform(src, stamp)

    # Idempotence is a property, not an intention: assert it here rather than
    # trusting that every field above was assigned outright. The stamp is held
    # fixed across the two runs, because a build time that differs between them
    # is the transform working correctly rather than drifting. Everything else
    # must agree byte for byte.
    if transform(out, stamp) != out:
        sys.exit("FATAL: transform is not idempotent. Re-running it would keep "
                 "changing the served document, which makes the vintage a lie.")

    n_epis = len(out.get("epis_findings", []))
    causes = {e["iso3"]: e["withholding_cause"] for e in out["epis_findings"]}
    print(f"{out['vintage']}  supersedes {out['supersedes']}")
    print(f"  {len(out['countries'])} states, "
          f"{sum(1 for c in out['countries'].values() if c['composite'] is not None)} ranked, "
          f"{n_epis} withheld")
    for iso, c in sorted(causes.items()):
        print(f"    {iso}: {c}")
    print(f"  concordance rows: {len(out['citation_concordance']['rows'])}")
    print(f"  errata: {', '.join(e['id'] for e in out['citation_concordance']['errata'])}")

    changed = [iso for iso, c in out["countries"].items()
               if c != src["countries"][iso]]
    print(f"  country records changed: {len(changed)}{' ' + str(changed) if changed else ''}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0
    Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                              encoding="utf-8", newline="\n")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
