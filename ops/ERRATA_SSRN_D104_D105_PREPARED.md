# Errata prepared for the SSRN deposit: D-104 and D-105

**Prepared 2026-08-28 by COUNSEL under the operator's authorisation of the standing
recommendations. Status: DRAFT AWAITING THE AUTHOR'S ACT.**

No agent can amend a deposit. This document exists so that the author's time with
the deposit is short: the text below is ready to paste, and every number in it is
read from the served index rather than recalled.

**Source of every figure here:** `data/qesis_v8.json`, vintage v9.0 (2026-08-13),
`index_sha256 8009815e4c19132048bf285cf6622cc864e7bc090fc31627b09ce0145463647d`,
which is the same hash the live endpoint reports and the same hash bound in
`data/RELEASES.json`. Three readings of the same bytes.

---

## Part 1. D-104. The two figures with no published method.

**What the deposit says.** Chapter IV, restated in V and VII: that 27 per cent of
states are compliant when EU AI Act compliance is re-scored against three QESIS+
substrate axes, and that 36 per cent of states face a risk of infrastructure
collapse.

**Why it cannot stand.** Neither figure names the three axes, the threshold, or
the rule. Neither is reproducible from the deposited dataset or from any vintage
since. This is the highest-severity item in the register and it has been open
since the concordance was written.

**Why withdrawal beats reconstruction.** A method reconstructed after the fact
that happens to land on a number already in print reads as fitted, and a reviewer
who suspects fitting will discount every other figure in the chapter. Withdrawal
costs two sentences and removes the largest attack surface in the work. It is
also the position the ecosystem's own doctrine requires: a claim carries the
command that produced it, or it is withdrawn.

### Text to paste

> **Erratum, Chapters IV, V and VII.** Two figures are withdrawn: the statement
> that 27 per cent of states are compliant when EU AI Act compliance is re-scored
> against QESIS+ substrate axes, and the statement that 36 per cent of states face
> a risk of infrastructure collapse. Neither figure carries a published method.
> The first does not specify which three axes were used in the re-scoring; the
> second specifies no threshold, no axis and no decision rule. Neither is
> therefore reproducible from the deposited dataset, and both are withdrawn rather
> than restated at a corrected value. No finding elsewhere in the work depends on
> either figure. The successor instrument publishes its composite formula, its
> coverage gate and its per-state withholding causes so that a reader can check
> every number in it against the axes published beside it.

---

## Part 2. D-105. Figure 4.1 does not match its own caption.

**What the deposit says.** The caption states a composite of 17.5 and a REE stress
of 91.5, a gap of 74.0. The plotted bars are 86 and 12. Inverting on 100 minus x
gives 82.5 and 8.5, which is neither pair. The bars preserve the gap in the label
while misstating both endpoints.

**What is true now.** Two things changed and both must be said. The composite
itself was retired: D-101 established that the v6.6 QESIS Theory column is not the
weighted sum its own header declares, so 17.5 was never a weighted index value.
And the axes have been recomputed since.

**Germany, read from the served index today:**

| Quantity | Deposit | Served index v9.0 |
|---|---|---|
| Composite | 17.5 | **33.3** |
| REE | 91.5 | **82.5** |
| Gap | 74.0 | **49.2** |
| Rank | 34 of 35 | **25 of 32** |

The full axis vector: WSE 40.8, CSE 7.3, REE 82.5, FPE 27.9, ODI 28.0, ESE 40.8,
RGD 22.2. Three states carry no composite and are excluded from the ranking, which
is why the denominator is 32 rather than 35.

**The redraw.** Two bars, 33.3 and 82.5, both on a 0 to 100 axis, gap annotated at
49.2, with the caption naming the vintage. Do not re-plot the deposited numbers:
the point of the figure survives the correction, because a gap of 49.2 between a
state's composite and its rare-earth stress makes the argument as well as 74.0 did.

### Text to paste

> **Erratum, Figure 4.1.** The published figure and its caption disagree: the
> caption states a composite of 17.5 and a REE stress of 91.5 while the plotted
> bars are 86 and 12, which correspond to no stated transform of the caption
> values. Separately, the composite of 17.5 is withdrawn on its own grounds: the
> source column it came from is not the weighted sum its header declares, and every
> composite was recomputed from the published axes in the successor vintages.
> Against the current instrument Germany carries a composite of 33.3 and a REE
> stress of 82.5, a gap of 49.2, and ranks 25 of the 32 states that satisfy the
> coverage gate. The figure is redrawn to those values and the caption names the
> vintage it plots.

---

## What closes each item

| Erratum | Closes when |
|---|---|
| D-104 | The withdrawal appears in the deposited version. It is then bound in the concordance and its status moves from OPEN to CLOSED. |
| D-105 | The redrawn figure and its caption appear in the deposited version. |

Both are author acts on a published deposit. Neither is delegable, and neither is
blocked by anything an agent still owes.
