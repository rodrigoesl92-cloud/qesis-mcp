# Close #66 and #67

Both trace to one cause and are resolved by `183dde1`. Four `gh` commands, and
`gh` behaves identically on Windows and Linux for these calls, which is why it is
the only tool used here (L-139).

```
gh issue comment 66 --body-file ops/issue_replies/close_66_67.md
gh issue close 66 --reason completed

gh issue comment 67 --body-file ops/issue_replies/close_66_67.md
gh issue close 67 --reason completed
```

`--body-file` rather than `--body`, so no shell quoting is involved. The
PowerShell quoting of a multi-paragraph string is a platform-variant behaviour
and has no business in a handover.

## Before closing, one check

The self-heal loop reopens on recurrence rather than duplicating, so closing a
condition that still exists produces a new issue within the hour rather than
silence. Confirm the run on `main` is green first:

Actions tab, `QESIS+ integrity gate`, branch `main`, most recent run.

If it is red, do not close. Open the failing step and paste it. The step name,
the command and the output, not the summary. Guessing from the summary is what
produced three structural fixes that never touched the failing step.
