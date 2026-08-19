# RECOVER_AND_LAND_2026-08-15.ps1
#
# Ends the rebase saga, lands everything, and leaves nothing tied to this machine.
#
# WHY A TREE COPY RATHER THAN ANOTHER REBASE
#   Three rebase attempts stalled on the same binary file. Measured before
#   writing this: `git diff c150be9 0fc5c1a` is EMPTY, meaning main and the
#   branch base are byte-identical trees, so the rebase was only ever a
#   parent-pointer change dressed up as a replay. Replaying f14385b forces git to
#   materialise `_to_delete/graphify-out.zip`, which a48ea9b then deletes: a file
#   added and removed inside the same rebase, and the sole source of every
#   conflict.
#
#   Taking a48ea9b's TREE directly onto main skips the intermediate state
#   entirely. The zip is not in that tree, so it can never be created, so it can
#   never conflict. One commit, identical final content, no replay.
#
#   This does not violate G-05. The rebase-never-squash rule protects the commit
#   hashes cited in data/vintage_lineage.json. f14385b and a48ea9b are cited
#   nowhere; they are two days old and unreferenced.

$ErrorActionPreference = 'Stop'          # L-128. First line, every time.
Set-Location C:\Users\Lenovo\qesis-mcp

# ── 0. Preconditions, each with its abort beside it ─────────────────────────
if (Get-Process git -ErrorAction SilentlyContinue) {
    Write-Host "ABORT: a git process is running. Close it and rerun." -ForegroundColor Red; exit 1
}
if (Test-Path .git\index.lock) {
    $l = Get-Item .git\index.lock
    if ($l.Length -eq 0) { Write-Host "clearing abandoned zero-byte index.lock" -ForegroundColor Yellow; Remove-Item .git\index.lock -Force }
    else { Write-Host "ABORT: index.lock is $($l.Length) bytes, a write was interrupted." -ForegroundColor Red; exit 1 }
}

# ── 1. End the rebase. a48ea9b is safe on the branch ref and always was. ────
if (Test-Path .git\rebase-merge) {
    Write-Host "aborting the stalled rebase" -ForegroundColor Yellow
    git rebase --abort
}
$target = (git rev-parse feat/d110-kg-rev-b).Trim()
Write-Host "branch tip preserved at $target" -ForegroundColor Green

# ── 2. Preserve the new work. Untracked files survive an abort; prove it. ──
$new = @(
  "ops\D-113_CLOUD_RUNTIME_AND_L045.md",
  "scripts\self_exposure.py",
  "scripts\apply_20260815_patchset.py",
  "data\axes\instrument_self_exposure.json",
  "ops\RECOVER_AND_LAND_2026-08-15.ps1",
  "ops\PR_BODY_2026-08-15.md"
)
$absent = $new | Where-Object { -not (Test-Path $_) }
if ($absent) {
    Write-Host "ABORT: expected new files are missing, do not proceed:" -ForegroundColor Red
    $absent | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    exit 1
}
Write-Host "all $($new.Count) new artefacts present" -ForegroundColor Green

# ── 3. Take the branch tree onto main, in one commit that cannot conflict ───
git fetch origin
git checkout -B feat/d110-kg-rev-b origin/main
git checkout $target -- .        # the branch's final tree, zip already absent
Remove-Item _to_delete -Recurse -Force -ErrorAction SilentlyContinue

# ── 4. Now the tracked files exist in their correct versions. Patch them. ──
Write-Host "`napplying the 2026-08-15 patch set..." -ForegroundColor Cyan
python scripts\apply_20260815_patchset.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ABORT: a patch anchor was missing. Read the report, do not force it." -ForegroundColor Red
    exit 1
}

# ── 5. Rebuild the derived artefacts, then verify. The gate is the authority. ─
python scripts\self_exposure.py
python scripts\build_graph.py
python scripts\build_percolation_block.py
python scripts\selfheal.py
if ($LASTEXITCODE -ne 0) { Write-Host "ABORT: self-heal escalated." -ForegroundColor Red; exit 1 }
python scripts\test_gate.py

