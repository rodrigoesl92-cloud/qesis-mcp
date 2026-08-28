# Filesystem reorganisation plan

**2026-08-28 · ARCHITECT · PROPOSAL ONLY. Nothing in this document has been executed.**
**Authority: `ops/FILESYSTEM_STANDARD.md` rule FS-14. Moving a file is an Article 14 act because it breaks the paths gates and scripts depend on. The operator signs, item by item or group by group.**

Scope: **`qesis-mcp` only.** `C:\Users\Lenovo\OneDrive\sovereign-infra` is not
connected to this session, so no proposal is made about it and none is implied.
`C:\Users\Lenovo\sovereign-infra` is the declared decoy and holds one directory.
A sovereign-infra pass needs either a session with the OneDrive folder connected
or a native run.

Every group below carries what breaks. A move landed without its call-site
changes is a broken build with a tidy directory listing (FS-15).

---

## Group A. Four public pages that return 404 today. **Highest priority.**

Measured 2026-08-28 against the origin, not inferred. `GET /overview`,
`/method`, `/console` and `/dashboard` all return **404**, as do the four
`.html` self-routes for the same pages. Eight dead declarations, four pages.

The platform serves `public/`. Proof from the same probe run: `/` returns
15167 bytes, which is exactly `public/index.html`, and `/blueprint.html`
returns 82582 bytes, which is exactly `public/blueprint.html`. The four pages
below sit in the repository root, where the platform does not look.

| Source | Destination | Bytes | Reason |
|---|---|---|---|
| `overview.html` | `public/overview.html` | 29973 | `vercel.json` routes `/overview` and `/overview.html` here and both 404 |
| `method.html` | `public/method.html` | 54138 | `vercel.json` routes `/method` and `/method.html` here and both 404 |
| `console.html` | `public/console.html` | 23776 | `vercel.json` routes `/console` and `/console.html` here and both 404 |
| `STIR_Governance_Dashboard.html` | `public/STIR_Governance_Dashboard.html` | 78549 | `vercel.json` routes `/dashboard` and the full filename here and both 404 |
| `index.html` (root) | delete | 1974 | dated 2026-08-14 and superseded. `public/index.html` is the generated landing page, is 15167 bytes, is gated by `build_landing.py --check`, and is what production actually serves. Two files with one name in one repository is the ambiguity this whole exercise exists to remove |

**What breaks.** Nothing measured breaks. `scripts/verify_dashboard.py` already
resolves the dashboard through a candidate list that includes
`public/STIR_Governance_Dashboard.html`, so the move satisfies it rather than
breaking it. No workflow references any of the five filenames.

**What must land in the same change set.** The wiring of
`scripts/verify_static_routes.py` into `.github/workflows/qesis-integrity.yml`.
The gate exists and its six fixtures pass; it is deliberately not armed yet,
because arming it before the remedy would turn the required check red on `main`
every run until the decision is made, and a gate no correct action can satisfy
is a deadlock wearing the costume of a control (SH-10f).

### COUNSEL's recommendation, named as such

**Take option A, move the four pages into `public/`.** The alternative, option
B, is to delete the eight route entries and retire the surface. A is
recommended on three grounds. First, the pages exist and are substantial:
`method.html` alone is 54 kB of methodology and the dashboard is the operator's
scientific control panel, which memory records as one of the two surfaces this
project deliberately maintains. Second, deleting routes retires a public
surface, and retiring a surface is a HERALD and operator decision about the
product, whereas restoring one that was already declared is a repair. Third,
the addresses have been published; an address this ecosystem gives to somebody
is followed by a control or it is withdrawn deliberately, never left dead
(L-191).

**What changes if the decision goes the other way.** If option B is chosen, the
eight route entries leave `vercel.json`, the four files move to
`ops/prototypes/` or are deleted, and `verify_static_routes.py` still passes
because it asserts a correspondence and not a page count. The gate is neutral
between the two remedies by construction. What is not acceptable is a third
option in which nothing is decided, because that leaves four published
addresses returning 404 with a green audit above them.

**What ARCHITECT does the moment this is signed.** One change set: the four
moves, the root `index.html` deletion, the gate wired into
`qesis-integrity.yml`, and `verify_static_routes.py --live` run against the
deployment as the after check.

---

## Group B. Operator PowerShell in `ops/`. Rule FS-9.

