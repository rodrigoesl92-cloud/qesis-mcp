#!/usr/bin/env python3
"""Generate public/blueprint.html, the institutional risk surface.

WHY THIS FILE AND NOT A HAND EDIT OF THE PAGE. `public/blueprint.html` is an
output. `test_gate.py::check_blueprint` runs `--check` against the committed
page, so a page edited by hand fails CI on the next landing and is overwritten
by the next generator run. The writer is the artefact. Fix the writer (L-082 to
L-094).

WHAT CHANGED AT REVISION 2 (2026-08-27). The page was a validator transcript
served to a buyer: Boolean expressions, field names and internal flag keys in
the visible DOM. HERALD publishes outcomes; SENTINEL and ANALYST own the
validation record. The two are now separated by construction:

  visible DOM      outcomes only, in the register a ministry or a fund reads
  hidden metadata  the Article 12 record: expressions, statistics, flag
                   statements, model, calibration, robustness, lineage

`check_separation` is the control. It strips the compliance block and refuses
the page if any validator token survives in what a reader sees. It is not a
prose rule (L-054), it is a fixture pair: one page it must accept with the
token inside the metadata block, one it must refuse with the same token moved
into the visible DOM.

WHAT IS NOT STRIPPED. Uncertainty. HERALD's mandate forbids removing it to make
content punchier, so every route carries its consistency, its PRI and its case
count in plain sentences behind a disclosure control, and the two routes that
fail the PRI convention carry a visible verdict a buyer cannot miss. Demoted,
never deleted.

DATA PLANE. Build time, not run time. The page carries an outcome island keyed
by position, never by condition name, so nothing in it can leak an identifier.
There is no fetch, no CORS surface, no spinner and no runtime failure mode, and
`--check` can still refuse a page whose numbers have drifted from the index.

Assets read:
  data/qesis_v8.json            the index, artefact plane
  data/qesis_percolation.json   the published percolation block, PUB-1
  data/axes/cse_percolation.json the evidence the block declares it reads,
                                 used only for the per step curve, and asserted
                                 against the block at the two published points

Usage:  python scripts/build_blueprint.py [--out public/blueprint.html]
        python scripts/build_blueprint.py --check
        python scripts/build_blueprint.py --selftest
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_landing import BANNED_WORDS, TOKENS, CSS, esc, doctrine_scan  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "qesis_v8.json"
PERC = ROOT / "data" / "qesis_percolation.json"
EVID = ROOT / "data" / "axes" / "cse_percolation.json"

#: The order the model states, so a column position is stable and the outcome
#: island can be keyed by position rather than by name.
CONDITION_ORDER = ["WSE", "CABLE", "REE", "HYPER", "ESC_inv", "GCI_inv"]

#: Reader-facing label, and the authority for it. A label with authority
#: "served" comes from AXIS_NAMES in server.py or from CODEBOOK.md. A label
#: with authority "provisional" is derived from what the index states about the
#: condition and says so on the page, because two of the six conditions carry
#: no served definition of their source variable at v9.0. Never imputed
#: (D-007): the gap is published as a gap.
CONDITION_LABELS = {
    "WSE": ("Water stress", "served", "axis WSE, Water Stress Exposure. Aqueduct 4.0 baseline and SSP3."),
    "CABLE": ("Submarine cable exposure", "served", "axis CSE, Cable Stress Exposure. EMODnet density and the cable registry."),
    "REE": ("Critical minerals dependence", "served", "axis REE, Rare Earth Element Stress. USGS and CRMA."),
    "HYPER": ("Hyperscaler concentration", "served", "axis ODI, Operator Dependency Index. Concentration over facility counts."),
    "ESC_inv": ("Effective sovereignty not held", "served", "derived. Effective Sovereignty Extended is a jurisdictional and key sovereignty measure over cloud infrastructure: the mean of key sovereignty, supply chain integrity, resource sovereignty, restoration sovereignty and the jurisdictional contract average, on a zero to one scale, inverted here so the condition reads as the share a state does not hold. Five of the 35 states are collected from the pilot audit and thirty are inferred from regulatory framework assessment, and any claim resting on this condition carries that split. Codebook."),
    "GCI_inv": ("Cybersecurity commitment gap", "served", "derived. The ITU Global Cybersecurity Index, 2024 fifth edition, scores state level legal, technical and organisational cybersecurity commitments out of 100, and the condition is the remaining gap. Coverage 33 of the 35 states. Codebook."),
}

#: Column headings. The matrix has to fit the measure, and the full name with
#: its authority is one screen below in the legend, so the head can be short.
SHORT_LABELS = {
    "WSE": "Water stress",
    "CABLE": "Cable exposure",
    "REE": "Minerals",
    "HYPER": "Operator",
    "ESC_inv": "Sovereignty",
    "GCI_inv": "Cyber gap",
}

#: The corner mapping the served trilemma statement asserts. Read from that
#: statement, not decided here, and `check_statement_tokens` fails the build if
#: the statement stops carrying the tokens this mapping depends on.
TRILEMMA_CORNERS = [
    ("ai", "Algorithmic independence"),
    ("he", "Hyperscale efficiency"),
    ("es", "Ecological sustainability"),
]
TRILEMMA_EDGES = {"HYPER": ["ai", "he"], "ESC_inv": ["es"]}
TRILEMMA_UNMAPPED = ["CABLE", "REE"]
STATEMENT_TOKENS = ["HYPER", "CABLE", "REE", "ESC_inv",
                    "Algorithmic Independence", "Hyperscale Efficiency",
                    "Ecological Sustainability"]

#: Tokens that belong to the validator and must never reach a reader. The list
#: is the contract; `check_separation` is the gate over it.
VALIDATOR_TOKENS = [
    "consistency_N", "RoN", "coverage_N",
    "raw_consistency", "raw_coverage", "consistency_pri_gap",
    "pri_flag", "n_cases", "per_path", "sufficient_configurations",
    "necessity_verdict", "necessity_gate", "agent_reading_contract",
    "trilemma_status", "theory_informed_limitation", "necessity_rule",
    "HIGH_SOV_VULN", "ESC_inv", "GCI_inv", "EFF_SOV_EXT", "GCI_2024",
    "~WSE", "~CABLE", "~REE", "~HYPER", "fsqca.", "effective_weights",
]

COMPLIANCE_OPEN = '<script type="application/json" id="qesis-compliance">'
COMPLIANCE_CLOSE = "</script>"

VERDICTS = {
    "clears": ("Relied on", "vg", "This route clears the working conventions the analysis publishes."),
    "below": ("Not relied on", "vy", "This route sits below the PRI working convention of 0.75. It is published rather than dropped, and no claim rests on it alone."),
    "set_aside": ("Set aside", "vr", "This route falls below PRI 0.50, which means it is close to equally consistent with the opposite outcome. It is published for completeness and carries no weight."),
}


EXTRA_CSS = """
.hero{margin:0 0 1.2rem}
.chip{display:inline-block;font-family:var(--mono);font-size:.7rem;letter-spacing:.05em;
      text-transform:uppercase;border:1px solid var(--rule);border-radius:2px;
      padding:.15rem .45rem;margin:0 .35rem .35rem 0;color:var(--ink-3)}
.tip{display:flex;flex-wrap:wrap;gap:1.4rem;margin:1rem 0;padding:.9rem 1rem;
     background:var(--paper-2);border:1px solid var(--rule);border-radius:3px}
.tip div{min-width:8rem}
.tip b{display:block;font-family:var(--mono);font-size:1.5rem;font-weight:600;
       font-variant-numeric:tabular-nums;letter-spacing:-.02em;color:var(--cool)}
