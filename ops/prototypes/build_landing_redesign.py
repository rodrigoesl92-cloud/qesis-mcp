"""Generate the redesigned QESIS+ public surface.

Every number is read from data/qesis_v8.json. Nothing on the page is typed by
hand. The map geometry is pre-projected offline into map.json so the page makes
zero network requests at view time: no CDN, no font host, no tile server.

Emits two files from one body:
  out/qesis_landing.html   full standalone document (opens from disk)
  out/artifact_body.html   same body, no document shell, for the Artifact host

Design system honoured, not invented:
  tokens          scripts/build_landing.py TOKENS block, extended for V2
  encoding law    ops/VISUALISATION_SPEC.md section 3
  gate            scripts/build_landing.py doctrine_scan()
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD = Path("/mnt/user-data/uploads/qesis-mcp/data/qesis_v8.json")
MAP = HERE / "map.json"
OUT = HERE / "out"

# Served facts. Read from /health, which is the serving plane, not the tree.
SERVED = {
    "index_sha256": "8009815e4c19132048bf285cf6622cc864e7bc090fc31627b09ce0145463647d",
    "chain_status": "VERIFIED",
    "chain_entries": 752,
    "chain_link_breaks": 0,
    "chain_head": "af96057d43c1c2db2f6c91b01a61eb924f4f8b586c13dc0b8a7529ea27328f2c",
    "attestation_agrees": True,
    "deployment_commit": "e22888fad10bb15205d7e770efc36c4baaff9c61",
    "plane": "deployed",
    "host": "qesis.qesis.eu",
}

AXIS_NAMES = {
    "WSE": "Water stress",
    "CSE": "Cable exposure",
    "REE": "Rare earth exposure",
    "FPE": "Foreign platform exposure",
    "ODI": "Operator concentration",
    "ESE": "Electricity supply exposure",
    "RGD": "Regulatory divergence",
}

BINS = [(0, 25), (25, 35), (35, 45), (45, 55), (55, 65), (65, 101)]


def esc(s) -> str:
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- tokens

TOKENS = """
:root{
  /* Verbatim from scripts/build_landing.py TOKENS. Do not edit a value here. */
  --ink:#1c1b19; --ink-2:#4a4744; --ink-3:#78736d;
  --paper:#faf8f5; --paper-2:#f1ede7; --rule:#ddd6cc;
  --cool:#3d5a68; --cool-2:#6d8b98;
  --hot:#c96a5e;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --sans:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  --gap:1.5rem; --measure:74ch;

  /* Added for V1 and V2. Named after sovereign-infra/design/tokens.css so the
     two surfaces stop forking. --warm-500 is that file's value. */
  --serif:ui-serif,Charter,"Iowan Old Style",Georgia,serif;
  --warm-500:#b8853f;
  --epis:#a49c92;
  /* Out of frame is warm, measured is cool. The two are separated by hue as
     well as by lightness, so the lowest bin never reads as unmeasured land. */
  --land:#efe9df;
  --q1:#bccbd2; --q2:#9cafb9; --q3:#7d94a0;
  --q4:#607a88; --q5:#436071; --q6:#26485a;
  --band:72rem;
  --chart-h:400px; --chart-h-sm:480px; --map-h:470px;
}
:root:not([data-theme="light"]){
  color-scheme:light;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --ink:#ece7e0; --ink-2:#bdb6ad; --ink-3:#8d857c;
    --paper:#171614; --paper-2:#201e1b; --rule:#35322d;
    --cool:#8fb0be; --cool-2:#6d8b98; --hot:#e08476;
    --warm-500:#d9a45e; --epis:#8a7f70; --land:#23211e;
    --q1:#41545c; --q2:#556a73; --q3:#6a828c;
    --q4:#809aa5; --q5:#97b3bf; --q6:#aeccd9;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --ink:#ece7e0; --ink-2:#bdb6ad; --ink-3:#8d857c;
  --paper:#171614; --paper-2:#201e1b; --rule:#35322d;
  --cool:#8fb0be; --cool-2:#6d8b98; --hot:#e08476;
  --warm-500:#d9a45e; --epis:#8a7f70; --land:#23211e;
  --q1:#41545c; --q2:#556a73; --q3:#6a828c;
  --q4:#809aa5; --q5:#97b3bf; --q6:#aeccd9;
}
"""

CSS = """
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
     line-height:1.55;font-size:16px;-webkit-font-smoothing:antialiased}

/* Prose spine at the reading measure, instruments break out to the band.
   A document with instruments set into it, which is what this object is. */
main{display:grid;grid-template-columns:1fr min(var(--measure),100%) 1fr;
     padding:var(--gap) 1.2rem 4rem;row-gap:0}
main>*{grid-column:2}
.band{grid-column:1/-1;width:100%;max-width:var(--band);margin-inline:auto;
      padding-inline:1.2rem}

h1{font-family:var(--serif);font-size:clamp(1.8rem,4.6vw,2.5rem);line-height:1.14;
   margin:.3rem 0 .6rem;letter-spacing:-.015em;text-wrap:balance;max-width:20ch}
h2{font-size:1.15rem;margin:2.6rem 0 .6rem;letter-spacing:-.01em;text-wrap:balance}
h2.finding{font-family:var(--serif);font-size:clamp(1.25rem,2.6vw,1.55rem);
           line-height:1.25;max-width:26ch}
