# Deployment audit, 2026-08-02

**RESTATED 2026-08-15 under AUDIT-1. Restated, not closed, and not deleted.**

The original sign-off is preserved verbatim in section 3. Nothing measured on
2026-08-02 is withdrawn. What is corrected is one line that reported a property
of a connection as a property of a result, twice.

**Scope warning, read first.** This document audits a **deployment**, meaning the
edge URL, the transport and the layout. It does not audit an **index vintage**.
The file was previously named `v9.0_FINAL_AUDIT.md`, which collided with the
`v9.0` that names the index vintage, and the two are different things. Renamed at
`c4b24a7`. This document is dated 2026-08-02 and therefore predates v8.5, v8.6,
v8.9 and the v9.0 index. It is a record of that day and is not a current state.

---

## 1. The correction

**Original line 5:** "Data Pipelines: ENTSO-E, Ember, and EMODnet verified ACTIVE."

ACTIVE is a property of a connection. It is never a property of a result
(L-055: `success` is a status of the operation, not of the result). One line
committed that error twice.

### EMODnet

**Restated:** The EMODnet connector was reachable on 2026-08-02. Reachability is
not reproduction. `data/axes/emodnet_cse_evidence.json` records release
`EMODnet_HA_Cables_Telecommunication_20230628` sourcing **12 of 35** states,
coverage **0.3429** against the 0.75 BIG gate, `passes_big_gate: false`.

The reproduction verdict is:

> **DIRECTIONALLY CONSISTENT, MAGNITUDE INCONCLUSIVE AT n=9.** The inherited
> column moves in the direction its own formula requires. It is neither
> reproduced nor refuted: |rho| 0.467 does not reach the 0.683 needed at n=9.

**This restatement uses the corrected verdict, and that matters.** An earlier
reading called the axis NOT REPRODUCIBLE on the strength of a negative rho
against cable length. ANALYST superseded that on 2026-08-13: CSE is inverted by
construction, `CSE_country = 100 - minmax(...)`, so more cable means lower
connectivity stress and a negative correlation against length is what the
formula predicts rather than evidence against it. POL carries 58 km and CSE_EMO
96.9; GBR carries 22,080 km and CSE_EMO 30.4.

Reporting this as NOT REPRODUCIBLE overstated the finding. Reporting it as
verified would overstate it in the other direction. Both readings are refused.

The constraint is **n=9, not the correlation**. EMODnet's remit is European seas
and it sources only 12 of the 35 states, so no re-analysis of this release raises
n. Settling it needs the two outliers, ITA at 0.0 against 10,826 km and DEU at
2.9 against 5,960 km, traced to their per-state components, or a cable source
with global remit.

**Correction to the correction, recorded because it happened here.** Until
2026-08-15 the evidence file carried the withdrawn verdict in its top-level
`verdict` field with the supersession nested inside it, so a consumer reading the
obvious field served the retracted claim. Two did: `scripts/build_graph.py`
hardcoded it, and `ops/DISPATCH_BOARD_2026-08-14.md` propagated it into the
board, including into the first draft of this restatement. Logged as EMO-1.

### ENTSO-E

**Restated:** The ENTSO-E entry on that line is not supportable and was not
supportable on 2026-08-02. `ops/INC-20260731-01.md` is open and the standing
position is that the **ENTSO-E token is deferred, not held**. A pipeline whose
credential is deferred cannot have been verified ACTIVE.

This half was not in the original AUDIT-1 brief and was found while confirming
the EMODnet half. One line, two instances of the same error, and only one of them
was being tracked.

### Ember

Untested by this restatement. Absence of a finding here is absence of a check,
not a clean bill. Stated so it is not read as the second thing.

---

## 2. Disposition

**SENTINEL: RESTATED, NOT CLOSED.** What closes AUDIT-1 is a line in this
document that no longer conflates reachability with reproduction, which section 1
now provides, plus confirmation that no other artefact carries the old wording.
That second half is not confirmed. The 2026-08-14 dispatch board still cites the
withdrawn EMODnet verdict and has not been amended.

Nothing in this restatement changes a number. Coverage stays 0.3429, rho stays
-0.467, `passes_big_gate` stays false, and the 12-of-35 sourcing is unchanged.
The reading changed.

---

## 3. Original sign-off, preserved verbatim

> ## v9.0 Live Deployment Audit Sign-Off (2026-08-02)
> * **Frontend Edge URL**: https://qesis-mcp.vercel.app (Verified HTTP 200 OK)
> * **MCP Serverless Endpoint**: https://qesis-mcp.vercel.app/mcp (Verified JSON-RPC transport)
> * **UI/UX Master Layout**: Fully restored (Narratives, Governance table, Live Sources table, and Dynamic Toggle active).
> * **Data Pipelines**: ENTSO-E, Ember, and EMODnet verified ACTIVE.
> * **Compliance Sign-Off**: ISO/IEC 42001 (A.4.5), EU AI Act Article 12 audit trails fully operational.

Lines 2, 3 and 4 stand as measured on 2026-08-02. Line 5 is restated in section 1.
Line 6 is not re-audited here and carries the same scope warning as the rest of
this document: it records that date, not this one.
