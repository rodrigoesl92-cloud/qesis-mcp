"""SENTINEL orchestration gate. Phase transition from divergence to convergence.

Rebuilt from the operator's `stochastic_gate` draft, 2026-08-14.

WHAT WAS KEPT. The calibration core is correct and matches
`fsqca.calibration.rule` in the served index: Ragin's direct method, two-sided
logistic, ln(19) because full membership is 0.95 and full non-membership 0.05,
so the odds at the anchors are 19 and 1/19. The dual-slope selection handles
increasing and decreasing sets correctly in both directions. None of that is
changed.

WHAT WAS WRONG, and it is not a naming slip.

    system_efficiency = sum(scores) / len(scores)

That is the arithmetic mean of fuzzy membership. In this ecosystem that quantity
is already published under its own name, `prevalence`, and it sits in
`necessity_gate` directly beside `relevance_of_necessity` as a DIFFERENT field.
Compare WSE in the served payload: prevalence 0.5, RoN 0.8446. The draft's
docstring labelled the mean "Relevance of Necessity". It is not.

RoN cannot be computed from a condition vector alone. It is

    RoN = sum(1 - X) / sum(1 - min(X, Y))

and it requires the outcome Y. A function with no Y cannot return it.

Why this matters more than a rename: D-109 exists precisely because a
single-measure gate is not safe here. Under the sensitivity anchors REE returns
consistency_N 0.9672, comfortably above any single threshold, and it is still
refused because its RoN is 0.5766. A gate that opens on one scalar readmits
exactly the case the conjunctive rule was written to exclude. Worse, a mean is
monotonic in a flat signal, so a condition that is high almost everywhere opens
it trivially. That is D-103 violation C restated as an orchestration primitive.

WHAT REPLACES IT. The gate is conjunctive and reproduces D-109 exactly:
consistency_N >= 0.90 AND RoN >= 0.60 AND coverage_N >= 0.60, and the condition
must not track the negated outcome at least as closely as the outcome. RoN below
0.50 is reported TRIVIAL. Otherwise the measures are published and the label is
declined. The verdict is derived from the measures, never asserted beside them.

Rule 1-1: this is a gate specification, so it belongs to SENTINEL. COUNSEL wrote
the critique and owns none of the enforcement.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

LN19 = math.log(19.0)
NUDGE = 0.001

#: D-109, 2026-08-12. Conjunctive. Every bar must clear.
CONSISTENCY_N_PUBLISHABLE = 0.90
RON_PUBLISHABLE = 0.60
RON_TRIVIAL_BELOW = 0.50
COVERAGE_N_PUBLISHABLE = 0.60


@dataclass
class Calibration:
    scores: list[float]
    nudged: int = 0
    #: A count, not a silent repair. Cases landing on 0.5 are neither in nor out
    #: and are dropped from truth-table assignment, so Ragin's convention is to
    #: move them off the line. If many land there the ANCHORS are wrong, which is
    #: a finding about the calibration rather than a rounding detail. Publishing
    #: the count is what lets a reader tell those two situations apart.
    anchors: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def nudge_share(self) -> float:
        return self.nudged / len(self.scores) if self.scores else 0.0


def calibrate(values: Sequence[float], x_in: float, x_cross: float,
              x_out: float) -> Calibration:
    """Ragin direct method, two-sided logistic, into fuzzy membership on [0, 1]."""
    if x_in == x_cross or x_cross == x_out:
        raise ValueError("Qualitative anchors must be distinct.")
    if not values:
        # V-5. An empty input is a defect in the caller, not a result of 0.0.
        # The draft returned efficiency 0.0 and a closed gate for an empty list,
        # which reads as a decision when it is an absence.
        raise ValueError("No values to calibrate. Assert counts, never infer from silence.")

    increasing = x_in > x_cross
    a_hi = LN19 / (x_in - x_cross)
    a_lo = LN19 / (x_cross - x_out)

    out: list[float] = []
    nudged = 0
    for v in values:
        val = float(v)
        alpha = a_hi if (val >= x_cross) == increasing else a_lo
        z = -alpha * (val - x_cross)
        if z > 700:
            s = 0.0
        elif z < -700:
            s = 1.0
        else:
            s = 1.0 / (1.0 + math.exp(z))
        if abs(s - 0.5) < NUDGE:
            s = 0.5 + NUDGE if s >= 0.5 else 0.5 - NUDGE
            nudged += 1
        out.append(round(min(max(s, 0.0), 1.0), 4))
    return Calibration(scores=out, nudged=nudged, anchors=(x_in, x_cross, x_out))


def _measures(X: Sequence[float], Y: Sequence[float]) -> dict[str, float]:
    if len(X) != len(Y):
        raise ValueError(f"condition and outcome differ in length: {len(X)} vs {len(Y)}")
    if not X:
        raise ValueError("empty vectors")
    smin = sum(min(a, b) for a, b in zip(X, Y))
    return {
        "consistency_N": smin / sum(Y) if sum(Y) else 0.0,
        "coverage_N": smin / sum(X) if sum(X) else 0.0,
        "relevance_of_necessity": (sum(1 - a for a in X)
                                   / sum(1 - min(a, b) for a, b in zip(X, Y))
                                   if sum(1 - min(a, b) for a, b in zip(X, Y)) else 0.0),
        # Published because it is what the draft computed. Named correctly here
        # so the two can never again be mistaken for one another.
        "prevalence": sum(X) / len(X),
        "cases_above_half": float(sum(1 for a in X if a > 0.5)),
    }


@dataclass
class Verdict:
    condition: str
    measures: dict[str, float]
    negated: dict[str, float]
    verdict: str
    reading: str
    thresholds: dict[str, float] = field(default_factory=lambda: {
        "consistency_N_publishable": CONSISTENCY_N_PUBLISHABLE,
        "RoN_publishable": RON_PUBLISHABLE,
        "RoN_trivial_below": RON_TRIVIAL_BELOW,
        "coverage_N_publishable": COVERAGE_N_PUBLISHABLE,
    })


def necessity_gate(condition: str, X: Sequence[float], Y: Sequence[float]) -> Verdict:
    """D-109. Conjunctive. The verdict is DERIVED from the measures.

    The draft's `substrate_threshold_met` was a single comparison against a bare
    scalar. One scalar cannot carry this decision: consistency alone readmits REE
    at 0.9672 under the sensitivity anchors, which is the whole reason the rule
    is conjunctive rather than a threshold.
    """
    m = _measures(X, Y)
    notY = [1 - y for y in Y]
    n = _measures(X, notY)

    tracks_negation = n["consistency_N"] >= m["consistency_N"]

    if m["relevance_of_necessity"] < RON_TRIVIAL_BELOW:
        v, r = "TRIVIAL", (
            f"Relevance of Necessity {m['relevance_of_necessity']:.4f} below "
            f"{RON_TRIVIAL_BELOW}. The condition is near-constant, so high "
            f"consistency is an artefact of prevalence, not a result.")
    elif tracks_negation:
        v, r = "LABEL-DECLINED", (
            f"Tracks the negated outcome at least as closely: {n['consistency_N']:.4f} "
            f"against {m['consistency_N']:.4f}. A condition that explains the absence "
            f"as well as the presence explains neither.")
    elif (m["consistency_N"] >= CONSISTENCY_N_PUBLISHABLE
          and m["relevance_of_necessity"] >= RON_PUBLISHABLE
          and m["coverage_N"] >= COVERAGE_N_PUBLISHABLE):
        v, r = "PUBLISHABLE-AS-NECESSARY", "All three bars cleared and it does not track the negation."
    else:
        failed = [k for k, bar in (("consistency_N", CONSISTENCY_N_PUBLISHABLE),
                                   ("relevance_of_necessity", RON_PUBLISHABLE),
                                   ("coverage_N", COVERAGE_N_PUBLISHABLE))
                  if m[k] < bar]
        v, r = "LABEL-DECLINED", (
            "Report the values and decline the necessity label: "
            + ", ".join(f"{k} {m[k]:.4f} below {dict((('consistency_N', CONSISTENCY_N_PUBLISHABLE), ('relevance_of_necessity', RON_PUBLISHABLE), ('coverage_N', COVERAGE_N_PUBLISHABLE)))[k]}" for k in failed)
            + ". D-109 is conjunctive, so one failing measure declines the label.")

    return Verdict(condition=condition,
                   measures={k: round(x, 4) for k, x in m.items()},
                   negated={k: round(x, 4) for k, x in n.items()},
                   verdict=v, reading=r)
