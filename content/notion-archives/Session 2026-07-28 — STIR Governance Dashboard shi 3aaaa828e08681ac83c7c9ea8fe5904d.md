# Session 2026-07-28 — STIR Governance Dashboard shipped + D-021 proposed

Besitzer/-in: Rodrigo Silva
Letzte Änderung um: 28 July 2026 00:18

**Shipped:** `_DATABASE\STIR_Governance_Dashboard.html` — self-contained (35 KB, offline), built from the CSV export layer: exposure ranking by tier · t0→2080 trajectories · 7-axis radar · coupling heatmap · sovereignty-gate card · governance strip · sortable detail. Kept OUT of the public repo per D-012.

**Incident (SEV3, L-013):** qesis.sqlite showed 0 bytes (OneDrive dehydration + hot journal). CSV layer carried the whole build — the portability doctrine proved itself. [RICO] pin the sqlite "Always keep on this device".

**Headline findings:** SAU most exposed (76.9) · USA #2 (65.5: CSE 100, CRD 100) · **ESP worst trajectory (+11.6 by 2080)**, Europe owns 5 of the 6 fastest-deteriorating · sovereignty gate: only USA/FRA/DEU/NLD pass, ESP fails at 0.83 · WSE–ESE coupling +0.41 · TWN BIG-gated (gap-as-value).

**D-021 PROPOSED:** public layer = Python static generation from CSVs → GitHub Pages; Power BI = private mirror; web app deferred. Awaiting CEO sign-off.

**Also:** `ops/AGENT_ACCEPTANCE_TESTS.md` — 7 binary tests (T-SCO/SEN/ANA/ARC/HER/COU), runnable in chat or Claude Code; first run feeds the 2026-08-03 review.