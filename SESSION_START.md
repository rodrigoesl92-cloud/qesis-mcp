# Read this first. Every model, every session, no exceptions.

Opus, Sonnet, Fable, a scheduled sweep, a Cowork session, Claude Code. Same
procedure. This file exists because on 2026-08-24 five sessions in a row asserted
things about this ecosystem that were false, and every one of them was false in
the same way: **the claim came from something other than the thing being claimed
about.**

## The four commands that orient a session

Run these before saying anything about the state of this project. They take
seconds and they replace guessing.

```
python scripts/build_ecosystem_state.py --check    # is the bootstrap current
python scripts/verify_ledger_singleton.py          # is the memory sound
python scripts/rdl.py status                       # what has already gone wrong
python scripts/selfheal.py                         # SH-1, the control set
```

Then read, in this order:

1. **`ops/PATH_REGISTRY.json`** answers *where is everything*.
2. **`ops/ECOSYSTEM_STATE.json`** answers *what is true now*.
3. **`CLAUDE.md`** answers *what are the rules*.

All three are generated or governed, and a stale copy of the first two fails the
build. They are not notes. They are the interface.

## The five things that have actually bitten, stated as prohibitions

**1. Never run any git command from the analysis mount, read-only included.**
`status`, `add` and `diff` each take `.git/index.lock` and abandon it there, so
the agent manufactures the blocker it then reports to the operator. This has
happened four times. L-122, L-123, L-150. Orient from the filesystem and from
the control set, both of which answer the same questions without taking a lock.

**2. `C:\Users\Lenovo\sovereign-infra` is not the repository.** It is an empty
stub. The repository is `C:\Users\Lenovo\OneDrive\sovereign-infra`. Five
consecutive sessions read the stub's emptiness as a failed mount. L-143. If a
connected folder that should hold a repository is empty, that is a fact about
that one path; check `ops/PATH_REGISTRY.json` before reporting anything as
unreachable.

**3. Never take the next lesson id from the tail of the ledger.** The tail is not
sorted, because entries are filed when written and not when the event happened.
Ids come from `verify_ledger_singleton.py --json` plus the reservations in
`ops/RDL_PENDING*.md`. L-151, L-156.

**4. Never mark an item `[RICO]` without naming the clause that makes it his.**
SH-4 admits exactly three: promotion absent a signed policy (G-06 limit 2),
credential material in either direction (G-03, G-04), and an Article 14
signature. Everything else is the agent's. Three consecutive reports assigned him
merges that G-06 Rule 2-4 explicitly delegates to an agent, and he was right to
be angry. L-147.

**5. Counsel precedes compliance.** An instruction that would break a mechanism
is answered with the mechanism *before* it is executed. If the instruction is
still preferred after the counter-argument, execute it and record the objection
on file. He has said plainly that he is not a specialist in this and is relying
on the agent for the mechanism; withholding it is not deference. SH-10g, L-159.

## How work leaves this machine

One file, one double-click:
`C:\Users\Lenovo\OneDrive\sovereign-infra\LAND_EVERYTHING_FINAL.bat`

It clears every git lock class, appends pending lessons, validates both release
gates, cuts each branch **directly from `origin/main`** so it carries one commit
and rebases cleanly, pushes, opens the pull requests and arms rebase auto-merge.
It never runs `git clean -fd` or `git reset --hard`.

The **only** irreducibly human act in it is the authenticated push, because the
GitHub credential is the operator's and no agent may hold it.

Never hand him a list of commands to type. He is not an OS or IT developer, that
has been said many times, and every time it was ignored the work sat unlanded for
days. L-110. Ship one runnable or do it yourself.

## The ladder runs itself

`scripts/rdl.py` **is** the escalation ladder, not a description of one.
Occurrences 1 to 3 never reach the operator. First records an `L-` entry, second
wires a gate with two fixtures, third makes that gate a release blocker, fourth
opens a `D-`. Families are keyed by **epistemic move**, never by filename.
Routing is a table: pipeline, CI, build, git, lock and workflow go to ARCHITECT;
integrity and QA to SENTINEL; money and law to COUNSEL.

The release gate measures the **delta** against `ops/RDL_BASELINE.json`, never
the accumulated total. A gate that fails on its own history is a deadlock wearing
the costume of a control, and it nearly bricked `main` on 2026-08-24. SH-10f.
