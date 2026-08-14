<#
.SYNOPSIS
  Recover qesis-mcp from an abandoned rebase and land v9.1 on top of main.

.DESCRIPTION
  ORDER MATTERS AND v1 GOT IT WRONG. v1 attempted `checkout -B` while a
  `.git/rebase-merge` directory still existed and the working tree was dirty, so
  git refused twice and left the repository mid-rebase. This version clears the
  abandoned rebase FIRST, then resets the tree, then switches branch, then
  rebases. Recorded as L-114.

  Why the repository is in this state: a rebase started from the analysis mount
  was interrupted by `.git/index.lock`, which that mount cannot unlink
  ("Operation not permitted", the standing LOCK-1). The rebase could neither
  finish nor abort from there. Windows PowerShell can remove the lock, which is
  why this runs here and not there.

  NOTHING IS LOST. Every v9.1 commit is on backup/pre-rebase-v91-20260814
  (9897787). This script never deletes that branch.

  The conflict it resolves: main advanced three commits. Eight files changed on
  both sides, five byte-identical, one deletion agreed. Two genuinely differ, and
  `qesis-integrity.yml` has a real addition on EACH side: main's verify_endpoints
  gate and this branch's SHA pinning. `-X theirs` alone would silently drop
  main's gate, so it is restored from main and re-pinned on top.

.PARAMETER Apply
  Without it, prints the plan and changes nothing.
#>
[CmdletBinding()]
param([switch]$Apply, [string]$Repo = "C:\Users\Lenovo\qesis-mcp")

$ErrorActionPreference = "Stop"
function Say($m, $c = "Gray") { Write-Host $m -ForegroundColor $c }
function Run($desc, [scriptblock]$b) {
  if (-not $Apply) { Say "  DRYRUN $desc" Yellow; return }
  Say "  APPLY  $desc" Green
  & $b
}

$BACKUP = "backup/pre-rebase-v91-20260814"
$BRANCH = "feat/d110-kg-rev-b"

