# Visualisation Spec: what the v9.0 payload can actually be drawn as

**v1.0 · 2026-08-13 · Owner: ARCHITECT · Gated by: `scripts/verify_dashboard.py`,
`qesis_agents/render_gate.py` · Tokens: `sovereign-infra/design/tokens.css`**

Written against the served payload, not against the design doctrine. Where the
two disagreed the payload won, per operator decision 2026-08-13. Section 6 records
what that cost.

---

## 1. The rule that generates this document

A view may encode a field only if the payload publishes that field for the states
the view claims to cover. Every violation below was found by applying that one
test, and every one of them is a view somebody would otherwise have built.

| Tempting view | Why it cannot ship as drawn |
|---|---|
| Fidelity ranking, 35 states | `fidelity.scores` holds 3 entries: DEU 0.943, ESP 0.782, GBR 0.833. U-03 |
| Trilemma corner plot | `trilemma_status` = `interpretive_overlay_only`. No pathway term or solution statistic may be described as a corner |
| "N of 35 states pass the sovereignty test" | No `sovereignty_test` field exists. This is D-104 with a country list attached, and `verify_dashboard.py` matches `\d{1,2} of 35` against declared counts only |
| Composite choropleth, all 35 | 32 carry a composite. HKG, SGP and TWN must render as `--epis` with the words "no coverage" and their withholding cause |
| Necessity claim for REE | `necessity_verdict`: no condition is publishable as necessary under D-109. The 0.916 figure is withdrawn |
| ODI capacity-weighted heat | AZ counts missing for 27 of 35. The Herfindahl is region-weighted and must say so. U-04 |

---

## 2. View inventory

Six views. Miller's bound is 7 chunks; this uses 6 and leaves headroom.

### V1. The finding (hero, above the fold)

**This is the page's argument and the only view that carries the hot accent.**

| Channel | Field | Note |
|---|---|---|
| Row | `effective_weights.axes` keys, ordered by `main_effect` desc | WSE, CSE, ODI, RGD, REE |
| Bar A, muted | `nominal` | `--cool-700`. What the index declares it weighs |
| Bar B | `main_effect` | `--cool-300`. What it behaves as if it weighs |
| Interval | `ci95` | `--line` whisker. **Mandatory.** E-2 forbids drawing the point estimate alone |
| Hot accent | WSE row only | `--hot`. The one axis with `nominal_in_ci: false` |
| Kicker | `reduction_test.spearman_vs_WSE_CSE_only` = 0.9329 | Deleting 40% of nominal weight leaves a ranking correlating at 0.9329 |
| Caveat, same viewport | `honesty_caveat` | Not a footnote and not behind a disclosure. It bounds the headline |

The claim the view is licensed to make: **nominal weights are not identified at
n=32, and WSE realises roughly 1.8x its declared weight.** It is not licensed to
say ODI, RGD and REE are weightless. Their intervals do not exclude nominal.

Falsifier, printed on the view per the Popper standing order: a sample large
enough to tighten the ODI, RGD and REE intervals away from zero.

### V2. Geography (attention anchor)

Choropleth, equal-earth, clickable, infrastructure only, never people.
Sequential `--cool-100` to `--cool-900` on `composite` for 32 states.
`--epis` fill for HKG, SGP, TWN with the literal string "no coverage" and the
`withholding_cause` code in the tooltip. Grey is a published gap, never a zero.

The two causes are not one label. HKG and SGP carry SOURCE_RESOLUTION, TWN carries
SOURCE_POLITICAL_COVERAGE, and collapsing them is the error `withholding_causes.
why_not_one_label` was written to prevent.

### V3. Country card

Seven axes from `axes`, `--font-num` with `tabular-nums`. Carries alongside every
value: `coverage`, `big_flags`, `csove.tier` and its deterministic `tier_rule`,
and for ODI the `odi_continuous.provider_shares` with `n_providers` and
`n_regions`. Semantic band (LOW / MODERATE / HIGH / CRITICAL) beside each score,
because a number without words is not published, it is displayed.

FPE and ESE render in a visually separated group labelled "diagnostic, enters no
composite" (U-05, D-044).

### V4. Coupling matrix

6x6 heatmap from `coupling.global.matrix`, diverging scale, `--cool-500` negative
through `--warm-500` positive. Annotate FPE x ODI = 0.783 as the known algebraic
coupling. Print `CR` 0.124, `S_nats` 1.57, `dominant_eigenmode` 0.40 and `n` 32.
State the exclusions on the view: HKG, SGP, TWN from global; ARE, BHR, IDN, MYS,
QAT, SAU from core. The exclusion rule is coverage-driven, not discretionary, and
saying so pre-empts the obvious accusation.

### V5. Pathways

`fsqca.solution`: conservative, 10 sufficient configurations, consistency 0.9048,
coverage 0.5807, n=32. Render `per_path` with `raw_consistency`, `pri`,
`raw_coverage` and `n_cases` in the same row. Any path carrying `pri_flag` renders
the flag text, not a colour alone: several sit below the 0.75 working convention
at `n_cases` of 1, and a one-case path presented without that fact is a finding
manufactured from a single observation.