.tip span{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-3)}
.tip .peak b{color:var(--hot)}
.sec{margin:2.6rem 0 0}
.figwrap{margin:1rem 0;overflow-x:auto}
.figwrap svg{width:100%;min-width:34rem;display:block}
.b{fill:var(--paper-2);stroke:var(--rule);stroke-width:1}
.bg{fill:var(--paper-2);stroke:var(--cool);stroke-width:2}
.t{fill:var(--ink);font-family:var(--sans);font-size:12px}
.ts{fill:var(--ink-3);font-family:var(--mono);font-size:9.5px}
.tm{fill:var(--ink-2);font-family:var(--sans);font-size:10.5px}
.ar{stroke:var(--cool-2);stroke-width:1.5;fill:none}
.ah{fill:var(--cool-2)}
.tri{fill:none;stroke:var(--rule);stroke-width:1.5}
.node{fill:var(--paper);stroke:var(--cool);stroke-width:1.5}
.node-off{fill:var(--paper);stroke:var(--rule);stroke-width:1.5}
.corner{fill:var(--paper-2);stroke:var(--cool);stroke-width:1.5}
.edge{stroke:var(--cool-2);stroke-width:1.2;fill:none}
.edge-clash{stroke:var(--hot);stroke-width:1.6;fill:none;stroke-dasharray:4 3}
.axis{stroke:var(--rule);stroke-width:1;fill:none}
.grid{stroke:var(--rule);stroke-width:.6;fill:none}
.ln-t{stroke:var(--cool);stroke-width:2;fill:none}
.ln-r{stroke:var(--cool-2);stroke-width:1.6;fill:none;stroke-dasharray:5 4}
.mk-hot{stroke:var(--hot);stroke-width:1.4;fill:none}
.mk-cool{stroke:var(--cool-2);stroke-width:1.2;fill:none;stroke-dasharray:3 3}
.dot-t{fill:var(--cool)}
.dot-r{fill:var(--cool-2)}
.mtx{width:100%;border-collapse:collapse;font-size:.8rem;margin:.6rem 0;table-layout:fixed}
.mtx th{font-size:.6rem;text-transform:uppercase;letter-spacing:.02em;
        color:var(--ink-3);font-weight:600;text-align:center;padding:.35rem .15rem;
        vertical-align:bottom;line-height:1.15;overflow-wrap:anywhere}
.mtx th.lead{text-align:left;width:9.5%}
.mtx th.c{width:10.5%;letter-spacing:0;font-size:.55rem;hyphens:none}
.mtx th.st{width:7%}
.mtx th.vh{width:21%}
.mtx td:last-child{padding-right:0}
.mtx td{border-bottom:1px solid var(--rule);padding:.42rem .2rem;text-align:center}
.mtx td.lead{text-align:left;color:var(--ink)}
.mtx tr.row{cursor:pointer}
.mtx tr.row:hover td{background:var(--paper-2)}
.pip{display:inline-block;width:.72rem;height:.72rem;border-radius:50%;
     border:1.5px solid var(--cool);vertical-align:middle}
.pip.on{background:var(--cool)}
.pip.off{border-color:var(--rule)}
.vd{display:inline-block;font-family:var(--mono);font-size:.66rem;letter-spacing:.04em;
    text-transform:uppercase;border:1px solid var(--rule);border-radius:2px;
    padding:.1rem .35rem;color:var(--ink-3);white-space:nowrap}
.vd.vg{border-color:var(--cool);color:var(--cool)}
.vd.vy{border-color:var(--ink-3)}
.vd.vr{border-color:var(--hot);color:var(--hot)}
.det td{background:var(--paper-2);text-align:left;padding:.7rem .9rem}
.det p{margin:.25rem 0;font-size:.88rem}
.det .kv{font-family:var(--mono);color:var(--ink);font-size:.82rem}
.filters{margin:.6rem 0 .2rem}
.fbtn{font:inherit;font-size:.76rem;background:var(--paper);color:var(--ink-2);
      border:1px solid var(--rule);border-radius:2px;padding:.2rem .6rem;
      margin:0 .3rem .3rem 0;cursor:pointer}
.fbtn[aria-pressed="true"]{border-color:var(--cool);color:var(--cool)}
.panel{border-left:2px solid var(--cool);padding:.1rem 0 .1rem .9rem;margin:.9rem 0}
.panel h4{margin:.2rem 0 .2rem;font-size:.9rem;color:var(--ink)}
.scrub{display:flex;flex-wrap:wrap;gap:.9rem;align-items:center;margin:.5rem 0 .2rem}
.scrub input[type=range]{flex:1 1 16rem;min-width:12rem;accent-color:var(--cool)}
.read{display:flex;flex-wrap:wrap;gap:1.2rem;margin:.4rem 0 .8rem;padding:.7rem .9rem;
      background:var(--paper-2);border:1px solid var(--rule);border-radius:3px}
.read div{min-width:7rem}
.read b{display:block;font-family:var(--mono);font-size:1.15rem;font-weight:600;
        font-variant-numeric:tabular-nums;color:var(--ink)}
.read span{font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-3)}
.cut{list-style:none;margin:.6rem 0;padding:0;font-size:.85rem}
.cut li{display:flex;gap:.7rem;padding:.28rem .5rem;border-bottom:1px solid var(--rule)}
.cut li.hit{background:var(--paper-2)}
.cut .r{font-family:var(--mono);color:var(--ink-3);min-width:1.6rem}
.cut .c{flex:1}
.cut .s{font-family:var(--mono);color:var(--ink-2)}
.gap{border-left:2px solid var(--cool);padding:.1rem 0 .1rem .9rem;margin:.9rem 0}
.src{font-size:.75rem;color:var(--ink-3);margin:.3rem 0 0;font-family:var(--mono)}
.prov{font-size:.82rem}
.prov li{margin:.2rem 0;color:var(--ink-2)}
.mono{font-family:var(--mono);font-size:.82rem}
.stage{fill:var(--paper-2);stroke:var(--rule);stroke-width:1}
.stage-gate{fill:var(--paper-2);stroke:var(--cool);stroke-width:2}
.raw{fill:none;stroke:var(--rule);stroke-width:1}
.raw-node{fill:var(--paper-2);stroke:var(--ink-3);stroke-width:.8}
.refused{stroke:var(--hot);stroke-width:1.2;fill:none;stroke-dasharray:3 3}
.clean{stroke:var(--cool);stroke-width:1.6;fill:none}
.cell{fill:var(--cool);opacity:.55}
.th{fill:var(--ink);font-family:var(--sans);font-size:12.5px;font-weight:600}
.agents{margin:.8rem 0 0;padding:0;list-style:none}
.agents li{border-left:2px solid var(--rule);padding:.15rem 0 .35rem .9rem;margin:.7rem 0}
.agents b{display:block;font-size:.9rem;color:var(--ink)}
.agents .k{font-family:var(--mono);font-size:.68rem;letter-spacing:.05em;
           text-transform:uppercase;color:var(--ink-3)}
.agents p{margin:.2rem 0 0;font-size:.88rem}
.agents li.gate{border-left-color:var(--cool)}
.axpick{margin:.7rem 0 .3rem}
.axbtn{font:inherit;font-size:.76rem;background:var(--paper);color:var(--ink-2);
       border:1px solid var(--rule);border-radius:2px;padding:.2rem .55rem;
       margin:0 .3rem .3rem 0;cursor:pointer}
.axbtn[aria-pressed="true"]{border-color:var(--cool);color:var(--cool)}
.cpl{margin:.4rem 0;padding:0;list-style:none}
.cpl li{display:grid;grid-template-columns:5.6rem 1fr 3.4rem 1fr 3.4rem;gap:.5rem;
        align-items:center;padding:.3rem .2rem;border-bottom:1px solid var(--rule);
        font-size:.82rem}
.cpl .nm{color:var(--ink)}
.bar{position:relative;height:1.05rem;background:var(--paper-2);border:1px solid var(--rule)}
.bar i{position:absolute;top:0;bottom:0;left:50%;display:block}
.bar i.pos{background:var(--cool)}
.bar i.neg{background:var(--ink-3)}
.cpl .v{font-family:var(--mono);font-size:.72rem;font-variant-numeric:tabular-nums;
        text-align:right;color:var(--ink-2)}
.bar span.mid{position:absolute;left:50%;top:0;bottom:0;width:1px;background:var(--rule)}
.cplhead{display:grid;grid-template-columns:5.6rem 1fr 3.4rem 1fr 3.4rem;gap:.5rem;
         font-size:.66rem;text-transform:uppercase;letter-spacing:.05em;
         color:var(--ink-3);padding:.2rem}
