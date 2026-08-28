# QESIS+ full ecosystem audit

Generated 2026-08-28T21:09:52Z by `scripts/audit_ecosystem.py`.
Every row carries the command that produced it, the exit code it returned, and
the predicate that decided its verdict. An exit code alone never decides a
measurement (D-116, V-5). Nothing here is asserted; V-1.

## Verdict: GREEN (6 informational)



| # | check | verdict | exit | basis |
|---|---|---|---|---|
| 1 | qesis-mcp: ledger mirror in sync | **PASS** | 0 | gate: exit code is the contract |
| 2 | qesis-mcp: ledger singleton | **PASS** | 0 | gate: exit code is the contract |
| 3 | qesis-mcp: ledger fixtures | **PASS** | 0 | gate: exit code is the contract |
| 4 | qesis-mcp: ecosystem bootstrap | **PASS** | 0 | gate: exit code is the contract |
| 5 | qesis-mcp: ecosystem fixtures | **PASS** | 0 | gate: exit code is the contract |
| 6 | qesis-mcp: RDL delta gate | **PASS** | 0 | gate: exit code is the contract |
| 7 | qesis-mcp: workflow contract | **PASS** | 0 | gate: exit code is the contract |
| 8 | qesis-mcp: self-heal fixtures | **PASS** | 0 | gate: exit code is the contract |
| 9 | qesis-mcp: lander contract | **PASS** | 0 | gate: exit code is the contract |
| 10 | qesis-mcp: landing base fixtures | **PASS** | 0 | gate: exit code is the contract |
| 11 | qesis-mcp: landing manifest fixtures | **PASS** | 0 | gate: exit code is the contract |
| 12 | qesis-mcp: preflight, CI's own steps | **PASS** | 0 | gate: exit code is the contract |
| 13 | qesis-mcp: self-heal loop, dry run (the `heal` check) | **PASS** | 0 | gate: exit code is the contract |
| 14 | sovereign-infra: ledger mirror in sync | **PASS** | 0 | gate: exit code is the contract |
| 15 | sovereign-infra: ledger singleton | **PASS** | 0 | gate: exit code is the contract |
| 16 | sovereign-infra: ledger fixtures | **PASS** | 0 | gate: exit code is the contract |
| 17 | sovereign-infra: ecosystem bootstrap | **PASS** | 0 | gate: exit code is the contract |
| 18 | sovereign-infra: ecosystem fixtures | **PASS** | 0 | gate: exit code is the contract |
| 19 | sovereign-infra: RDL delta gate | **PASS** | 0 | gate: exit code is the contract |
| 20 | sovereign-infra: workflow contract | **PASS** | 0 | gate: exit code is the contract |
| 21 | sovereign-infra: self-heal fixtures | **PASS** | 0 | gate: exit code is the contract |
| 22 | sovereign-infra: preflight, CI's own steps | **PASS** | 0 | gate: exit code is the contract |
| 23 | sovereign-infra: self-heal loop, dry run (the `heal` check) | **PASS** | 0 | gate: exit code is the contract |
| 24 | compliance chain | **PASS** | 0 | predicate: every prev_hash equals the previous entry_hash (0 breaks) |
| 25 | qesis-mcp: open pull requests | **INFO** | 0 | measurement: 1 open, none DIRTY. Open is unlanded work, not a defect; the lander merges or closes it |
| 26 | qesis-mcp: main | **INFO** | 0 | measurement: recorded for the deployment comparison |
| 27 | qesis-mcp: required and owned checks on main | **PASS** | 0 | measurement: all 1 required check(s) and every completed owned check on main are success; integrations the eco |
| 28 | qesis-mcp: open issues | **INFO** | 0 | measurement: 0 open issue(s), recorded |
| 29 | sovereign-infra: open pull requests | **INFO** | 0 | measurement: 1 open, none DIRTY. Open is unlanded work, not a defect; the lander merges or closes it |
| 30 | sovereign-infra: main | **INFO** | 0 | measurement: recorded for the deployment comparison |
| 31 | sovereign-infra: required and owned checks on main | **PASS** | 0 | measurement: ruleset unreadable; every ecosystem-owned check on main is success |
| 32 | sovereign-infra: open issues | **INFO** | 0 | measurement: 0 open issue(s), recorded |
| 33 | live /health | **PASS** | 0 | measurement: status ok, chain VERIFIED with 0 breaks, attestation agrees, and deployment_commit equals main |
| 34 | landing page HTTP | **PASS** | 0 | measurement: HTTP 200, predicate: 200 |

