# Handoff, 2026-08-09: landing the corrected governance lock

**Written by COUNSEL. The push was NOT performed. This document exists because
claiming otherwise would be the exact defect L-062 records.**

---

## 1. Why the agent did not push

Measured, from the analysis mount:

```
$ git add -A CLAUDE.md
fatal: Unable to create '.../qesis-mcp/.git/index.lock': File exists.

$ touch .git/_probe && rm -f .git/_probe
rm: cannot remove '.git/_probe': Operation not permitted
```

Two separate conditions, and only one of them is the one already on the register:

1. A **stale `.git/index.lock`** is present. No git process is running. This is a
   leftover, not contention.
2. The mount **cannot unlink files inside `.git`** at all, so the lock cannot be
   cleared from this side and no git write can complete.

`gh` is also not installed in this environment, so no pull request can be opened
from here either.

**This widens `LOCK-1`.** The register recorded a memory mapping on
`eval/evaluation.xml`. The condition is broader: the whole `.git` directory is
unlinkable from the analysis mount. Anyone who hits it will read `errno 22` or
`File exists` as git corruption or as a concurrent process, and will go looking
for a process that does not exist.

---

## 2. What is uncommitted, in both repositories

`qesis-mcp`

```
 M ops/LESSONS_LEDGER.md          converted to a pointer file, L-073
?? CLAUDE.md                      v2.0 session lock, corrected
?? ops/MILESTONE_v8.6.md          v2.0, two retractions
?? ops/V9.0_PATH_AND_ROUTING.md   v2.0, corrected v9.0 state and routing spec
?? ops/HANDOFF_2026-08-09_LAND_THE_LOCK.md   this file
```

`sovereign-infra`

```
 M ops/LESSONS_LEDGER.md          L-069 to L-079 appended, canonical
```

These are **one change set**, not two. `qesis-mcp/CLAUDE.md` cites L-076 through
L-079, which exist only in `sovereign-infra`. A partial landing leaves dangling
references, which is the condition G-05 clause 2 describes as a paired
remediation: both halves must land together and a partial landing would itself be
the defect.

---

## 3. The commands, in order, on the Windows host

Run these in **PowerShell on the host**, not from an analysis mount. Each block
names its repository explicitly, per L-065.

### 3.1 Clear the stale lock

```powershell
cd C:\Users\Lenovo\qesis-mcp
Get-Process git -ErrorAction SilentlyContinue      # expect: nothing
Remove-Item .git\index.lock -Force
git status
```

If `Remove-Item` refuses, a process holds a handle. Find it with
`handle64.exe .git\index.lock` or Resource Monitor, and close that process rather
than forcing anything.

### 3.2 `qesis-mcp`, branch and push

```powershell
cd C:\Users\Lenovo\qesis-mcp
git checkout -b docs/governance-lock-v2
git add CLAUDE.md ops\LESSONS_LEDGER.md ops\MILESTONE_v8.6.md `
        ops\V9.0_PATH_AND_ROUTING.md ops\HANDOFF_2026-08-09_LAND_THE_LOCK.md
git commit -m "docs: governance lock v2, six-agent registry restored, three findings retracted

Corrects a lock written from the served payload and the ledger without
opening GOVERNANCE.md, ARTICLE_14_REGISTER.md or agents/*.md.

- restores SENTINEL and HERALD to the closed six-agent registry
- returns the gate mandate to SENTINEL; COUNSEL is legal and commercial
- retracts PROV-1: plane 'working tree' is G-01b as specified (L-076)
- retracts PROBE-1: qesis-integrity.yml already runs verify_chain.py (L-077)
- retracts PAIR-1: verify_vintage_pairing.py PASSES on a declared exemption
- records L-076 to L-079 in sovereign-infra, paired with this change
- ops/LESSONS_LEDGER.md becomes a pointer; its orphan L-068 migrated to L-075
- em dashes removed per L-015

Refs L-073 L-076 L-077 L-078 L-079"
git push -u origin docs/governance-lock-v2
```

### 3.3 `sovereign-infra`, branch and push

```powershell
cd C:\Users\Lenovo\sovereign-infra
git checkout -b docs/lessons-l069-l079
git add ops\LESSONS_LEDGER.md
git commit -m "ops: register L-069 to L-079, including the retraction of L-071 and L-072

L-069 attestation is read back off disk, never from the writer's object
L-070 a script that has never executed has never been tested
L-071 RETRACTED by L-076
L-072 RETRACTED by L-077
L-073 the ledger is single instance; two files issued L-068
L-074 a status document names the vintage it describes, or is deleted
L-075 migrated from the duplicate ledger in qesis-mcp
L-076 find the clause before filing a served field as a defect
L-077 enumerate the control set before calling a property unverified
L-078 a governance lock is written from the governance documents
L-079 run the doctrine gate as the last act of writing

Pairs with qesis-mcp docs/governance-lock-v2."
git push -u origin docs/lessons-l069-l079
```

The `pre-push` hook permits both. It refuses `main`, `master` and `production`
only, and neither branch is one of those.

### 3.4 Pull requests

```powershell
cd C:\Users\Lenovo\qesis-mcp
gh pr create --base main --head docs/governance-lock-v2 `
  --title "docs: governance lock v2, registry restored, three findings retracted" `
  --body "Paired with sovereign-infra docs/lessons-l069-l079. See ops/HANDOFF_2026-08-09_LAND_THE_LOCK.md."

cd C:\Users\Lenovo\sovereign-infra
gh pr create --base main --head docs/lessons-l069-l079 `
  --title "ops: register L-069 to L-079" `
  --body "Paired with qesis-mcp docs/governance-lock-v2."
```

`gh` resolves the repository from the working directory. Running the second block
from the first directory is L-065 verbatim, and the error it produces names a real
branch on the wrong remote, which is indistinguishable from a genuine problem.

### 3.5 Merge

Under **G-06** an agent may merge a paired remediation pull request once its
checks pass, by rebase, because squash rewrites the hashes
`data/vintage_lineage.json` cites.

```powershell
gh pr merge --rebase <n>    # in each repository, after checks are green on both
```

I am not exercising that delegation in this change set, and the reason is not
procedural caution. This change set is the correction of an audit I performed
badly four hours ago. An agent merging its own retraction without a human reading
it is the arrangement that produced the error. Read it, then merge, or tell me to.

### 3.6 Deploy

**Not performed and not delegable.** G-06 limit 2: promotion to production is a
human act and no amendment reaches it. Nothing in this change set touches
`data/qesis_v8.json`, the server code or the served contract, so **no promotion is
required**. The served vintage stays v8.6 at `d78f39f7964e`. If you promote
anyway, `scripts/vercel_promote.py` closes the G-01b loop by comparing
`provenance.index_sha256` on the live endpoint against the promoted commit.

---

## 4. Verification after landing

```powershell
cd C:\Users\Lenovo\qesis-mcp
python scripts\verify_index.py
python scripts\verify_chain.py
python scripts\verify_vintage_pairing.py
python scripts\verify_axis_sfc.py
python -m qesis_agents run SENTINEL doctrine_audit --params '{}'   # in sovereign-infra
```

The last one is the control this change set failed on. Four documents shipped
with em dashes into a repository that bans them in code. They are clean now,
verified by scan, but the habit that matters is running the gate rather than
scanning by hand.