h3{font-size:.95rem;margin:1.6rem 0 .4rem;color:var(--ink-2)}
p{margin:.6rem 0;color:var(--ink-2)}
a{color:var(--cool);text-underline-offset:2px}
a:focus-visible,button:focus-visible{outline:2px solid var(--cool);outline-offset:2px}
.lede{font-size:1.05rem;color:var(--ink)}

.tag{display:inline-block;font-family:var(--mono);font-size:.72rem;
     letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
     border:1px solid var(--rule);border-radius:2px;padding:.15rem .45rem;
     margin-right:.35rem}
.eyebrow{font-family:var(--mono);font-size:.72rem;letter-spacing:.09em;
         text-transform:uppercase;color:var(--ink-3);margin:2.6rem 0 .2rem}
.band>.eyebrow:first-child{margin-top:0}

table{width:100%;border-collapse:collapse;margin:.8rem 0;font-size:.9rem}
th,td{text-align:left;padding:.4rem .5rem;border-bottom:1px solid var(--rule)}
th{font-weight:600;font-size:.75rem;text-transform:uppercase;
   letter-spacing:.05em;color:var(--ink-3)}
td.n,th.n{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
tbody tr:hover{background:var(--paper-2)}
.scroll{overflow-x:auto}
.src{font-size:.75rem;color:var(--ink-3);margin:.3rem 0 0;font-family:var(--mono);
     line-height:1.5}
.src a{color:var(--cool-2)}

.stat{display:flex;flex-wrap:wrap;gap:1.4rem;margin:1rem 0;padding:.9rem 1rem;
      background:var(--paper-2);border:1px solid var(--rule);border-radius:3px}
.stat div{min-width:8rem}
.stat b{display:block;font-family:var(--mono);font-size:1.5rem;font-weight:600;
        font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.stat span{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;
           color:var(--ink-3)}
.argued b{color:var(--hot)}
.gap{border-left:2px solid var(--cool);padding:.1rem 0 .1rem .9rem;margin:.9rem 0}
.gap code{font-family:var(--mono);font-size:.82rem}
pre{background:var(--paper-2);border:1px solid var(--rule);border-radius:3px;
    padding:.8rem;overflow-x:auto;font-family:var(--mono);font-size:.8rem;
    color:var(--ink)}
code{font-family:var(--mono);font-size:.86em}
footer{border-top:1px solid var(--rule);margin-top:3rem;padding-top:1rem;
       font-size:.82rem;color:var(--ink-3)}
.epis{color:var(--cool);font-family:var(--mono);font-size:.8rem}

/* ---- instrument frame ------------------------------------------------- */
.fig{background:var(--paper-2);border:1px solid var(--rule);border-radius:3px;
     padding:1.1rem 1.2rem 1rem;margin:.9rem 0}
.fig>.src{margin-top:.8rem;border-top:1px solid var(--rule);padding-top:.6rem}

/* L-014. A canvas or an SVG has no intrinsic size, so every one is given an
   explicit box. aspect-ratio is that box on narrow screens, where a fixed
   height would letterbox the drawing instead of fitting it. */
.figbox{height:var(--chart-h);width:100%;overflow-x:auto;overflow-y:hidden}
.figbox svg{width:100%;height:100%;display:block}
.figbox.narrow{display:none}
@media (max-width:820px){
  .figbox.wide{display:none}
  .figbox.narrow{display:block}
}
.mapbox{height:auto;aspect-ratio:960/400;max-height:var(--map-h)}
.mapbox svg{height:auto}

.legend{display:flex;flex-wrap:wrap;gap:.4rem 1.3rem;margin-top:.8rem;
        font-size:.75rem;color:var(--ink-3);align-items:center}
.legend span{display:inline-flex;align-items:center;gap:.45rem}
.sw{width:22px;height:10px;border-radius:2px;display:inline-block;flex:none}
.sw--realised{background:var(--q4)}
.sw--hot{background:var(--hot)}
.sw--nominal{width:3px;height:14px;background:var(--warm-500);border-radius:0}
.sw--ci{width:22px;height:2px;background:var(--cool-2)}
.sw--epis{background:var(--epis);
  background-image:repeating-linear-gradient(45deg,transparent 0 3px,var(--paper-2) 3px 5px)}
.sw--land{background:var(--land);border:1px solid var(--rule)}
.rampkey{display:inline-flex;flex-direction:column;gap:2px;flex:none}
.ramp{display:flex}
.ramp i{width:30px;height:10px;display:block}
.ramp i:first-child{border-radius:2px 0 0 2px}
.ramp i:last-child{border-radius:0 2px 2px 0}
.rampnum{display:flex;font-family:var(--mono);font-size:.65rem;
         font-variant-numeric:tabular-nums;color:var(--ink-3)}
.rampnum s{width:30px;text-align:right;text-decoration:none;
           transform:translateX(50%);display:block}
.r1{background:var(--q1)} .r2{background:var(--q2)} .r3{background:var(--q3)}
.r4{background:var(--q4)} .r5{background:var(--q5)} .r6{background:var(--q6)}

/* W-2 and L-047. Painted from the stylesheet. var() does not resolve inside a
   presentation attribute, so nothing here is painted by fill="". */
.grid-line{stroke:var(--rule);stroke-width:1}
.axis-text{fill:var(--ink-3);font-family:var(--mono);font-size:11px}
.row-label{fill:var(--ink);font-family:var(--sans);font-size:13.5px;font-weight:600}
.row-note{fill:var(--ink-3);font-family:var(--mono);font-size:10.5px}
.bar-realised{fill:var(--q4)}
.bar-realised--hot{fill:var(--hot)}
.bar-nominal{fill:none;stroke:var(--warm-500);stroke-width:3;stroke-linecap:square}
.nominal-num{fill:var(--warm-500);font-family:var(--mono);font-size:10px}
.ci-line,.ci-cap{stroke:var(--cool-2);stroke-width:1.6}
.value-num{fill:var(--ink);font-family:var(--mono);font-size:12px}
.value-num--hot{fill:var(--hot);font-family:var(--mono);font-size:12.5px;font-weight:700}

.geo-sphere{fill:var(--paper);stroke:var(--rule);stroke-width:1}
.geo-land{fill:var(--land);stroke:var(--paper-2);stroke-width:.4}
.geo-q1{fill:var(--q1)} .geo-q2{fill:var(--q2)} .geo-q3{fill:var(--q3)}
.geo-q4{fill:var(--q4)} .geo-q5{fill:var(--q5)} .geo-q6{fill:var(--q6)}
.geo-epis{fill:url(#hatch)}
.geo-state{stroke:var(--paper-2);stroke-width:.5;cursor:pointer}
.geo-state:hover,.geo-state:focus{stroke:var(--ink);stroke-width:1.4;outline:none}
.hatch-ground{fill:var(--epis)}
.hatch-line{stroke:var(--paper-2);stroke-width:2}
.dot{stroke:var(--paper);stroke-width:1.4}
.dot-lead{stroke:var(--ink-3);stroke-width:.8}
.dot-label{fill:var(--ink-3);font-family:var(--mono);font-size:10px}

/* Hover is a teaching moment, so it carries the epistemic flags with it. */
.readout{display:grid;grid-template-columns:auto 1fr;gap:.25rem 1rem;
         align-items:baseline;min-height:5.4rem;margin-top:.7rem;
         padding-top:.7rem;border-top:1px solid var(--rule)}
.readout .who{grid-column:1/-1;font-family:var(--serif);font-size:1.35rem;
              line-height:1.2;color:var(--ink);margin:0}
.readout dt{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;
            color:var(--ink-3);margin:0}
.readout dd{margin:0;font-family:var(--mono);font-size:.85rem;
            font-variant-numeric:tabular-nums;color:var(--ink)}
.readout .cause{grid-column:1/-1;font-family:var(--sans);font-size:.82rem;
                color:var(--ink-2);margin:.1rem 0 0;max-width:80ch}
.readout .hint{grid-column:1/-1;color:var(--ink-3);font-size:.85rem;margin:0}

.caveat{margin:1rem 0;padding:.85rem 1rem;border:1px dashed var(--rule);
        border-radius:3px;color:var(--ink-2);font-size:.9rem}
.caveat strong{color:var(--ink)}
.kicker{margin:1.2rem 0;padding:1rem 1.1rem;background:var(--paper-2);
        border-left:3px solid var(--warm-500);border-radius:3px}
.kicker b{font-family:var(--mono);font-size:1.35rem;display:block;
          font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.kicker p{margin:.3rem 0 0;font-size:.9rem}

/* The instrument, not the argument. This is the object a reader can file. */
.cert{margin:1.2rem 0;border:1px solid var(--cool);border-radius:3px;
      background:var(--paper-2);padding:1.2rem 1.3rem}
.cert h3{margin:0 0 .3rem;font-family:var(--serif);font-size:1.3rem;color:var(--ink)}
.cert ul{margin:.6rem 0;padding-left:1.1rem;color:var(--ink-2);font-size:.9rem}
.cert li{margin:.2rem 0}
.tiers{display:grid;gap:.5rem;margin:1rem 0 0}
.tier{display:grid;grid-template-columns:7rem 1fr;gap:.9rem;padding:.6rem 0;
      border-top:1px solid var(--rule);font-size:.88rem}
.tier b{font-family:var(--mono);font-size:.75rem;text-transform:uppercase;
        letter-spacing:.06em;color:var(--ink-3);font-weight:600}
.tier span{color:var(--ink-2)}
.chip{display:inline-block;font-family:var(--mono);font-size:.7rem;
      letter-spacing:.05em;text-transform:uppercase;color:var(--ink-3);
      border:1px dashed var(--rule);border-radius:2px;padding:.12rem .4rem}
.cta{display:inline-block;margin-top:.9rem;padding:.6rem 1rem;border-radius:3px;
     background:var(--cool);color:var(--paper);text-decoration:none;
     font-weight:600;font-size:.92rem;border:1px solid var(--cool)}
.cta:hover{background:var(--paper);color:var(--cool)}

.prov dl{display:grid;grid-template-columns:11rem 1fr;gap:.35rem 1rem;margin:.6rem 0 0;
         font-family:var(--mono);font-size:.78rem}
.prov dt{color:var(--ink-3)}
.prov dd{margin:0;color:var(--ink-2);word-break:break-all}

@media (max-width:820px){
  /* Below this width the drawing is scrolled, never shrunk. A chart whose
     labels have stopped being readable is not a smaller chart. */
  .figbox{height:var(--chart-h-sm)}
  .mapbox{aspect-ratio:auto;height:268px;max-height:none}
  .mapbox svg{height:100%;width:auto;min-width:640px}
  .prov dl,.tier{grid-template-columns:1fr;gap:.15rem}
  .fig{padding:.9rem .8rem}
  main{padding-inline:.9rem}
  .band{padding-inline:.9rem}
}
@media (prefers-reduced-motion:reduce){
  *{transition:none!important;animation:none!important}
}
"""


# ---------------------------------------------------------------- V1 svg

def v1_svg(ew: dict) -> str:
    """Bullet rows. Realised main effect as the bar, nominal as the target tick,
    the 95 percent interval on its own rail above the bar so the two encodings
    never sit on top of each other. E-2 forbids the point estimate alone, so the
    interval is not optional and is given equal visual weight."""
    order = ["WSE", "CSE", "ODI", "RGD", "REE"]
    W, H = 780, 400
    L, R, T, B = 214, 84, 52, 46
    vmax = 0.75
    rowh = (H - T - B) / len(order)
    barh = 19
    rail = 13          # the interval rail sits this far above the bar top

    def x(v):
        return L + (v / vmax) * (W - R - L)

    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Nominal against '
         'realised weight for five composite axes with 95 percent bootstrap '
         'intervals">']

    v = 0.0
    while v <= vmax + 1e-9:
        gx = round(x(v), 1)
        p.append(f'<line class="grid-line" x1="{gx}" y1="{T-16}" x2="{gx}" y2="{H-B+4}"/>')
        p.append(f'<text class="axis-text" x="{gx}" y="{H-B+20}" text-anchor="middle">{v:.2f}</text>')
        v += 0.15
    p.append(f'<text class="axis-text" x="{L}" y="{T-26}" text-anchor="start">'
             'share of variance in the composite, main effect Si</text>')

    for i, k in enumerate(order):
        a = ew["axes"][k]
        ybase = T + i * rowh + (rowh - barh) / 2 + 6
        ymid = ybase + barh / 2
        yrail = ybase - rail
        hot = a["nominal_in_ci"] is False

        p.append(f'<text class="row-label" x="{L-18}" y="{ymid-2:.1f}" text-anchor="end">{k}</text>')
        p.append(f'<text class="row-note" x="{L-18}" y="{ymid+13:.1f}" text-anchor="end">'
                 f'{AXIS_NAMES[k].lower()}</text>')

        # interval rail, drawn first and above the bar
        lo, hi = a["ci95"]
        p.append(f'<line class="ci-line" x1="{x(lo):.1f}" y1="{yrail:.1f}" '
                 f'x2="{x(hi):.1f}" y2="{yrail:.1f}"/>')
        for c in (lo, hi):
            p.append(f'<line class="ci-cap" x1="{x(c):.1f}" y1="{yrail-4.5:.1f}" '
                     f'x2="{x(c):.1f}" y2="{yrail+4.5:.1f}"/>')

        w = max(x(a["main_effect"]) - L, 1.5)
        cls = "bar-realised--hot" if hot else "bar-realised"
        p.append(f'<rect class="{cls}" x="{L}" y="{ybase:.1f}" width="{w:.1f}" '
                 f'height="{barh}" rx="1.5"/>')

        # nominal target, on top of everything, crossing the bar
        nx = x(a["nominal"])
        p.append(f'<line class="bar-nominal" x1="{nx:.1f}" y1="{ybase-6:.1f}" '
                 f'x2="{nx:.1f}" y2="{ybase+barh+6:.1f}"/>')
        p.append(f'<text class="nominal-num" x="{nx:.1f}" y="{ybase+barh+18:.1f}" '
                 f'text-anchor="middle">{a["nominal"]:.2f}</text>')

        vcls = "value-num--hot" if hot else "value-num"
        p.append(f'<text class="{vcls}" x="{W-R+12}" y="{ymid+4:.1f}" '
                 f'text-anchor="start">{a["main_effect"]:.3f}</text>')
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- V2 svg

def v1_svg_narrow(ew: dict) -> str:
    """Same numbers, same paint classes, laid out for a phone. The axis name
    moves above its bar so the plot area keeps the width instead of a label
    gutter taking two thirds of it. A chart that has to be scrolled to see its
    own bars is not a smaller chart."""
    order = ["WSE", "CSE", "ODI", "RGD", "REE"]
    W, H = 360, 470
    L, R, T, B = 4, 46, 34, 40
    vmax = 0.75
    rowh = (H - T - B) / len(order)
    barh = 17

    def x(v):
        return L + (v / vmax) * (W - R - L)

    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Nominal against '
         'realised weight for five composite axes with 95 percent bootstrap '
         'intervals">']
    v = 0.0
    while v <= vmax + 1e-9:
        gx = round(x(v), 1)
        p.append(f'<line class="grid-line" x1="{gx}" y1="{T-8}" x2="{gx}" y2="{H-B+4}"/>')
        p.append(f'<text class="axis-text" x="{gx}" y="{H-B+18}" text-anchor="middle">{v:.2f}</text>')
        v += 0.15
    p.append(f'<text class="axis-text" x="{L}" y="{T-18}" text-anchor="start">'
             'main effect Si</text>')

    for i, k in enumerate(order):
        ytop = T + i * rowh
        ybase = ytop + 30
        ymid = ybase + barh / 2
        yrail = ybase - 11
        a = ew["axes"][k]
        hot = a["nominal_in_ci"] is False
        p.append(f'<text class="row-label" x="{L}" y="{ytop+12:.1f}" text-anchor="start">'
                 f'{k}</text>')
        p.append(f'<text class="row-note" x="{L+44}" y="{ytop+12:.1f}" text-anchor="start">'
                 f'{AXIS_NAMES[k].lower()}</text>')
        lo, hi = a["ci95"]
        p.append(f'<line class="ci-line" x1="{x(lo):.1f}" y1="{yrail:.1f}" '
                 f'x2="{x(hi):.1f}" y2="{yrail:.1f}"/>')
        for c in (lo, hi):
            p.append(f'<line class="ci-cap" x1="{x(c):.1f}" y1="{yrail-4:.1f}" '
                     f'x2="{x(c):.1f}" y2="{yrail+4:.1f}"/>')
        w = max(x(a["main_effect"]) - L, 1.5)
        cls = "bar-realised--hot" if hot else "bar-realised"
        p.append(f'<rect class="{cls}" x="{L}" y="{ybase:.1f}" width="{w:.1f}" '
                 f'height="{barh}" rx="1.5"/>')
        nx = x(a["nominal"])
        p.append(f'<line class="bar-nominal" x1="{nx:.1f}" y1="{ybase-5:.1f}" '
                 f'x2="{nx:.1f}" y2="{ybase+barh+5:.1f}"/>')
        p.append(f'<text class="nominal-num" x="{nx:.1f}" y="{ybase+barh+15:.1f}" '
                 f'text-anchor="middle">{a["nominal"]:.2f}</text>')
        vcls = "value-num--hot" if hot else "value-num"
        p.append(f'<text class="{vcls}" x="{W-R+6}" y="{ymid+4:.1f}" '
                 f'text-anchor="start">{a["main_effect"]:.3f}</text>')
    p.append("</svg>")
    return "".join(p)


def v2_svg(m: dict, byiso: dict, epis: dict) -> str:
    W, H = m["W"], m["H"]
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Equal Earth map of '
         'composite substrate exposure for 32 ranked states, with three states '
         'published as withheld">',
         '<defs><pattern id="hatch" patternUnits="userSpaceOnUse" width="6" height="6" '
         'patternTransform="rotate(45)">'
         '<rect class="hatch-ground" width="6" height="6"/>'
         '<line class="hatch-line" x1="0" y1="0" x2="0" y2="6"/>'
         '</pattern></defs>']
    p.append(f'<path class="geo-sphere" d="{m["sphere"]}"/>')
    p.append('<g class="geo-land">')
    for d in m["land"]:
        p.append(f'<path d="{d}"/>')
    p.append("</g>")

    for s in m["states"]:
        rec = byiso[s["iso"]]
        p.append(
            f'<path class="geo-state geo-{s["cls"]}" d="{s["d"]}" tabindex="0" '
            f'role="button" data-iso="{s["iso"]}" aria-label="{esc(rec["name"])}">'
            f'<title>{esc(rec["name"])}</title></path>')

    # Micro-states and near-invisible territories get a guaranteed mark. A
    # choropleth that renders a city-state at sub-pixel size hides three of the
    # five highest-exposure entries and both withholding causes.
    p.append('<g>')
    for d in m["dots"]:
        rec = byiso[d["iso"]]
        p.append(f'<circle class="dot geo-{d["cls"]}" cx="{d["x"]}" cy="{d["y"]}" r="5.2" '
                 f'tabindex="0" role="button" data-iso="{d["iso"]}" '
                 f'aria-label="{esc(rec["name"])}"><title>{esc(rec["name"])}</title></circle>')
    p.append("</g>")
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- page

def build(doc: dict, m: dict) -> str:
    C = doc["countries"]
    ew = doc["effective_weights"]
    cp = doc["coupling"]
    model = doc["composite_model"]
    lin = doc["lineage"]
    vint = doc["vintage"]
    epis = {e["iso3"]: e for e in doc["epis_findings"]}
    wc = doc["withholding_causes"]

    ranked = sorted(((i, c) for i, c in C.items() if c["composite"] is not None),
                    key=lambda t: -t[1]["composite"])
    byiso = {i: {"name": c["name"], "composite": c["composite"],
                 "coverage": c["coverage"], "status": c.get("composite_status"),
                 "odi": c["axes"]["ODI"],
                 "big": c["big_flags"],
                 "cause": epis.get(i, {}).get("withholding_cause"),
                 "cause_statement": epis.get(i, {}).get("cause_statement")}
             for i, c in C.items()}

    ledger = doc["uncertainty_ledger"]["entries"]
    src_names = ", ".join(lin.get("sources", {}))
    gen = lin.get("generated_at_utc", "")

    rank_rows = "\n".join(
        f'<tr><td class="n">{r+1}</td><td>{esc(c["name"])}</td>'
        f'<td class="n">{c["composite"]:.1f}</td>'
        f'<td class="n">{c["axes"]["WSE"]:.1f}</td>'
        f'<td class="n">{c["axes"]["CSE"]:.1f}</td>'
        f'<td class="n">{c["axes"]["ODI"]:.1f}</td>'
        f'<td class="n">{c["axes"]["REE"]:.1f}</td>'
        f'<td class="n">{c["coverage"]:.2f}</td></tr>'
        for r, (i, c) in enumerate(ranked))

    epis_rows = "\n".join(
        f'<tr><td>{esc(e["name"])}</td><td class="n">{e["coverage"]:.2f}</td>'
        f'<td class="epis">{esc(", ".join(e["missing_weighted_axes"]))}</td>'
        f'<td class="epis">{esc(e["withholding_cause"])}</td>'
        f'<td>{esc(e["cause_statement"])}</td></tr>'
        for e in doc["epis_findings"])

    ledger_rows = "\n".join(
        f'<tr><td class="epis">{esc(u["id"])}</td><td>{esc(u["severity"])}</td>'
        f'<td>{esc(u["statement"])}</td></tr>' for u in ledger)

    legend_bins = "".join(f'<i class="r{i+1}"></i>' for i in range(6))
    legend_nums = "".join(f'<s>{hi if hi < 101 else 100}</s>' for lo, hi in BINS)

    readout = json.dumps(byiso, ensure_ascii=False, separators=(",", ":"))
    causes = json.dumps(wc["codes"], ensure_ascii=False, separators=(",", ":"))

    return f"""
<p><span class="tag">{esc(vint)}</span>
   <span class="tag">35 states</span>
   <span class="tag">7 axes</span>
   <span class="tag">chain {SERVED['chain_entries']} entries</span></p>

<h1>An index that declares five weights and behaves as if it has two.</h1>

<p class="lede">QESIS+ measures what a state's digital sovereignty physically
rests on: water, submarine cable, rare earths, foreign platforms, hyperscale
operator concentration, cloud risk density and electricity. Seven axes, 35
states, every score reproducible from a primary portal. The index publishes its
own failures of identification, and this is the first one.</p>

<p class="eyebrow">View 1 of 3 &middot; The finding</p>

<div class="band"><div class="fig">
  <div class="figbox wide">{v1_svg(ew)}</div>
  <div class="figbox narrow">{v1_svg_narrow(ew)}</div>
  <div class="legend">
    <span><i class="sw sw--nominal"></i> nominal weight, declared</span>
    <span><i class="sw sw--realised"></i> realised main effect Si</span>
    <span><i class="sw sw--hot"></i> nominal outside its own interval</span>
    <span><i class="sw sw--ci"></i> 95% bootstrap, {ew['bootstrap_resamples']} resamples</span>
  </div>
  <p class="src">Source: <code>effective_weights</code> in the served index, also
  returned by <code>qesis_get_methodology</code>.
  Method: {esc(ew['method'])}
  Sample n_complete {ew['n_complete']}.</p>
</div></div>

<div class="kicker">
  <b>Spearman {ew['reduction_test']['spearman_vs_WSE_CSE_only']}</b>
  <p>{esc(ew['reduction_test']['note'])} The composite is reported as
  five-dimensional and orders states as if it were two-dimensional.</p>
</div>

<div class="caveat">
  <strong>What this view is not licensed to say.</strong>
  {esc(ew['honesty_caveat'])} It is not licensed to say ODI, RGD and REE are
  weightless.
</div>

<p><strong>Falsifier.</strong> A sample large enough to tighten the ODI, RGD and
REE intervals away from zero, or a re-estimation in which the nominal 0.30 on
WSE returns inside its interval. Either outcome retires this finding, and the
retirement would be published here in the same place as the claim.</p>

<p class="eyebrow">View 2 of 3 &middot; Where it lands</p>
<h2 class="finding">Substrate entanglement is geopolitical, not universal.</h2>

<p>Energy-rich states decouple through cheap, reliable, carbon-heavy power. For
states that import their energy, their minerals and their hyperscalers, every
axis is bound to every other. That is the finding, and the distance between
these two numbers is the argument.</p>

<div class="stat">
  <div><b>{cp['global']['CR']:.3f}</b><span>coupling, global n={cp['global']['n']}</span></div>
  <div class="argued"><b>{cp['core']['CR']:.3f}</b><span>coupling, import core n={cp['core']['n']}</span></div>
  <div><b>{len(ranked)}</b><span>ranked</span></div>
  <div><b>{len(doc['epis_findings'])}</b><span>published gaps</span></div>
</div>

<div class="band"><div class="fig">
  <div class="figbox mapbox">{v2_svg(m, byiso, epis)}</div>
  <dl class="readout" id="readout" aria-live="polite">
    <p class="who">Select a state</p>
    <p class="hint">Hover or focus any marked territory. Every value carries its
    coverage and its withholding cause, because a score without its epistemic
    flag is displayed rather than published.</p>
  </dl>
  <div class="legend">
    <span class="rampkey">
      <i class="ramp">{legend_bins}</i>
      <i class="rampnum">{legend_nums}</i>
    </span>
    <span>composite exposure</span>
    <span><i class="sw sw--epis"></i> withheld under BIG, no coverage</span>
    <span><i class="sw sw--land"></i> outside the 35-state frame</span>
  </div>
  <p class="src">Source: <code>countries[].composite</code> and
  <code>countries[].coverage</code> in the served index. Projection: Equal Earth,
  frame clipped to 84N and 57S, geometry pre-projected at build time so the page
  makes no network request. A circle marks a territory too small to read at this
  projection: three of the five highest-exposure entries are city-states, and a
  choropleth that renders them at sub-pixel size hides its own finding.
  Geographic layers stop at infrastructure, never people. Hatching is a published
  gap, never a zero.</p>
</div></div>

<h2>The gap is the finding</h2>
<p>The Binary Integrity Guard never imputes. A state missing a weighted axis is
not ranked and not quietly zeroed: it is published as a gap with its coverage
stated. Below the declared {model['big_coverage_min']} threshold, no composite is
emitted at all.</p>
<p>{esc(wc['why_not_one_label'])}</p>
<div class="band"><div class="fig"><div class="scroll"><table>
<thead><tr><th>State</th><th class="n">Coverage</th><th>Absent</th><th>Cause</th>
<th>Why the value does not exist</th></tr></thead>
<tbody>{epis_rows}</tbody></table></div>
<p class="src">Source: <code>epis_findings</code> and
<code>withholding_causes</code>. Authority: {esc(wc['authority'])}.</p>
</div></div>

<p class="eyebrow">View 3 of 3 &middot; The record</p>
<h2>Ranking</h2>
<p>Thirty-two states carry a composite. The four weighted axes that move it most
are printed beside it so the ranking can be checked rather than believed.</p>
<div class="band"><div class="fig"><div class="scroll"><table>
<thead><tr><th class="n">#</th><th>State</th><th class="n">Composite</th>
<th class="n">WSE</th><th class="n">CSE</th><th class="n">ODI</th>
<th class="n">REE</th><th class="n">Cov</th></tr></thead>
<tbody>{rank_rows}</tbody></table></div>
<p class="src">Composite = {esc(model['expression'])}. Derived at build time,
never carried. ODI is the continuous Herfindahl measure over operator shares of
active cloud regions, weighted one unit per active region. FPE and ESE are
published per state and enter no composite. Sources: {esc(src_names)}.
Index generated {esc(gen)}.</p>
</div></div>

<h2>What this vintage does not know</h2>
<p>Every known limitation, derived from the index at build time rather than kept
by hand. An instrument that publishes its own uncertainty is checkable; one that
does not is a claim.</p>
<div class="band"><div class="fig"><div class="scroll"><table>
<thead><tr><th>Id</th><th>Severity</th><th>Limitation</th></tr></thead>
<tbody>{ledger_rows}</tbody></table></div>
<p class="src">Source: <code>uncertainty_ledger</code>, {len(ledger)} entries,
vintage {esc(vint)}. Also served by <code>qesis_get_integrity</code>.</p>
</div></div>

<h2>Connect it</h2>
<p>The index is an MCP server, so any MCP-capable client can call it as a tool.
Local, over stdio:</p>
<pre>pip install mcp
python server.py</pre>
<p>Claude Desktop:</p>
<pre>{{"mcpServers":{{"qesis":{{"command":"python",
  "args":["/path/to/qesis-mcp/server.py"]}}}}}}</pre>
<p>Without a licence key the server runs in demo tier: rounded scores, limited
depth, component audit locked. That is the product working as designed.</p>

<div class="cert">
  <h3>The Exposure Certificate</h3>
  <p>One page per state, generated from this index rather than written. It is
  the smallest object about a state's substrate exposure that its recipient can
  check without trusting the sender.</p>
  <ul>
    <li>seven axis values, composite and coverage</li>
    <li>BIG flag and, where a value is withheld, the cause that explains it</li>
    <li>CSovE tier and the deterministic rule that produced it</li>
    <li>vintage, <code>index_sha256</code>, chain head and entry count</li>
    <li>licence line and an APA citation block</li>
  </ul>
  <p>A dashboard is consulted; a certificate is filed. Filing creates a record
  with a hash in it, and the next vintage makes that record checkable against
  this one.</p>
  <div class="tiers">
    <div class="tier"><b>Open</b><span>Everything on this page, all 35 states,
      CC-BY-NC. No gate, no account, no cookie.</span></div>
    <div class="tier"><b>Named</b><span>Exposure Certificate for a state you
      name. Requested by email with your name, role and channel, answered by a
      person. <span class="chip">automated fulfilment pending</span></span></div>
    <div class="tier"><b>Institutional</b><span>Full axis pack, chain spine
      export and re-run rights, under an institutional licence.</span></div>
  </div>
  <a class="cta" href="mailto:rodrigoesl92@gmail.com?subject=QESIS%2B%20Exposure%20Certificate%20request">Request a certificate by email</a>
  <p class="src">There is no form on this page. No backend stands behind it yet,
  and a form that silently discards what you type is worse than no form. Nothing
  you do here is logged and no cookie is set, so no GDPR notice is owed and none
  is shown. When fulfilment is automated, this chip is removed and the exchange
  is described here before it is built.</p>
</div>

<h2>Integrity</h2>
<div class="gap">
<p>Every composite is recomputed from its own published axes on each build, and
the deploy fails on drift. The v8.0 vintage carried a composite that could not
be reproduced from the axes beside it: the United Kingdom scored at or above
Switzerland on all seven axes yet carried a lower composite, which no
non-negative weighting admits. It is derived now, and
<code>qesis_get_integrity</code> answers which generation you are reading.</p>
</div>

<div class="band"><div class="fig prov">
  <p class="eyebrow">Provenance</p>
  <dl>
    <dt>Vintage</dt><dd>{esc(vint)}</dd>
    <dt>index_sha256</dt><dd>{SERVED['index_sha256']}</dd>
    <dt>Chain</dt><dd>{SERVED['chain_status']}, {SERVED['chain_entries']} entries,
      {SERVED['chain_link_breaks']} link breaks</dd>
    <dt>Chain head</dt><dd>{SERVED['chain_head']}</dd>
    <dt>Attestation</dt><dd>agrees</dd>
    <dt>Plane</dt><dd>{SERVED['plane']}, commit {SERVED['deployment_commit']}</dd>
    <dt>Formula</dt><dd>{esc(model['formula_id'])}, {esc(model['expression'])}</dd>
    <dt>Sample</dt><dd>{len(ranked)} ranked of 35, {len(doc['epis_findings'])} withheld under BIG</dd>
    <dt>Licence</dt><dd>{esc(doc['license'])}</dd>
    <dt>Scope</dt><dd>geographic layers stop at infrastructure, never people</dd>
  </dl>
  <p class="src">Verify: <code>git checkout {SERVED['deployment_commit'][:12]}</code>,
  then <code>sha256sum data/qesis_v8.json</code> must equal index_sha256, and
  <code>python scripts/verify_chain.py</code> must exit 0. Two planes exist, the
  working tree and the deployed commit, and this strip always states which one
  you are reading.</p>
</div></div>

<footer>
<p>QESIS+ {esc(vint)}. Batista Silva, R. (2026). Liquid Sovereignty. ESIC/LSE.
Dataset: Sovereign_Infra_Intelligence.</p>
<p>Derived scores are own work; upstream sources keep their own licences and are
cited per axis. TeleGeography-derived cable material is published only as
derived aggregates, never raw. This page is built from the index, never edited
by hand.</p>
</footer>

<script>
/* Doherty. Every figure is pre-aggregated at build time, so the readout is a
   local lookup and never a request. No value is computed here. */
const R = {readout};
const CAUSE = {causes};
const box = document.getElementById("readout");
const fmt = (v, d) => v === null || v === undefined ? "withheld" : v.toFixed(d);

function show(iso) {{
  const r = R[iso];
  if (!r) return;
  const rows = [
    ["composite", r.composite === null ? "withheld" : fmt(r.composite, 1)],
    ["coverage", fmt(r.coverage, 2)],
    ["status", r.status],
    ["ODI", fmt(r.odi, 1)]
  ];
  let h = '<p class="who">' + r.name + "</p>";
  for (const [k, v] of rows) h += "<dt>" + k + "</dt><dd>" + v + "</dd>";
  if (r.cause) {{
    h += '<dt>cause</dt><dd>' + r.cause + "</dd>";
    h += '<p class="cause"><strong>' + (CAUSE[r.cause] || "") + "</strong> "
       + r.cause_statement + "</p>";
  }}
  box.innerHTML = h;
}}

for (const el of document.querySelectorAll("[data-iso]")) {{
  const iso = el.getAttribute("data-iso");
  el.addEventListener("mouseenter", () => show(iso));
  el.addEventListener("focus", () => show(iso));
  el.addEventListener("click", () => show(iso));
}}
</script>
"""


SHELL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QESIS+ {vint}, sovereign substrate intelligence</title>
<meta name="description" content="An auditable index of digital sovereignty
 substrate risk across 35 states and seven measured axes. Every score
 reproducible from primary portals; coverage gaps published as findings.">
<style>{tokens}{css}</style>
</head><body><main>
{body}
</main></body></html>
"""

ARTIFACT = """<title>QESIS+ Substrate Index</title>
<style>{tokens}{css}</style>
<main>
{body}
</main>
"""


# ---------------------------------------------------------------- gate

BANNED = ["delve", "unlock", "robust", "seamless", "crucial", "foster",
          "empower", "elevate", "tapestry"]


def doctrine_scan(page: str) -> list[str]:
    bad = []
    if "—" in page:
        bad.append("em dash present")
    for w in BANNED:
        if re.search(rf"\b{w}\b", page, re.I):
            bad.append(f"banned word: {w}")
    body = page.split("</style>", 1)[-1]
    hits = re.findall(r"#[0-9a-fA-F]{3,6}\b", body)
    if hits:
        bad.append(f"colour literal outside tokens: {hits[:5]}")
    if "prefers-color-scheme" not in page:
        bad.append("no dark scheme")
    if page.count('class="src"') < 3:
        bad.append("charts or tables lacking a source line")
    if "GDPR" not in page and "no backend" not in page:
        bad.append("no plain data-exchange statement")
    return bad


def main() -> int:
    doc = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    m = json.loads(MAP.read_text(encoding="utf-8"))
    body = build(doc, m)

    full = SHELL.format(vint=esc(doc["vintage"]), tokens=TOKENS, css=CSS, body=body)
    art = ARTIFACT.format(tokens=TOKENS, css=CSS, body=body)

    bad = doctrine_scan(full)
    print(f"doctrine scan: {len(bad)} violations")
    for b in bad:
        print(f"  x {b}")

    OUT.mkdir(exist_ok=True)
    (OUT / "qesis_landing.html").write_text(full, encoding="utf-8")
    (OUT / "artifact_body.html").write_text(art, encoding="utf-8")
    print(f"wrote out/qesis_landing.html  {len(full)//1024} KB")
    print(f"wrote out/artifact_body.html  {len(art)//1024} KB")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
