# Landing a change set. Git only.

**No Python. No PowerShell logic. Nothing an agent wrote and could not run on
your machine.** L-139: four consecutive handovers failed on Windows and none
failed on the Linux box they were authored on. The code was never the defect.
The handover was.

Verification happens in **GitHub Actions on ubuntu-latest**, which is the same
environment the agent runs in, so what was tested is what runs.

## The three lines

```
git add -A
git commit -F ops/COMMIT_MSG.txt
git push
```

That is the whole procedure. `git` behaves identically on every platform, which
is why it is the only tool left in it.

## If git refuses

**`index.lock` exists.** An agent session on the analysis mount creates it and
cannot remove it (L-123). Delete it and rerun. It is a zero-byte file with no
process behind it.

```
del .git\index.lock
```

**A file you expect is not in the commit.** Ask git, not the filesystem:

```
git check-ignore -v <path>
```

This is what cost a month. `.gitignore` line 79 `*SECRET*` swallowed
`scripts/verify_no_plaintext_secrets.py`, `git add -A` skipped it in silence,
and CI ran a step whose script was not in the checkout (L-135).

## After the push

Read the checks on the pull request. If one is red, open it and read the failing
step. Do not ask an agent to guess from the summary: that guess is what produced
three structural fixes that never touched the failing step (L-136).

Merge with `--rebase`, never squash, because `data/vintage_lineage.json` cites
commit hashes and squash strands them (G-05).