## Output of every check

### 1. qesis-mcp: ledger mirror in sync  (PASS, exit 0)

`python scripts/ledger_sync.py --check`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
LEDGER SYNC: 2 reachable cop(y/ies), repository qesis-mcp
  canonical    C:\Users\Lenovo\qesis-mcp\ops\LESSONS_LEDGER.md  entries 194 max L-211 sha256 e74ea87a5334
  canonical    C:\Users\Lenovo\OneDrive\sovereign-infra\ops\LESSONS_LEDGER.md  entries 194 max L-211 sha256 e74ea87a5334
LEDGER SYNC: every reachable copy is already canonical and identical. Zero is zero.
```

### 2. qesis-mcp: ledger singleton  (PASS, exit 0)

`python scripts/verify_ledger_singleton.py`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
ledger: C:\Users\Lenovo\qesis-mcp\ops\LESSONS_LEDGER.md  (repository: qesis-mcp)
  entries 194, unique 194, max L-211, sha256 e74ea87a5334ac73
  R1  no duplicate id
  R2  17 absent ids, all declared
  R3  sibling agrees (C:\Users\Lenovo\OneDrive\sovereign-infra\ops\LESSONS_LEDGER.md)
LEDGER SINGLETON CHECK PASSED
```

### 3. qesis-mcp: ledger fixtures  (PASS, exit 0)

`python scripts/verify_ledger_singleton.py --selftest`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
LEDGER SINGLETON SELFTEST: PASSED, 10 fixtures
```

### 4. qesis-mcp: ecosystem bootstrap  (PASS, exit 0)

`python scripts/build_ecosystem_state.py --check`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
ECOSYSTEM STATE CHECK PASSED
```

### 5. qesis-mcp: ecosystem fixtures  (PASS, exit 0)

`python scripts/build_ecosystem_state.py --selftest`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
ECOSYSTEM STATE SELFTEST: PASSED, 13 fixtures
```

### 6. qesis-mcp: RDL delta gate  (PASS, exit 0)

`python scripts/rdl.py ci-blocking`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
RDL: git_lock_family at rung 4 is accepted history (baseline rung 4), gate scripts/git_unlock.py landed. Not a regression.
RDL: guard_not_executed at rung 4 is accepted history (baseline rung 4). Not a regression.
RDL: success_literal_not_measured at rung 4 is accepted history (baseline rung 4). Not a regression.
RDL: claim_from_proxy_not_resource at rung 4 is accepted history (baseline rung 4). Not a regression.
RDL: paired_what_is_not_pairable at rung 3 is accepted history (baseline rung 3), gate scripts/verify_workflow_contract.py landed. Not a regression.
RDL: gate_cannot_be_satisfied at rung 3 is accepted history (baseline rung 3), gate scripts/build_ecosystem_state.py landed. Not a regression.
RDL DELTA GATE PASSED: 6 accepted, 0 regressions. The ladder introduces no new escalation in this change set.
```

### 7. qesis-mcp: workflow contract  (PASS, exit 0)

`python scripts/verify_workflow_contract.py`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
OK   workflow contract holds: 31 CI scripts, 19 local controls, 17 declared exemptions, tracked via git ls-files
```

### 8. qesis-mcp: self-heal fixtures  (PASS, exit 0)

`python scripts/selfheal.py --selftest`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
scope: 19 control(s) out of scope in this repository, script not present: verify_index, verify_chain, chain_diagnosis, verify_vintage_pairing, verify_axis_sfc, verify_action_pinning, verify_secrets, verify_workflow, kill_switch, build_graph_check, build_percolation_check, self_exposure_check, build_eval_check, build_landing_check, public_domain, ecosystem_state_check, runner_merge_selftest, reading_contract, test_gate
SELFHEAL SELFTEST: PASSED, 6 fixtures
```