`ops/` is the record. Executables live in `scripts/`. `scripts/ops/` already
exists and already holds two of these.

| Source | Destination | Reason |
|---|---|---|
| `ops/PUSH_2026-08-15.ps1` | `scripts/ops/archive/` | one-shot dated recovery script, superseded by `LAND_EVERYTHING_FINAL.bat` rev 6 |
| `ops/RECOVER_AND_LAND_2026-08-15.ps1` | `scripts/ops/archive/` | same |
| `ops/RESUME_REBASE_2026-08-15.ps1` | `scripts/ops/archive/` | same |
| `ops/DEPLOY_2026-08-19.ps1` | `scripts/ops/archive/` | same |
| `ops/FIX_CI_2026-08-19.ps1` | `scripts/ops/archive/` | same |
| `ops/LAND_2026-08-19.ps1` | `scripts/ops/archive/` | same |
| `ops/ROOTCAUSE_2026-08-19.ps1` | `scripts/ops/archive/` | same |
| `ops/FIX_PR68.ps1` | `scripts/ops/archive/` | one-shot, the pull request is closed |
| `install-production-probe.ps1` (root) | `scripts/ops/` | still live, belongs with the other operator scripts, not loose in the root |

**What breaks.** Nothing measured. No workflow and no Python file references any
of the nine filenames. The risk is that the operator has a shortcut pointing at
one of the dated scripts, which is why they are archived rather than deleted.

---

## Group C. Transient message buffers in `ops/`.

| Source | Destination | Reason |
|---|---|---|
| `ops/COMMIT_MSG.txt` | delete | a commit message buffer is not a record. `LANDING_MANIFEST.json` beside the lander now carries the branch and the messages, per `SESSION_START.md` |
| `ops/COMMIT_MSG_2026-08-21.txt` | delete | same, and dated seven days before the manifest existed |

**What breaks.** Nothing. `verify_lander_contract.py` reads the manifest, not
these files.

---

## Group D. Legacy scripts loose in the repository root.

Fifteen Python files sit in the root. Most are single-purpose agent scripts
from before `scripts/` was the convention.

| Source | Destination | Reason |
|---|---|---|
| `agent_analyst_fix_headers.py` | `scripts/legacy/` | one-shot agent script |
| `agent_architect_format_html.py` | `scripts/legacy/` | one-shot agent script |
| `agent_architect_migrate_pg.py` | `scripts/legacy/` | one-shot agent script |
| `agent_architect_promote_v85.py` | `scripts/legacy/` | one-shot, v8.5 is four vintages back |
| `agent_architect_update_ledger.py` | delete | superseded and dangerous. The ledger is written only by `rdl.py record` and `rdl_append.py`. A second writer is how a ledger stops being one file |
| `agent_scout_license_audit.py` | `scripts/legacy/` | superseded by `SENTINEL licence_audit` |
| `audit_licenses.py` | `scripts/legacy/` | 403 bytes, superseded by the same |
| `audit_phase2_completion.py` | `scripts/legacy/` | phase 2 is closed |
| `v86_reseal.py` | `scripts/legacy/` | v8.6 is three vintages back |
| `test_client.py` | `tests/` | it is a test and `tests/` exists |
| `infrastructure_mcp.py` | `scripts/legacy/` | 1111 bytes, no importer |
| `telegeography_connector.py` | `scripts/legacy/` | superseded by the acquisition register and the axes evidence files |
| `qesis_endpoints.py` | `scripts/legacy/` | superseded by `data/endpoints.json` and `verify_endpoints.py` |
| `locate_db.py` | delete | **this is the ad-hoc locator the mandate exists to replace.** `data/DATA_MAP.json` is now generated and gated. Keeping a second locator that answers the same question differently is the defect restated |
| `locate_json.py` | delete | same |

**MUST NOT MOVE: `server.py`.** `.github/workflows/qesis-integrity.yml` line 10
names `server.py` explicitly in its `paths` filter, and
`verify_served_contract.py` imports it. Moving it silently removes the gate's
trigger and the contract check at once.

**What breaks.** Nothing measured for the thirteen moves. Verify before landing
that no `.github/workflows/**` file and no `scripts/**` file imports any of
them; a grep at landing time is cheaper than a revert.

---

## Group E. Root artefacts that are records, not code.

