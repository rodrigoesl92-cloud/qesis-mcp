# ARCHITECT session report: filesystem standard and locator

**2026-08-28 · qesis-mcp · scheduled task `ops-filesystem-reorganisation`, mandate ratified 2026-08-14.**
**SENTINEL gating, COUNSEL reviewing. Operator: R. Batista Silva.**

**Why this file is not `ops/reports/2026-08-28.md`.** That path is the runner's
output namespace, written by `scripts/build_ops_report.py` under
`daily-ops-report.yml` at 06:20 daily. A hand-authored document there would be
overwritten by the next cron and, until it was, would present authored content
as measured. Rule FS-6 of the standard this session wrote. The mandate asked for
`ops/reports/2026-08-15.md`; the date is thirteen days stale and the namespace
is generated, so both were corrected and the correction is stated rather than
made silently.

---

## 1. What ran

Read first, on the operator's mid-session instruction, before any deliverable:

| Read | Result |
|---|---|
| `ops/AUDIT_REPORT.md`, generated 2026-08-28T04:11:59Z natively | **Verdict GREEN.** 34 checks, 4 informational, 0 failures, across both repositories |
| `ops/SELFHEAL_LATEST.json`, 2026-08-28T18:06:09Z | 20 controls, all PASS. Verdict DEGRADED, sole degradation `git_write_capability`, class B, declared |
| `ops/reports/2026-08-27.md` | runner narrative, one repository, no action required |
| `ops/CI_LAST_FAILURE.md` | last real failure 2026-08-24, root-caused as L-170, closed |
| `ops/PATH_REGISTRY.json`, `ops/ECOSYSTEM_STATE.json`, generated 03:57Z | current, not stale |
| `SESSION_START.md`, `CLAUDE.md`, `ops/SOURCE_ACQUISITION_REGISTER.md`, `ops/LESSONS_LEDGER.md` | read |

Ecosystem standing, from the audit rather than from inference:

- `main` in qesis-mcp is **b0450fb7bf0b**, "fix(ops): pair the ledger with the doctrine gate lesson".
- Live `/health`: vintage v9.0 (2026-08-13), chain VERIFIED, 754 entries, 0 breaks, `deployment_commit` **equals** main. Main is the deployment.
- Required check `qesis-integrity` success; owned checks binding, guard, heal, probe all success.
- 0 open pull requests and 0 open issues in both repositories.
- Ledger: 185 entries, 185 unique, max **L-202**, sha256 `0b4ca2d6c30b`, byte-identical across both repositories.

Gates run by this session, each with the command that produced the value (V-1):

| Command | Result |
|---|---|
| `python scripts/verify_ledger_singleton.py --json` | entries 185, unique 185, max 202, PASS |
| `python scripts/build_data_map.py --selftest` | `16/16 data-map behaviours hold` |
| `python scripts/build_data_map.py` | 265 files indexed, 14 of 17 critical located, 2 of 3 roots reachable |
| `python scripts/build_data_map.py --check` | PASS, twice, proving idempotence |
| `python scripts/verify_static_routes.py --selftest` | `6/6 static-route behaviours hold` |
| `python scripts/verify_static_routes.py --live` | **FAILED, 8 dead declarations, 8 live 404s, prediction matches the origin item for item** |

Not run, deliberately: `scripts/test_gate.py` and `scripts/preflight.py`. L-200
prohibits both from this shell, because they mutate the index to prove the gate
can fail and a shell whose calls die at 45 seconds cannot guarantee the restore.
The lander runs them natively at step 1.

---

## 2. What changed

### Assets created

| Path | Kind | What it does |
|---|---|---|
| `ops/FILESYSTEM_STANDARD.md` | governed, hand maintained | fifteen rules FS-0 to FS-15: retrieval order, the three roots, generated versus hand maintained, ops naming, the `lineage.sources` reachability rule, and that a move is an Article 14 act |
| `scripts/build_data_map.py` | generator | the locator the map has named since 2026-08-14 and never had. 16 fixtures, `--check`, `--selftest` |
| `scripts/verify_static_routes.py` | gate, not yet armed | asserts every static route resolves to a file the platform serves. 6 fixtures, `--live` origin probe |
| `ops/FILESYSTEM_REORG_PLAN_2026-08-28.md` | proposal | 36 files across 8 groups, each with source, destination, reason and what breaks. Nothing executed |
| `ops/reports/ARCHITECT_FILESYSTEM_2026-08-28.md` | this file | |

### Assets regenerated

| Path | Before | After |
|---|---|---|
| `data/DATA_MAP.json` | 99005 bytes, generated 2026-08-14, generator absent, roots recorded as one sandbox session's mount, 6 of 15 critical entries drifted | 36207 bytes, generated and gated, logical roots only, content compared by SHA-256 and never by mtime |