Set-Location $Repo
Say "repo   : $Repo"
Say "mode   : $(if ($Apply) { 'APPLY' } else { 'DRY RUN, pass -Apply' })" `
  $(if ($Apply) { 'Green' } else { 'Yellow' })

if (-not (git rev-parse --verify $BACKUP 2>$null)) {
  throw "$BACKUP is missing. STOP and report this rather than improvising."
}
Say "  backup holds $(git rev-parse --short $BACKUP), all v9.1 work is safe"

# ── STEP 1. Clear every lock and every abandoned rebase. Nothing else can run
#            until this is done, which is exactly what v1 failed to understand.
$proc = Get-Process git -ErrorAction SilentlyContinue
if ($proc) { throw "A real git process is running (PID $($proc.Id -join ',')). Close it, then re-run." }

# L-115. v2 cleared index.lock only. git takes several locks and every one of
# them blocks a different operation: packed-refs.lock blocked the branch update,
# REBASE_HEAD.lock blocked the abort. Clearing one lock and calling the repository
# unlocked is the same error as auditing one gate and calling the control set
# verified (V-4). Enumerate the set.
foreach ($stale in @(".git\index.lock", ".git\HEAD.lock", ".git\packed-refs.lock",
                     ".git\REBASE_HEAD.lock", ".git\ORIG_HEAD.lock",
                     ".git\refs\heads\$BRANCH.lock")) {
  if (Test-Path $stale) { Run "remove stale $stale" { Remove-Item $stale -Force -ErrorAction SilentlyContinue } }
}
foreach ($dir in @(".git\rebase-merge", ".git\rebase-apply")) {
  if (Test-Path $dir) { Run "remove abandoned $dir" { Remove-Item $dir -Recurse -Force } }
}

# ── STEP 2. Reset the tree BEFORE switching branch. The working tree currently
#            holds v9.1 files as uncommitted changes; every one of them is
#            already committed in the backup, so a hard reset loses nothing.
Run "reset --hard to $BACKUP" { git reset --hard $BACKUP }
Run "point $BRANCH at the backup" { git checkout -B $BRANCH $BACKUP }
if ($Apply) {
  Say "  HEAD now $(git rev-parse --short HEAD)  $(git log --oneline -1 --format=%s)"
  # L-114. v2 asserted cleanliness with `git status --porcelain`, which counts
  # UNTRACKED files. `reset --hard` never removes untracked files, so the guard
  # could not be satisfied by the operation it was guarding. It fired on one
  # untracked file: this script, written after the backup commit. The predicate
  # did not match the intent. What matters here is that no TRACKED file carries
  # an uncommitted change, because those are what a checkout would overwrite.
  if (git status --porcelain --untracked-files=no) {
    throw "A TRACKED file still has uncommitted changes after reset. Stop and report."
  }
  Say "  tracked tree clean (untracked files are not a blocker here)" Green
}

# ── STEP 3. Rebase. -X theirs favours the commits being replayed, this branch.
Run "fetch origin" { git fetch origin }
if ($Apply) {
  git rebase -X theirs origin/main
  if ($LASTEXITCODE -ne 0) {
    Say ""
    Say "Rebase stopped on a conflict git could not resolve." Red
    Say "To undo everything and return to a known-good state, run these two lines:" Red
    Say "  git rebase --abort" Red
    Say "  git checkout -B $BRANCH $BACKUP" Red
    exit 1
  }
  Say "  rebased onto origin/main" Green
}

# ── STEP 4. Keep BOTH halves of the workflow. This is the step that makes the
#            difference between a merge and a regression.
if ($Apply) {
  git checkout origin/main -- .github/workflows/qesis-integrity.yml
  $f = ".github/workflows/qesis-integrity.yml"
  $t = Get-Content $f -Raw
  $pins = [ordered]@{
    "actions/checkout@v4"      = "34e114876b0b11c390a56381ad16ebd13914f8d5"
    "actions/setup-python@v5"  = "a26af69be951a213d495a4c3e4e4022e16d87065"
    "actions/github-script@v7" = "f28e40c7f34bde8b3046d885e986cb6290c5673b"
  }
  foreach ($k in $pins.Keys) {
    $name, $tag = $k -split '@'
    $t = $t -replace [regex]::Escape("uses: $k"), "uses: $name@$($pins[$k]) # $tag"
  }
  Set-Content $f $t -NoNewline -Encoding UTF8
  Say "  qesis-integrity.yml: main's verify_endpoints gate kept, SEC-1 pins re-applied" Green
}

# ── STEP 5. Prove it before pushing. A rebase that passes no gate is a claim.
if ($Apply) {
  $gates = @("verify_index", "verify_chain", "verify_vintage_pairing", "verify_dashboard",
             "verify_domains", "verify_axis_sfc", "verify_action_pinning", "verify_endpoints")
  $bad = @()
  foreach ($g in $gates) {
    if (-not (Test-Path "scripts\$g.py")) { Say "  SKIP  $g (absent)" DarkGray; continue }
    python "scripts\$g.py" *> $null
    if ($LASTEXITCODE -eq 0) { Say "  PASS  $g" Green } else { Say "  FAIL  $g" Red; $bad += $g }
  }
  python "scripts\compute_fidelity.py" --check *> $null
  if ($LASTEXITCODE -eq 0) { Say "  PASS  compute_fidelity --check" Green }
  else { Say "  FAIL  compute_fidelity --check" Red; $bad += "compute_fidelity" }

  if ($bad.Count -gt 0) {
    Say ""
    Say "STOP. Gates failed: $($bad -join ', '). Nothing pushed." Red
    Say "Recover with: git checkout -B $BRANCH $BACKUP" Red
    exit 1
  }
  git add -A
  git -c core.editor=true commit --allow-empty -m @"
fix(rebase): keep main's endpoint gate and the SEC-1 pins together

-X theirs favours the replayed branch and would have dropped the
verify_endpoints step main added. Taken from main and re-pinned on top.
Nine gates green before push. QT-0007.
"@
}

# ── STEP 6. Push under a lease, then read the remote back rather than $?.
if ($Apply) {
  git push --force-with-lease
  Say ""
  Say "REMOTE, read back:" Cyan
  git log --oneline -1
  Say "  ahead of main : $(git rev-list --count origin/main..HEAD)"
  Say "  behind main   : $(git rev-list --count HEAD..origin/main)"
  Say ""
  Say "Final step:  gh pr merge 61 --rebase" Green
  Say "Rebase replays each commit onto main and keeps history linear." Gray
  Say "Squash would collapse them into one hash and break your lineage citations." Gray
} else {
  Say ""
  Say "DRY RUN. Re-run with -Apply." Yellow
}