"""


def parse_expression(expr: str) -> dict:
    """A solution term into a presence map. Parsing beats transcribing."""
    out = {}
    for term in expr.split("*"):
        t = term.strip()
        if not t:
            continue
        out[t.lstrip("~")] = not t.startswith("~")
    return out


def verdict_key(pri_flag: str) -> str:
    """The reader-facing verdict, derived from the published flag."""
    f = pri_flag.lower()
    if "disqualif" in f:
        return "set_aside"
    if "below" in f:
        return "below"
    return "clears"


def routes_of(doc: dict) -> list:
    """Every published route, in the shape the page and the island both use."""
    out = []
    for i, p in enumerate(doc["fsqca"]["solution"]["per_path"]):
        present = parse_expression(p["expression"])
        out.append({
            "i": i,
            "present": [bool(present.get(c)) for c in CONDITION_ORDER],
            "consistency": round(float(p["raw_consistency"]), 4),
            "pri": round(float(p["pri"]), 4),
            "coverage": round(float(p["raw_coverage"]), 4),
            "cases": int(p["n_cases"]),
            "verdict": verdict_key(p["pri_flag"]),
            "expression": p["expression"],
            "flag": p["pri_flag"],
        })
    return out


def curve_of(evid: dict, label: str) -> list:
    """One removal campaign, per step, from the evidence the block declares."""
    for c in evid["campaigns"]:
        if c["label"] == label:
            return c["curve"]
    raise KeyError(f"campaign {label} absent from the evidence")


# Plot box for the removal chart. Named once so the axis, the lines and the
# markers cannot disagree about where the origin is.
PX0, PX1, PY0, PY1 = 58.0, 734.0, 26.0, 232.0
XMAX, YMAX = 88.0, 0.72


def _px(step: float) -> float:
    return PX0 + (PX1 - PX0) * (float(step) / XMAX)


def _py(share: float) -> float:
    return PY1 - (PY1 - PY0) * (float(share) / YMAX)


def _path(points: list) -> str:
    d = []
    for k, (x, y) in enumerate(points):
        d.append(f"{'M' if k == 0 else 'L'}{x:.1f} {y:.1f}")
    return " ".join(d)


def removal_chart(evid: dict, perc: dict) -> str:
    """The fragmentation curve, drawn at build time so it survives no script.

    Two campaigns on one axis: the aimed campaign the finding is about, and the
    mean random campaign it must be compared against. The comparison is the
    claim. One curve alone says nothing.
    """
    tgt = curve_of(evid, perc["finding"]["headline_campaign"])
    rnd = curve_of(evid, "random_mean")
    two = perc["two_numbers_that_are_not_the_same_number"]
    tip = int(two["single_step_severance"]["at_removal"])
    half = int(two["half_collapse_threshold"]["at_removal"])

    pt = _path([(_px(p["step"]), _py(p["lcc_share"])) for p in tgt])
    pr = _path([(_px(p["step"]), _py(p["lcc_share"])) for p in rnd])

    ticks = []
    for s in (0, 13, 19, 44, 88):
        x = _px(s)
        ticks.append(f'<path class="grid" d="M{x:.1f} {PY1:.1f} L{x:.1f} {PY1 + 4:.1f}"/>')
        ticks.append(f'<text class="ts" x="{x:.1f}" y="{PY1 + 16:.1f}" text-anchor="middle">{s}</text>')
    for share in (0.0, 0.2, 0.4, 0.6):
        y = _py(share)
        ticks.append(f'<path class="grid" d="M{PX0:.1f} {y:.1f} L{PX1:.1f} {y:.1f}"/>')
        ticks.append(f'<text class="ts" x="{PX0 - 6:.1f}" y="{y + 3:.1f}" text-anchor="end">{int(share * 100)}%</text>')

    xt, xh = _px(tip), _px(half)
    return f"""
<svg viewBox="0 0 760 300" role="img"
     aria-label="Share of cities still connected to the main network as chokepoints
     are removed, one line for an aimed campaign and one for the mean random
     campaign, with the single step severance at removal {tip} and half collapse at
     removal {half} marked.">
  {''.join(ticks)}
  <path class="axis" d="M{PX0:.1f} {PY0:.1f} L{PX0:.1f} {PY1:.1f} L{PX1:.1f} {PY1:.1f}"/>
  <path class="mk-hot" d="M{xt:.1f} {PY0:.1f} L{xt:.1f} {PY1:.1f}"/>
  <path class="mk-cool" d="M{xh:.1f} {PY0:.1f} L{xh:.1f} {PY1:.1f}"/>
  <text class="tm" x="{xt + 6:.1f}" y="{_py(0.115):.1f}">largest single step loss, removal {tip}</text>
  <text class="tm" x="{xh + 6:.1f}" y="{_py(0.045):.1f}">half collapse, removal {half}</text>
  <path class="ln-r" d="{pr}"/>
  <path class="ln-t" d="{pt}"/>
  <circle id="dt" class="dot-t" cx="{_px(tip):.1f}" cy="{_py(tgt[tip]['lcc_share']):.1f}" r="4"/>
  <circle id="dr" class="dot-r" cx="{_px(tip):.1f}" cy="{_py(rnd[tip]['lcc_share']):.1f}" r="4"/>
  <path id="sc" class="axis" d="M{xt:.1f} {PY0:.1f} L{xt:.1f} {PY1:.1f}"/>
  <text class="tm" x="{PX0:.1f}" y="{PY1 + 34:.1f}">chokepoint cities removed</text>
  <text class="tm" x="{PX1:.1f}" y="{PY1 + 34:.1f}" text-anchor="end">aimed removal, solid. random removal, dashed.</text>
  <text class="tm" x="{PX0:.1f}" y="{PY0 - 8:.1f}">share of all cities still connected to the main network</text>
</svg>"""


def trilemma_figure(labels: dict) -> str:
    """The three corners, and the conditions that did or did not reach them.

    Drawn from what the served statement asserts. One condition reaches two
    corners, which is the collision, and two conditions reach none. That is why
    the constraint is carried as a reading of the measurements rather than as a
    variable inside the model, and the figure is the argument for it.
    """
    pos = {"ai": (556.0, 58.0), "he": (444.0, 262.0), "es": (664.0, 262.0)}
    rows = []
    edges = []
    for k, code in enumerate(CONDITION_ORDER):
        y = 46.0 + k * 44.0
        name, auth, _ = labels[code]
        mapped = TRILEMMA_EDGES.get(code, [])
        cls = "node" if mapped else "node-off"
        note = ("reaches two corners at once" if len(mapped) > 1
                else "assigned one corner it does not measure" if mapped
                else "reaches no corner" if code in TRILEMMA_UNMAPPED
                else "not named in the statement")
        rows.append(
            f'<circle class="{cls}" cx="238" cy="{y:.0f}" r="6"/>'
            f'<text class="t" x="16" y="{y - 3:.0f}">{esc(name)}</text>'
            f'<text class="ts" x="16" y="{y + 11:.0f}">{esc(note)}</text>')
        for c in mapped:
            cx, cy = pos[c]
            ecls = "edge-clash" if len(mapped) > 1 else "edge"
            edges.append(f'<path class="{ecls}" d="M244 {y:.0f} L{cx - 10:.0f} {cy:.0f}"/>')

    corners = []
    for key, title in TRILEMMA_CORNERS:
        cx, cy = pos[key]
        anchor = "middle"
        dy = -16 if key == "ai" else 26
        tx = cx
        corners.append(
            f'<circle class="corner" cx="{cx:.0f}" cy="{cy:.0f}" r="8"/>'
            f'<text class="t" x="{tx:.0f}" y="{cy + dy:.0f}" text-anchor="{anchor}">{esc(title)}</text>')

    tri = (f'M{pos["ai"][0]:.0f} {pos["ai"][1]:.0f} '
           f'L{pos["he"][0]:.0f} {pos["he"][1]:.0f} '
           f'L{pos["es"][0]:.0f} {pos["es"][1]:.0f} Z')
    return f"""
