# ROOTCAUSE_2026-08-19.ps1
#
# The root cause of the month, found and fixed. Run this once.
#
# WHAT WAS ACTUALLY WRONG
#   .gitignore line 79 carries `*SECRET*`, correctly, to keep credentials out of
#   the repository. It also matched scripts/verify_no_plaintext_secrets.py,
#   which is the GATE and not a secret.
#
#   `git add -A` skipped it without a word. `git status --short` did not list it,
#   because status hides ignored files. The commit shipped without it. CI ran
#   `python scripts/verify_no_plaintext_secrets.py` against a checkout that did
#   not contain the file and died in thirteen seconds.
#
#   The secrets gate was excluded by the secrets ignore rule.
#
# WHY IT SURVIVED THREE ROUNDS OF REPAIR
#   Every local gate passed because the file was ON DISK. Every CI check failed
#   because it was not IN THE COMMIT. Nothing in this repository ever asserted
#   that those are different questions. Local gates read the working tree; CI
#   reads the commit (L-135).
#
#   And the timing said so from the first occurrence. Thirteen seconds is not
#   enough to install dependencies and run a gate suite, so the failure was
#   necessarily at or before install, which excluded every hypothesis about gate
#   logic before it was written. I did not read that, three times (L-136).
#
# WHAT IS FIXED, STRUCTURALLY
#   .gitignore                        negation, not a rename. A rename removes
#                                     the symptom and leaves the rule free to
#                                     swallow the next file it guards the name of
#   verify_workflow_contract.py C-2   every workflow-referenced script must be
#                                     TRACKED, via git ls-files, not merely present
#   verify_workflow_contract.py C-4   the same assertion for the local control set
#   scripts/ci_local.py               executes the REAL workflow step list in
#                                     order and stops at the first failure with
#                                     its command and output. It found this in
#                                     one run and should have existed on 08-13

$ErrorActionPreference = 'Stop'
Set-Location C:\Users\Lenovo\qesis-mcp

if (Get-Process git -ErrorAction SilentlyContinue) { Write-Host "ABORT: git is running." -ForegroundColor Red; exit 1 }
if (Test-Path .git\index.lock) {
    $l = Get-Item .git\index.lock
    if ($l.Length -eq 0) { Remove-Item .git\index.lock -Force } else { Write-Host "ABORT: index.lock is $($l.Length) bytes." -ForegroundColor Red; exit 1 }
}

# ── 1. Prove the defect before fixing it, so the fix is falsifiable ─────────
Write-Host "`n=== the defect, stated as a command ===" -ForegroundColor Cyan
Write-Host "git check-ignore -v scripts/verify_no_plaintext_secrets.py"
git check-ignore -v scripts/verify_no_plaintext_secrets.py
Write-Host "`n(the negation now wins; before this change set, line 79 did)" -ForegroundColor Yellow

# ── 2. Force-add what the ignore rule swallowed ─────────────────────────────
# -f is correct here and is not a bypass: the negation makes it unnecessary for
# future adds, and -f covers the case where the index still carries the old
# ignore decision.
git add -f scripts/verify_no_plaintext_secrets.py
git add -A

# ── 3. The gate must now pass. If it does not, do not commit. ──────────────
Write-Host "`n=== workflow contract ===" -ForegroundColor Cyan
python scripts\verify_workflow_contract.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ABORT: still failing. The gate names the file and the reason." -ForegroundColor Red
    exit 1
}

# ── 4. Run the REAL CI step list locally. This is the new standing check. ──
Write-Host "`n=== ci_local: the actual workflow, step by step ===" -ForegroundColor Cyan
python scripts\ci_local.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nABORT: a CI step fails locally. It names the step, the command" -ForegroundColor Red
    Write-Host "and the output. Fix that before pushing, because CI will do the same." -ForegroundColor Red
    exit 1
}

python scripts\selfheal.py
if ($LASTEXITCODE -ne 0) { Write-Host "ABORT: self-heal escalated." -ForegroundColor Red; exit 1 }

# ── 5. Commit ───────────────────────────────────────────────────────────────
git add -A
git status --short
git commit -m @"
fix(CI): the secrets gate was excluded by the secrets ignore rule

ROOT CAUSE of three CI failures in one week and a month of repair by hypothesis.

.gitignore line 79 carries *SECRET*, correctly, to keep credentials out of the
repository. It also matched scripts/verify_no_plaintext_secrets.py, which is the
GATE and not a secret. git add -A skipped it silently, git status --short hides
ignored files, the commit shipped without it, and qesis-integrity.yml died in
thirteen seconds running a step whose script was not in the checkout.

WHY IT SURVIVED THREE REPAIRS. Every local gate passed because the file was on
disk. Every CI check failed because it was not in the commit. Nothing asserted
that those are different questions: local gates read the working tree, CI reads
the commit (L-135). The timing said so from the first occurrence and was not
read: thirteen seconds cannot install dependencies and run a gate suite, which
excluded every hypothesis about gate logic before it was written (L-136).

STRUCTURAL FIXES, not another instance repair:
  .gitignore negates the two credential-GUARDING tools by name. Negated rather
  than renamed: a rename removes the symptom and leaves the rule free to swallow
  the next file whose name contains the word it guards.
  verify_workflow_contract C-2 asserts every workflow-referenced script is
  TRACKED via git ls-files, not merely present on disk.
  verify_workflow_contract C-4 extends that to the local control set.
  Both report which mode established the answer rather than silently downgrading
  where git is unavailable.
  scripts/ci_local.py executes the real workflow step list in declared order and
  stops at the first failure with its command and its output. It found this in
  one run and should have existed on 2026-08-13.

FOURTH naming failure in this .gitignore. ENTSO-E API KEY.txt escaped *.key
because that matches an extension not a name. .env2 escaped .env.* because that
pattern requires the dot. _to_delete/graphify-out.zip escaped graphify-out/
because that names a directory. Those three are a rule too NARROW letting a
secret out; this is a rule too BROAD swallowing a control, which is the same
defect from the other side. An ignore rule is matched by name and nobody ever
verified the resulting tracked set against intent.

Refs L-118 L-123 L-124 L-133 L-134 L-135 L-136 INC-20260731-01 INC-20260805-01
"@

git push
git fetch origin
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$local  = (git rev-parse HEAD).Trim()
$remote = (git rev-parse "origin/$branch").Trim()
if ($local -ne $remote) { Write-Host "NOT LANDED local=$local remote=$remote" -ForegroundColor Red; exit 1 }
Write-Host "`nLANDED $local on origin/$branch" -ForegroundColor Green

Write-Host @"

FROM NOW ON, one command before every push, and it is the whole lesson:

    python scripts\ci_local.py

It runs the real workflow steps in order against your tree. If it is green, CI
is green, because it is the same list executed rather than the same list
compared. If it is red, it names the step, the command and the output.

Issues #66 and #67 were opened by the self-heal loop with the correct diagnosis
before I found it. The loop was working. The reading was not.
"@ -ForegroundColor Cyan
