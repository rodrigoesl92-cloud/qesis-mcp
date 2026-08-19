# RESUME_REBASE_2026-08-15.ps1
#
# Resumes the rebase my own command block stalled, then opens the pull request.
#
# WHAT WENT WRONG, so this script is read rather than trusted:
#   The block told you to `git rm --cached _to_delete/graphify-out.zip`, commit,
#   and THEN rebase. `--cached` untracks a file and leaves it on disk, and the
#   rebase has to replay f14385b, which ADDS that path. Git refused to overwrite
#   an untracked working-tree file and stopped mid-rebase in detached HEAD.
#   The removal had to come after the replay, or the file had to leave the tree
#   first. I sequenced it so the conflict was guaranteed (L-125).
#
# WHAT IS NOT WRONG, measured before writing this:
#   Nothing is lost. refs/heads/feat/d110-kg-rev-b still points at a48ea9b.
#   Main's b3a3cd1, 330032e and c150be9 are rebased twins of your df355b4,
#   dacb16f and 0fc5c1a, which is why the rebase reported them as previously
#   applied. Both ledgers end at L-117 at the base and `scripts/test_gate.py` is
#   identical at the base, so there is NO content conflict on either file. The
#   untracked zip is the whole of the blockage.

$ErrorActionPreference = 'Stop'
Set-Location C:\Users\Lenovo\qesis-mcp

# ── 0. Preconditions, each with its abort next to it (L-082) ────────────────
if (-not (Test-Path .git\rebase-merge)) {
    Write-Host "No rebase in progress. If you already aborted, run PUSH_2026-08-15.ps1 instead." -ForegroundColor Yellow
    exit 0
}
if (Test-Path .git\index.lock) {
    $l = Get-Item .git\index.lock
    if ($l.Length -eq 0) { Write-Host "clearing abandoned zero-byte index.lock" -ForegroundColor Yellow; Remove-Item .git\index.lock -Force }
    else { Write-Host "ABORT: index.lock is $($l.Length) bytes, a write was interrupted. Inspect it." -ForegroundColor Red; exit 1 }
}
Write-Host "rebase in progress, todo:" -ForegroundColor Cyan
Get-Content .git\rebase-merge\git-rebase-todo

# ── 1. Move the blocker OUT of the working tree. Move, never delete. ────────
# These are your files. `_to_delete/` is now gitignored as a directory, so once
# they are outside the tree nothing in this repository refers to them again.
$scratch = "C:\Users\Lenovo\_qesis_scratch"
New-Item -ItemType Directory -Force -Path $scratch | Out-Null
if (Test-Path _to_delete) {
    Get-ChildItem _to_delete -Force | ForEach-Object {
        Write-Host "moving $($_.Name) -> $scratch" -ForegroundColor Yellow
        Move-Item $_.FullName -Destination $scratch -Force
    }
    Remove-Item _to_delete -Force -Recurse -ErrorAction SilentlyContinue
}

# ── 2. Continue the rebase ──────────────────────────────────────────────────
Write-Host "`ncontinuing the rebase..." -ForegroundColor Cyan
git rebase --continue
if ($LASTEXITCODE -ne 0) {
    Write-Host @"

The rebase stopped again. It is recoverable and nothing is lost.

  git status                 see which paths it is asking about
  git rebase --abort         returns you to feat/d110-kg-rev-b at a48ea9b

If it stopped on a CONTENT conflict rather than an untracked file, the two
candidates are ops/LESSONS_LEDGER.md and scripts/test_gate.py. Both are
append-only in effect, so the resolution is KEEP BOTH SIDES in id order, never
pick one. Measured before writing this: neither should conflict, because main's
commits are rebased twins of yours and both files are identical at the base. If
one does conflict anyway, that is new information and it should be read rather
than resolved by reflex.
"@ -ForegroundColor Red
    exit 1
}

# ── 3. Confirm we are back on a branch, not detached ────────────────────────
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -eq 'HEAD') {
    Write-Host "ABORT: still detached. Do not push from here." -ForegroundColor Red
    exit 1
}
Write-Host "back on branch '$branch'" -ForegroundColor Green

# ── 4. Verify. The gate is the authority, not the rebase exit code. ─────────
Write-Host "`nrunning the control set..." -ForegroundColor Cyan
python scripts\selfheal.py
if ($LASTEXITCODE -ne 0) { Write-Host "ABORT: self-heal escalated. Read it before pushing." -ForegroundColor Red; exit 1 }
python scripts\test_gate.py

# ── 5. Push, then ASSERT the landing (L-062, L-080) ─────────────────────────
# --force-with-lease, never --force: it refuses if the remote moved since your
# last fetch, which is the entire reason to prefer it.
git push --force-with-lease
git fetch origin
$local  = (git rev-parse HEAD).Trim()
$remote = (git rev-parse "origin/$branch").Trim()
if ($local -ne $remote) {
    Write-Host "NOT LANDED  local=$local  remote=$remote. Do not report this as pushed." -ForegroundColor Red
    exit 1
}
Write-Host "`nLANDED  $local  on origin/$branch" -ForegroundColor Green

# ── 6. Open the pull request with a real title ──────────────────────────────
# GitHub's generated title was "Feat/d110 kg rev b", which tells a reader
# nothing. A PR title is the sentence the merge commit carries into main.
$body = Get-Content ops\PR_BODY_2026-08-15.md -Raw
gh pr create --base main --head $branch `
  --title "G-07: the ecosystem repairs itself. PUB-1, KG-1, KG-5, EMO-1 land with it" `
  --body $body

Write-Host @"

Merge with rebase, never squash:
  gh pr merge --rebase

Squash rewrites every branch commit into one new hash, and
data/vintage_lineage.json cites commit hashes. verify_vintage_pairing.py checks
that the fields are populated, not that they resolve, so a squash would break
the references and pass CI silently, which is worse than failing (G-05).

Promotion is NOT required. Nothing here touches data/qesis_v8.json, so
index_sha256 does not move and the served vintage stays v9.0 (2026-08-13).
"@ -ForegroundColor Cyan