### 9. qesis-mcp: lander contract  (PASS, exit 0)

`python scripts/verify_lander_contract.py`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
OK   lander contract holds for LAND_EVERYTHING_FINAL.ps1: no shell parsing, manifest-driven, selective restore, ASCII
```

### 10. qesis-mcp: landing base fixtures  (PASS, exit 0)

`python scripts/landing_base.py --selftest`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
PASS  landing base: normal: base is HEAD
  PASS  landing base: rebased: base is the pushed commit, by tree
  PASS  landing base: aborted run: base is HEAD~1
  PASS  landing base: push failed: base is HEAD~1
  PASS  landing base: fallback: merge-base, and it says so
landing base selftest: 5/5 fixtures hold
```

### 11. qesis-mcp: landing manifest fixtures  (PASS, exit 0)

`python scripts/landing_manifest.py --selftest`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
PASS  manifest: accepts a complete manifest
  PASS  manifest: refuses branch main
  PASS  manifest: refuses a missing repository title
  PASS  manifest: refuses an em dash and a banned word in prose
  PASS  manifest: refuses a non-object
landing manifest selftest: 5/5 fixtures hold
```

### 12. qesis-mcp: preflight, CI's own steps  (PASS, exit 0)

`python scripts/preflight.py`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
  PASS  Dashboard agrees with the served index
  PASS  Service identity is declared once
  PASS  Outbound endpoints are declared once
  PASS  Ecosystem state and path registry are not stale
  PASS  RDL ladder has no family at rung 3

PREFLIGHT PASSED: every step CI will run passes on this tree.
This is not a proxy for CI. It is CI's own step list, executed.
```

### 13. qesis-mcp: self-heal loop, dry run (the `heal` check)  (PASS, exit 0)

`python scripts/selfheal.py --dry-run`  in `C:\Users\Lenovo\qesis-mcp`

Basis: gate: exit code is the contract

```
  ok  ecosystem_state_check    PASS
  ok  runner_merge_selftest    PASS
  ok  reading_contract         PASS
  ok  test_gate                PASS

  verdict GREEN   repaired 0   degraded 0   escalations 0
  action gap: friction 0   time to action 0.0s over 0 repairs   unmodified execution n/a (no findings)
  promotion: PROCEED  (policy signed and predicate holds)
```

### 14. sovereign-infra: ledger mirror in sync  (PASS, exit 0)

`python scripts/ledger_sync.py --check`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
LEDGER SYNC: 2 reachable cop(y/ies), repository sovereign-infra
  canonical    C:\Users\Lenovo\OneDrive\sovereign-infra\ops\LESSONS_LEDGER.md  entries 194 max L-211 sha256 e74ea87a5334
  canonical    C:\Users\Lenovo\qesis-mcp\ops\LESSONS_LEDGER.md  entries 194 max L-211 sha256 e74ea87a5334
LEDGER SYNC: every reachable copy is already canonical and identical. Zero is zero.
```

### 15. sovereign-infra: ledger singleton  (PASS, exit 0)

`python scripts/verify_ledger_singleton.py`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
ledger: C:\Users\Lenovo\OneDrive\sovereign-infra\ops\LESSONS_LEDGER.md  (repository: sovereign-infra)
  entries 194, unique 194, max L-211, sha256 e74ea87a5334ac73
  R1  no duplicate id
  R2  17 absent ids, all declared
  R3  sibling agrees (C:\Users\Lenovo\qesis-mcp\ops\LESSONS_LEDGER.md)
LEDGER SINGLETON CHECK PASSED
```

### 16. sovereign-infra: ledger fixtures  (PASS, exit 0)

`python scripts/verify_ledger_singleton.py --selftest`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
LEDGER SINGLETON SELFTEST: PASSED, 10 fixtures
```

### 17. sovereign-infra: ecosystem bootstrap  (PASS, exit 0)

`python scripts/build_ecosystem_state.py --check`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
ECOSYSTEM STATE CHECK PASSED
```

### 18. sovereign-infra: ecosystem fixtures  (PASS, exit 0)