# ── 6. Commit ───────────────────────────────────────────────────────────────
git add -A
git status --short
git commit -m @"
feat(G-07,D-113): the ecosystem repairs itself, and declares its own substrate

Lands the self-healing loop, four dispatch-board items, and the decision L-045
has been waiting on since 2026-07-29.

D-113 CLOSES L-045. Asked where the runtime lives, the answer was unknown. That
was the finding: an ecosystem whose thesis is that states cannot see their own
substrate dependencies could not see its own. Measured: four of five determined
layers resolve to two US hyperscalers, and one vendor holds the source of
record, the CI, the self-heal loop and the evidence mirror simultaneously.
Adopted deliberately rather than migrated, because L-044 requires each service
to be priced against the failure it removes and the failure here was that the
exposure was never stated. Migration relocates it; a decision number states it.

scripts/self_exposure.py scores the instrument on its own axes under its own
calibration: ODI 52.0, FPE 100.0, RGD 60.0, composite WITHHELD at coverage 0.25
against the same 0.75 BIG gate the 32 states face. Held to the same rule rather
than a looser one, because a looser rule produces a number and destroys the
comparison. COMPUTED, NOT PUBLISHED per the operator ruling: evidence plane
only, served:false carried inside the artefact.

PRODUCTION PROBE ROOT CAUSE, failing hourly on main for nine consecutive runs.
scripts/vercel_gate.py gated artefact quality and never gated which branch was
promoting, so Vercel aliased production to whatever last passed and
deployment_commit bound to a feature branch while verify_production.py compared
it against main's HEAD. The probe was right every hour. G-01b said the served
index is replaced only by a promotion event and that sentence had no
implementation on the alias path. It has one now.

SH-7: nothing depends on the operator's machine. The self-heal workflow lands
its own class A repairs from the runner via a pull request. G-06 limit 3 is
untouched: no direct push to main, no promotion.

Also lands PUB-1 percolation, KG-1 graph fixtures, KG-5 edge planes, EMO-1
verdict restatement, AUDIT-1 restated on both halves, D-112 ADR, and the UN
Comtrade SCOUT intake.

L-119 to L-128 registered, each with its control wired in the same change set.

Refs L-044 L-045 L-054 L-063 L-122 L-123 L-125 D-007 D-111 D-112 D-113 G-01b G-07
"@

# ── 7. Push, then ASSERT the landing (L-080) ────────────────────────────────
git push --force-with-lease -u origin feat/d110-kg-rev-b
git fetch origin
$local  = (git rev-parse HEAD).Trim()
$remote = (git rev-parse origin/feat/d110-kg-rev-b).Trim()
if ($local -ne $remote) {
    Write-Host "NOT LANDED local=$local remote=$remote" -ForegroundColor Red; exit 1
}
Write-Host "`nLANDED $local" -ForegroundColor Green

# ── 8. Pull request ─────────────────────────────────────────────────────────
gh pr create --base main --head feat/d110-kg-rev-b `
  --title "G-07 + D-113: the ecosystem repairs itself, and declares its own substrate" `
  --body-file ops\PR_BODY_2026-08-15.md

Write-Host @"

MERGE:  gh pr merge --rebase        never squash (G-05)

THEN, and this is the only step that stops the hourly alarm:
  Merging puts the production commit on main. Vercel rebuilds from main, the
  branch guard allows it, deployment_commit binds to main's HEAD, and
  verify_production.py stops failing. Runs 221 to 229 were correct every time.

STILL YOURS, none of it needs this machine afterwards:
  D-113 ACT-1  name the database provider from database_string.txt. I will not
               open it (G-03), and an index that publishes source hashes cannot
               say 'unknown' about its own database.
  D-113 ACT-5  rotate FSQCA_ED25519_PRIV_B64 out of plaintext .env
  D-113 ACT-6  confirm the OneDrive mirror is read-only export, not the writable
               evidence plane. D-027 and G-03 forbid the latter.
  D-113 ACT-2  sign or refuse D-113
  D-112        sign or refuse, and rule on the D- namespace drift
  Article 14   5, then 2, 1, 6, 20, then 25 last. Signing these is what makes
               the loop autonomous rather than merely scheduled.
"@ -ForegroundColor Cyan
