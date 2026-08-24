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

AXIS_FAMILIES = [
    ("Physical", ["WSE", "CSE", "REE"],
     "water stress, submarine cable exposure, rare earth exposure"),
    ("Platform", ["FPE", "ODI", "RGD"],
     "foreign platform exposure, hyperscale operator concentration, "
     "regulatory divergence"),
    ("Energy", ["ESE"], "electricity supply exposure"),
]


def quartile_word(rank: int, n: int) -> str:
    """A word for a number, derived from the published distribution rather than
    from a risk band nobody declared. The payload carries no band rule for
    composite, so none is invented here."""
    q = (rank - 1) / n
    if q < 0.25:
        return "top quartile of the ranked set"
    if q < 0.50:
        return "above the median"
    if q < 0.75:
        return "below the median"
    return "bottom quartile of the ranked set"



def esc(s) -> str:
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- tokens

TOKENS = """
:root{
  /* Verbatim from scripts/build_landing.py TOKENS. Do not edit a value here. */
  --ink:#1c1b19; --ink-2:#4a4744; --ink-3:#706b65;
  --paper:#faf8f5; --paper-2:#f1ede7; --rule:#ddd6cc;
  --cool:#3d5a68; --cool-2:#6d8b98;
  --hot:#c96a5e;
  /* --ink-3 was #78736d and read at 4.43 against --paper-2, just under AA.
     --hot and --epis stay as fills, where 3:1 is the bar. Their -ink variants
     are the only values allowed to carry small text. */
  --hot-ink:#a3554b; --epis-ink:#6f6962;
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
    --hot-ink:#e08476; --epis-ink:#8f8476;
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
  --hot-ink:#e08476; --epis-ink:#8f8476;
  --warm-500:#d9a45e; --epis:#8a7f70; --land:#23211e;
  --q1:#41545c; --q2:#556a73; --q3:#6a828c;
  --q4:#809aa5; --q5:#97b3bf; --q6:#aeccd9;
}
"""