<svg viewBox="0 0 760 330" role="img"
     aria-label="Six measured conditions on the left and the three corners of the
     constraint on the right. One condition reaches two corners, two conditions
     reach none, which is why the constraint is carried as a reading rather than
     as a variable.">
  <path class="tri" d="{tri}"/>
  {''.join(edges)}
  {''.join(rows)}
  {''.join(corners)}
  <text class="tm" x="16" y="316">solid line, one corner. broken line, the same condition claimed by two corners.</text>
</svg>"""


SCRIPT = """
(function(){
 var el=document.getElementById("qesis-outcomes");
 if(!el)return;
 var D=JSON.parse(el.textContent);
 var P=D.plot;
 function px(s){return P.x0+(P.x1-P.x0)*(s/P.xmax);}
 function py(v){return P.y1-(P.y1-P.y0)*(v/P.ymax);}
 function set(id,v){var n=document.getElementById(id);if(n)n.textContent=v;}
 function move(id,s,v){var n=document.getElementById(id);
   if(n){n.setAttribute("cx",px(s).toFixed(1));n.setAttribute("cy",py(v).toFixed(1));}}
 var rows=[].slice.call(document.querySelectorAll("tr.row"));
 function toggle(r){
   var d=document.getElementById("d"+r.getAttribute("data-i"));
   if(!d)return;
   var opening=d.hasAttribute("hidden");
   if(opening){d.removeAttribute("hidden");}else{d.setAttribute("hidden","");}
   r.setAttribute("aria-expanded",opening?"true":"false");
 }
 rows.forEach(function(r){
   r.setAttribute("tabindex","0");
   r.setAttribute("role","button");
   r.setAttribute("aria-expanded","false");
   var d=document.getElementById("d"+r.getAttribute("data-i"));
   if(d)d.setAttribute("hidden","");
   r.addEventListener("click",function(){toggle(r);});
   r.addEventListener("keydown",function(e){
     if(e.key==="Enter"||e.key===" "){e.preventDefault();toggle(r);}});
 });
 var fb=[].slice.call(document.querySelectorAll(".fbtn"));
 fb.forEach(function(b){
   b.addEventListener("click",function(){
     var k=b.getAttribute("data-k");
     fb.forEach(function(o){o.setAttribute("aria-pressed",o===b?"true":"false");});
     rows.forEach(function(r){
       var show=(k==="all")||(r.getAttribute("data-k")===k);
       r.style.display=show?"":"none";
       var d=document.getElementById("d"+r.getAttribute("data-i"));
       if(d&&!show){d.setAttribute("hidden","");r.setAttribute("aria-expanded","false");}
     });
     set("rShown",rows.filter(function(r){return r.style.display!=="none";}).length);
   });
 });
 var ax=[].slice.call(document.querySelectorAll(".axbtn"));
 var panes=[].slice.call(document.querySelectorAll(".cplpanel"));
 function showAxis(code){
   panes.forEach(function(n){
     if(n.id==="cp-"+code){n.removeAttribute("hidden");}else{n.setAttribute("hidden","");}});
   ax.forEach(function(b){b.setAttribute("aria-pressed",b.getAttribute("data-ax")===code?"true":"false");});
 }
 if(ax.length&&panes.length){
   ax.forEach(function(b){
     b.addEventListener("click",function(){showAxis(b.getAttribute("data-ax"));});});
   showAxis(ax[0].getAttribute("data-ax"));
 }
 var s=document.getElementById("scrub");
 if(s&&D.perc){
   var draw=function(){
     var i=parseInt(s.value,10);
     var t=D.perc.t[i],r=D.perc.r[i];
     var prev=i>0?D.perc.t[i-1][0]:t[0];
     set("rSteps",i);
     set("rCities",t[0]);
     set("rDrop",Math.max(0,prev-t[0]));
     set("rShare",t[1].toFixed(4));
     set("rRand",r[0].toFixed(4));
     set("rPair",t[2].toFixed(4));
     move("dt",i,t[1]);move("dr",i,r[0]);
     var sc=document.getElementById("sc");
     if(sc){var x=px(i).toFixed(1);
       sc.setAttribute("d","M"+x+" "+P.y0+" L"+x+" "+P.y1);}
     [].slice.call(document.querySelectorAll(".cut li")).forEach(function(li){
       var rk=parseInt(li.getAttribute("data-r"),10);
       if(rk<=i){li.classList.add("hit");}else{li.classList.remove("hit");}
     });
   };
   s.addEventListener("input",draw);
   draw();
 }
})();
"""


def build(doc: dict, perc: dict, evid: dict) -> str:
    cp = doc["coupling"]
    g, c = cp["global"], cp["core"]
    f = doc["fsqca"]
    sol = f["solution"]
    arc = doc.get("agent_reading_contract", {})
    gr, find = perc["graph"], perc["finding"]
    two = perc["two_numbers_that_are_not_the_same_number"]
    tip = int(two["single_step_severance"]["at_removal"])
    half = int(two["half_collapse_threshold"]["at_removal"])
    cc = doc.get("citation_concordance", {})
    errata = cc.get("errata", []) or []
    ul = doc.get("uncertainty_ledger", {}) or {}
    ul_entries = ul.get("entries", []) or []
    sev = ul.get("by_severity", {}) or {}
    withheld = doc.get("epis_findings", []) or []
    ew = doc["effective_weights"]
    outside = [k for k, v in ew["axes"].items() if not v["nominal_in_ci"]]
    rts = routes_of(doc)
    counts = {k: sum(1 for r in rts if r["verdict"] == k) for k in VERDICTS}

    tgt = curve_of(evid, find["headline_campaign"])
    rnd = curve_of(evid, "random_mean")
    cut = evid.get("critical_set", []) or []

    agent_items = "".join(
        f'<li class="{"gate" if n == "SENTINEL" else ""}">'
        f'<span class="k">{esc(r)}</span><b>{esc(n)}</b>'
        f'<p>{esc(t.format(withheld=len(withheld)))}</p></li>'
        for n, r, t in AGENT_COPY)
    axis_buttons = "".join(
        f'<button class="axbtn" type="button" data-ax="{esc(a)}" '
        f'aria-pressed="{"true" if k == 0 else "false"}">{esc(a)}</button>'
        for k, a in enumerate(cp["global"]["axes"]))

    # Matrix header. Short labels only, full name and authority in the legend.
    heads = "".join(
        f'<th class="c">{esc(SHORT_LABELS[k])}</th>' for k in CONDITION_ORDER)

    body = []
    for r in rts:
        label, cls, meaning = VERDICTS[r["verdict"]]
        pips = "".join(
            f'<td><span class="pip {"on" if p else "off"}" '
            f'aria-label="{"present" if p else "absent"}"></span></td>'
            for p in r["present"])
        on = [CONDITION_LABELS[k][0] for k, p in zip(CONDITION_ORDER, r["present"]) if p]
        off = [CONDITION_LABELS[k][0] for k, p in zip(CONDITION_ORDER, r["present"]) if not p]
        body.append(
            f'<tr class="row" data-i="{r["i"]}" data-k="{r["verdict"]}">'
            f'<td class="lead">Route {r["i"] + 1}</td>{pips}'
            f'<td class="n">{r["cases"]}</td>'
            f'<td><span class="vd {cls}">{esc(label)}</span></td></tr>')
        body.append(
            f'<tr class="det" id="d{r["i"]}" hidden><td colspan="9">'
            f'<p><b>Present in this route:</b> {esc(", ".join(on)) or "none"}.</p>'
            f'<p><b>Absent in this route:</b> {esc(", ".join(off)) or "none"}.</p>'
            f'<p>States on this route: <span class="kv">{r["cases"]}</span>.</p>'
            f'<p>Agreement <span class="kv">{r["consistency"]:.4f}</span>. '
            f'Among the states that combine these conditions in this way, that is the '
            f'share which also carry high substrate vulnerability, on a zero to one scale.</p>'
            f'<p>Specificity <span class="kv">{r["pri"]:.4f}</span>. '
            f'How much of that agreement is specific to high vulnerability rather than '
            f'equally true of its opposite. The working convention is 0.75, and 0.50 is '
            f'the point below which a route is set aside.</p>'
            f'<p>Share of the outcome this route accounts for: '
            f'<span class="kv">{r["coverage"]:.4f}</span>.</p>'
            f'<p><b>Verdict.</b> {esc(meaning)}</p>'
            f'</td></tr>')

    legend = "".join(
        f'<li><b>{esc(CONDITION_LABELS[k][0])}</b>. {esc(CONDITION_LABELS[k][2])}'
        + ("" if CONDITION_LABELS[k][1] == "served"
           else ' <span class="vd">label provisional</span>')
        + "</li>"
        for k in CONDITION_ORDER)

    cut_rows = "".join(
        f'<li data-r="{int(x["rank"])}"><span class="r">{int(x["rank"])}</span>'
        f'<span class="c">{esc(x["city"])}</span>'
        f'<span class="s">{int(x["cities_severed"])} cut off</span></li>'
        for x in cut)

    island = json.dumps({
        "v": doc["vintage"],
        "plot": {"x0": PX0, "x1": PX1, "y0": PY0, "y1": PY1,
                 "xmax": XMAX, "ymax": YMAX},
        "cond": [CONDITION_LABELS[k][0] for k in CONDITION_ORDER],
        "routes": [{"p": [int(b) for b in r["present"]], "c": r["consistency"],
                    "s": r["pri"], "g": r["coverage"], "n": r["cases"],
                    "k": r["verdict"]} for r in rts],
        "perc": {
            "tip": tip, "half": half, "cities": gr["cities"],
            "t": [[p["lcc_cities"], round(p["lcc_share"], 4),
                   round(p["pair_connectivity"], 4)] for p in tgt],
            "r": [[round(p["lcc_share"], 4),
                   round(p["pair_connectivity"], 4)] for p in rnd],
        },
    }, separators=(",", ":")).replace("</", "<\\/")

    compliance = json.dumps({
        "_doc": "Article 12 record keeping. The validation record behind the "
                "visible surface, machine readable, never rendered. Emitted by "
                "scripts/build_blueprint.py at build time from the assets named "
                "in provenance.",
        "vintage": doc["vintage"],
        "provenance": {"index": "data/qesis_v8.json",
                       "percolation_block": "data/qesis_percolation.json",
                       "percolation_evidence": "data/axes/cse_percolation.json",
                       "lineage": doc.get("lineage", {})},
        "model": f["model"],
        "calibration": f["calibration"],
        "solution": {k: sol[k] for k in
                     ("type", "sufficient_configurations", "consistency",
                      "coverage", "per_path") if k in sol},
        "necessity_verdict": f.get("necessity_verdict"),
        "robustness": f.get("robustness"),
        "sensitivity": f.get("sensitivity"),
        "agent_reading_contract": arc,
        "percolation_finding": find,
        "two_numbers_that_are_not_the_same_number": two,
        "article_14": {
            "approver": "human in the loop, sole signatory on the Article 14 register",
            "gate": "SENTINEL. Nothing reaches this surface without passing it.",
            "publication_rule": "HERALD publishes only from cleared material. "
                                "Removing uncertainty to make content shorter is "
                                "forbidden, which is why every route on the visible "
                                "surface carries its agreement, its specificity and "
                                "its verdict.",
        },
    }, separators=(",", ":"), default=str)

    compliance = json.dumps(
        _doctrine_safe(json.loads(compliance)), separators=(",", ":")
    ).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QESIS+ risk surface, {esc(doc['vintage'])}</title>
<meta name="description" content="A validation pipeline that publishes what it can
 certify and withholds what it cannot. The current reading: ten routes to high
 substrate vulnerability, and a cable network that tolerates random loss and
 fails under an aimed one.">
<meta name="qesis-vintage" content="{esc(doc['vintage'])}">
<meta name="qesis-record" content="Article 12 record in the qesis-compliance block">
<meta name="qesis-oversight" content="Article 14, human in the loop, sole signatory">
<style>{TOKENS}{CSS}{EXTRA_CSS}</style>
</head><body><main>

<div class="hero">
<p><span class="chip">{esc(doc['vintage'])}</span>
   <span class="chip">continuously republished</span>
   <span class="chip">{len(withheld)} states withheld with cause</span></p>

<h1>The instrument that refuses its own bad data.</h1>

<p class="lede">This endpoint does not sell a dataset. It publishes what a
validation pipeline currently certifies, withholds what it cannot verify, and
refuses its own release when a published number stops agreeing with the source
it came from. The first thing it caught was an error in the study it was built
to support.</p>
</div>

<div class="tip">
  <div class="peak"><b>{len(errata)}</b><span>corrections raised against its own source</span></div>
  <div><b>{len(ul_entries)}</b><span>limitations published with this vintage</span></div>
  <div><b>{len(withheld)}</b><span>states withheld, never filled in</span></div>
  <div><b>{len(rts)}</b><span>routes to the same failure</span></div>
</div>

<h2 class="sec">What the pipeline caught, in its own numbers</h2>

<p>An instrument that has never contradicted the person who built it has not
been tested. This one has. {esc(errata[0]['title']) if errata else 'The concordance carries no erratum at this vintage.'}: recomputing the
declared formula from the axis columns published beside it disagreed with the
published column on most rows, and the deviation was sign ordered rather than
random. The figure was withdrawn, not softened. Every correction since is
carried in the concordance with its evidence, and {sev.get('high', 0)} of the
{len(ul_entries)} limitations on this vintage are marked high severity by the
pipeline itself.</p>

<ul class="prov">
  <li>{len(withheld)} of the 35 states carry no composite. Coverage falls below the
      declared threshold, the cause is published per state, and the value is left
      absent rather than imputed.</li>
  <li>{len(outside)} of the {len(ew['axes'])} declared weights falls outside its own
      confidence interval, estimated over {ew['n_complete']} complete cases with
      {ew['bootstrap_resamples']} resamples. The page reports the realised
      influence, not the intention.</li>
  <li>The release blocks itself. This page is regenerated from the index and the
      build fails when a figure here stops matching the asset it came from, so a
      stale number cannot reach a reader by being forgotten.</li>
</ul>
<p class="src">Assets: data/qesis_v8.json, concordance errata and uncertainty
ledger, vintage {esc(doc['vintage'])}. Provenance chain and the full validation
record travel with this page as machine readable metadata.</p>

<h2 class="sec">How a number gets from a public registry onto this page</h2>

<p>Four runtimes, one gate, and a cleared vintage that this page carries rather
than requests. Intake is deliberately permissive and emission is deliberately
strict, so everything ambiguous is settled in one place instead of in every
place. The three feeds that stop at the gate in the figure are not decoration:
they are the {len(withheld)} states whose coverage fell below the declared
threshold, withheld and published as a gap rather than filled in.</p>

<div class="figwrap">{clean_room_figure(len(withheld), len(errata), len(rts), doc['vintage'])}</div>

<ul class="agents">{agent_items}</ul>
<p class="src">Mandates summarised from sovereign-infra/agents, which remain
authoritative. The registry is closed at six runtimes; the two not drawn are
HERALD, which publishes only from cleared material, and COUNSEL, which owns
money and law. Counts derived at build time from data/qesis_v8.json.</p>

<h2 class="sec">The constraint, and why it is a reading rather than a variable</h2>

<p>Algorithmic independence, hyperscale efficiency and ecological sustainability
do not fit in one state at once. That is the claim the work is built on, and it
is carried here as an interpretation of the measurements, never as a term inside
the model. The reason is visible in the figure: one measured condition is
claimed by two corners at the same time, and two conditions belong to no corner
at all. A constraint whose corners cannot be told apart by the data cannot also
be a variable in the model that data feeds.</p>

<div class="figwrap">{trilemma_figure(CONDITION_LABELS)}</div>
<p class="src">Corner assignment read from the served statement that governs how
this claim may be used. No result on this page is described as a corner of the
constraint, because the pipeline forbids it.</p>

<p>What the measurements do price is the cost of the trade. Across
{g['n']} states the six axes are weakly entangled at {g['CR']:.3f}. Restricted to
the states that import their energy, their minerals and their hyperscalers,
entanglement rises to {c['CR']:.3f} over {c['n']} states. The constraint is cheap
where the substrate is domestic and expensive where it is imported, and the gap
between those two numbers is the whole of it.</p>

<p>That is also the only form of the constraint the measurements support you
handling directly. There is no calibrated function here that makes a corner
collapse when you raise the other two, and staging one would be inventing a law
this model does not carry. What was measured is entanglement: pick an axis and
see what is observed moving with it, across all {g['n']} states and again inside
the import core.</p>

<div class="axpick" role="group" aria-label="Choose an axis">{axis_buttons}</div>
{coupling_panels(cp)}
<p class="src">Correlation stated as correlation, not as cause. Bars run from the
centre, right for positive and left for negative, on the same scale in both
columns. Asset: data/qesis_v8.json, coupling block, vintage
{esc(doc['vintage'])}.</p>

<h2 class="sec">Ten routes to the same failure, not one</h2>

<p>There is no single road to high substrate vulnerability. The analysis returns
{len(rts)} combinations of conditions that are each sufficient on their own.
{counts['clears']} of them clear the working conventions and are relied on;
{counts['below']} sit below the specificity convention and are shown without
being relied on; {counts['set_aside']} fall far enough that they are published
for completeness and carry no weight. Nothing is dropped, because a route
removed from a public surface is a route nobody can check.</p>

<div class="filters" role="group" aria-label="Filter routes by verdict">
  <button class="fbtn" type="button" data-k="all" aria-pressed="true">All {len(rts)}</button>
  <button class="fbtn" type="button" data-k="clears" aria-pressed="false">Relied on {counts['clears']}</button>
  <button class="fbtn" type="button" data-k="below" aria-pressed="false">Shown, not relied on {counts['below']}</button>
  <button class="fbtn" type="button" data-k="set_aside" aria-pressed="false">Set aside {counts['set_aside']}</button>
</div>

<div class="scroll"><table class="mtx">
<caption class="src" style="text-align:left;caption-side:bottom">
A filled circle is a condition present in that route, an open circle is the same
condition absent. Absence is a term in the model, not a missing value. Select a
route for its agreement, its specificity and its verdict in full.</caption>
<thead><tr><th class="lead">Route</th>{heads}<th class="st">States</th><th class="vh">Verdict</th></tr></thead>
<tbody>{''.join(body)}</tbody></table></div>

<h3>What each column measures</h3>
<ul class="prov">{legend}</ul>
<p class="src">Across all {len(rts)} routes together, agreement
{sol['consistency']:.4f} and coverage {sol['coverage']:.4f} over n={f['sample']['n']}.
Coverage below one is deliberate: the solution explains the cases it covers and
declines the rest. Asset: data/qesis_v8.json, solution block, vintage
{esc(doc['vintage'])}.</p>

<div class="gap"><p><b>What is not claimed.</b> No condition is publishable as
necessary at this vintage. None reaches the conjunctive bar the pipeline
declares, and one that would have passed a weaker single test is refused by it.
The full verdict travels with this page as metadata.</p></div>

<h2 class="sec">The cable network tolerates random loss and fails under an aimed one</h2>

<p>An independent rebuild of the topology reproduces the published articulation
set exactly, {gr['articulation_cities']} of {gr['articulation_cities']}, which is
what makes the rest of this block citable. Over {gr['cities']} cities and
{gr['cables']} cables, removing chokepoints at random costs little. Removing them
in order of how much traffic they carry is a different curve entirely, and the
first twelve removals are cheap. The thirteenth is not.</p>

<div class="figwrap">{removal_chart(evid, perc)}</div>

<div class="scrub">
  <label for="scrub">Chokepoints removed</label>
  <input id="scrub" type="range" min="0" max="{len(tgt) - 1}" value="{tip}" step="1"
         aria-describedby="readout">
</div>
<div class="read" id="readout">
  <div><b id="rSteps">{tip}</b><span>removed</span></div>
  <div><b id="rCities">{tgt[tip]['lcc_cities']}</b><span>cities still connected</span></div>
  <div><b id="rDrop">{tgt[tip - 1]['lcc_cities'] - tgt[tip]['lcc_cities']}</b><span>cut off at this step</span></div>
  <div><b id="rShare">{find['targeted_at_13_removals']:.4f}</b><span>share connected, aimed</span></div>
  <div><b id="rRand">{find['random_at_13_removals']:.4f}</b><span>share connected, random</span></div>
  <div><b id="rPair">{find['pair_connectivity_after']:.4f}</b><span>pair connectivity, aimed</span></div>
</div>

<div class="tip">
  <div><b>{two['single_step_severance']['cities_severed']}</b>
       <span>cities cut off in one step, at removal {tip}</span></div>
  <div><b>{half}</b><span>removals to half collapse</span></div>
  <div><b>{find['lcc_before_tip']}</b><span>cities connected before the step</span></div>
  <div><b>{find['lcc_after_tip']}</b><span>connected after it</span></div>
</div>

<p>Those two thresholds are different quantities and are published side by side
so neither is quoted as the other. The single step severance is the largest one
step loss and it arrives at removal {tip}. Half collapse arrives later, at
removal {half}, when the connected core first falls below half its baseline. The
node at the tip in this release is {esc(find['critical_node'])}, and which city
sits there is a property of the release rather than of the finding.</p>

<h3>The removal order, as the pipeline computed it</h3>
<ol class="cut">{cut_rows}</ol>
<p class="src">Assets: data/qesis_percolation.json for every published figure,
data/axes/cse_percolation.json for the per step curve. The build asserts the two
agree at the two published points before this page is written.</p>

<h2 class="sec">What would refute all of this</h2>
<div class="gap"><p>The fragmentation finding fails if an independent topology of
comparable coverage produces an aimed removal curve whose largest single step
loss falls inside the range of its own random curve, or if the
{gr['articulation_cities']} articulation cities fail to reproduce from that
topology. A different city at the tip does not refute it. The equifinality result
fails if the solution does not survive the declared anchor sensitivity, which is
why both anchor regimes are published and their disagreement is carried as data
rather than settled by preference.</p></div>
<p class="src">Standing order: every headline finding states what would falsify
it. A finding published without one is not published here.</p>

<h2 class="sec">Point your own systems at it, rather than at this page</h2>
<p>A report nobody can act on is the failure mode this instrument was built to
avoid, so the surface is not the product. The same values this page renders are
served as tools an analyst or an agent calls directly:
<span class="mono">qesis_get_coupling</span>,
<span class="mono">qesis_get_pathways</span>,
<span class="mono">qesis_get_country</span>,
<span class="mono">qesis_rank_countries</span> and
<span class="mono">qesis_get_integrity</span>, the last of which answers which
generation you are reading and whether its chain verifies. Every figure above is
derived at build time from the assets named in the source lines, so this page
cannot say something those tools do not.</p>
<p>The deployment plane serves what was promoted and the local plane reads the
working tree, and a reader is always told which one they hold. The
<a href="/dashboard">full country dashboard</a> carries the per state profiles
and the <a href="/">index summary</a> carries the ranking and the published
gaps.</p>
<p>Nothing you do here is logged, no cookie is set and there is no backend behind
this page. The validation record travels with it as metadata rather than as a
request to a server.</p>

<footer>
<p>QESIS+ {esc(doc['vintage'])}. Batista Silva, R. (2026). Liquid Sovereignty.
ESIC/LSE. Dataset: Sovereign_Infra_Intelligence.</p>
<p>Generated {esc(doc['lineage'].get('generated_at_utc', ''))} from
data/qesis_v8.json, data/qesis_percolation.json and data/axes/cse_percolation.json.
Built by scripts/build_blueprint.py, never edited by hand.</p>
</footer>
</main>
<script type="application/json" id="qesis-outcomes">{island}</script>
{COMPLIANCE_OPEN}{compliance}{COMPLIANCE_CLOSE}
<script>{SCRIPT}</script>
</body></html>
"""


