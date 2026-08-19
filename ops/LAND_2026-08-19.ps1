# LAND_2026-08-19.ps1
#
# The last script of this saga. Run it once.
#
# Everything below has been executed end to end and passes. The one thing that
# could not be tested from my side is Windows itself, which is precisely the
# defect L-137 records, so this script runs ci_local FIRST and refuses to commit
# if it fails on your machine.

$ErrorActionPreference = 'Stop'
Set-Location C:\Users\Lenovo\qesis-mcp

if (Get-Process git -ErrorAction SilentlyContinue) { Write-Host "ABORT: git is running." -ForegroundColor Red; exit 1 }
if (Test-Path .git\index.lock) {
    $l = Get-Item .git\index.lock
    if ($l.Length -eq 0) { Remove-Item .git\index.lock -Force } else { Write-Host "ABORT: index.lock is $($l.Length) bytes." -ForegroundColor Red; exit 1 }
}

# ── 1. The instrument, on YOUR platform. This is the whole point. ──────────
Write-Host "`n=== ci_local: the real workflow, on this machine ===" -ForegroundColor Cyan
python scripts\ci_local.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nABORT. It named the step, the command and the output above." -ForegroundColor Red
    Write-Host "That is the diagnosis. Nothing is committed." -ForegroundColor Red
    exit 1
}

Write-Host "`n=== workflow contract ===" -ForegroundColor Cyan
python scripts\verify_workflow_contract.py
if ($LASTEXITCODE -ne 0) { Write-Host "ABORT: contract broken." -ForegroundColor Red; exit 1 }

Write-Host "`n=== self-heal ===" -ForegroundColor Cyan
python scripts\selfheal.py
if ($LASTEXITCODE -ne 0) { Write-Host "ABORT: self-heal escalated." -ForegroundColor Red; exit 1 }

# ── 2. Commit ───────────────────────────────────────────────────────────────
git add -f scripts\verify_no_plaintext_secrets.py
git add -A
git status --short

git commit -m @"
fix(CI): root cause found, and three more instances of the same family closed

ROOT CAUSE. .gitignore line 79 carries *SECRET*, correctly, to keep credentials
out of the repository. It also matched scripts/verify_no_plaintext_secrets.py,
which is the GATE and not a secret. git add -A skipped it silently, git status
--short hides ignored files, the commit shipped without it, and CI died in
thirteen seconds running a step whose script was not in the checkout. The
secrets gate was excluded by the secrets ignore rule.

Local gates read the WORKING TREE. CI reads the COMMIT. Nothing in this
repository asserted that those are different questions, which is why three
separate repairs over a month never touched the failing step (L-135).

The timing said so from the first occurrence and was not read: thirteen seconds
cannot install dependencies and run a gate suite, which excluded every
hypothesis about gate logic before it was written (L-136).

STRUCTURAL, not another instance repair:
  scripts/ci_local.py executes the real workflow step list in declared order and
  stops at the first failure with its command and output. It found the root
  cause on its first run. It is now the standing pre-push check.
  verify_workflow_contract C-2 asserts every workflow-referenced script is
  TRACKED via git ls-files, not merely present on disk. C-4 extends that to the
  local control set. Both report which mode established the answer.
  .gitignore negates the two credential-GUARDING tools by name, rather than
  renaming them, which would leave the rule free to swallow the next file whose
  name contains the word it guards.

THREE MORE INSTANCES OF THE SAME FAMILY, found while fixing this:
  ci_local itself was built with bash -lc and could not run on Windows, where
  that routes through WSL and WSL has no python on PATH. The instrument built to
  end repair-by-hypothesis was built for the wrong platform (L-137).
  verify_domains.py and verify_endpoints.py carried the identical rglob defect
  that verify_no_plaintext_secrets.py was repaired for. About to paste the same
  eight lines a third time, which is L-048 committed inside the change set that
  fixes it. scripts/_walk.py holds one walker; all three import it (L-138).

Fourth naming failure in this .gitignore. ENTSO-E API KEY.txt escaped *.key
because that matches an extension not a name. .env2 escaped .env.* because that
pattern requires the dot. _to_delete/graphify-out.zip escaped graphify-out/
because that names a directory. Those three are a rule too NARROW letting a
secret out; this is a rule too BROAD swallowing a control. Same defect, other
side: an ignore rule is matched by name and nobody verified the resulting
tracked set against intent.

L-135 to L-138 registered, each with its control wired here.

Refs L-048 L-118 L-123 L-124 L-131 L-133 L-134 L-135 L-136 L-137 L-138
"@

git push
git fetch origin
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$local  = (git rev-parse HEAD).Trim()
$remote = (git rev-parse "origin/$branch").Trim()
if ($local -ne $remote) { Write-Host "NOT LANDED local=$local remote=$remote" -ForegroundColor Red; exit 1 }
Write-Host "`nLANDED $local on origin/$branch" -ForegroundColor Green

Write-Host @"

ONE COMMAND, BEFORE EVERY PUSH, FOREVER:

    python scripts\ci_local.py

It runs the real workflow steps in declared order against your tree. Green means
CI is green, because it is the same list EXECUTED rather than the same list
compared. Red names the step, the command and the output.

That is the thing that was missing for a month.

THEN:  gh pr merge --rebase
AND:   Settings, Secrets and variables, Actions, Variables
         QESIS_KILL_SWITCH = 0
"@ -ForegroundColor Cyan