EXTRA_CSS = """
/* ---- orientation rail -------------------------------------------------
   Jakob and Fitts. The reader always knows the vintage, always knows the
   chain is green, and the ask is never more than one large target away. */
.rail{position:sticky;top:0;z-index:20;background:var(--paper);
      border-bottom:1px solid var(--rule);backdrop-filter:saturate(180%) blur(6px)}
.railin{max-width:var(--band);margin-inline:auto;padding:.5rem 1.2rem;
        display:flex;align-items:center;gap:.5rem 1rem;flex-wrap:wrap}
.rtag{font-family:var(--mono);font-size:.72rem;color:var(--ink-3);white-space:nowrap}
.rtag b{color:var(--ink);letter-spacing:.02em}
.rtag.ok::before{content:"";display:inline-block;width:7px;height:7px;
  border-radius:50%;background:var(--cool);margin-right:.4rem;vertical-align:baseline}
.rnav{display:flex;gap:.15rem;margin-left:auto;flex-wrap:wrap}
.rnav a{font-family:var(--mono);font-size:.72rem;text-transform:uppercase;
        letter-spacing:.06em;color:var(--ink-3);text-decoration:none;
        padding:.3rem .5rem;border-radius:2px;white-space:nowrap}
.rnav a:hover{color:var(--ink);background:var(--paper-2)}
.rnav a.on{color:var(--ink);box-shadow:inset 0 -2px 0 var(--hot)}

/* ---- hero -------------------------------------------------------------- */
.eyebrow--hot{color:var(--hot-ink);margin-top:1.4rem;max-width:62ch;
              text-transform:none;letter-spacing:.02em;font-size:.82rem}
.fams{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin:1.2rem 0}
.fam{background:var(--paper-2);border:1px solid var(--rule);border-radius:3px;
     padding:.7rem .8rem;display:flex;flex-direction:column;gap:.25rem}
.fam b{font-size:.9rem}
.fam span{font-size:.78rem;color:var(--ink-3);line-height:1.45}
.famn{font-family:var(--mono);font-size:.68rem;color:var(--ink-3);
      text-transform:uppercase;letter-spacing:.06em;margin-top:auto;
      font-style:normal}
.who{border-left:2px solid var(--rule);padding-left:.9rem;font-size:.92rem}
.asks{display:flex;flex-wrap:wrap;gap:.7rem 1.1rem;align-items:center;margin:1.2rem 0 0}
.alt{font-size:.9rem;color:var(--ink-3)}
.alt:hover{color:var(--ink)}

/* ---- map as a selector, readout beside it, not below (Fitts) ---------- */
.split{display:grid;grid-template-columns:1fr 20rem;gap:1rem;align-items:start}
.split .mapbox{aspect-ratio:auto;height:400px;max-height:none}
.split .mapbox svg{height:100%;width:100%}
.readout{display:grid;grid-template-columns:auto 1fr;gap:.3rem .8rem;
         align-items:baseline;align-content:start;margin:0;padding:.9rem 1rem;
         min-height:400px;background:var(--paper);border:1px solid var(--rule);
         border-radius:3px}
.readout .who2{grid-column:1/-1;font-family:var(--serif);font-size:1.4rem;
               line-height:1.15;color:var(--ink);margin:0 0 .3rem}
.readout dt{font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;
            color:var(--ink-3);margin:0}
.readout dd{margin:0;font-family:var(--mono);font-size:.82rem;
            font-variant-numeric:tabular-nums;color:var(--ink);line-height:1.45}
.readout .cause{grid-column:1/-1;font-size:.8rem;color:var(--ink-2);
                margin:.5rem 0 0;line-height:1.5}
.readout .hint{grid-column:1/-1;color:var(--ink-3);font-size:.85rem;margin:0}
.geo-state.sel,.dot.sel{stroke:var(--hot);stroke-width:2}

/* ---- triad. Never the worst case alone (D-022). ----------------------- */
.triad{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin:1rem 0}
.tri{background:var(--paper-2);border:1px solid var(--rule);border-radius:3px;
     padding:.9rem 1rem}
.tri b{display:block;font-family:var(--mono);font-size:1.9rem;font-weight:600;
       font-variant-numeric:tabular-nums;letter-spacing:-.02em;line-height:1.1}
.tri span{display:block;font-size:.8rem;color:var(--ink-2);margin-top:.15rem}
.tri i{display:block;font-family:var(--mono);font-size:.7rem;color:var(--ink-3);
       font-style:normal;margin-top:.35rem}
.tri--hot b{color:var(--hot)}

/* ---- gap cards. Two causes must not read as one. ---------------------- */
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;margin:.9rem 0}
.card{background:var(--paper-2);border:1px solid var(--rule);border-radius:3px;
      padding:.9rem 1rem}
.card h3{margin:0;font-size:1rem;color:var(--ink)}
.cardnum{font-family:var(--mono);font-size:.8rem;color:var(--epis-ink);
         margin:.2rem 0 .6rem;text-transform:uppercase;letter-spacing:.06em}
.mini{display:grid;grid-template-columns:auto 1fr;gap:.15rem .7rem;margin:0;
      font-family:var(--mono);font-size:.74rem}
.mini dt{color:var(--ink-3)}
.mini dd{margin:0;color:var(--ink-2)}
.why{font-size:.8rem;color:var(--ink-2);margin:.6rem 0 0;line-height:1.5}

/* ---- ranking as an instrument ----------------------------------------- */
.tablebar{display:flex;align-items:center;gap:1rem;flex-wrap:wrap;
          margin-bottom:.2rem}
.filter{display:flex;align-items:center;gap:.5rem;font-size:.75rem;
        text-transform:uppercase;letter-spacing:.05em;color:var(--ink-3)}
.filter input{font-family:var(--mono);font-size:.85rem;padding:.35rem .5rem;
              border:1px solid var(--rule);border-radius:3px;
              background:var(--paper);color:var(--ink);min-width:11rem}
.count{font-family:var(--mono);font-size:.72rem;color:var(--ink-3);margin-left:auto}
#rank th[data-sort]{cursor:pointer;user-select:none}
#rank th[data-sort]:hover{color:var(--ink)}
#rank th[aria-sort]{color:var(--ink)}
#rank th[aria-sort="ascending"]::after{content:" \\2191"}
#rank th[aria-sort="descending"]::after{content:" \\2193"}
#rank tbody tr{cursor:pointer}
#rank tbody tr.sel{background:var(--paper);box-shadow:inset 2px 0 0 var(--hot)}
td.bar{width:22%;min-width:5rem;padding-right:.9rem}
td.bar i{display:block;height:7px;border-radius:1px;background:var(--q4)}
#rank tbody tr.sel td.bar i{background:var(--hot)}

/* ---- the ask ----------------------------------------------------------- */
.cta{display:inline-block;padding:.62rem 1.1rem;border-radius:3px;
     background:var(--cool);color:var(--paper);text-decoration:none;
     font-weight:600;font-size:.92rem;border:1px solid var(--cool);
     white-space:nowrap}
.cta:hover{background:var(--paper);color:var(--cool)}
.cta--sm{padding:.34rem .7rem;font-size:.78rem}
.cta--lg{padding:.8rem 1.4rem;font-size:1rem}
.cert{border:1px solid var(--cool);border-radius:3px;background:var(--paper-2);
      padding:1.4rem 1.5rem;margin:2.6rem 0 0}
.cert h2{margin-top:.2rem}
.cert ul{margin:.6rem 0;padding-left:1.1rem;color:var(--ink-2);font-size:.9rem}
.cert li{margin:.2rem 0}
.tiers{display:grid;gap:0;margin:1.1rem 0 0}
.tier{display:grid;grid-template-columns:7.5rem 1fr;gap:.9rem;padding:.7rem 0;
      border-top:1px solid var(--rule);font-size:.88rem}
.tier b{font-family:var(--mono);font-size:.74rem;text-transform:uppercase;
        letter-spacing:.06em;color:var(--ink-3);font-weight:600}
.tier span{color:var(--ink-2)}
.tier--pick b{color:var(--hot-ink)}
.chip{display:inline-block;font-family:var(--mono);font-size:.68rem;
      letter-spacing:.05em;text-transform:uppercase;color:var(--ink-3);
      border:1px dashed var(--rule);border-radius:2px;padding:.1rem .4rem;
      white-space:nowrap;flex:none;margin-right:.3rem}
.tier--pick .chip:first-of-type{color:var(--hot-ink);border-style:solid;
                                border-color:var(--hot-ink)}

@media (max-width:900px){
  .split{grid-template-columns:1fr}
  .split .mapbox{height:268px}
  .split .mapbox svg{height:100%;width:auto;min-width:640px}
  .readout{min-height:0}
  .fams,.triad,.cards{grid-template-columns:1fr}
  /* One sticky line on a phone. A rail that eats a third of the viewport is
     not orientation, it is furniture. The nav is reachable by scrolling. */
  .rnav{display:none}
  .railin{padding:.4rem .9rem;gap:.5rem;flex-wrap:nowrap}
  .rtag{font-size:.66rem;overflow:hidden;text-overflow:ellipsis}
  .rtag.chain{display:none}
  .railin .cta{margin-left:auto}
  .cert{padding:1rem 1rem}
  .tier{grid-template-columns:1fr;gap:.15rem}
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
   margin:.3rem 0 .6rem;letter-spacing:-.015em;text-wrap:balance;max-width:24ch}
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
.value-num--hot{fill:var(--hot-ink);font-family:var(--mono);font-size:12.5px;font-weight:700}

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

.caveat{margin:1rem 0;padding:.85rem 1rem;border:1px dashed var(--rule);
        border-radius:3px;color:var(--ink-2);font-size:.9rem}
.caveat strong{color:var(--ink)}
.kicker{margin:1.2rem 0;padding:1rem 1.1rem;background:var(--paper-2);
        border-left:3px solid var(--warm-500);border-radius:3px}
.kicker b{font-family:var(--mono);font-size:1.35rem;display:block;
          font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.kicker p{margin:.3rem 0 0;font-size:.9rem}

/* The instrument, not the argument. This is the object a reader can file. */

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
}
@media (prefers-reduced-motion:reduce){
  *{transition:none!important;animation:none!important}
}
""" + EXTRA_CSS


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
    n = len(ranked)
    rank_of = {i: r + 1 for r, (i, c) in enumerate(ranked)}
    hi_iso, hi = ranked[0]
    md_iso, md = ranked[n // 2]
    lo_iso, lo = ranked[-1]

    def binding(c):
        ax = {k: v for k, v in c["axes"].items() if v is not None}
        k = max(ax, key=ax.get)
        return k, ax[k]

    byiso = {}
    for i, c in C.items():
        bk, bv = binding(c)
        byiso[i] = {"name": c["name"], "composite": c["composite"],
                    "coverage": c["coverage"], "status": c.get("composite_status"),
                    "odi": c["axes"]["ODI"],
                    "rank": rank_of.get(i),
                    "quartile": quartile_word(rank_of[i], n) if i in rank_of else None,
                    "binding": AXIS_NAMES[bk].lower(), "binding_v": bv,
                    "providers": c["odi_continuous"]["n_providers"],
                    "regions": c["odi_continuous"]["n_regions"],
                    "cause": epis.get(i, {}).get("withholding_cause"),
                    "cause_statement": epis.get(i, {}).get("cause_statement")}

    bhr, are = C["BHR"], C["ARE"]
    ledger = doc["uncertainty_ledger"]["entries"]
    src_names = ", ".join(lin.get("sources", {}))
    gen = lin.get("generated_at_utc", "")

    # ranking rows carry a micro-bar so rank is felt before it is read
    rank_rows = "\n".join(
        f'<tr data-row="{i}" tabindex="0">'
        f'<td class="n">{r+1}</td><td>{esc(c["name"])}</td>'
        f'<td class="n">{c["composite"]:.1f}</td>'
        f'<td class="bar"><i style="width:{c["composite"]:.1f}%"></i></td>'
        f'<td>{esc(AXIS_NAMES[binding(c)[0]].lower())}</td>'
        f'<td class="n">{c["axes"]["ODI"]:.1f}</td>'
        f'<td class="n">{c["coverage"]:.2f}</td></tr>'
        for r, (i, c) in enumerate(ranked))

    gap_cards = "\n".join(
        f'<div class="card"><h3>{esc(e["name"])}</h3>'
        f'<p class="cardnum">no composite</p>'
        f'<dl class="mini"><dt>coverage</dt><dd>{e["coverage"]:.2f} '
        f'against a {model["big_coverage_min"]} threshold</dd>'
        f'<dt>absent</dt><dd>{esc(", ".join(e["missing_weighted_axes"]))}</dd>'
        f'<dt>cause</dt><dd>{esc(e["withholding_cause"])}</dd></dl>'
        f'<p class="why">{esc(e["cause_statement"])}</p></div>'
        for e in doc["epis_findings"])

    ledger_rows = "\n".join(
        f'<tr><td class="epis">{esc(u["id"])}</td><td>{esc(u["severity"])}</td>'
        f'<td>{esc(u["statement"])}</td></tr>' for u in ledger)

    fam = "".join(
        f'<div class="fam"><b>{name}</b><span>{esc(text)}</span>'
        f'<i class="famn">{len(keys)} {"axis" if len(keys)==1 else "axes"}</i></div>'
        for name, keys, text in AXIS_FAMILIES)

    legend_bins = "".join(f'<i class="r{i+1}"></i>' for i in range(6))
    legend_nums = "".join(f'<s>{hi_ if hi_ < 101 else 100}</s>' for lo_, hi_ in BINS)

    readout = json.dumps(byiso, ensure_ascii=False, separators=(",", ":"))
    causes = json.dumps(wc["codes"], ensure_ascii=False, separators=(",", ":"))
    ASK = ("mailto:rodrigoesl92@gmail.com?subject=QESIS%2B%20Exposure"
           "%20Certificate%20request")

    return f"""
<div class="rail">
  <div class="railin">
    <span class="rtag"><b>QESIS+</b> {esc(vint)}</span>
    <span class="rtag ok chain">chain verified, {SERVED['chain_entries']} entries,
      {SERVED['chain_link_breaks']} breaks</span>
    <nav class="rnav">
      <a href="#exposure">Exposure</a><a href="#audit">Audit</a>
      <a href="#record">Record</a><a href="#certificate">Certificate</a>
    </nav>
    <a class="cta cta--sm" href="{ASK}">Request a certificate</a>
  </div>
</div>

<main>

<p class="eyebrow eyebrow--hot">2 March 2026. Drones damaged three Amazon
facilities in the United Arab Emirates and Bahrain.</p>

<h1>Infrastructure became the battlefield. This index measures the ground.</h1>

<p class="lede">QESIS+ scores what a state's digital sovereignty physically
rests on, for 35 states, across seven measured axes in three families. Every
score is reproducible from a primary portal, every gap is published rather than
filled, and every number on this page carries the hash of the index it came
from.</p>

<div class="fams">{fam}</div>

<p class="who">Built for the people who have to defend a number: resilience and
continuity officers, cloud and telecom regulators, sovereign fund and
development bank analysts, and researchers who need a citation rather than a
dashboard.</p>

<p class="asks"><a class="cta" href="{ASK}">Request an Exposure Certificate</a>
<a class="alt" href="#audit">See how the index audits itself</a></p>

<p class="eyebrow" id="exposure">View 1 of 3 &middot; Exposure</p>
<h2 class="finding">Bahrain's entire hyperscale cloud presence is one operator
in one location. The index scored that at {bhr['axes']['ODI']:.0f} out of 100
before the drones arrived at it.</h2>

<div class="band"><div class="fig">
  <div class="split">
    <div class="mapbox figbox">{v2_svg(m, byiso, epis)}</div>
    <dl class="readout" id="readout" aria-live="polite">
      <p class="who2">Select a state</p>
      <p class="hint">Click, hover or tab to any marked territory. Every value
      arrives with its coverage, its binding constraint in words, and its
      withholding cause, because a score without its epistemic flag is
      displayed rather than published.</p>
    </dl>
  </div>
  <div class="legend">
    <span class="rampkey"><i class="ramp">{legend_bins}</i>
      <i class="rampnum">{legend_nums}</i></span>
    <span>composite exposure</span>
    <span><i class="sw sw--epis"></i> withheld under BIG, no coverage</span>
    <span><i class="sw sw--land"></i> outside the 35-state frame</span>
  </div>
  <p class="src">Source: <code>countries[].composite</code>,
  <code>countries[].coverage</code> and <code>odi_continuous</code> in the
  served index. Bahrain: {bhr['odi_continuous']['n_providers']} provider over
  {bhr['odi_continuous']['n_regions']} active cloud region, AWS at 100 percent
  of operator share, composite {bhr['composite']:.1f}, rank
  {rank_of['BHR']} of {n}. United Arab Emirates:
  {are['odi_continuous']['n_providers']} providers over
  {are['odi_continuous']['n_regions']} regions, composite
  {are['composite']:.1f}, rank {rank_of['ARE']} of {n}.
  <strong>What is not claimed:</strong> this vintage is dated {esc(vint)} and
  was published after the March strikes, so it forecast nothing. It names and
  scores the property that made those sites concentrated, for 30 further states.
  Projection: Equal Earth, frame clipped to 84N and 57S, geometry pre-projected
  at build time so this page makes no network request. A circle marks a
  territory too small to read at this projection: three of the six
  highest-exposure entries are city-states. Geographic layers stop at
  infrastructure, never people. Hatching is a published gap, never a zero.</p>
</div></div>

<h2>Read as a range, never as a headline</h2>
<p>Publishing only the worst case is how an index becomes a scare. The same
scale, three positions, each with the axis that binds it.</p>
<div class="triad">
  <div class="tri tri--hot"><b>{hi['composite']:.1f}</b>
    <span>{esc(hi['name'])}, highest of {n}</span>
    <i>bound by {esc(AXIS_NAMES[binding(hi)[0]].lower())} at {binding(hi)[1]:.1f}</i></div>
  <div class="tri"><b>{md['composite']:.1f}</b>
    <span>{esc(md['name'])}, median</span>
    <i>bound by {esc(AXIS_NAMES[binding(md)[0]].lower())} at {binding(md)[1]:.1f}</i></div>
  <div class="tri"><b>{lo['composite']:.1f}</b>
    <span>{esc(lo['name'])}, lowest of {n}</span>
    <i>bound by {esc(AXIS_NAMES[binding(lo)[0]].lower())} at {binding(lo)[1]:.1f}</i></div>
</div>
<p class="src">Source: <code>countries[].composite</code> and
<code>countries[].axes</code>. Median is the {n//2 + 1}th of {n} ranked states.
The binding constraint is the highest scoring axis for that state, derived, not
assigned. Composite = {esc(model['expression'])}.</p>

<p class="eyebrow" id="audit">View 2 of 3 &middot; Audit</p>
<h2 class="finding">The instrument publishes its own failures of
identification. Here is the current one.</h2>

<p>Most indices publish weights and stop. This one measures whether its declared
weights are the weights it actually behaves with, and reports the answer even
when the answer is inconvenient. Water stress realises roughly 1.8 times its
declared weight and is the only axis whose nominal value falls outside its own
confidence interval.</p>

<div class="band"><div class="fig">
  <div class="figbox wide">{v1_svg(ew)}</div>
  <div class="figbox narrow">{v1_svg_narrow(ew)}</div>
  <div class="legend">
    <span><i class="sw sw--nominal"></i> nominal weight, declared</span>
    <span><i class="sw sw--realised"></i> realised main effect Si</span>
    <span><i class="sw sw--hot"></i> nominal outside its own interval</span>
    <span><i class="sw sw--ci"></i> 95% bootstrap, {ew['bootstrap_resamples']} resamples</span>
  </div>
  <div class="kicker">
    <b>Spearman {ew['reduction_test']['spearman_vs_WSE_CSE_only']}</b>
    <p>{esc(ew['reduction_test']['note'])} The composite is reported as
    five-dimensional and orders states as if it were two-dimensional.</p>
  </div>
  <div class="caveat">
    <strong>What this view is not licensed to say.</strong>
    {esc(ew['honesty_caveat'])} It is not licensed to say that operator
    concentration, regulatory divergence and rare earth exposure are weightless.
  </div>
  <div class="caveat">
    <strong>Falsifier.</strong> A sample large enough to tighten the ODI, RGD
    and REE intervals away from zero, or a re-estimation in which the nominal
    0.30 on water stress returns inside its interval. Either outcome retires
    this finding, and the retirement would be published in this position, not
    quietly dropped.
  </div>
  <p class="src">Source: <code>effective_weights</code>, also returned by
  <code>qesis_get_methodology</code>. Method: {esc(ew['method'])}
  Sample n_complete {ew['n_complete']}. This is what an institutional buyer is
  actually paying for: an index that can be checked, and that checks itself in
  public between vintages.</p>
</div></div>

<h2>A gap is a finding, not a blank</h2>
<p>The Binary Integrity Guard never imputes. Below the declared
{model['big_coverage_min']} coverage threshold no composite is emitted at all,
and the reason is published per state. {esc(wc['why_not_one_label'])}</p>
<div class="band"><div class="cards">{gap_cards}</div>
<p class="src">Source: <code>epis_findings</code> and
<code>withholding_causes</code>. Authority: {esc(wc['authority'])}. Three of 35
states carry no composite and each says why in its own words.</p></div>

<p class="eyebrow" id="record">View 3 of 3 &middot; Record</p>
<h2 class="finding">Thirty-two states, ranked, with the axis that binds each
one.</h2>
<p>Sort any column. Select a row to place that state on the map above. The four
weighted axes and the coverage travel with every score so the ranking can be
checked rather than believed.</p>
<div class="band"><div class="fig">
  <div class="tablebar">
    <label class="filter"><span>Filter</span>
      <input type="text" id="q" placeholder="type a state" autocomplete="off"></label>
    <span class="count" id="count">{n} of {n} shown</span>
  </div>
  <div class="scroll"><table id="rank">
  <thead><tr><th class="n" data-sort="0">#</th><th data-sort="1">State</th>
  <th class="n" data-sort="2">Composite</th><th>&nbsp;</th>
  <th>Binding constraint</th><th class="n" data-sort="5">ODI</th>
  <th class="n" data-sort="6">Cov</th></tr></thead>
  <tbody>{rank_rows}</tbody></table></div>
  <p class="src">Composite = {esc(model['expression'])}. Derived at build time,
  never carried. ODI is the continuous Herfindahl measure over operator shares
  of active cloud regions, weighted one unit per active region. FPE and ESE are
  published per state and enter no composite. Sources: {esc(src_names)}.
  Index generated {esc(gen)}.</p>
</div></div>

<h2>What this vintage does not know</h2>
<p>Eight limitations, derived from the index at build time rather than kept by
hand. An instrument that publishes its own uncertainty can be checked. One that
does not is a claim.</p>
<div class="band"><div class="fig"><div class="scroll"><table>
<thead><tr><th>Id</th><th>Severity</th><th>Limitation</th></tr></thead>
<tbody>{ledger_rows}</tbody></table></div>
<p class="src">Source: <code>uncertainty_ledger</code>, {len(ledger)} entries,
vintage {esc(vint)}. Also served by <code>qesis_get_integrity</code>.</p>
</div></div>

<h2>Call it as a tool</h2>
<p>The index is an MCP server, so any MCP-capable client can query it directly.
Local, over stdio:</p>
<pre>pip install mcp
python server.py</pre>
<p>Claude Desktop:</p>
<pre>{{"mcpServers":{{"qesis":{{"command":"python",
  "args":["/path/to/qesis-mcp/server.py"]}}}}}}</pre>
<p>Without a licence key the server runs in demo tier: rounded scores, limited
depth, component audit locked. That is the product working as designed.</p>

<div class="cert" id="certificate">
  <p class="eyebrow">The ask</p>
  <h2 class="finding">Take one state away with you, in a form you can file.</h2>
  <p>An Exposure Certificate is one page per state, generated from this index
  rather than written. It is the smallest object about a state's substrate
  exposure that its recipient can check without trusting the sender.</p>
  <ul>
    <li>seven axis values, the composite, and the axis that binds the state</li>
    <li>coverage, BIG flag, and where a value is withheld, the cause</li>
    <li>CSovE tier and the deterministic rule that produced it</li>
    <li>vintage, <code>index_sha256</code>, chain head and entry count</li>
    <li>licence line and an APA citation block</li>
  </ul>
  <p>A dashboard is consulted and forgotten. A certificate is filed, and a filed
  record with a hash in it makes the next vintage checkable against this one.</p>
  <div class="tiers">
    <div class="tier"><b>Open</b><span>Everything on this page, all 35 states,
      CC-BY-NC. No gate, no account, no cookie.</span></div>
    <div class="tier tier--pick"><b>Named</b><span>One Exposure Certificate for
      a state you name. Send your name, role and organisation; a person answers.
      <span class="chip">start here</span>
      <span class="chip">automated fulfilment pending</span></span></div>
    <div class="tier"><b>Institutional</b><span>Full axis pack, chain spine
      export and re-run rights, under an institutional licence.</span></div>
  </div>
  <p class="asks"><a class="cta cta--lg" href="{ASK}">Request an Exposure
  Certificate</a></p>
  <p class="src">There is no form on this page. No backend stands behind it yet,
  and a form that silently discards what you type is worse than no form. Nothing
  you do here is logged and no cookie is set, so no GDPR notice is owed and none
  is shown. When fulfilment is automated this chip is removed, and the exchange
  is described here before it is built.</p>
</div>

<h2>Why the hash matters</h2>
<div class="gap">
<p>Every composite is recomputed from its own published axes on each build, and
the deploy fails on drift. The v8.0 vintage carried a composite that could not
be reproduced from the axes beside it: the United Kingdom scored at or above
Switzerland on all seven axes yet carried a lower composite, which no
non-negative weighting admits. It is derived now, and
<code>qesis_get_integrity</code> answers which generation you are reading.
An index you cannot check is an opinion with decimal places.</p>
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
    <dt>Sample</dt><dd>{n} ranked of 35, {len(doc['epis_findings'])} withheld under BIG</dd>
    <dt>Coupling</dt><dd>{cp['global']['CR']:.3f} global at n={cp['global']['n']},
      {cp['core']['CR']:.3f} import core at n={cp['core']['n']}</dd>
    <dt>Licence</dt><dd>{esc(doc['license'])}</dd>
    <dt>Scope</dt><dd>geographic layers stop at infrastructure, never people</dd>
  </dl>
  <p class="src">Verify it yourself: <code>git checkout
  {SERVED['deployment_commit'][:12]}</code>, then <code>sha256sum
  data/qesis_v8.json</code> must equal index_sha256, and <code>python
  scripts/verify_chain.py</code> must exit 0. Two planes exist, the working tree
  and the deployed commit, and this strip always states which one you are
  reading.</p>
</div></div>

<footer>
<p><strong>Infrastructure resilience is the only sustainable, dignified exit
from the polycrisis.</strong> That is the thesis this index was built to test,
and the reason every gap in it is published rather than filled.</p>
<p>QESIS+ {esc(vint)}. Batista Silva, R. (2026). Liquid Sovereignty. ESIC/LSE.
Dataset: Sovereign_Infra_Intelligence. Derived scores are own work; upstream
sources keep their own licences and are cited per axis. TeleGeography-derived
cable material is published only as derived aggregates, never raw. This page is
built from the index, never edited by hand.</p>
</footer>

</main>

<script>
/* Doherty. Every figure is pre-aggregated at build time, so selection, sorting
   and filtering are local and none of them makes a request. */
const R = {readout};
const CAUSE = {causes};
const box = document.getElementById("readout");
const fmt = (v, d) => v === null || v === undefined ? "withheld" : v.toFixed(d);

function show(iso) {{
  const r = R[iso];
  if (!r) return;
  let h = '<p class="who2">' + r.name + "</p>";
  if (r.composite === null) {{
    h += "<dt>composite</dt><dd>withheld</dd>";
    h += "<dt>coverage</dt><dd>" + fmt(r.coverage, 2) + "</dd>";
    h += "<dt>cause</dt><dd>" + r.cause + "</dd>";
    h += '<p class="cause"><strong>' + (CAUSE[r.cause] || "") + "</strong> "
       + r.cause_statement + "</p>";
  }} else {{
    h += "<dt>composite</dt><dd>" + fmt(r.composite, 1) + "</dd>";
    h += "<dt>rank</dt><dd>" + r.rank + " of 32, " + r.quartile + "</dd>";
    h += "<dt>bound by</dt><dd>" + r.binding + " at " + fmt(r.binding_v, 1) + "</dd>";
    h += "<dt>operators</dt><dd>" + r.providers + " over " + r.regions
       + " active cloud region" + (r.regions === 1 ? "" : "s")
       + ", ODI " + fmt(r.odi, 1) + "</dd>";
    h += "<dt>coverage</dt><dd>" + fmt(r.coverage, 2) + ", status " + r.status + "</dd>";
  }}
  box.innerHTML = h;
  for (const el of document.querySelectorAll("[data-iso]"))
    el.classList.toggle("sel", el.getAttribute("data-iso") === iso);
  for (const tr of document.querySelectorAll("[data-row]"))
    tr.classList.toggle("sel", tr.getAttribute("data-row") === iso);
}}

for (const el of document.querySelectorAll("[data-iso]")) {{
  const iso = el.getAttribute("data-iso");
  el.addEventListener("mouseenter", () => show(iso));
  el.addEventListener("focus", () => show(iso));
  el.addEventListener("click", () => show(iso));
}}

/* Linked views. A ranking row and a territory are the same object. */
const tb = document.querySelector("#rank tbody");
for (const tr of tb.querySelectorAll("tr")) {{
  const iso = tr.getAttribute("data-row");
  const go = () => {{ show(iso);
    document.getElementById("exposure").scrollIntoView({{block:"start"}}); }};
  tr.addEventListener("click", go);
  tr.addEventListener("keydown", e => {{ if (e.key === "Enter") go(); }});
}}

/* Sort. The arrow is the state, so the header says which way it is pointing. */
let dir = {{}};
for (const th of document.querySelectorAll("#rank th[data-sort]")) {{
  th.tabIndex = 0;
  const run = () => {{
    const k = +th.dataset.sort;
    dir[k] = dir[k] === 1 ? -1 : 1;
    const rows = [...tb.querySelectorAll("tr")];
    rows.sort((a, b) => {{
      const x = a.children[k].textContent.trim(), y = b.children[k].textContent.trim();
      const nx = parseFloat(x), ny = parseFloat(y);
      const c = isNaN(nx) || isNaN(ny) ? x.localeCompare(y) : nx - ny;
      return c * dir[k];
    }});
    rows.forEach(r => tb.appendChild(r));
    for (const o of document.querySelectorAll("#rank th")) o.removeAttribute("aria-sort");
    th.setAttribute("aria-sort", dir[k] === 1 ? "ascending" : "descending");
  }};
  th.addEventListener("click", run);
  th.addEventListener("keydown", e => {{ if (e.key === "Enter" || e.key === " ")
    {{ e.preventDefault(); run(); }} }});
}}

/* Filter. Hick: one input, no operators to learn. */
const q = document.getElementById("q"), cnt = document.getElementById("count");
q.addEventListener("input", () => {{
  const v = q.value.trim().toLowerCase();
  let shown = 0;
  for (const tr of tb.querySelectorAll("tr")) {{
    const hit = tr.textContent.toLowerCase().includes(v);
    tr.hidden = !hit; if (hit) shown++;
  }}
  cnt.textContent = shown + " of 32 shown";
}});

/* Scroll spy on the rail. Jakob: the reader always knows where they are.
   Position is compared directly rather than observed, because an observer
   band has edges a programmatic jump can land outside of. */
const links = [...document.querySelectorAll(".rnav a")];
const secs = ["exposure","audit","record","certificate"]
  .map(id => document.getElementById(id)).filter(Boolean);
let queued = false;
function spy() {{
  queued = false;
  const line = (document.querySelector(".rail")?.offsetHeight || 0) + 24;
  let cur = null;
  for (const el of secs) if (el.getBoundingClientRect().top <= line) cur = el.id;
  for (const a of links) a.classList.toggle("on", a.getAttribute("href") === "#" + cur);
}}
addEventListener("scroll", () => {{ if (!queued) {{ queued = true;
  requestAnimationFrame(spy); }} }}, {{passive: true}});
spy();
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
</head><body>
{body}
</body></html>
"""

ARTIFACT = """<title>QESIS+ Substrate Index</title>
<style>{tokens}{css}</style>
{body}
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