def _prose_hits(s: str) -> bool:
    """Does this string carry prose the writing doctrine refuses (W-1)?"""
    if "—" in s:
        return True
    return any(re.search(rf"\b{w}\b", s, re.I) for w in BANNED_WORDS)


def _doctrine_safe(obj, path: str = "asset"):
    """The compliance record carries pointers where the doctrine refuses text.

    The record must be complete enough to audit and must not smuggle prose the
    page would be refused for. Where a source string trips the doctrine, the
    record carries the path to it instead of the words. Nothing is silently
    dropped: the reader of the record is told where to look.
    """
    if isinstance(obj, dict):
        return {k: _doctrine_safe(v, f"{path}.{k}") for k, v in obj.items()}
    if isinstance(obj, list):
        return [_doctrine_safe(v, f"{path}[{i}]") for i, v in enumerate(obj)]
    if isinstance(obj, str) and _prose_hits(obj):
        return f"withheld from this record by the writing doctrine. Read it at {path} in the source asset."
    return obj


def visible_dom(page: str) -> str:
    """The page minus the compliance record, which is what a reader sees."""
    i = page.find(COMPLIANCE_OPEN)
    if i < 0:
        return page
    j = page.find(COMPLIANCE_CLOSE, i)
    if j < 0:
        return page
    return page[:i] + page[j + len(COMPLIANCE_CLOSE):]


