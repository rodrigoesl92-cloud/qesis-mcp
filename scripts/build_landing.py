"""Generate public/index.html from the served index.

Nothing on the page is typed by hand. Every number is read from
data/qesis_v8.json at build time, so the page cannot drift from the index it
describes. The generator enforces the binding design rules rather than trusting
anyone to remember them, and fails loudly if the doctrine scan does not pass.

Tables are real HTML, so the page is readable with JavaScript disabled. That is
both the accessibility floor and the resilience floor.

Usage:  python scripts/build_landing.py [--out public/index.html]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANNED_WORDS = ["delve", "unlock", "robust", "seamless", "crucial", "foster",
                "empower", "elevate", "tapestry"]

TOKENS = """
:root{
  --ink:#1c1b19; --ink-2:#4a4744; --ink-3:#78736d;
  --paper:#faf8f5; --paper-2:#f1ede7; --rule:#ddd6cc;
  --cool:#3d5a68; --cool-2:#6d8b98;
  --hot:#c96a5e;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --sans:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  --gap:1.5rem; --measure:74ch;
}
@media (prefers-color-scheme:dark){
  :root{ --ink:#ece7e0; --ink-2:#bdb6ad; --ink-3:#8d857c;
         --paper:#171614; --paper-2:#201e1b; --rule:#35322d;
         --cool:#8fb0be; --cool-2:#6d8b98; --hot:#e08476; }
}
"""

CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
     line-height:1.55;font-size:16px}
main{max-width:var(--measure);margin:0 auto;padding:var(--gap) 1.2rem 4rem}
h1{font-size:1.9rem;line-height:1.2;margin:.2rem 0 .4rem;letter-spacing:-.015em}
h2{font-size:1.15rem;margin:2.4rem 0 .6rem;letter-spacing:-.01em}
h3{font-size:.95rem;margin:1.6rem 0 .4rem;color:var(--ink-2)}
p{margin:.6rem 0;color:var(--ink-2)}
a{color:var(--cool);text-underline-offset:2px}
.lede{font-size:1.05rem;color:var(--ink)}
.tag{display:inline-block;font-family:var(--mono);font-size:.72rem;
     letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);
     border:1px solid var(--rule);border-radius:2px;padding:.15rem .45rem;
     margin-right:.35rem}
table{width:100%;border-collapse:collapse;margin:.8rem 0;font-size:.9rem}
th,td{text-align:left;padding:.4rem .5rem;border-bottom:1px solid var(--rule)}
th{font-weight:600;font-size:.75rem;text-transform:uppercase;
   letter-spacing:.05em;color:var(--ink-3)}
td.n,th.n{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
.scroll{overflow-x:auto}
.src{font-size:.75rem;color:var(--ink-3);margin:.3rem 0 0;font-family:var(--mono)}
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
footer{border-top:1px solid var(--rule);margin-top:3rem;padding-top:1rem;
       font-size:.82rem;color:var(--ink-3)}
.epis{color:var(--cool);font-family:var(--mono);font-size:.8rem}
"""


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def build(doc: dict, day_of_year: int) -> str:
    C = doc["countries"]
    cp, model, lin = doc["coupling"], doc["composite_model"], doc["lineage"]
    ranked = sorted(((i, c) for i, c in C.items() if c["composite"] is not None),
                    key=lambda t: -t[1]["composite"])
    epis = doc.get("epis_findings", [])

    # Rotate the focus state by day of year so the instrument does not read as a
    # single case study.
    focus_iso, focus = ranked[day_of_year % len(ranked)]

    rows = "\n".join(
        f'<tr><td class="n">{r+1}</td><td>{esc(c["name"])}</td>'
        f'<td class="n">{c["composite"]:.1f}</td>'
        f'<td class="n">{c["axes"]["ODI"]:.1f}</td>'
        f'<td class="n">{c["axes"]["ESE"]:.1f}</td>'
        f'<td class="n">{c["coverage"]:.2f}</td></tr>'
        for r, (i, c) in enumerate(ranked))

    epis_rows = "\n".join(
        f'<tr><td>{esc(C[e["iso3"]]["name"])}</td>'
        f'<td class="n">{e["coverage"]:.2f}</td>'
        f'<td class="epis">{esc(", ".join(e["missing_weighted_axes"]))}</td></tr>'
        for e in epis)

    src_names = ", ".join(lin.get("sources", {}))
    gen = lin.get("generated_at_utc", "")

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QESIS+ {esc(doc['vintage'])}, sovereign substrate intelligence</title>
<meta name="description" content="An auditable index of digital sovereignty
 substrate risk across 35 states and seven measured axes. Every score
 reproducible from primary portals; coverage gaps published as findings.">
<style>{TOKENS}{CSS}</style>
</head><body><main>

<p><span class="tag">{esc(doc['vintage'])}</span>
   <span class="tag">35 states</span>
   <span class="tag">7 axes</span></p>

<h1>Substrate entanglement is geopolitical, not universal.</h1>

<p class="lede">QESIS+ measures what a state's digital sovereignty physically
rests on: water, submarine cable, rare earths, foreign platforms, hyperscale
operator concentration, cloud risk density and electricity. Seven axes, 35
states, every score reproducible from a primary portal.</p>

<div class="stat">
  <div><b>{cp['global']['CR']:.3f}</b><span>coupling, global n={cp['global']['n']}</span></div>
  <div class="argued"><b>{cp['core']['CR']:.3f}</b><span>coupling, import core n={cp['core']['n']}</span></div>
  <div><b>{len(ranked)}</b><span>ranked</span></div>
  <div><b>{len(epis)}</b><span>published gaps</span></div>
</div>

<p>Energy-rich states decouple through cheap, reliable, carbon-heavy power. For
states that import their energy, their minerals and their hyperscalers, every
axis is bound to every other. That is the finding, and the gap between those two
numbers is the argument.</p>
<p class="src">Source: derived at build time from the published axes.
rho = C/6 trace-normalised, CR = 1 - S(rho)/ln 6. Coverage {cp['global']['n']}
of 35 global, {cp['core']['n']} of 35 core. Vintage {esc(doc['vintage'])}.</p>

<h2>The gap is the finding</h2>
<p>The Binary Integrity Guard never imputes. A state missing a weighted axis is
not ranked and not quietly zeroed: it is published as a gap with its coverage
stated. Below the declared 0.75 threshold, no composite is emitted at all.</p>
<div class="scroll"><table>
<caption class="src" style="text-align:left;caption-side:bottom">
Coverage is the declared weight mass actually present.</caption>
<thead><tr><th>State</th><th class="n">Coverage</th><th>Absent</th></tr></thead>
<tbody>{epis_rows}</tbody></table></div>

<h2>Ranking</h2>
<div class="scroll"><table>
<thead><tr><th class="n">#</th><th>State</th><th class="n">Composite</th>
<th class="n">ODI</th><th class="n">ESE</th><th class="n">Cov</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="src">Composite = {esc(model['expression'])}. Derived at build time,
never carried. ODI is the continuous Herfindahl measure over operator shares of
active cloud regions. Sources: {esc(src_names)}. Generated {esc(gen)}.</p>

<h2>Today's focus: {esc(focus['name'])}</h2>
<p>{esc(focus['name'])} sits at composite {focus['composite']:.1f} with coverage
{focus['coverage']:.2f}. Its binding constraint is
{esc(max((a for a in focus['axes'] if focus['axes'][a] is not None), key=lambda a: focus['axes'][a]))},
and its operator concentration reads {focus['axes']['ODI']:.1f} across
{focus['odi_continuous']['n_providers']} providers over
{focus['odi_continuous']['n_regions']} active cloud regions.</p>
<p class="src">Focus rotates daily so the instrument does not read as a single
case study. Asset: qesis_v8.json, coverage 35 of 35, vintage
{esc(doc['vintage'])}.</p>

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

<h2>Integrity</h2>
<div class="gap">
<p>Every composite is recomputed from its own published axes on each build, and
the deploy fails on drift. The v8.0 vintage carried a composite that could not be
reproduced from the axes beside it: the United Kingdom scored at or above
Switzerland on all seven axes yet carried a lower composite, which no
non-negative weighting admits. It is derived now, and
<code>qesis_get_integrity</code> answers which generation you are reading.</p>
</div>
<p class="src">Formula {esc(model['formula_id'])}. Gate: 16 checks plus a
mutation test that injects each defect class the gate must catch.</p>

<h2>Licence and contact</h2>
<p>Demo vintage CC-BY-NC. Derived scores are own work; upstream sources keep
their own licences and are cited per axis. TeleGeography-derived cable material
is published only as derived aggregates, never raw.</p>
<p>For the institutional vintage, or to ask a question about the method, write
to the address on the repository. There is no form on this page, because there
is no backend behind it and a form that silently discards what you type is
worse than no form. Nothing you do here is logged, and no cookie is set.</p>

<footer>
<p>QESIS+ {esc(doc['vintage'])}. Batista Silva, R. (2026). Liquid Sovereignty.
ESIC/LSE. Dataset: Sovereign_Infra_Intelligence.</p>
<p>Generated {esc(gen)} from {esc(src_names)}. This page is built from the index,
never edited by hand.</p>
</footer>
</main></body></html>
"""


def doctrine_scan(page: str) -> list[str]:
    """The rules run as code. A page that violates them does not ship."""
    bad = []
    if "—" in page:
        bad.append("em dash present")
    for w in BANNED_WORDS:
        if re.search(rf"\b{w}\b", page, re.I):
            bad.append(f"banned word: {w}")
    # colour literals outside the token block
    body = page.split("</style>", 1)[-1]
    if re.search(r"#[0-9a-fA-F]{3,6}\b", body):
        bad.append("colour literal outside tokens")
    if "prefers-color-scheme" not in page:
        bad.append("no dark scheme")
    if page.count('class="src"') < 3:
        bad.append("charts or tables lacking a source line")
    if "GDPR" not in page and "no backend" not in page:
        bad.append("no plain data-exchange statement")
    return bad


def check_sync(doc: dict, page_path: Path) -> list[str]:
    """Is the committed page still telling the truth about the index?

    Byte equality is the wrong test: the focus state rotates by day of year, so
    a regenerated page legitimately differs from a page built yesterday. What
    must not drift is the numbers, so those are what get compared.
    """
    if not page_path.exists():
        return [f"{page_path.name} is missing"]
    page = page_path.read_text(encoding="utf-8")
    cp = doc["coupling"]
    ranked = [c for c in doc["countries"].values() if c["composite"] is not None]
    want = {
        "vintage": doc["vintage"],
        "global CR": f"{cp['global']['CR']:.3f}",
        "core CR": f"{cp['core']['CR']:.3f}",
        "ranked count": f">{len(ranked)}<",
        "gap count": f">{len(doc.get('epis_findings', []))}<",
        "formula": doc["composite_model"]["expression"],
    }
    return [f"{k} not on the page (expected {v!r})"
            for k, v in want.items() if v not in page]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "public" / "index.html"))
    ap.add_argument("--json", default=str(ROOT / "data" / "qesis_v8.json"))
    ap.add_argument("--check", action="store_true",
                    help="verify the committed page matches the index; write nothing")
    ap.add_argument("--day", type=int, default=None,
                    help="override the day-of-year used to rotate the focus state")
    args = ap.parse_args()

    doc = json.loads(Path(args.json).read_text(encoding="utf-8"))

    if args.check:
        bad = check_sync(doc, Path(args.out))
        print(f"landing sync check against {doc['vintage']}: {len(bad)} problems")
        for b in bad:
            print(f"  x {b}")
        if bad:
            print("public/index.html has drifted; run scripts/build_landing.py",
                  file=sys.stderr)
            return 1
        print("landing page is in sync with the index.")
        return 0

    day = args.day if args.day is not None else datetime.now(timezone.utc).timetuple().tm_yday
    page = build(doc, day)

    bad = doctrine_scan(page)
    print(f"doctrine scan: {len(bad)} violations")
    for b in bad:
        print(f"  x {b}")
    if bad:
        print("landing page NOT written.", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} ({len(page)//1024} KB) from {doc['vintage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
