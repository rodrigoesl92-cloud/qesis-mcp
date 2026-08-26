# QESIS+ full ecosystem audit

Generated 2026-08-24T19:07:46Z by `scripts/audit_ecosystem.py`.
Every row carries the command that produced it and the exit code it returned.
Nothing here is asserted; V-1.

## Verdict: NOT GREEN, 4 failing

| # | check | exit | command |
|---|---|---|---|
| 1 | qesis-mcp: ledger singleton | **1** | `python scripts/verify_ledger_singleton.py` |
| 2 | qesis-mcp: ledger fixtures | **0** | `python scripts/verify_ledger_singleton.py --selftest` |
| 3 | qesis-mcp: RDL delta gate | **0** | `python scripts/rdl.py ci-blocking` |
| 4 | qesis-mcp: ecosystem bootstrap | **0** | `python scripts/build_ecosystem_state.py --check` |
| 5 | qesis-mcp: preflight, CI's own steps | **1** | `python scripts/preflight.py` |
| 6 | sovereign-infra: ledger singleton | **0** | `python scripts/verify_ledger_singleton.py` |
| 7 | sovereign-infra: ledger fixtures | **0** | `python scripts/verify_ledger_singleton.py --selftest` |
| 8 | sovereign-infra: RDL delta gate | **0** | `python scripts/rdl.py ci-blocking` |
| 9 | sovereign-infra: ecosystem bootstrap | **1** | `python scripts/build_ecosystem_state.py --check` |
| 10 | sovereign-infra: preflight, CI's own steps | **1** | `python scripts/preflight.py` |
| 11 | compliance chain | **0** | `sqlite recompute link by link` |
| 12 | qesis-mcp: open pull requests | **0** | `gh pr list --repo rodrigoesl92-cloud/qesis-mcp --state open --json num` |
| 13 | qesis-mcp: main check conclusions | **0** | `gh api repos/rodrigoesl92-cloud/qesis-mcp/commits/main/check-runs --jq` |
| 14 | qesis-mcp: open issues | **0** | `gh issue list --repo rodrigoesl92-cloud/qesis-mcp --state open --json ` |
| 15 | sovereign-infra: open pull requests | **0** | `gh pr list --repo rodrigoesl92-cloud/sovereign-infra --state open --js` |
| 16 | sovereign-infra: main check conclusions | **0** | `gh api repos/rodrigoesl92-cloud/sovereign-infra/commits/main/check-run` |
| 17 | sovereign-infra: open issues | **0** | `gh issue list --repo rodrigoesl92-cloud/sovereign-infra --state open -` |
| 18 | live /health | **0** | `curl.exe -s --max-time 25 https://qesis-mcp.vercel.app/health` |
| 19 | landing page HTTP | **0** | `curl.exe -s -o NUL -w %{http_code} --max-time 25 https://qesis-mcp.ver` |

## Output of every check

### 1. qesis-mcp: ledger singleton  (exit 1)

`python scripts/verify_ledger_singleton.py`  in `C:\Users\Lenovo\qesis-mcp`

```
ledger: C:\Users\Lenovo\qesis-mcp\ops\LESSONS_LEDGER.md
  entries 148, unique 148, max L-165, sha256 5d344926e764c250
  R1  no duplicate id
  R2  17 absent ids, all declared
  R3  sibling disagrees: C:\Users\Lenovo\OneDrive\sovereign-infra\ops\LESSONS_LEDGER.md hashes 5323cb3f964a, this copy 5d344926e764. The ledger is not a singleton.
LEDGER SINGLETON CHECK FAILED
```

### 2. qesis-mcp: ledger fixtures  (exit 0)

`python scripts/verify_ledger_singleton.py --selftest`  in `C:\Users\Lenovo\qesis-mcp`

```
LEDGER SINGLETON SELFTEST: PASSED, 5 fixtures
```

### 3. qesis-mcp: RDL delta gate  (exit 0)

`python scripts/rdl.py ci-blocking`  in `C:\Users\Lenovo\qesis-mcp`