`python scripts/build_ecosystem_state.py --selftest`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
ECOSYSTEM STATE SELFTEST: PASSED, 13 fixtures
```

### 19. sovereign-infra: RDL delta gate  (PASS, exit 0)

`python scripts/rdl.py ci-blocking`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
RDL: git_lock_family at rung 4 is accepted history (baseline rung 4), gate scripts/git_unlock.py landed. Not a regression.
RDL: guard_not_executed at rung 4 is accepted history (baseline rung 4). Not a regression.
RDL: success_literal_not_measured at rung 4 is accepted history (baseline rung 4). Not a regression.
RDL: claim_from_proxy_not_resource at rung 4 is accepted history (baseline rung 4). Not a regression.
RDL: paired_what_is_not_pairable at rung 3 is accepted history (baseline rung 3), gate scripts/verify_workflow_contract.py landed. Not a regression.
RDL: gate_cannot_be_satisfied at rung 3 is accepted history (baseline rung 3), gate scripts/build_ecosystem_state.py landed. Not a regression.
RDL DELTA GATE PASSED: 6 accepted, 0 regressions. The ladder introduces no new escalation in this change set.
```

### 20. sovereign-infra: workflow contract  (PASS, exit 0)

`python scripts/verify_workflow_contract.py`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
OK   workflow contract holds: 13 CI scripts, 21 local controls, 17 declared exemptions, tracked via git ls-files
     scope: 10 control script(s) absent from this repository, out of scope here per selfheal.controls_present(): build_eval.py, build_graph.py, build_landing.py, build_percolation_block.py, self_exposure.py, test_gate.py, verify_axis_sfc.py, verify_index.py, verify_no_plaintext_secrets.py, verify_vintage_pairing.py
```

### 21. sovereign-infra: self-heal fixtures  (PASS, exit 0)

`python scripts/selfheal.py --selftest`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
scope: 22 control(s) out of scope in this repository, script not present: verify_index, verify_chain, verify_vintage_pairing, verify_axis_sfc, verify_action_pinning, verify_secrets, verify_workflow, doctrine_gate, doctrine_fixtures, kill_switch, build_graph_check, build_percolation_check, self_exposure_check, build_eval_check, build_landing_check, ecosystem_state_check, ecosystem_state_fixtures, rdl_allocator_fixtures, runner_merge_selftest, reading_contract, gcp_triggers, test_gate
SELFHEAL SELFTEST: PASSED, 6 fixtures
```

### 22. sovereign-infra: preflight, CI's own steps  (PASS, exit 0)

`python scripts/preflight.py`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
  PASS  Every third-party action is pinned to a full-length commit
  PASS  The runner merge decision refuses and accepts what it must
  PASS  The writing doctrine holds over every tracked document
  PASS  The doctrine gate refuses and accepts what it must
  PASS  Workflow contract holds for this repository's own script s

PREFLIGHT PASSED: every step CI will run passes on this tree.
This is not a proxy for CI. It is CI's own step list, executed.
```

### 23. sovereign-infra: self-heal loop, dry run (the `heal` check)  (PASS, exit 0)

`python scripts/selfheal.py --dry-run`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: gate: exit code is the contract

```
  ok  rdl_allocator_fixtures   PASS
  ok  runner_merge_selftest    PASS
  ok  reading_contract         PASS
  ok  gcp_triggers             PASS

  verdict GREEN   repaired 0   degraded 0   escalations 0
  action gap: friction 0   time to action 0.0s over 0 repairs   unmodified execution n/a (no findings)
  promotion: PROCEED  (policy signed and predicate holds)
