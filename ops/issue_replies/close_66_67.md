Resolved by `183dde1`, merged to `main` in #65.

## Root cause, single, for both issues

`.gitignore` line 79 carries `*SECRET*`, correctly, to keep credentials out of
the repository. It also matched `scripts/verify_no_plaintext_secrets.py`, which
is the **gate**, not a secret.

`git add -A` skipped it in silence. `git status --short` hides ignored files.
The commit shipped without it. Every CI step that touched it died.

## Why each check failed, mechanically

**#66 `test_gate`.** `check_secrets` in `scripts/test_gate.py` begins with
`if not SECRETS_GATE.exists(): results.append(("secrets: gate present", False))`.
The file was not in the checkout, so one behaviour failed, `passed != total`,
and `test_gate` exited 1.

**#67 `verify_workflow, test_gate`.** `scripts/verify_workflow_contract.py`
landed at `16f76f8`. Its C-2 check asserted that every script a workflow
references exists. `qesis-integrity.yml` references
`scripts/verify_no_plaintext_secrets.py`, which did not exist in the checkout,
so C-2 failed. `test_gate` failed alongside it for the reason above. Two
controls, one missing file.

Both jobs died in roughly thirteen seconds, which is before dependency
installation completes. That timing excluded every hypothesis about gate logic
and was not read for three rounds of repair (L-136).

## Fixed, and verified on `main`

- `.gitignore` **negates** the two credential-guarding tools by name rather than
  renaming them. A rename removes the symptom and leaves the rule free to
  swallow the next file whose name contains the word it guards.
- `scripts/verify_no_plaintext_secrets.py` and `scripts/_walk.py` are both
  present on `main`, confirmed by fetching them from `raw.githubusercontent.com`.
  The dependency chain holds, so the missing-file error is not traded for an
  `ImportError`.
- `verify_workflow_contract` **C-2 now asserts TRACKED via `git ls-files`**, not
  present on disk. **C-4** extends the same assertion to the local control set.
  Both report which mode established the answer rather than silently downgrading
  where git is unavailable.

## Why this class cannot recur silently

Local gates read the **working tree**. CI reads the **commit**. Nothing in this
repository asserted those are different questions, which is why three separate
structural fixes over a month never touched the failing step (L-135).

`scripts/ci_local.py` executes the real workflow step list in declared order and
stops at the first failure with its command and output. It found this root cause
on its first run.

Registered as **L-135** through **L-139**, each with its control wired in the
same change set.