```
RDL: git_lock_family at rung 4 is accepted history (baseline rung 4), gate scripts/git_unlock.py landed. Not a regression.
RDL: guard_not_executed at rung 4 is accepted history (baseline rung 4), gate scripts/git_unlock.py landed. Not a regression.
RDL: success_literal_not_measured at rung 3 is accepted history (baseline rung 3), gate scripts/build_ops_report.py landed. Not a regression.
RDL: claim_from_proxy_not_resource at rung 4 is accepted history (baseline rung 4), gate scripts/ci_feedback.py landed. Not a regression.
RDL DELTA GATE PASSED: 4 accepted, 0 regressions. The ladder introduces no new escalation in this change set.
```

### 4. qesis-mcp: ecosystem bootstrap  (exit 0)

`python scripts/build_ecosystem_state.py --check`  in `C:\Users\Lenovo\qesis-mcp`

```
ECOSYSTEM STATE CHECK PASSED
```

### 5. qesis-mcp: preflight, CI's own steps  (exit 1)

`python scripts/preflight.py`  in `C:\Users\Lenovo\qesis-mcp`

```
        
        65/66 gate behaviours verified
        GATE IS NOT TRUSTWORTHY: it missed a defect it must catch.

PREFLIGHT FAILED. This step will fail the required status check, so the pull request could not merge.
Nothing has been pushed. Fix this, then run again.
```

### 6. sovereign-infra: ledger singleton  (exit 0)

`python scripts/verify_ledger_singleton.py`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

```
ledger: C:\Users\Lenovo\OneDrive\sovereign-infra\ops\LESSONS_LEDGER.md
  entries 148, unique 148, max L-165, sha256 5323cb3f964ab0a8
  R1  no duplicate id
  R2  17 absent ids, all declared
  R3  sibling agrees (C:\Users\Lenovo\OneDrive\sovereign-infra\ops\LESSONS_LEDGER.md)
LEDGER SINGLETON CHECK PASSED
```

### 7. sovereign-infra: ledger fixtures  (exit 0)

`python scripts/verify_ledger_singleton.py --selftest`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

```
LEDGER SINGLETON SELFTEST: PASSED, 5 fixtures
```

### 8. sovereign-infra: RDL delta gate  (exit 0)

`python scripts/rdl.py ci-blocking`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

```
RDL: git_lock_family at rung 4 is accepted history (baseline rung 4), gate scripts/git_unlock.py landed. Not a regression.
RDL: guard_not_executed at rung 4 is accepted history (baseline rung 4), gate scripts/git_unlock.py landed. Not a regression.
RDL: success_literal_not_measured at rung 3 is accepted history (baseline rung 3), gate scripts/build_ops_report.py landed. Not a regression.
RDL: claim_from_proxy_not_resource at rung 4 is accepted history (baseline rung 4), gate scripts/ci_feedback.py landed. Not a regression.
RDL DELTA GATE PASSED: 4 accepted, 0 regressions. The ladder introduces no new escalation in this change set.
```

### 9. sovereign-infra: ecosystem bootstrap  (exit 1)

`python scripts/build_ecosystem_state.py --check`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

```
STALE  ECOSYSTEM_STATE.json disagrees with a fresh measurement
ECOSYSTEM STATE CHECK FAILED
  Regenerate with: python scripts/build_ecosystem_state.py
```

### 10. sovereign-infra: preflight, CI's own steps  (exit 1)

`python scripts/preflight.py`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

```
        STALE  ECOSYSTEM_STATE.json disagrees with a fresh measurement
        ECOSYSTEM STATE CHECK FAILED
          Regenerate with: python scripts/build_ecosystem_state.py

PREFLIGHT FAILED. This step will fail the required status check, so the pull request could not merge.
Nothing has been pushed. Fix this, then run again.
```

### 11. compliance chain  (exit 0)

`sqlite recompute link by link`  in `C:\Users\Lenovo\OneDrive\sovereign-infra`

```
754 entries, max 2026-08-13T08:55:59Z
0 linkage breaks
1 Article 14 executions held
13 open tasks
```

### 12. qesis-mcp: open pull requests  (exit 0)

`gh pr list --repo rodrigoesl92-cloud/qesis-mcp --state open --json number,headRefName,mergeable,mergeStateStatus`  in `C:\Users\Lenovo\qesis-mcp`