def check_separation(page: str) -> list:
    """The validator does not reach the reader.

    HERALD publishes outcomes. The expressions, the field names and the internal
    flag keys belong to the validation record, which is machine readable and not
    rendered. This is the control over that split, and it is the reason the
    metadata block is delimited rather than scattered.
    """
    vis = visible_dom(page)
    return [f"validator token in the visible surface: {t}"
            for t in VALIDATOR_TOKENS if t in vis]


def check_statement_tokens(doc: dict) -> list:
    """The corner mapping is read from the served statement, so the statement
    must still carry what the mapping depends on. If the statement is rewritten,
    this fails and the figure is revisited rather than left asserting something
    the index no longer says."""
    flags = (doc.get("agent_reading_contract") or {}).get("flags") or {}
    st = (flags.get("trilemma_status") or {}).get("statement", "")
    return [f"the served trilemma statement no longer carries {t!r}"
            for t in STATEMENT_TOKENS if t not in st]


def check_evidence_agreement(perc: dict, evid: dict) -> list:
    """The animated curve and the published headline are the same object.

    The page draws its curve from the evidence the published block declares it
    reads. That is only sound if the two agree where both speak, so the build
    asserts it at the published points rather than assuming the pipeline that
    wrote one wrote the other.
    """
    bad = []
    find = perc["finding"]
    tip = int(perc["two_numbers_that_are_not_the_same_number"]
              ["single_step_severance"]["at_removal"])
    try:
        tgt = curve_of(evid, find["headline_campaign"])
        rnd = curve_of(evid, "random_mean")
    except KeyError as e:
        return [str(e)]
    # targeted_at_13_removals and random_at_13_removals are giant component
    # SHARES, not pair connectivity. Revision 1 of this page labelled them as
    # pair connectivity and served that label in public. The two quantities sit
    # in adjacent fields of the same block, the label was taken from the
    # neighbour rather than from what the value measures, and the only thing
    # that could catch it was reading the curve those fields summarise. That is
    # what these assertions do, and both quantities are now checked, each
    # against the field that actually carries it.
    checks = [
        ("cities connected after the tip", tgt[tip]["lcc_cities"], find["lcc_after_tip"]),
        ("cities connected before the tip", tgt[tip - 1]["lcc_cities"], find["lcc_before_tip"]),
        ("aimed giant component share at the tip", round(tgt[tip]["lcc_share"], 4),
         round(float(find["targeted_at_13_removals"]), 4)),
        ("random giant component share at the tip", round(rnd[tip]["lcc_share"], 4),
         round(float(find["random_at_13_removals"]), 4)),
        ("random giant component share at the last removal",
         round(rnd[len(rnd) - 1]["lcc_share"], 4),
         round(float(find["random_at_88_removals"]), 4)),
        ("aimed pair connectivity after the tip", round(tgt[tip]["pair_connectivity"], 4),
         round(float(find["pair_connectivity_after"]), 4)),
        ("aimed pair connectivity before the tip",
         round(tgt[tip - 1]["pair_connectivity"], 4),
         round(float(find["pair_connectivity_before"]), 4)),
        ("articulation cities", evid["graph"]["articulation_cities_recomputed"],
         perc["graph"]["articulation_cities"]),
    ]
    for name, got, want in checks:
        if got != want:
            bad.append(f"{name}: evidence {got!r} against the published block {want!r}")
    return bad


