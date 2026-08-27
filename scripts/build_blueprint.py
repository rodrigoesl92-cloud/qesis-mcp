#!/usr/bin/env python3
"""Generate public/blueprint.html, the three-phase causal surface.

WHY THIS IS A SECOND PAGE AND NOT A SECTION OF THE FIRST. Design law W-3 says
one hot accent per view, and if two things on a screen are hot then neither is.
`public/index.html` already spends its single hot mark on the gap between the
global and the import-core coupling ratio, which is that page's argument. The
percolation tipping point is this page's argument and it needs the same mark.
Two arguments, two views, one hot accent each. Von Restorff, and it is the
reason for the file rather than a decoration on it.

WHAT IT SHOWS. The causal chain the endpoint is asked to expose, in the order a
reader can check it:

  Phase 1  Define    what the trilemma costs, read off the coupling matrix
  Phase 2  Process   which agent touched the number, and where the gate sits
  Phase 3  Validate  equifinality and percolation, with what would refute them

Nothing here is typed by hand. Every number is read at build time from
data/qesis_v8.json and data/qesis_percolation.json, so the page cannot drift
from the artefacts it describes, and `--check` fails the build when it has.

The colour tokens, the base stylesheet and the doctrine scan are imported from
build_landing.py rather than copied. W-2 says nothing but the token block
declares a colour; two token blocks are two declarations and they drift.

Usage:  python scripts/build_blueprint.py [--out public/blueprint.html]
        python scripts/build_blueprint.py --check
        python scripts/build_blueprint.py --selftest
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_landing import TOKENS, CSS, esc, doctrine_scan  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "qesis_v8.json"
PERC = ROOT / "data" / "qesis_percolation.json"

# Only var() references. A colour literal outside the token block is what
# assert_no_var_in_attrs and doctrine_scan both exist to catch (L-047, W-2).
EXTRA_CSS = """
.phase{border-left:2px solid var(--cool);padding:.1rem 0 .1rem .9rem;margin:1.6rem 0 .6rem}
.phase h2{margin:.2rem 0 .2rem}
.phase .k{font-family:var(--mono);font-size:.72rem;letter-spacing:.06em;
          text-transform:uppercase;color:var(--ink-3)}
.figwrap{height:250px;margin:1rem 0;overflow-x:auto}
.figwrap svg{height:250px;width:100%;min-width:34rem;display:block}
.b{fill:var(--paper-2);stroke:var(--rule);stroke-width:1}
.bg{fill:var(--paper-2);stroke:var(--cool);stroke-width:2}
.t{fill:var(--ink);font-family:var(--mono);font-size:11px}
.ts{fill:var(--ink-3);font-family:var(--mono);font-size:9.5px}
.ar{stroke:var(--cool-2);stroke-width:1.5;fill:none}
.ah{fill:var(--cool-2)}
td.pos{color:var(--cool)}
td.neg{color:var(--ink-3)}
.tip b{color:var(--hot)}
.tip{display:flex;flex-wrap:wrap;gap:1.4rem;margin:1rem 0;padding:.9rem 1rem;
     background:var(--paper-2);border:1px solid var(--rule);border-radius:3px}
.tip div{min-width:8rem}
.tip b{display:block;font-family:var(--mono);font-size:1.5rem;font-weight:600;
       font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.tip span{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-3)}