```
PR 76 head fix/land-20260824-consolidated MERGEABLE BLOCKED
PR 71 head feat/land-20260824-r2 CONFLICTING DIRTY
```

### 13. qesis-mcp: main check conclusions  (exit 0)

`gh api repos/rodrigoesl92-cloud/qesis-mcp/commits/main/check-runs --jq .check_runs[] | .name + ": " + (.conclusion // "pending")`  in `C:\Users\Lenovo\qesis-mcp`

```
rmgpgab-qesis-mcp-europe-west1-rodrigoesl92-cloud-qesis-mcp-ltg (project-5c4e8a9a-723a-453e-80d): failure
guard: success
heal: success
probe: success
qesis-integrity: success
cloudrun-qesis-mcp-git-europe-west1-rodrigoesl92-cloud-qesisflp (project-5c4e8a9a-723a-453e-80d): failure
```

### 14. qesis-mcp: open issues  (exit 0)

`gh issue list --repo rodrigoesl92-cloud/qesis-mcp --state open --json number`  in `C:\Users\Lenovo\qesis-mcp`

```
[{"number":74}]
```

### 15. sovereign-infra: open pull requests  (exit 0)

`gh pr list --repo rodrigoesl92-cloud/sovereign-infra --state open --json number,headRefName,mergeable,mergeStateStatus`  in `C:\Users\Lenovo\qesis-mcp`

```
0 open pull requests
```

### 16. sovereign-infra: main check conclusions  (exit 0)

`gh api repos/rodrigoesl92-cloud/sovereign-infra/commits/main/check-runs --jq .check_runs[] | .name + ": " + (.conclusion // "pending")`  in `C:\Users\Lenovo\qesis-mcp`

```
heal: failure
cloudrun-sovereign-infra-git-europe-west1-rodrigoesl92-cloudtyt (project-5c4e8a9a-723a-453e-80d): failure
qesis-integrity: failure
heal: failure
guard: success
verify: success
```

### 17. sovereign-infra: open issues  (exit 0)

`gh issue list --repo rodrigoesl92-cloud/sovereign-infra --state open --json number`  in `C:\Users\Lenovo\qesis-mcp`

```
[]
```

### 18. live /health  (exit 0)

`curl.exe -s --max-time 25 https://qesis-mcp.vercel.app/health`  in `C:\Users\Lenovo\qesis-mcp`

```
{"status":"ok","service":"qesis-mcp","mcp_endpoint":"/mcp","transport":"streamable-http","vintage":"v9.0 (2026-08-13)","index_sha256":"8009815e4c19132048bf285cf6622cc864e7bc090fc31627b09ce0145463647d","chain":{"status":"VERIFIED","entries":752,"link_breaks":0,"head_sha256":"af96057d43c1c2db2f6c91b01a61eb924f4f8b586c13dc0b8a7529ea27328f2c","attestation_agrees":true},"tools":["qesis_compare_countries","qesis_get_component_audit","qesis_get_country","qesis_get_coupling","qesis_get_integrity","qesis_get_methodology","qesis_get_pathways","qesis_rank_countries"],"tool_count":8,"licensed":false,"deployment_commit":"8775fc52c7e8d9bd792f7c8e698f5b820059dd53","database":"connected","verify":"git checkout <deployment_commit> && sha256sum data/qesis_v8.json must equal index_sha256; python scripts/verify_chain.py must exit 0"}
```

### 19. landing page HTTP  (exit 0)

`curl.exe -s -o NUL -w %{http_code} --max-time 25 https://qesis-mcp.vercel.app/`  in `C:\Users\Lenovo\qesis-mcp`

```
200
```

## What is failing

- **qesis-mcp: ledger singleton** exit 1: LEDGER SINGLETON CHECK FAILED
- **qesis-mcp: preflight, CI's own steps** exit 1: Nothing has been pushed. Fix this, then run again.
- **sovereign-infra: ecosystem bootstrap** exit 1:   Regenerate with: python scripts/build_ecosystem_state.py
- **sovereign-infra: preflight, CI's own steps** exit 1: Nothing has been pushed. Fix this, then run again.

