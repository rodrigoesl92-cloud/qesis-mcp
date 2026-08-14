<#
.SYNOPSIS
  Repair the GitHub state of the QESIS+ ecosystem so the daily ops run is clean.

.DESCRIPTION
  Idempotent by construction. Every step reads current state before acting and
  is safe to run twice. That is the defect this script exists to correct: the
  push block issued on 2026-08-13 had no guards, was run twice, and opened
  duplicate pull requests 56 and 58 from one branch at one commit.

  Rule 2-5: every command that mutates state names its repository explicitly and
  the confirmation read back is the remote, not the exit code.
  Rule 2-4 / G-06: an agent may merge a paired remediation PR with --rebase once
  checks pass. Nothing here pushes to main and nothing here promotes.

.PARAMETER Apply
  Without it, this is a dry run and prints what it would do. Nothing is deleted,
  closed or pushed until you pass -Apply.

.EXAMPLE
  .\scripts\ops\Repair-GitHub.ps1
  .\scripts\ops\Repair-GitHub.ps1 -Apply
#>
[CmdletBinding()]
param(
  [switch]$Apply,
  [string]$Repo = "C:\Users\Lenovo\qesis-mcp",
  [string]$KeepPr = "56"
)

$ErrorActionPreference = "Stop"
function Say($m, $c = "Gray") { Write-Host $m -ForegroundColor $c }
function Head($m) { Say ""; Say ("=" * 72) DarkGray; Say $m Cyan; Say ("=" * 72) DarkGray }
function Do-It($what, [scriptblock]$act) {
  if ($Apply) { Say "  APPLY  $what" Green; & $act }
  else { Say "  DRYRUN $what" Yellow }
}