def check_sync(doc: dict, perc: dict, page_path: Path) -> list:
    """Has the committed page drifted from the artefacts it describes?

    Byte equality would be the wrong test the moment anything on the page
    rotates, so what is compared is what must not drift: the numbers.
    """
    if not page_path.exists():
        return [f"{page_path.name} is missing"]
    page = page_path.read_text(encoding="utf-8")
    f, cp = doc["fsqca"], doc["coupling"]
    sol = f["solution"]
    two = perc["two_numbers_that_are_not_the_same_number"]
    want = {
        "vintage": doc["vintage"],
        "global coupling": f"{cp['global']['CR']:.3f}",
        "core coupling": f"{cp['core']['CR']:.3f}",
        "solution agreement": f"{sol['consistency']:.4f}",
        "solution coverage": f"{sol['coverage']:.4f}",
        "route count": f">{sol['sufficient_configurations']}</b>",
        "cities cut off in one step": f">{two['single_step_severance']['cities_severed']}</b>",
        "removals to half collapse": f">{two['half_collapse_threshold']['at_removal']}</b>",
        "articulation cities": str(perc["graph"]["articulation_cities"]),
        "node at the tip": perc["finding"]["critical_node"],
    }
    return [f"{k} not on the page (expected {v!r})"
            for k, v in want.items() if v not in page]