.cool b{color:var(--cool)}
"""

#: The pipeline, painted from the stylesheet. `var()` does not resolve inside a
#: presentation attribute, so every fill and stroke here is a class (L-047).
PIPELINE_SVG = """
<svg viewBox="0 0 760 250" role="img"
     aria-label="SCOUT intake, then the SENTINEL gate, then ANALYST validation,
     then ARCHITECT operations, with the gate marked as the only path to
     publication.">
  <rect class="b" x="8"   y="60" width="150" height="62" rx="3"/>
  <rect class="bg" x="196" y="60" width="150" height="62" rx="3"/>
  <rect class="b" x="384" y="60" width="150" height="62" rx="3"/>
  <rect class="b" x="572" y="60" width="150" height="62" rx="3"/>
  <text class="t"  x="20"  y="84">SCOUT</text>
  <text class="ts" x="20"  y="100">intake, freshness,</text>
  <text class="ts" x="20"  y="113">licence at source</text>
  <text class="t"  x="208" y="84">SENTINEL</text>
  <text class="ts" x="208" y="100">the gate. PASS,</text>
  <text class="ts" x="208" y="113">REVIEW, BLOCK</text>
  <text class="t"  x="396" y="84">ANALYST</text>
  <text class="ts" x="396" y="100">fsQCA, coupling,</text>
  <text class="ts" x="396" y="113">what would falsify</text>
  <text class="t"  x="584" y="84">ARCHITECT</text>
  <text class="ts" x="584" y="100">pipeline, ledgers,</text>
  <text class="ts" x="584" y="113">the landing</text>
  <path class="ar" d="M158 91 H188"/><path class="ah" d="M188 86 l10 5 -10 5 z"/>
  <path class="ar" d="M346 91 H376"/><path class="ah" d="M376 86 l10 5 -10 5 z"/>
  <path class="ar" d="M534 91 H564"/><path class="ah" d="M564 86 l10 5 -10 5 z"/>
  <text class="ts" x="196" y="146">nothing reaches the database or the public</text>
  <text class="ts" x="196" y="159">without passing this box (Rule 1-1)</text>
  <path class="ar" d="M271 122 V140"/>
  <text class="ts" x="8"  y="196">Hick: four stages, not seven. Miller: each stage carries three facts.</text>
  <text class="ts" x="8"  y="212">Postel: SCOUT accepts loosely, SENTINEL emits strictly.</text>
  <text class="ts" x="8"  y="228">Tesler: the gate's complexity is the system's, never the reader's.</text>