### Decisions taken, and they are ARCHITECT's under SH-10b

1. **The report goes to a non-generated path.** FS-6. Stated above.
2. **`verify_static_routes.py` is not wired into `qesis-integrity.yml` in this change set.** Arming it would turn the required check red on `main` every run until four pages are decided. SH-10f: a gate no correct action can satisfy is a deadlock wearing the costume of a control.
3. **Fixtures ship inside the new scripts under `--selftest`, not by editing `scripts/test_gate.py`.** Editing the file the required gate runs, from a shell forbidden to run it, is how a green tree goes red for a reason nobody can reproduce. The `--selftest` form matches `verify_public_domain.py` and is parsed as a proportion by `test_gate.all_declared_hold` under D-119, so it does not carry the literal-count trap of L-201.
4. **The DM-3 gate gained a carve-out on its first live run and became stricter, not weaker.** It fired on the declared decoy paths carried from `PATH_REGISTRY.json`. Declared decoys are now stripped before the scan and the rule became: the only absolute paths permitted in the document are exactly the ones the registry declares as traps. Two fixtures added for the carve-out.
5. **The map does not renumber, delete or move anything.** Rule FS-14.

### Counter-arguments to this session's own work, stated before they are asked for

- The reachability gate DM-1 and DM-2 would have caught nothing today, because both cited sources reproduce. That is the point and it is also the weakness: a control validated only against a passing case has been exercised, not tested. Its refuse fixtures are therefore synthetic, and the first real drift will be its first real trial.
- `verify_static_routes.py` asserts a correspondence between a config file and a directory listing, and then cross-checks it against the origin. The local half can pass while the platform's own resolution order changes underneath it. The `--live` mode exists for that reason and it is the half that should be trusted.
- Roughly ninety `ROOT / "data" / "x.json"` expressions in `scripts/` are repository-relative and correct. They are not listed as defects and rewriting them to route through the map would add a dependency and a failure mode to code that has neither.

---

## 3. Staleness flags

| Flag | Measurement | Verdict |
|---|---|---|
| `data/DATA_MAP.json` | 14 days old, generator absent, 6 of 15 critical hashes drifted | **repaired this session** |
| Four public addresses | `/overview`, `/method`, `/console`, `/dashboard` return 404 at the origin | **open, Group A of the plan, operator signature under FS-14** |
| `ops/D-103_STATUS.md` | dated 2026-08-05, describes a release that had not happened; v8.6 superseded it | open, already carried as `DOC-1` in `CLAUDE.md` section 7. Not reopened |
| This checkout versus `main` | `scripts/doctrine_gate.py`, `ops/D-119_SUBSUITE_RESULT_CONTRACT.md`, `ops/GCP_FOOTPRINT.json`, `ops/POSTGRES_RUNBOOK.md` and `scripts/gcp_triggers.py` are named as shipped remedies by L-194 to L-202 and are not present as this session reads the tree, while `main` already carries their commit | **unsettled, and NOT reported as a defect.** Either the mount is a stale snapshot or the checkout is behind. Settled by one native double-click of `AUDIT_ECOSYSTEM.bat`, which measures and changes nothing. No agent runs git from this mount, L-122, L-123, L-150 |
| `ops/reports/` in qesis-mcp | holds `2026-08-27.md` only; no report for 2026-08-28 in this checkout | same cause as the row above, same settling command. Not reported as a missed cron |

**Residue this session left, declared rather than hidden.** A write probe created
`ops/.arch_writetest.2`, three bytes. The analysis mount can create and cannot
unlink, so it could not be removed from here. It is a dotfile, so
`build_data_map.py` skips it and it does not enter the index. It is deleted by
the lander or by hand. This is the same class as the fifteen stray probes
`selfheal.py` already declares.

---

## 4. Open gaps

**Named so their absence is visible rather than silent. None is imputed.**

1. **`sovereign-infra` was not assessed.** `C:\Users\Lenovo\OneDrive\sovereign-infra` is not connected to this session. `C:\Users\Lenovo\sovereign-infra` is the declared decoy and holds one directory, which `build_data_map.py` now correctly refuses to resolve as a root. The mandate's deliverable 4 asked for a grep of **both** repositories; **half of it is not done** and saying so is the whole point of this section. It needs a session with the OneDrive folder connected, or a native run.
2. **G-01 pairing is not satisfied by this change set.** Everything written here landed in `qesis-mcp` alone. Under Rule 2-1 that is recorded with its reason rather than left silent: the paired repository was unreachable. `ops/FILESYSTEM_STANDARD.md` and `data/DATA_MAP.json` both describe the sovereign-infra plane, so the mirror is owed.
3. **The static-route gate is not armed.** By design, and it stays unarmed until Group A is signed. Until then the four addresses stay dead and the only thing standing between them and silence is this report.
4. **Three of seventeen critical sources were not located**, being `GOVERNANCE.md`, `ARTICLE_14_REGISTER.md` and `tokens.css`. All three live in the unreachable root. The map records `unreachable_root`, not `not_found`. Withheld with cause, never imputed. D-007.

