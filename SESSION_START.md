# Read this first. Every model, every session, no exceptions.

> **2026-08-26 handover.** Read `ops/HANDOVER_2026-08-26.md` before anything
> else. It states what is on `main` (PR 76 and PR 41 merged by rebase), what the
> 00:00Z lander run did against what it said, the three defects recorded and
> repaired (L-175 to L-177), and the one file the operator double-clicks:
> `LAND_EVERYTHING_FINAL.bat`, revision 6, which judges itself, reads its
> landing from `LANDING_MANIFEST.json`, carries only the session's delta, and
> ends with the audit. `AUDIT_ECOSYSTEM.bat` measures everything and changes
> nothing. Both live in the `sovereign-infra` root,
> `C:\Users\Lenovo\OneDrive\sovereign-infra`. The 2026-08-24 handover is
> superseded in full.

> **2026-08-26, second change set.** After the 10:27Z landing, one more is
> prepared and not yet landed: `ops/SESSION_2026-08-26_STIR_DIRECTIVE.md`. It
> carries `gh_ops.py runner-merge` (a runner landing merges itself once its
> owned checks are green, G-06 Rule 2-4), **D-117** and **L-180** behind it,
> the three-phase causal surface at `public/blueprint.html`, and the COUNSEL
> record on authorship, copyright and the signature convention. Three things
> are the operator's and only three, each with its clause, in section 5 of that
> file. `LANDING_MANIFEST.json` beside the lander describes this change set.

Opus, Sonnet, Fable, a scheduled sweep, a Cowork session, Claude Code. Same
procedure. This file exists because on 2026-08-24 five sessions in a row asserted
things about this ecosystem that were false, and every one of them was false in
the same way: **the claim came from something other than the thing being claimed
about.**

## Before the four commands: read the dispatch

`ops/DISPATCH.json` is written every morning by a GitHub runner, not by a person
and not on anybody's machine. It carries the verdict, every control with the
command that produced it, and every finding **already routed by the SH-10b table**.

Open it first. Execute the rows that carry your mandate, in the session that reads
them. Occurrences one to three never reach the operator, and the dispatch is where
they go instead. A row addressed to HUMAN that names no SH-4 clause is misrouted by
definition and is yours, not his.

The plain-English half of the same run is `ops/OPERATOR_BRIEF.md`, published to
qesis.eu/status so the operator can read it from a phone in any country with every
machine of his switched off.

## The four commands that orient a session

Run these before saying anything about the state of this project. They take
seconds and they replace guessing.

```
python scripts/build_ecosystem_state.py --check    # is the bootstrap current
python scripts/verify_ledger_singleton.py          # is the memory sound, and in sync with its mirror
python scripts/ledger_sync.py --check              # if not: what differs, and whether a script may repair it
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

It judges itself first (`scripts/verify_lander_contract.py`: the shell parses
nothing, L-176), reads the branch and the messages from `LANDING_MANIFEST.json`
beside it, installs any pending workflow, clears every git lock class, appends
pending lessons, validates both release gates, cuts each branch **directly from
`origin/main`**, carries **only the delta this session made** (`landing_base.py`,
L-177) so a runner's commits on `main` survive the click, pushes, opens the pull
requests, merges by rebase once CI is green, and syncs the disk to `main`. It
never runs `git clean -fd` or `git reset --hard`. A session that prepares a
landing writes the manifest; a lander without one refuses to run.

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