Set-Location $Repo
Say "repo   : $Repo"
Say "remote : $(git remote get-url origin)"
Say "mode   : $(if ($Apply) { 'APPLY' } else { 'DRY RUN, pass -Apply to execute' })" `
  $(if ($Apply) { "Green" } else { "Yellow" })

# Preconditions. A dirty tree turns a prune into data loss.
if (git status --porcelain) { throw "Working tree is dirty. Commit or stash first." }
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw "gh CLI not found." }
git fetch --all --prune | Out-Null

# ─────────────────────────────────────────────────────────────────────────────
Head "1. Duplicate pull requests"
# One branch at one commit cannot need two PRs. Close every duplicate but $KeepPr.
$prs = gh pr list --state open --json number,headRefName,title --limit 100 | ConvertFrom-Json
$dupes = $prs | Group-Object headRefName | Where-Object Count -gt 1
if (-not $dupes) { Say "  none open" }
foreach ($g in $dupes) {
  $keep = ($g.Group | Where-Object { "$($_.number)" -eq $KeepPr } | Select-Object -First 1)
  if (-not $keep) { $keep = $g.Group | Sort-Object number | Select-Object -First 1 }
  Say "  branch $($g.Name): keeping #$($keep.number)"
  foreach ($p in $g.Group | Where-Object number -ne $keep.number) {
    Do-It "close duplicate PR #$($p.number)" {
      gh pr close $p.number --comment "Duplicate of #$($keep.number). Same head, same commit. Closed by Repair-GitHub.ps1."
    }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
Head "2. Branches whose content already landed on main"
# A rebase merge strands the source branch: the content is on main under a new
# hash, so --no-merged still lists it. Match on commit SUBJECT, not hash, or
# these accumulate forever. This is the cost G-06 accepts by forbidding squash.
$mainSubjects = git log origin/main --format="%s" -n 400
$remotes = git branch -r --format="%(refname:short)" |
  Where-Object { $_ -notmatch 'origin/(HEAD|main)$' }

$stranded = @()
foreach ($b in $remotes) {
  $only = git log "origin/main..$b" --format="%s"
  if (-not $only) { continue }
  $landed = @($only | Where-Object { $mainSubjects -contains $_ })
  if ($landed.Count -eq @($only).Count) { $stranded += $b }
}
if (-not $stranded) { Say "  none" }
foreach ($b in $stranded) {
  Say "  stranded (content on main under a different hash): $b"
  Do-It "delete remote $b" { git push origin --delete ($b -replace '^origin/', '') }
}

# ─────────────────────────────────────────────────────────────────────────────
Head "3. Fully merged remote branches"
$merged = git branch -r --merged origin/main --format="%(refname:short)" |
  Where-Object { $_ -notmatch 'origin/(HEAD|main)$' }
if (-not $merged) { Say "  none" }
foreach ($b in $merged) {
  Do-It "delete merged remote $b" { git push origin --delete ($b -replace '^origin/', '') }
}

# ─────────────────────────────────────────────────────────────────────────────
Head "4. Local branches with no remote (gone or never pushed)"
$dead = git branch -vv | Select-String ': gone]' | ForEach-Object {
  ($_ -replace '^\*?\s*', '' -split '\s+')[0] }
$noUpstream = git for-each-ref --format="%(refname:short) %(upstream)" refs/heads |
  Where-Object { $_ -notmatch ' refs/' } | ForEach-Object { ($_ -split ' ')[0] } |
  Where-Object { $_ -notmatch '^(main|backup/)' }
$cur = git rev-parse --abbrev-ref HEAD
foreach ($b in (@($dead) + @($noUpstream) | Sort-Object -Unique | Where-Object { $_ -and $_ -ne $cur })) {
  Say "  local-only: $b"
  Do-It "delete local $b (use -D only if you accept losing it)" { git branch -D $b }
}
Say "  backup/* branches are never touched by this script."

# ─────────────────────────────────────────────────────────────────────────────
Head "5. SEC-1: pin every GitHub Action to a full-length commit SHA"
# A mutable tag is a supply-chain hole and a daily-ops hazard: the tag moves and
# a green pipeline turns red with no change on your side. MODELING_LAYERS_MDA.md
# section 5(b) recorded this control as closed while zero actions were pinned.
$wf = Get-ChildItem .github/workflows -Filter *.yml -ErrorAction SilentlyContinue
$resolved = @{}
foreach ($f in $wf) {
  $text = Get-Content $f.FullName -Raw
  $hits = [regex]::Matches($text, 'uses:\s*([\w.-]+/[\w.-]+)@(v[\w.-]+)\s*$', 'Multiline')
  foreach ($m in $hits) {
    $action = $m.Groups[1].Value; $tag = $m.Groups[2].Value; $key = "$action@$tag"
    if (-not $resolved.ContainsKey($key)) {
      $sha = (gh api "repos/$action/commits/$tag" --jq '.sha' 2>$null)
      if ($sha) { $resolved[$key] = $sha; Say "  $key -> $sha" }
      else { Say "  COULD NOT RESOLVE $key" Red }
    }
  }
}
foreach ($f in $wf) {
  $text = Get-Content $f.FullName -Raw; $new = $text
  foreach ($k in $resolved.Keys) {
    $a, $t = $k -split '@'
    $new = $new -replace [regex]::Escape("uses: $a@$t"), "uses: $a@$($resolved[$k]) # $t"
  }
  if ($new -ne $text) {
    Do-It "pin actions in $($f.Name)" { Set-Content $f.FullName $new -NoNewline -Encoding UTF8 }
  }
}

# ─────────────────────────────────────────────────────────────────────────────
Head "6. Runner burn: qesis-integrity fires on branches: [\"**\"]"
# With 20+ stale remotes every push to any branch runs the full gate set. The
# pull_request trigger has no paths filter DELIBERATELY (a required check that
# does not run blocks the merge forever), so narrow the PUSH trigger only.
Say "  Steps 2 to 4 remove the stale branches, which removes most of the burn."
Say "  Recommended, not automated: change the push trigger to"
Say "    push:" DarkCyan
Say "      branches: [main, 'fix/**', 'feat/**', 'release/**']" DarkCyan
Say "  Leave the pull_request trigger exactly as it is. L-091 is written on that line."

# ─────────────────────────────────────────────────────────────────────────────
Head "7. ANOMALY, human decision required. Do not automate this."
$ahead = (git rev-list --count origin/main..origin/fix/python-canonical-runtime)
$behind = (git rev-list --count origin/fix/python-canonical-runtime..origin/main)
Say "  origin/fix/python-canonical-runtime is $ahead ahead / $behind behind origin/main" Red
Say "  origin/fix/vercel-production-branch carries one unmerged commit:" Red
git log --oneline origin/main..origin/fix/vercel-production-branch
Say ""
Say "  If Vercel still deploys from fix/python-canonical-runtime, production is" Red
Say "  serving commits that never passed through main, and main is not the" Red
Say "  production plane it claims to be. If Vercel already deploys from main," Red
Say "  then fix/vercel-production-branch is a stale branch to merge or delete." Red
Say "  Settle it in the Vercel dashboard, then merge or drop that branch." Red
Say "  Promotion is a human act (G-06). This script will not touch it."

Head "Done. Read the remote back, not the exit code."
Say "  git branch -r"
Say "  gh pr list --state open"
if (-not $Apply) { Say ""; Say "DRY RUN. Re-run with -Apply to execute." Yellow }