| Source | Destination | Reason |
|---|---|---|
| `Executive Synthesis The STIR Architecture OS Strategy.pdf` | `docs/` | a document belongs in `docs/`, and a filename with six spaces in a repository root is a shell hazard on every platform |
| `LAND_EVERYTHING_FINAL.bat_Proof of execution_human.txt` | `ops/evidence/LANDING_PROOF_2026-08-27.txt` | it is landing evidence. Rename to the FS-7 convention: the current name encodes a tool, a claim and an audience and sorts nowhere useful |

---

## Group F. Superseded data artefacts.

| Source | Destination | Reason |
|---|---|---|
| `data/qesis_v8.2_superseded.json` | `data/archive/` | superseded, already gitignored |
| `data/qesis_v8.3_CANDIDATE.json` | `data/archive/` | a candidate that was never promoted |
| `data/qesis_v8.json.pre-v8.5.bak` | `data/archive/` | a backup, already gitignored |

**`data/qesis_v8.0_superseded.json` MUST NOT MOVE without its register entry.**
`data/vintage_lineage.json` records for the v8.0 row: `single_repo_reason:
"Predates both repositories. Retained as data/qesis_v8.0_superseded.json."`
Moving the file falsifies the lineage register, and the lineage register is
gated by `verify_vintage_pairing.py`. If it moves, the register text changes in
the same change set, in both repositories, under G-01.

---

## Group G. Named so the absence of a proposal is visible

These were examined and are **deliberately not proposed for any change**.

- `server.py`, `api/`, `data/qesis_v8.json`, `data/chain_spine.jsonl`,
  `ops/LESSONS_LEDGER.md`, every `ops/D-NNN_*.md`: each has a gate or a
  workflow pointing at it by path.
- `database_string.txt` (root, 113 bytes): matched by `.gitignore` line 97 and
  cleared by `verify_no_plaintext_secrets.py`, which passed in the
  2026-08-28T18:06Z control set. **Not opened by this session and not proposed
  for movement.** Credential material is G-03 and G-04 in both directions.
- `Digital Twin R&D/`, `04_Workspace_Handshakes/`, `content/`, `dashboard/`,
  `docs/`, `graphify-out/`, `lib/`, `workers/`, `var/`: not assessed. They were
  outside the walk this session indexed and reporting an unassessed directory
  as untidy would be an inference, not a measurement.
- `ops/D-103_STATUS.md`: already carried as open item `DOC-1` in `CLAUDE.md`
  section 7. Not reopened here.

---

## Group H. Hardcoded path remediation. See the report for the full grep.

Not a file move, so not an Article 14 act, and it lands as ordinary agent work
once Group A is decided.

| File | Line | Change |
|---|---|---|
| `scripts/compute_odi_bounds.py` | 54 to 56 | resolve `cloud_regions_master.csv` through `data/DATA_MAP.json` instead of two literals, one of which is the dead sandbox root `/sessions/trusting-brave-fermat/...` |
| `scripts/audit_ecosystem.py` | 52 | read the sovereign-infra path from `ops/PATH_REGISTRY.json` |
| `scripts/apply_operator_decisions.py` | 37 | read the store path from `ops/PATH_REGISTRY.json` |
| `scripts/gh_ops.py` | 97 | same |
| `scripts/rdl.py` | 65 | same |
| `scripts/verify_ledger_singleton.py` | 59 | same |
| `scripts/verify_lander_contract.py` | 53 | same |

**`scripts/build_ecosystem_state.py` lines 52, 65 and 70 are NOT in this list
and must keep their literals.** It is the script that writes
`PATH_REGISTRY.json`, so it is the declaring authority, and a bootstrap cannot
read the file it is about to write. Rule FS-13.

---

## Summary of what the operator is being asked to sign

| Group | Files | Risk | Recommendation |
|---|---|---|---|
| A | 5 | low, and four public addresses are dead until it lands | **sign first, today** |
| B | 9 | very low | sign with A |
| C | 2 | none | sign with A |
| D | 15 | low, 2 deletions are load-bearing corrections | sign after a landing-time grep |
| E | 2 | none | sign with A |
| F | 3, with 1 explicitly excluded | low | sign with A |
| G | 0 | none | nothing to sign |
| H | 7 call sites, no moves | low | agent work, no signature needed |

Nothing here is urgent except Group A, and Group A is urgent only because the
addresses are already published.