`agent_reading_contract.theory_informed_limitation` renders above this view, with
its statement, before any pathway is read. R1.26 fails the build if a flag arrives
without its statement, and the same rule applies to the human reader.

### V6. Provenance strip (page end)

`vintage`, `index_sha256`, chain `entries` / `link_breaks` / `head_sha256`,
`provenance.plane`, licence, and the line "geographic layers stop at
infrastructure, never people". When `plane` is `working tree`, the strip prints the
warning verbatim. Two planes, and the reader is always told which one this is.

---

## 3. Encoding law

1. Nothing but `design/tokens.css` declares a colour. An SVG is painted from the
   stylesheet, never from a presentation attribute, because `var()` does not
   resolve inside one (L-047, `assert_no_var_in_attrs`).
2. One hot accent per view. V1 owns it. If a second view needs emphasis it takes
   `--warm-500`, not `--hot`.
3. Every canvas sits in an explicit-height wrapper carrying `--chart-h`,
   `--chart-h-tall` or `--chart-h-spark` (L-014). A canvas has no intrinsic size.
4. No em dash in prose anywhere on the surface (L-015). Run
   `SENTINEL doctrine_audit` as the last act of writing.
5. Every numeric cell uses `--font-num` with `tabular-nums`. Columns of figures
   that do not align are columns nobody compares.
6. Epistemic flags travel with the data. BIG status, coverage and withholding
   cause appear wherever the value appears, not once in a methods note.
7. Name the law in the code wherever it drives a choice.

---

## 4. The ROI instrument

Lead with the instrument, never the argument. The argument is V1; the instrument
is what a risk officer can put in a file.

**The Exposure Certificate.** One page per state, generated rather than written,
carrying: the seven axis values, composite and coverage, BIG flag and cause,
CSovE tier with its rule, the vintage, `index_sha256`, chain head and entry count,
the licence line, and an APA citation block. It is the smallest object that is
independently checkable by its recipient, which is the entire product.

Why this converts and a dashboard does not: a dashboard is consulted, a
certificate is filed. Filing creates a record with a hash in it, and the next
vintage makes that record stale. The renewal is structural rather than sold.

| Tier | Object | Gate |
|---|---|---|
| Open | V1 to V6, all 35 states, CC-BY-NC | none |
| Named | Exposure Certificate, per state | name, email, occupation, channel via visible mailto with a GDPR line. No silent forms, no fake liveness |
| Institutional | Full axis pack, chain spine export, re-run rights | institutional licence, COUNSEL triage |

Constraint: automated fulfilment ships only when a real server exists. Until then
the exchange is a visible mailto and the roadmap chip says so. An honesty label is
cheaper than a retraction.

---

## 5. Build order

1. V1 alone, against the real payload. It is the argument, and if it does not hold
   up nothing downstream matters.
2. V6, because a view without provenance is unpublishable.
3. V2, the attention anchor. One CDN load for the map projection; everything else
   offline and embedded.
4. V3 and V4.
5. V5 last. It carries the most caveats and the least commercial weight.
6. Exposure Certificate generator, from the same payload, no second source.

`verify_dashboard.py` runs at every step, not at the end. A surface nobody gates
will say whatever it said last.

---

## 6. What the doctrine rewrite cost

`stir-data-storytelling` v2 named the Infrastructural Trilemma as the thesis and
the emotional frame. The payload demoted it to `interpretive_overlay_only` on
2026-08-12 under QT-0007, and `verify_dashboard.py` refuses the structural
assertion by regex. The doctrine was therefore driving a build that fails the gate
on its own headline.

Three further conflicts in the same document, all stale rather than wrong when
written:

| Doctrine said | Payload says |
|---|---|
| `QESIS_THEORY = ... 0.08*CRD ...` | `0.08*RGD`. D-106 |
| `v8.0 canonical`, source `_DATABASE/csv_exports/` | v9.0, source `data/qesis_v8.json` |
| Palette listing `#6FA08C`, `#8CA6BC`, `#BC7A72`, `#C2B28A` | Not in `tokens.css`. Only tokens declare colour |

The trilemma is not deleted from the project. It stays where the payload puts it:
an interpretive claim in the theory chapter, nameable on the surface, never drawn
as a corner and never attached to a solution statistic.

The replacement headline is stronger. "A sovereignty index that declares five
weights and behaves as if it has two" is a finding a reviewer can check and a risk
officer can act on. "Pick two" was a slogan the model never supported.

**One external check, 2026-08-13.** The doctrine's standing geopolitical frame
verifies: Iranian Shahed drones struck two AWS data centres in the UAE before dawn
on 1 March 2026, with a third commercial facility hit in Bahrain, the first
deliberate wartime targeting of commercial data centres. The Bahrain limb is the
one to hedge, since deliberate targeting there is less clearly established than in
the UAE. Keep the frame, tighten that clause.