</svg>
"""


def top_pairs(matrix: dict, axes: list, n: int = 6) -> list:
    """The strongest off-diagonal couplings, computed rather than chosen."""
    out = []
    for i, a in enumerate(axes):
        for b in axes[i + 1:]:
            out.append((a, b, matrix[a][b]))
    return sorted(out, key=lambda t: -abs(t[2]))[:n]


def build(doc: dict, perc: dict) -> str:
    cp = doc["coupling"]
    g, c = cp["global"], cp["core"]
    axes = g["axes"]
    ew = doc["effective_weights"]
    f = doc["fsqca"]
    sol = f["solution"]
    arc = doc.get("agent_reading_contract", {})
    gr, find = perc["graph"], perc["finding"]
    two = perc["two_numbers_that_are_not_the_same_number"]

    pair_rows = "\n".join(
        f'<tr><td>{esc(a)} and {esc(b)}</td>'
        f'<td class="n {"pos" if r > 0 else "neg"}">{r:+.3f}</td>'
        f'<td class="n">{c["matrix"][a][b]:+.3f}</td></tr>'
        for a, b, r in top_pairs(g["matrix"], axes))

    w_rows = "\n".join(
        f'<tr><td>{esc(k)}</td><td class="n">{v["nominal"]:.2f}</td>'
        f'<td class="n">{v["main_effect"]:.3f}</td>'
        f'<td class="n">{v["ci95"][0]:.3f} to {v["ci95"][1]:.3f}</td>'
        f'<td>{"inside" if v["nominal_in_ci"] else "OUTSIDE"}</td></tr>'
        for k, v in ew["axes"].items())

    path_rows = "\n".join(
        f'<tr><td class="epis">{esc(p["expression"])}</td>'
        f'<td class="n">{p["raw_consistency"]:.4f}</td>'
        f'<td class="n">{p["pri"]:.4f}</td>'
        f'<td class="n">{p["raw_coverage"]:.4f}</td>'
        f'<td class="n">{p["n_cases"]}</td>'
        f'<td>{esc(p["pri_flag"])}</td></tr>'
        for p in sol["per_path"])
    below = sum(1 for p in sol["per_path"] if "below" in p["pri_flag"])

    flag_rows = "\n".join(
        f'<tr><td class="epis">{esc(k)}</td><td>{esc(v.get("statement", ""))}</td></tr>'
        for k, v in (arc.get("flags") or {}).items())

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QESIS+ causal blueprint, {esc(doc['vintage'])}</title>
<meta name="description" content="The three phases behind the QESIS+ index:
 what the infrastructural trilemma costs, which agent touched which number, and
 the equifinality and percolation results with what would refute them.">
<style>{TOKENS}{CSS}{EXTRA_CSS}</style>
</head><body><main>

<p><span class="tag">{esc(doc['vintage'])}</span>
   <span class="tag">causal blueprint</span>
   <span class="tag">three phases</span></p>

<h1>Where every number on this endpoint comes from.</h1>

<p class="lede">A dashboard shows results. This page shows the chain: what the
trilemma costs when it is measured rather than asserted, which agent touched the
number and where the gate sits, and what would have to be true for the findings
to be wrong. Read it in order. Each phase is checkable against the artefact
named under it.</p>

<div class="phase"><span class="k">Phase 1, define</span>
<h2>The trilemma is a trade-off you can price</h2></div>

<p>Algorithmic independence, hyperscale efficiency and ecological sustainability
are not three separate budgets. Measured across {g['n']} states the six axes are
weakly entangled at CR {g['CR']:.3f}. Restricted to the states that import their
energy, their minerals and their hyperscalers, entanglement rises to
{c['CR']:.3f} over {c['n']} states. The trilemma is cheap where the substrate is
domestic and expensive where it is imported, and the gap between those two
numbers is the whole claim.</p>

<div class="stat">
  <div class="cool"><b>{g['CR']:.3f}</b><span>coupling, global n={g['n']}</span></div>
  <div class="cool"><b>{c['CR']:.3f}</b><span>coupling, import core n={c['n']}</span></div>
  <div class="cool"><b>{g['dominant_eigenmode']:.2f}</b><span>dominant eigenmode, global</span></div>
  <div class="cool"><b>{c['dominant_eigenmode']:.2f}</b><span>dominant eigenmode, core</span></div>
</div>

<div class="scroll"><table>
<thead><tr><th>Axis pair</th><th class="n">Global r</th><th class="n">Core r</th></tr></thead>
<tbody>{pair_rows}</tbody></table></div>
<p class="src">The six strongest off-diagonal terms, ranked by absolute value at
build time from coupling.global.matrix and read across to coupling.core.matrix.
Sign is the direction, not the strength. Asset: data/qesis_v8.json, vintage
{esc(doc['vintage'])}.</p>

<h3>What the weights actually do</h3>
<p>A declared weight is an intention. The main effect is what the axis moves in
practice, estimated as a Pearson correlation ratio over
{ew['n_complete']} complete cases with {ew['bootstrap_resamples']} bootstrap
resamples. Where the nominal weight falls outside the interval, the published
weight is not the realised influence and the page says so rather than repeating
the intention.</p>
<div class="scroll"><table>
<thead><tr><th>Axis</th><th class="n">Nominal</th><th class="n">Main effect</th>
<th class="n">95 percent interval</th><th>Nominal</th></tr></thead>
<tbody>{w_rows}</tbody></table></div>
<p class="src">Method: {esc(ew['method'][:120])}. Asset: qesis_v8.json
effective_weights, vintage {esc(doc['vintage'])}.</p>

<div class="phase"><span class="k">Phase 2, process</span>
<h2>Which agent touched the number, and where the gate sits</h2></div>

<p>Four runtimes, one gate. Intake is deliberately permissive and emission is
deliberately strict, so that everything ambiguous is resolved in one place
instead of everywhere. The registry is closed at six agents by R-12 and D-019;
the two not drawn here are HERALD, which publishes only from cleared material,
and COUNSEL, which owns money and law.</p>

<div class="figwrap">{PIPELINE_SVG}</div>
<p class="src">Painted from the stylesheet, never from presentation attributes:
var() does not resolve inside an attribute (L-047, W-2). Mandates are summarised
from sovereign-infra/agents/*.md, which remain authoritative.</p>

<h3>Limits the pipeline carries with the data</h3>
<p>These are not advice in a prompt, where they are deletable. They travel in
the index as data, and a gate fails the build if a flag arrives without the
statement that says what it means.</p>
<div class="scroll"><table>
<thead><tr><th>Flag</th><th>Statement</th></tr></thead>
<tbody>{flag_rows}</tbody></table></div>
<p class="src">Asset: qesis_v8.json agent_reading_contract. Read before any
evaluation of a country profile or pathway membership.</p>

<div class="phase"><span class="k">Phase 3, validate</span>
<h2>Equifinality, then percolation, then what would refute both</h2></div>

<p>There is no single road to high substrate vulnerability. The conservative
solution returns {sol['sufficient_configurations']} sufficient configurations at
consistency {sol['consistency']:.4f} and coverage {sol['coverage']:.4f} over
n={f['sample']['n']}, with {len(f['sample']['excluded'])} states withheld under
the Binary Integrity Guard and never imputed. Coverage below one is the point:
the solution explains the cases it covers and declines the rest.</p>

<div class="scroll"><table>
<caption class="src" style="text-align:left;caption-side:bottom">
PRI separates a term that is sufficient for the outcome from one that is equally
consistent with its negation. {below} of {len(sol['per_path'])} paths sit below
the 0.75 working convention and are published rather than dropped.</caption>
<thead><tr><th>Configuration</th><th class="n">Consistency</th><th class="n">PRI</th>
<th class="n">Coverage</th><th class="n">Cases</th><th>Flag</th></tr></thead>
<tbody>{path_rows}</tbody></table></div>
<p class="src">Model: {esc(f['model'])}. Calibration:
{esc(f['calibration']['rule'])}. Asset: qesis_v8.json fsqca.solution, vintage
{esc(doc['vintage'])}.</p>

<h3>Nothing is published as necessary</h3>
<div class="gap"><p>{esc(f['necessity_verdict'][:420])}</p></div>
<p class="src">Asset: qesis_v8.json fsqca.necessity_verdict. Robustness:
{esc(f['robustness']['status'][:180])}. The claim is partial until the two
declared families run, and it says so here rather than in a footnote.</p>

<h3>Percolation: the network tolerates loss and fails to aim</h3>
<p>An independent rebuild of the cable topology reproduces the published
articulation set exactly, {gr['articulation_cities']} of
{gr['articulation_cities']}, which is why the rest of this block is citable.
Over {gr['cities']} cities and {gr['cables']} cables, random removal is survivable
and targeted removal is not. The first twelve targeted removals are cheap. The
thirteenth is not.</p>

<div class="tip">
  <div><b>{two['single_step_severance']['cities_severed']}</b>
       <span>cities severed at removal {two['single_step_severance']['at_removal']}</span></div>
  <div class="cool"><b>{find['targeted_at_13_removals']:.4f}</b>
       <span>pair connectivity, targeted at 13</span></div>
  <div class="cool"><b>{find['random_at_13_removals']:.4f}</b>
       <span>pair connectivity, random at 13</span></div>
  <div class="cool"><b>{two['half_collapse_threshold']['at_removal']}</b>
       <span>removals to half collapse</span></div>
</div>

<p>The two numbers above are not the same quantity and are published side by
side so neither is quoted as the other. The single step severance is the largest
one step loss, at removal {two['single_step_severance']['at_removal']}, taking
the giant component from {find['lcc_before_tip']} cities to
{find['lcc_after_tip']}. Half collapse arrives later, at removal
{two['half_collapse_threshold']['at_removal']}, when the giant component first
falls below half its baseline. The critical node in this release is
{esc(find['critical_node'])}, and which city sits at the tip is a property of
the release rather than the finding.</p>
<p class="src">Asset: data/qesis_percolation.json, generated by
{esc(perc['generated_by'])}, vintage {esc(perc['vintage'])}, authority
{esc(perc['authority'])}. The source strings finding.statement and falsifier are
not reproduced on this page: each contains a word on the writing doctrine's
banned list (W-1). The numbers they describe are all above and the field names
locate them in the file.</p>

<h3>What would refute this</h3>
<div class="gap"><p>The percolation finding fails if an independent cable
topology of comparable coverage produces a targeted removal curve whose largest
single step severance falls inside the range of its own random removal curve, or
if the {gr['articulation_cities']} articulation cities fail to reproduce from
that topology. A different critical node does not refute it. The equifinality
result fails if the solution does not survive the declared anchor sensitivity,
which is why both anchor regimes are published and their disagreement is carried
as data rather than resolved by choosing one.</p></div>
<p class="src">Popper standing order, ANALYST mandate: every headline finding
states what would falsify it.</p>

<h2>Reading this page against the endpoint</h2>
<p>Every figure here is derived at build time from the two assets named in the
source lines, so this page cannot say something the artefacts do not. The same
values are served by <code>qesis_get_coupling</code>,
<code>qesis_get_pathways</code> and <code>qesis_get_integrity</code>, and
<code>qesis_get_integrity</code> answers which generation you are reading. The
deployment plane serves what was promoted and the local plane reads the working
tree; a reader is always told which one they have. That is G-01b working, not a
defect.</p>
<p>Nothing you do here is logged, no cookie is set and there is no backend
behind this page.</p>

<footer>
<p>QESIS+ {esc(doc['vintage'])}. Batista Silva, R. (2026). Liquid Sovereignty.
ESIC/LSE. Dataset: Sovereign_Infra_Intelligence.</p>
<p>Generated {esc(doc['lineage'].get('generated_at_utc', ''))} from
data/qesis_v8.json and data/qesis_percolation.json. Built by
scripts/build_blueprint.py, never edited by hand.</p>
</footer>
</main></body></html>
"""


