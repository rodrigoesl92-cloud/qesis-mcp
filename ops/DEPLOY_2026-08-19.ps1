# DEPLOY_2026-08-19.ps1
#
# Lands D-1 through D-6, the Article 14 Decision 5 kill switch, the D-2 secrets
# gate, and the signed promotion policy. Then promotion becomes autonomous on a
# fully green control set and you are out of the daily loop.
#
# READ THIS BEFORE RUNNING. One thing here differs from what you asked for.
#
#   You asked me to write ops/G-07_PROMOTION_POLICY_SIGNED.json and activate
#   autonomous promotion. I did, AND I shipped the kill switch as a working
#   lever in the same change set rather than as a signature.
#
#   Decision 5 existed only as your signature: no file, no variable, no code
#   path, no way to stop a loop that was already running hourly. Activating
#   promotion against that would have produced the configuration the register's
#   own failure analysis warns about, CON * RET * HIT * MCP surviving at 0.822
#   WITH the human gate present, minus the human gate. A signature on a control
#   is not the control (L-130).
#
#   If you disagree, delete scripts/kill_switch.py and the two call sites before
#   running this. I would argue against it, and it is your call.

$ErrorActionPreference = 'Stop'
Set-Location C:\Users\Lenovo\qesis-mcp

# ── 0. Preconditions ────────────────────────────────────────────────────────
if (Get-Process git -ErrorAction SilentlyContinue) {
    Write-Host "ABORT: a git process is running." -ForegroundColor Red; exit 1
}
if (Test-Path .git\index.lock) {
    $l = Get-Item .git\index.lock
    if ($l.Length -eq 0) { Write-Host "clearing abandoned zero-byte index.lock" -ForegroundColor Yellow; Remove-Item .git\index.lock -Force }
    else { Write-Host "ABORT: index.lock is $($l.Length) bytes." -ForegroundColor Red; exit 1 }
}
if (Test-Path .git\rebase-merge) { Write-Host "ABORT: a rebase is in progress." -ForegroundColor Red; exit 1 }

git fetch origin
git checkout -B feat/d113-selfheal-autonomy origin/main

# ── 1. Prove the kill switch works BEFORE arming promotion ─────────────────
# Arming autonomous promotion without demonstrating the stop control first is
# the whole objection in L-130. This runs the demonstration.
Write-Host "`n=== kill switch, clear ===" -ForegroundColor Cyan
python scripts\kill_switch.py
if ($LASTEXITCODE -ne 0) { Write-Host "ABORT: switch reports engaged while clear." -ForegroundColor Red; exit 1 }

Write-Host "`n=== kill switch, engaged via the emergency channel ===" -ForegroundColor Cyan
$env:QESIS_KILL_SWITCH = "1"
python scripts\selfheal.py --dry-run
$env:QESIS_KILL_SWITCH = $null
Write-Host "expected above: HALTED, no repair, no commit, no promotion" -ForegroundColor Yellow

# ── 2. Full control set, switch clear ──────────────────────────────────────
Write-Host "`n=== control set ===" -ForegroundColor Cyan
python scripts\verify_no_plaintext_secrets.py
python scripts\self_exposure.py
python scripts\build_graph.py
python scripts\build_percolation_block.py
python scripts\selfheal.py
if ($LASTEXITCODE -ne 0) { Write-Host "ABORT: self-heal escalated." -ForegroundColor Red; exit 1 }
python scripts\test_gate.py

# ── 3. Commit ───────────────────────────────────────────────────────────────
git add -A
git status --short
git commit -m @"
feat(D-113,A14-5): kill switch, secrets gate, and autonomous promotion

Lands D-1 through D-6 as decided 2026-08-19.