```

### 24. compliance chain  (PASS, exit 0)

`sqlite recompute link by link`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

Basis: predicate: every prev_hash equals the previous entry_hash (0 breaks)

```
755 entries, max 2026-08-28T03:47:32Z
0 linkage breaks
1 Article 14 executions held
4 open tasks
```

### 25. qesis-mcp: open pull requests  (INFO, exit 0)

`gh pr list --repo rodrigoesl92-cloud/qesis-mcp --state open --limit 50 --json number,headRefName,mergeable,mergeStateStatus`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: 1 open, none DIRTY. Open is unlanded work, not a defect; the lander merges or closes it

```
PR 86 head ops/report-2026-08-28 MERGEABLE BLOCKED
```

### 26. qesis-mcp: main  (INFO, exit 0)

`gh api repos/rodrigoesl92-cloud/qesis-mcp/commits/main`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: recorded for the deployment comparison

```
main 17ce8ec2f4b6  feat(axes): the withheld water stress becomes computable, and its fals
```

### 27. qesis-mcp: required and owned checks on main  (PASS, exit 0)

`gh api repos/rodrigoesl92-cloud/qesis-mcp/commits/main/check-runs?per_page=100`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: all 1 required check(s) and every completed owned check on main are success; integrations the ecosystem does not own (e.g. Cloud Build) are informational

```
required by ruleset: qesis-integrity
REQUIRED qesis-integrity: success
owned by this repository's workflows: binding, guard, heal, probe, report
OWNED binding: success
OWNED guard: success
OWNED heal: success
OWNED probe: in_progress (not finished at read time; rerun the audit)
OWNED report: no run on this commit
informational cloudrun-qesis-mcp-git-europe-west1-rodrigoesl92-cloud-qesis: failure
informational rmgpgab-qesis-mcp-europe-west1-rodrigoesl92-cloud-qesis-mcp-: failure
```

### 28. qesis-mcp: open issues  (INFO, exit 0)

`gh issue list --repo rodrigoesl92-cloud/qesis-mcp --state open --json number,title`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: 0 open issue(s), recorded

```
0 open issues
```

### 29. sovereign-infra: open pull requests  (INFO, exit 0)

`gh pr list --repo rodrigoesl92-cloud/sovereign-infra --state open --limit 50 --json number,headRefName,mergeable,mergeStateStatus`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: 1 open, none DIRTY. Open is unlanded work, not a defect; the lander merges or closes it

```
PR 52 head ops/report-2026-08-28 MERGEABLE UNSTABLE
```

### 30. sovereign-infra: main  (INFO, exit 0)

`gh api repos/rodrigoesl92-cloud/sovereign-infra/commits/main`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: recorded for the deployment comparison

```
main 569155ae29be  feat(ops): the operator queue drops to two, and a rejection stops coun
```

### 31. sovereign-infra: required and owned checks on main  (PASS, exit 0)

`gh api repos/rodrigoesl92-cloud/sovereign-infra/commits/main/check-runs?per_page=100`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: ruleset unreadable; every ecosystem-owned check on main is success

```
required by ruleset unreadable: {"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","documentation_url":"https://docs.github.com/rest/repos/rules#get-rules-for-a-branch","status":"403"}gh: Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403): none readable
owned by this repository's workflows: claude, disconnect, guard, heal, promote, qesis-integrity, report, verify
OWNED claude: no run on this commit
OWNED disconnect: no run on this commit
OWNED guard: success
OWNED heal: no run on this commit
OWNED promote: no run on this commit
OWNED qesis-integrity: success
OWNED report: no run on this commit
OWNED verify: success
informational cloudrun-sovereign-infra-git-europe-west1-rodrigoesl92-cloud: failure
```

### 32. sovereign-infra: open issues  (INFO, exit 0)

`gh issue list --repo rodrigoesl92-cloud/sovereign-infra --state open --json number,title`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: 0 open issue(s), recorded

```
0 open issues
```

### 33. live /health  (PASS, exit 0)

`curl.exe -s --max-time 25 https://qesis-mcp.vercel.app/health`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: status ok, chain VERIFIED with 0 breaks, attestation agrees, and deployment_commit equals main

```
status ok  vintage v9.0 (2026-08-13)  chain VERIFIED 755 entries 0 breaks
deployment_commit 17ce8ec2f4b6  main 17ce8ec2f4b6
tools 8  database connected
```

### 34. landing page HTTP  (PASS, exit 0)

`curl.exe -s -o NUL -w %{http_code} --max-time 25 https://qesis-mcp.vercel.app/`  in `C:\Users\Lenovo\qesis-mcp`

Basis: measurement: HTTP 200, predicate: 200

```
HTTP 200
```