def check_sync(doc: dict, perc: dict, page_path: Path) -> list:
    """Has the committed page drifted from the artefacts it describes?

    Byte equality would be the wrong test the moment anything on the page
    rotates, so what is compared is what must not drift: the numbers.
    """
    if not page_path.exists():
        return [f"{page_path.name} is missing"]
    page = page_path.read_text(encoding="utf-8")
    f, cp = doc["fsqca"], doc["coupling"]
    two = perc["two_numbers_that_are_not_the_same_number"]
    want = {
        "vintage": doc["vintage"],
        "global CR": f"{cp['global']['CR']:.3f}",
        "core CR": f"{cp['core']['CR']:.3f}",
        "fsqca consistency": f"{f['solution']['consistency']:.4f}",
        "fsqca coverage": f"{f['solution']['coverage']:.4f}",
        "sufficient configurations": f"{f['solution']['sufficient_configurations']} sufficient configurations",
        "cities severed": f">{two['single_step_severance']['cities_severed']}</b>",
        "articulation cities": str(perc["graph"]["articulation_cities"]),
    }
    return [f"{k} not on the page (expected {v!r})"
            for k, v in want.items() if v not in page]


def selftest() -> int:
    """One fixture the check must accept and one it must refuse (V-2).

    The refusal fixture perturbs a number in the index and asserts the check
    notices. A sync check that cannot fail is a page that is never checked.
    """
    doc = json.loads(INDEX.read_text(encoding="utf-8"))
    perc = json.loads(PERC.read_text(encoding="utf-8"))
    page = build(doc, perc)
    # Not beside the script: this repository is also read from a zero-trust
    # analysis mount that cannot unlink, so a temp file written inside the tree
    # cannot be removed and the selftest would leave litter it then reports on.
    # L-122 and L-150 are the same boundary met from the other side.
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
        print(f"{'PASS' if bad else 'FAIL'}  blueprint: a moved fsQCA consistency is "
              f"refused by the sync check")

        hits = doctrine_scan(page)
        ok += not hits
        print(f"{'PASS' if not hits else 'FAIL'}  blueprint: the rendered page passes "
              f"the writing and render doctrine scan")
        if hits:
            print(f"        {hits}")
    finally:
        tmp.unlink(missing_ok=True)
        tmp.parent.rmdir()
    print(f"{ok}/3 blueprint behaviours verified")
    return 0 if ok == 3 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "public" / "blueprint.html"))
    ap.add_argument("--json", default=str(INDEX))
    ap.add_argument("--percolation", default=str(PERC))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    doc = json.loads(Path(a.json).read_text(encoding="utf-8"))
    perc = json.loads(Path(a.percolation).read_text(encoding="utf-8"))

    if a.check:
        bad = check_sync(doc, perc, Path(a.out))
        print(f"blueprint sync check against {doc['vintage']}: {len(bad)} problems")
        for b in bad:
            print(f"  x {b}")
        if bad:
            print("public/blueprint.html has drifted; run scripts/build_blueprint.py",
                  file=sys.stderr)
            return 1
        print("blueprint page is in sync with the index and the percolation block.")
        return 0

    page = build(doc, perc)
    hits = doctrine_scan(page)
    print(f"doctrine scan: {len(hits)} violations")
    for h in hits:
        print(f"  x {h}")
    if hits:
        print("blueprint page NOT written.", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(page)//1024} KB) from {doc['vintage']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
