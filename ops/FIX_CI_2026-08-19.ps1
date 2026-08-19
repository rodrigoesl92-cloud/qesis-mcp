# FIX_CI_2026-08-19.ps1
#
# Closes the "green locally, red in CI" class after its third occurrence in one
# week, and lands it on the open PR #65 branch.
#
# THE INSTANCE was .github/workflows/selfheal.yml declaring `contents: read`
# with a step nine lines below running `git push` and `gh pr create`. GitHub
# reports that as a runtime 403 in a log nobody opens.
#
# THE CLASS is that the local control set and the CI step list were two
# independent lists and nothing asserted they should agree, so any drift between
# them was discoverable only by a red check. Fixed three times individually,
# which is why it happened three times.
#
# scripts/verify_workflow_contract.py now asserts:
#   C-1 every mutating step declares the permission it needs
#   C-2 every referenced script exists at this commit
#   C-3 every verification script CI runs is in the local control set, or is
#       declared EXEMPT with a stated reason. Silence is not an exemption.
#
# It runs in CI, in the self-heal loop, and it owns two fixtures. The refuse
# fixture is today's failure itself.

$ErrorActionPreference = 'Stop'
Set-Location C:\Users\Lenovo\qesis-mcp

if (Get-Process git -ErrorAction SilentlyContinue) {
    Write-Host "ABORT: a git process is running." -ForegroundColor Red; exit 1
}
if (Test-Path .git\index.lock) {
    $l = Get-Item .git\index.lock
    if ($l.Length -eq 0) { Remove-Item .git\index.lock -Force; Write-Host "cleared abandoned lock" -ForegroundColor Yellow }
    else { Write-Host "ABORT: index.lock is $($l.Length) bytes." -ForegroundColor Red; exit 1 }
}

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -ne 'feat/d113-selfheal-autonomy') {
    Write-Host "ABORT: expected feat/d113-selfheal-autonomy, on '$branch'." -ForegroundColor Red
    exit 1
}

# ── 1. The new gate first. If it fails, nothing else matters. ──────────────
Write-Host "`n=== workflow contract ===" -ForegroundColor Cyan
python scripts\verify_workflow_contract.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ABORT: the workflow contract does not hold. Read the findings." -ForegroundColor Red
    exit 1
}

# ── 2. Full control set ────────────────────────────────────────────────────
Write-Host "`n=== control set ===" -ForegroundColor Cyan
python scripts\selfheal.py
if ($LASTEXITCODE -ne 0) { Write-Host "ABORT: self-heal escalated." -ForegroundColor Red; exit 1 }
python scripts\test_gate.py

# ── 3. Commit and push onto the existing PR ────────────────────────────────
git add -A
git status --short
git commit -m @"
fix(CI): close the local-green CI-red class, third occurrence in one week

INSTANCE. .github/workflows/selfheal.yml declared permissions contents: read
while its own step ran git push and gh pr create. GitHub reports that as a
runtime 403 in a log nobody opens, and the declaration sat nine lines above the
step that contradicted it. Corrected to contents: write, pull-requests: write.

CLASS. The local control set and the CI step list were two independent lists and
nothing asserted they should agree, so drift was discoverable only by a red
check. Repaired individually on 2026-08-13 and 2026-08-15, which is exactly why
it recurred. Under D-112 this is one epistemic family and the third occurrence
is a blocker rather than a fourth ledger entry.

scripts/verify_workflow_contract.py asserts three properties:
  C-1 every mutating step declares the permission it needs
  C-2 every referenced script exists at this commit
  C-3 every verification script CI runs is in the local control set or is
      declared EXEMPT with a stated reason. Silence is not an exemption and the
      target state for EXEMPT is empty.
Wired into qesis-integrity.yml and into the self-heal control set. Classified C:
rewriting a permissions block automatically would let the loop widen its own
authority, which is the one thing G-07 refuses outright.

Two fixtures. The refuse fixture is today's failure itself, a git push under
contents: read. The accept fixture carries a comment inside the permissions
block, because the gate's own block reader treated a comment as end-of-structure
and reported a workflow as lacking a permission it plainly granted.

L-133 the class. L-134 a parser that stops early does not fail, it lies: three
defects in this one gate, all the same shape, nineteen findings on the first run
of which six were real.

Refs L-048 L-063 L-133 L-134 D-112 G-07
"@

git push
git fetch origin
$local  = (git rev-parse HEAD).Trim()
$remote = (git rev-parse "origin/$branch").Trim()
if ($local -ne $remote) { Write-Host "NOT LANDED local=$local remote=$remote" -ForegroundColor Red; exit 1 }
Write-Host "`nLANDED $local on origin/$branch" -ForegroundColor Green

Write-Host @"

PR #65 updates automatically. Watch the three checks that were red:
  QESIS+ integrity gate (pull_request)   expect green
  QESIS+ integrity gate (push)           expect green
  Self-heal loop / heal (push)           expect green, it can now push and open a PR

If the integrity gate is still red, the new gate will have named the reason in
its own step rather than leaving it to a log. That is the whole point of it.

THEN:  gh pr merge --rebase
AND:   Settings, Secrets and variables, Actions, Variables, New repository variable
         QESIS_KILL_SWITCH = 0
"@ -ForegroundColor Cyan