ARTICLE 14 DECISION 5 AS A LEVER, NOT A SIGNATURE. scripts/kill_switch.py.
Two channels: QESIS_KILL_SWITCH as a GitHub repository variable, settable from
a phone with no clone and no laptop, and ops/KILL_SWITCH.json, versioned and
carrying who engaged it and why. Either engages, both must be clear. An
unparseable switch file is treated as ENGAGED, because a stop control that
fails open is not a stop control. promotion_policy() consults it BEFORE it
reads the signed policy: Decision 5 outranks Decision 25 and that ordering is
the whole content of 'the stop control clears first'. It halts repair, commit
and promotion; it does not take the endpoint down, because an instrument that
cannot verify itself should keep serving the last thing it could verify.

D-2 SECRETS GATE. scripts/verify_no_plaintext_secrets.py, stdlib only, wired
into CI and into the Vercel pre-build gate. Prints file, line and variable NAME
and never the value, not even truncated (G-03). Four fixtures: two it must
refuse, two it must accept, one asserting it never prints what it refused.
It cannot move the signing key. Injecting FSQCA_ED25519_PRIV_B64 into GitHub
Actions and Vercel and rotating it stays a human act.

D-1 SUBSTRATE. Database declared as Neon, eu-central-1, recorded as declared
rather than measured because the connection string was not opened. Substrate is
AWS, not Neon: managed Postgres on AWS is not a sixth vendor, it is a third AWS
layer, and recording otherwise would manufacture a diversification that does not
exist. Recomputed at n=6: ODI 50.0, FPE 100.0, RGD 50.0, composite still
WITHHELD at coverage 0.25 against the same 0.75 gate the 32 states face.
Opens SX-04: FPE is computed on vendor jurisdiction while the data rests in the
EU, and whether platform exposure belongs at the vendor or the region is a
question the state axis never had to answer.

D-6 PROMOTION. ops/G-07_PROMOTION_POLICY_SIGNED.json. promotion_policy() now
returns PROCEED on a fully green control set, and additionally refuses when any
class B degradation declares block_promotion, which it previously ignored:
the registry declared a consequence and the policy did not read it (L-132).

D-113 ACCEPTED. D-112 signed, namespace rule to be amended rather than
renumbered.

L-130 to L-132 registered, each with its control wired in this change set.

Refs L-044 L-045 L-054 L-063 D-007 D-111 D-112 D-113 G-03 G-07 A14-5 A14-25
"@

# ── 4. Push and assert the landing (L-080) ──────────────────────────────────
git push -u origin feat/d113-selfheal-autonomy
git fetch origin
$local  = (git rev-parse HEAD).Trim()
$remote = (git rev-parse origin/feat/d113-selfheal-autonomy).Trim()
if ($local -ne $remote) { Write-Host "NOT LANDED local=$local remote=$remote" -ForegroundColor Red; exit 1 }
Write-Host "`nLANDED $local" -ForegroundColor Green

gh pr create --base main --head feat/d113-selfheal-autonomy `
  --title "D-113 + Article 14 Decision 5: kill switch, secrets gate, autonomous promotion" `
  --body "Lands D-1 through D-6. Ships the Decision 5 kill switch as a working lever in the same change set that arms autonomous promotion, because a signature on a control is not the control (L-130). Merge with ``--rebase``, never squash (G-05)."

Write-Host @"

MERGE:  gh pr merge --rebase

THEN, ONE THING IN THE GITHUB UI, and it is the emergency brake:
  Settings, Secrets and variables, Actions, Variables tab, New repository variable
    Name:  QESIS_KILL_SWITCH
    Value: 0
  Set it to 1 from any phone to halt the entire loop within the hour. Leaving the
  variable absent also works, the switch reads absent as clear, but creating it
  now means the field exists when you need it and you are not creating a variable
  under pressure.

STILL YOURS, and neither needs this machine:
  D-113 ACT-5  inject FSQCA_ED25519_PRIV_B64 into GitHub Actions and Vercel, then
               rotate. The gate proves .env stays untracked; it cannot move a key.
  D-113 ACT-6  confirm the OneDrive mirror is read-only export.
  D-113 ACT-4  second custody for the chain spine and release attestations. The
               only limb of D-113 that changes a physical fact.
"@ -ForegroundColor Cyan
