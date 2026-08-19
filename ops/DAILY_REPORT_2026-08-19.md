# Daily report, 2026-08-19

**COUNSEL, under SH-9. One page. Every claim carries the command that produced it.**

---

## 1. What ran

| Control | Result |
|---|---|
| `verify_workflow_contract` | OK. 25 CI scripts, 14 local controls, 13 exemptions, tracked via `git ls-files` |
| `selfheal --dry-run` | verdict DEGRADED, repaired 0, **escalations 0**, promotion PROCEED |
| `test_gate` | 54/54 with the runtime installed. 51/52 without, the single skip being build idempotence |
| `ci_local` | 25 steps, every runnable step passed |
| `kill_switch` | clear on both channels; engaged via environment halts the loop, verified |
| Production `/health` | v9.0, chain VERIFIED 752, 0 link breaks, attestation agrees, database connected |

The one degradation is `host_only_git`: this mount cannot unlink inside `.git`,
so the loop writes repairs to the working tree and does not commit them. It does
not exist on a runner.

---

## 2. What was repaired, and none of it needed a decision

**The root cause of the month.** `.gitignore` line 79 carries `*SECRET*`,
correctly, to keep credentials out of the repository. It also matched
`scripts/verify_no_plaintext_secrets.py`, which is the **gate**, not a secret.
`git add -A` skipped it in silence, `git status --short` hides ignored files, the
commit shipped without it, and CI died in thirteen seconds running a step whose
script was not in the checkout. **The secrets gate was excluded by the secrets
ignore rule.**

Three CI failures in a week and three structural fixes that never touched the
failing step, because local gates read the working tree and CI reads the commit,
and nothing asserted those are different questions.

Closed by `183dde1`, merged in #65. Issues **#66 and #67 closed** with the
mechanical explanation for each: `check_secrets` calls `SECRETS_GATE.exists()`,
and C-2 asserted the same missing file, so two controls failed on one absence.

**Also landed:** the Article 14 Decision 5 kill switch as a working lever rather
than a signature, the D-2 secrets gate, the signed promotion policy, D-113
closing L-045 with the instrument scored on its own axes at ODI 50.0, FPE 100.0,
RGD 50.0 and composite WITHHELD at coverage 0.25.

---

## 3. Production is current. Verified, after one false alarm.

```
GET /health?cachebust=...
deployment_commit: c5f0fc676020588ce57bf5b6fc73eb44dae413db
vintage:           v9.0 (2026-08-13)
index_sha256:      8009815e4c19132048bf285cf6622cc864e7bc090fc31627b09ce0145463647d
chain:             VERIFIED, 752 entries, 0 link breaks, attestation agrees
database:          connected
```

`c5f0fc6` is the Production deployment on branch `main`, Ready, and it is the
newest build in the Vercel dashboard. `verify_production.py` asserts
`deployment_commit == github.sha`, so the scheduled probe against `main` now
passes. **The nine-hour hourly failure is closed at its cause**, which was
`vercel_gate.py` gating artefact quality without gating which branch was
promoting.

**A false alarm was raised in the first draft of this report and is recorded
rather than deleted.** It claimed production served `f14385b` and predicted
hourly probe failures. The `/health` read had been deduplicated by the fetch
tool, which returned a response cached twenty-five minutes earlier together with
a notice saying so, and the notice was not read. The operator's Vercel screenshot
corrected it. Registered as **L-140**: a freshness-sensitive read carries a
cache-buster, and a response announcing itself as cached is a stale value, never
a measurement. Manufacturing an open item is the same failure as suppressing one,
and it is worse inside a report, because the report is what the next session
reads as fact.

## 4. Open gaps

| Id | Item | Owner |
|---|---|---|
| `ACT-5` | `FSQCA_ED25519_PRIV_B64` still in plaintext `.env`. The gate proves it stays untracked; it cannot move a key | HUMAN |
| `ACT-6` | Confirm the OneDrive mirror is read-only export, not the writable evidence plane | HUMAN |
| `ACT-4` | Second custody for the chain spine and release attestations. The only limb of D-113 that changes a physical fact | HUMAN approves |
| `D-104` | Thesis 27% and 36% have no published method. Highest severity in the register | HUMAN, SSRN |
| `PUB-1` | Percolation published; the EMODnet non-reproducibility finding is still evidence-plane only | ANALYST, then SENTINEL |

---

## 5. Lessons

**L-131 to L-141.** Eleven, and ten of them are mine.

The one that matters: **L-139.** Four consecutive deliveries failed on the
operator's Windows machine and none failed on the Linux box they were authored
on. `bash -lc` through WSL with no `python`. `rglob` on a path only the mount
has. Two more copies of that walker. A regex whose string replacement parsed
`C:\Users\...` as a template and died on `\U`. An agent that cannot execute in
the operator's environment does not hand the operator code to run.
`ops/LAND.md` is now three git commands.

**L-136** is the expensive one: three structural fixes built from reconstructions
of a log never read. The thirteen-second runtime excluded every one of those
hypotheses before they were written.

---

## 6. Next three, ranked

1. **Nothing.** Production is bound to `main` at `c5f0fc6`, the chain reproduces,
   the loop runs hourly in Actions and the scheduled sweep needs no machine of
   yours. The correct action tomorrow morning is to read the self-heal step
   summary and do nothing if it is green.
2. **Create the repository variable `QESIS_KILL_SWITCH = 0`.** Absent reads as
   clear, so this changes nothing today. It means the field exists before you
   need it rather than being created under pressure.
3. **`ACT-5`, move the signing key.** It is the only open item that is a security
   finding rather than a governance one, and it would be true on any cloud.

**Standing, before every push:** `python scripts\ci_local.py`. It runs the real
workflow steps in declared order. Green means CI is green, because it is the same
list executed rather than the same list compared.