def selftest() -> int:
    """One fixture each control must accept and one it must refuse (V-2).

    A check that cannot fail is a page nobody checks. Six behaviours, and the
    separation pair is the one that matters most: the same token is accepted
    inside the compliance record and refused in the visible surface, which is
    what proves the control measures the split rather than mere absence.
    """
    doc = json.loads(INDEX.read_text(encoding="utf-8"))
    perc = json.loads(PERC.read_text(encoding="utf-8"))
    evid = json.loads(EVID.read_text(encoding="utf-8"))
    page = build(doc, perc, evid)
    tmp = Path(tempfile.mkdtemp()) / "blueprint_selftest.html"
    ok = 0
    try:
        tmp.write_text(page, encoding="utf-8", newline="\n")
        good = check_sync(doc, perc, tmp)
        ok += not good
        print(f"{'PASS' if not good else 'FAIL'}  blueprint: a page built from this "
              f"index passes its own sync check")
        if good:
            print(f"        {good}")

        drifted = copy.deepcopy(doc)
        drifted["fsqca"]["solution"]["consistency"] = 0.5001
        bad = check_sync(drifted, perc, tmp)
        ok += bool(bad)
        print(f"{'PASS' if bad else 'FAIL'}  blueprint: a moved solution consistency is "
              f"refused by the sync check")

        leak = check_separation(page)
        ok += not leak
        print(f"{'PASS' if not leak else 'FAIL'}  blueprint: the built page keeps the "
              f"validator out of the visible surface")
        if leak:
            print(f"        {leak}")

        injected = page.replace("<h1>", "<p>~WSE * CABLE * REE, pri_flag</p><h1>", 1)
        caught = check_separation(injected)
        ok += bool(caught)
        print(f"{'PASS' if caught else 'FAIL'}  blueprint: a validator expression moved "
              f"into the visible surface is refused")

        drift = check_evidence_agreement(perc, evid)
        ok += not drift
        print(f"{'PASS' if not drift else 'FAIL'}  blueprint: the per step curve agrees "
              f"with the published block at the published points")
        if drift:
            print(f"        {drift}")

        hits = doctrine_scan(page)
        ok += not hits
        print(f"{'PASS' if not hits else 'FAIL'}  blueprint: the rendered page passes "
              f"the writing and render doctrine scan")
        if hits:
            print(f"        {hits}")
    finally:
        tmp.unlink(missing_ok=True)
        tmp.parent.rmdir()
    print(f"{ok}/6 blueprint behaviours verified")
    return 0 if ok == 6 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "public" / "blueprint.html"))
    ap.add_argument("--json", default=str(INDEX))
    ap.add_argument("--percolation", default=str(PERC))
    ap.add_argument("--evidence", default=str(EVID))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    doc = json.loads(Path(a.json).read_text(encoding="utf-8"))
    perc = json.loads(Path(a.percolation).read_text(encoding="utf-8"))
    evid = json.loads(Path(a.evidence).read_text(encoding="utf-8"))

    if a.check:
        bad = check_sync(doc, perc, Path(a.out))
        page = Path(a.out).read_text(encoding="utf-8") if Path(a.out).exists() else ""
        bad += check_separation(page) if page else []
        bad += check_statement_tokens(doc)
        bad += check_evidence_agreement(perc, evid)
        print(f"blueprint check against {doc['vintage']}: {len(bad)} problems")
        for b in bad:
            print(f"  x {b}")
        if bad:
            print("public/blueprint.html has drifted; run scripts/build_blueprint.py",
                  file=sys.stderr)
            return 1
        print("blueprint page is in sync with the index, keeps the validator out of "
              "the visible surface, and agrees with the percolation evidence.")
        return 0

    stale = check_statement_tokens(doc) + check_evidence_agreement(perc, evid)
    if stale:
        for s in stale:
            print(f"  x {s}")
        print("blueprint page NOT written: an input the page depends on has moved.",
              file=sys.stderr)
        return 1

    page = build(doc, perc, evid)
    hits = doctrine_scan(page)
    leak = check_separation(page)
    print(f"doctrine scan: {len(hits)} violations, separation: {len(leak)} leaks")
    for h in hits + leak:
        print(f"  x {h}")
    if hits or leak:
        print("blueprint page NOT written.", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(page) // 1024} KB) from {doc['vintage']}")
    return 0



#: What each runtime is, in the register a buyer reads, and bounded by what this
#: pipeline can evidence. Every phrase here is checkable against a control that
#: exists: no claim of realtime, none of zero error, none of immutability, and
#: no scale the sample does not carry. An overclaim on this surface is the same
#: defect as a leaked expression, one direction out instead of in.
AGENT_COPY = [
    ("SCOUT", "continuous intake",
     "Reads the declared source registry for every axis and records the vintage, "
     "the licence and the coverage at the point of collection, so a figure can "
     "always be traced back to the release it came from."),
    ("SENTINEL", "the compliance gate",
     "One gate, three verdicts, and nothing reaches the index or this page "
     "without passing it. Coverage below the declared threshold is withheld and "
     "published as a gap rather than filled in, which is why {withheld} of the 35 "
     "states carry no composite and each says why."),
    ("ANALYST", "equifinality engine",
     "Reduces the truth table of the six measured conditions to the smallest set "
     "of combinations that are each sufficient on their own, publishes the "
     "combinations it cannot rely on beside the ones it can, and states what "
     "would falsify the result."),
    ("ARCHITECT", "the island builder",
     "Writes the cleared vintage into a hash chained record this page carries "
     "with it, so a reader fetches nothing at run time and a figure that stops "
     "agreeing with its source fails the build instead of reaching a screen."),
]


def clean_room_figure(withheld: int, errata: int, routes: int, vintage: str) -> str:
    """Intake, gate, island. The pipeline as the product, drawn once.

    The left band is deliberately irregular and the right band deliberately
    regular, because that difference is the whole claim and a reader should get
    it before reading a word. The refused paths stop at the gate rather than
    fading out: a gate that never refuses anything is decoration.
    """
    # An irregular intake cluster. Positions are fixed here rather than random
    # so two builds of the same vintage produce the same bytes.
    cluster = [(28, 46), (62, 74), (22, 104), (74, 128), (36, 158), (86, 182),
               (30, 208), (68, 236), (24, 264), (92, 96), (52, 118), (96, 148),
               (46, 196), (88, 224), (58, 258)]
    nodes = "".join(f'<circle class="raw-node" cx="{x}" cy="{y}" r="3.4"/>'
                    for x, y in cluster)
    feeds = "".join(f'<path class="raw" d="M{x + 5} {y} C150 {y}, 170 66, 212 66"/>'
                    for x, y in cluster[:9])
    refused = "".join(
        f'<path class="refused" d="M{x + 5} {y} C150 {y}, 170 124, 204 124"/>'
        f'<path class="refused" d="M200 120 l8 8 M208 120 l-8 8"/>'
        for x, y in cluster[9:12])

    boxes = []
    for k, (name, role, _) in enumerate(AGENT_COPY):
        y = 44 + k * 58
        cls = "stage-gate" if name == "SENTINEL" else "stage"
        boxes.append(
            f'<rect class="{cls}" x="216" y="{y}" width="196" height="44" rx="3"/>'
            f'<text class="th" x="230" y="{y + 19}">{esc(name)}</text>'
            f'<text class="ts" x="230" y="{y + 34}">{esc(role)}</text>')
        if k < len(AGENT_COPY) - 1:
            boxes.append(
                f'<path class="ar" d="M314 {y + 44} V{y + 53}"/>'
                f'<path class="ah" d="M309 {y + 53} l5 9 5 -9 z"/>')

    grid = "".join(
        f'<rect class="cell" x="{506 + (i % 6) * 34}" y="{58 + (i // 6) * 26}" '
        f'width="26" height="18" rx="2"/>' for i in range(24))

    return f"""
<svg viewBox="0 0 760 320" role="img"
     aria-label="Three stages left to right. An irregular cluster of unverified
     source streams feeds four stacked runtimes, SCOUT then the SENTINEL gate then
     ANALYST then ARCHITECT, and a regular grid of cleared values leaves on the
     right. Three feeds stop at the gate rather than passing it.">
  {feeds}{refused}{nodes}
  <text class="th" x="16" y="26">Intake</text>
  <text class="ts" x="16" y="286">unverified at collection,</text>
  <text class="ts" x="16" y="299">every source dated and licensed</text>
  {''.join(boxes)}
  <text class="th" x="216" y="26">The clean room</text>
  <text class="ts" x="216" y="286">{withheld} states withheld here, {errata} corrections</text>
  <text class="ts" x="216" y="299">raised against the source that fed it</text>
  <path class="clean" d="M412 232 C452 232, 462 120, 500 120"/>
  <path class="ah" d="M500 115 l10 5 -10 5 z"/>
  {grid}
  <text class="th" x="506" y="26">The cleared vintage</text>
  <text class="ts" x="506" y="164">{esc(vintage)}, {routes} routes, carried by</text>
  <text class="ts" x="506" y="177">this page, fetched from nothing</text>
  <text class="ts" x="506" y="286">a figure that stops agreeing with</text>
  <text class="ts" x="506" y="299">its source fails the build</text>
</svg>"""


def coupling_panels(cp: dict) -> str:
    """The constraint, made interactive over values that were measured.

    A widget that refuses to let three sliders rise together would stage a law
    the model does not carry, and staging one is the same class of defect as
    publishing a figure the artefact does not hold. What the measurements do
    carry is entanglement, published for both sets. Selecting an axis shows what
    moves with it, correlation stated as correlation.
    """
    axes = cp["global"]["axes"]
    out = []
    for a in axes:
        rows = []
        for b in axes:
            if b == a:
                continue
            rg = float(cp["global"]["matrix"][a][b])
            rc = float(cp["core"]["matrix"][a][b])
            cells = []
            for r in (rg, rc):
                w = min(abs(r), 1.0) * 50.0
                side = (f'left:50%;width:{w:.1f}%' if r >= 0
                        else f'left:{50 - w:.1f}%;width:{w:.1f}%')
                cells.append(
                    f'<div class="bar"><span class="mid"></span>'
                    f'<i class="{"pos" if r >= 0 else "neg"}" style="{side}"></i></div>'
                    f'<span class="v">{r:+.3f}</span>')
            rows.append(f'<li><span class="nm">{esc(b)}</span>{cells[0]}{cells[1]}</li>')
        out.append(
            f'<div class="cplpanel" id="cp-{esc(a)}">'
            f'<div class="cplhead"><span>Axis</span><span>All {cp["global"]["n"]} states</span>'
            f'<span>Import core, {cp["core"]["n"]}</span></div>'
            f'<ul class="cpl">{"".join(rows)}</ul></div>')
    return "".join(out)

if __name__ == "__main__":
    raise SystemExit(main())