### Hardcoded path grep, qesis-mcp only

The mandate's deliverable 4. Full table in Group H of the plan. The finding in one line:

**One file carries the exact defect the mandate describes.**
`scripts/compute_odi_bounds.py` lines 54 to 56 resolve `cloud_regions_master.csv`
through two literals, and the second is
`/sessions/trusting-brave-fermat/mnt/Final Master Thesis/...`, a sandbox root
belonging to one session that ended a fortnight ago. It is dead by construction
in every subsequent session, which is the same defect the old `DATA_MAP.json`
carried in its `roots` block, in a second file, unnoticed.

Six further files hold `C:\Users\Lenovo\OneDrive\sovereign-infra` as a literal:
`audit_ecosystem.py:52`, `apply_operator_decisions.py:37`, `gh_ops.py:97`,
`rdl.py:65`, `verify_ledger_singleton.py:59`, `verify_lander_contract.py:53`.
Each duplicates a declaration that `ops/PATH_REGISTRY.json` already owns.

**`scripts/build_ecosystem_state.py` lines 52, 65 and 70 are excluded and must
keep their literals.** It writes `PATH_REGISTRY.json`, so it is the declaring
authority, and a bootstrap cannot read the file it is about to write. Reporting
it as a defect would be reporting the operator's correct work as broken, which
is the most expensive error available here.

---

## 5. Lessons added

Reserved in `ops/RDL_PENDING_APPEND.md`, allocated from
`verify_ledger_singleton.py --json` plus the pending reservations, never from
the tail of the ledger. L-151, L-156.

| Id | Family | Occurrence, rung | Action taken |
|---|---|---|---|
| **L-203** | `surface_added_without_its_control` | 2, rung 2 | gate wired: `verify_static_routes.py`, 6 fixtures, refuse fixture is the live defect exactly as it stands |
| **L-204** | `generated_artefact_without_a_live_generator` | 1, rung 1 | recorded, and the generator built in the same session |

**Concurrency note, and it is not a defect of either session.** A different
session appended **L-205** to the same pending file while this one was writing.
Its text refers to recording an L-203 for family
`claim_from_proxy_not_resource`, which is not the family of the L-203 above.
Either that session recorded its own L-203 into a store this session cannot
read, in which case 203 and 204 collide, or the reference is to its earlier work
and the numbering is consistent. **This session did not renumber on a guess**,
because renumbering upward manufactures gaps that R2 of the singleton gate then
fails on unless declared, trading a detectable problem for a silent one. The
collision cannot reach `main`: R1 of `verify_ledger_singleton.py` fails the
build on a duplicate id and the lander runs it before touching git. A comment
block at the head of the pending file records this with the settling command.

L-205 itself is read and applied in this report: every operator-facing item
below names the SH-4 clause that makes it his, and no technical question is
handed to him.

---

## 6. Next three actions, ranked

**1. Sign Group A of the reorganisation plan. THE OPERATOR'S, and the clause is named.**
Four published addresses return 404. The remedy is a file move, and a file move
is an Article 14 act under FS-14 and under the mandate's own words. That is one
of the exactly three SH-4 classes and it is why this reaches him.
COUNSEL's recommendation, named as such: **option A, move the four pages into
`public/`.** The pages exist, are substantial, and the addresses are already
published; retiring a surface is a product decision, restoring a declared one is
a repair. If he prefers option B, the eight route entries leave `vercel.json`
instead and the gate passes either way, because it asserts a correspondence and
not a page count. The moment he signs, ARCHITECT lands one change set: the four
moves, the stale root `index.html` deletion, the gate wired into
`qesis-integrity.yml`, and `verify_static_routes.py --live` as the after check.

**2. Mirror this change set into `sovereign-infra` and finish the grep. ARCHITECT'S.**
Routed by the SH-10b table: pipeline, build and repository-structure work is
ARCHITECT's and is never shown to the operator. It needs the OneDrive folder
connected to a session, or a native run. Until it lands, G-01 Rule 2-1 is
satisfied by the stated reason in gap 2 above and not by silence.

**3. Wire `build_data_map.py --check` into `qesis-integrity.yml`. ARCHITECT'S.**
Safe to arm immediately and independently of Group A: it passes on this tree
today, twice, and its volatile-path exclusions mean an hourly cron cannot make
it fail. It lands with action 2 so the pairing is one change set rather than
two.

---

_Nothing in this session moved, deleted or renamed a file. Two scripts, two
documents and one regenerated artefact were written, and every claim above
carries the command that produced it._
