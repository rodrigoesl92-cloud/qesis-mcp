# QESIS+ Daily Ops Report: 2026-08-24

Generated on the runner by `.github/workflows/daily-ops-report.yml` under SH-7. Repository `qesis-mcp`. No human ran this and none was asked to.

**Scope, declared.** This runner sees one repository. The thesis governance folder, the operational SQLite store and the OneDrive mounts are not reachable from here, so `_GOVERNANCE`, `_DATABASE`, the compliance chain and the Article 14 queue are OUT OF SCOPE in this report and are not reported as zero. D-007: withheld with cause.

## 1. What ran

**Self-heal:** `2026-08-24T15:34:07.022994+00:00`, mode repair. 14 of 15 controls passed, 0 repaired, 1 escalations, 1 failed (verify_workflow). Degraded: git_write_capability.

**Declared schedules in this repository:**

- `daily-ops-report.yml: 20 6 * * *`
- `production-integrity-probe.yml: 0 * * * *`
- `production-probe.yml: 17 * * * *`
- `qesis-integrity.yml: 0 6 * * *`
- `selfheal.yml: 17 * * * *`

## 2. What changed

HEAD `fix/report-l140-v2`, **1 ahead of origin/main, 1 behind**. origin/main at `e22888f 2026-08-19 21:50:48 +0200 docs(report): remove fabricated PROD-1, register L-140 and L-141`.

Working tree: **9 modified, 24 untracked.**

Untracked, therefore unhashed, unlineaged and on one disk only:

- `.github/workflows/daily-ops-report.yml`
- `data/axes/eti_convergence_evidence.json`
- `ops/CLOSE_ISSUES.md`
- `ops/COMMIT_MSG_2026-08-21.txt`
- `ops/FIX_PR68.ps1`
- `ops/LAND_2026-08-21.md`
- `ops/LEDGER_GAPS.json`
- `ops/PRIOR_ART_ETI_2026.md`
- `ops/RDL_PENDING_2026-08-24_scheduled_sweep.md`
- `ops/RD_INTAKE_ASSESSMENT_2026-08-21.md`
- `ops/issue_replies/`
- `ops/prototypes/V1_V2_V6_landing_redesign.html`
- `ops/prototypes/V1_V2_V6_landing_v2.html`
- `ops/prototypes/build_landing_redesign.py`
- `ops/prototypes/build_landing_v2.py`
- and 9 more

Last five commits:

- `ce03a65 2026-08-19 21:50:48 +0200 docs(report): remove fabricated PROD-1, register L-140 and L-141`
- `c5f0fc6 2026-08-19 21:13:55 +0200 fix(CI): root cause found. The secrets gate was excluded by the secrets ignore rule`
- `df5236b 2026-08-19 20:49:34 +0200 fix(CI): close the local-green CI-red class, third occurrence in one week`
- `8b2c4ad 2026-08-19 17:15:42 +0200 feat(D-113,A14-5): kill switch, secrets gate, and autonomous promotion`
- `8b12760 2026-08-19 16:28:00 +0200 feat(G-07,D-113): the ecosystem repairs itself, and declares its own substrate`

Served vintage: v9.0 (2026-08-13) (from data/qesis_v8.json).

## 3. Staleness and gaps

**Lessons ledger singleton: PASS.** 132 entries, 132 unique, max L-149, sha256 `67ab0161abe97540`.

- R1: no duplicate id
- R2: 17 absent ids, all declared
- R3: DEGRADED, sibling not reachable
- R3 DEGRADED: no declared sibling ledger path exists from here. Expected under CI, which checks out one repository. Reported, not imputed (D-007).

Out of scope from this runner and therefore NOT measured today: the Article 14 queue, the compliance chain length, the operational task board, `_GOVERNANCE` and `_DATABASE` drift, and the ENTSO-E task. Each lives behind a mount this job does not have. They are named so their absence is visible rather than silent.

## 4. Lessons

Ledger stands at 132 unique ids, max L-149. Declared absent ids are listed in `ops/LEDGER_GAPS.json` with an owner and a closing condition; R2 of the singleton gate fails the build on any absent id that is not declared there.

## 5. Next actions

1. **1 commits sit ahead of origin/main on `fix/report-l140-v2`.** Under G-06 an agent MAY merge a remediation pull request once its checks pass, by `gh pr merge --rebase`. This is not an operator action unless it promotes.
2. **24 untracked paths carry no hash and no lineage.** Commit or record them withdrawn. Owner: ARCHITECT.
3. **Self-heal controls failing: verify_workflow.** Owner: SENTINEL.

**Operator actions.** Only three classes reach the operator under SH-4: promotion absent a signed policy (G-06 limit 2), credential material in either direction (G-03, G-04), and an Article 14 signature. Nothing else in this report is his. If an item above is written as his and does not fall in one of those three, that is a defect in this generator.

---

_Generated at 2026-08-24T15:36:20+00:00 by `scripts/build_ops_report.py` on the runner. Read-only except this file. Zeros are zeros._
