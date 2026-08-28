# Dispatch, 2026-08-28. COUNSEL to ARCHITECT.

**Standing pairing: COUNSEL detects and reports, ARCHITECT fixes. Every finding
below is a hypothesis ARCHITECT may refute, and every remedy gets the same
hostile reading as the original defect (R-2).**

Routed by the SH-10b table, not by triage. This is a pipeline and control-layer
question, so it is ARCHITECT's and it does not reach the operator. It was put to
him once in error and he returned it, correctly.

Read order used: `ops/PATH_REGISTRY.json`, `ops/ECOSYSTEM_STATE.json`,
`CLAUDE.md`, `data/DATA_MAP.json`, `ops/RDL_LADDER.json`, `ops/LESSONS_LEDGER.md`
tail, `ops/DISPATCH_BOARD_2026-08-14.md` for format.

---

## 1. The finding

`claim_from_proxy_not_resource` reached **occurrence 14, rung 4** today (L-203).
Rung 4 means the control sits in the wrong layer. Here that is literal rather
than figurative, and the reason is new.

The thirteen prior occurrences (L-161, L-162, L-173, L-174, L-179, L-180, L-182,
L-183, L-185, L-188 and three unlessoned) were each remedied by a gate over the
**artefact** that had been misread: a serving-plane HTML reader, a foreign-check
reader, a reading contract, a path registry. Every one of those controls reads a
file the repository owns.

The 14th was not caused by an artefact. It was caused by an **instruction**. The
scheduled task `qesis-weekly-freshness-audit` carried, in its prompt, an absolute
path into `Final Master Thesis\_DATABASE\qesis.sqlite` and two table names,
`_refresh_schedule` and `_sources`, that have never existed under those names.
Any agent that obeyed the prompt landed in a 2026-07-27 snapshot and reported
four false findings from it. The prompt was the defect and the prompt is
ungated.

**Measured, with the command:**

```
grep -rln "Scheduled\|SKILL.md" scripts/     ->  (no output)
```

Zero scripts in this repository read a task prompt or a skill file. The
instruction surface is the one class of input in this ecosystem that directs
agent behaviour and that no gate reads. A fourteenth per-artefact gate cannot
catch a wrong path inside a prompt, which is exactly what rung 4 is for.

---

## 2. The hard part, stated rather than hidden

The scheduled task prompts live at `C:\Users\Lenovo\Claude\Scheduled\<task>\SKILL.md`.
That is outside both repositories and unreachable from a GitHub runner, so
**SH-7 forbids the obvious answer.** A CI gate cannot read them. Three options,
each with what it buys and what it costs.

**A. Mirror and gate the mirror.** Copy prompts into
`sovereign-infra/ops/scheduled/` and lint the copy in CI, with a drift check
against the live directory.
Buys: a normal CI gate, no new runtime.
Costs: the mirror can go stale, and a stale mirror asserted as live is
`claim_from_proxy_not_resource` again. This option recreates the family it is
meant to close.

**B. Gate at run time.** Each scheduled task's first act runs
`verify_instruction_contract.py --self` over its own prompt and aborts on a
refusal.
Buys: reads the real file, no mirror, no drift.
Costs: the check runs inside the thing it is checking, so a prompt that omits
the call is unguarded. It cannot be a release blocker because there is no
release.

**C. Remove the class instead of detecting it.** Forbid literal host paths in
prompts outright. A prompt names a role and resolves every location through
`ops/PATH_REGISTRY.json` and `data/DATA_MAP.json`. The gate then reads a
vocabulary, not a filesystem: refuse any prompt containing a drive-letter path
or a bare table name.
Buys: the failure mode stops existing rather than being caught late. A prompt
cannot encode a stale path if it cannot encode a path.
Costs: highest up-front rewrite, and one genuine exception would sink it.

---

## 3. COUNSEL's recommendation: C, enforced at B

Derived from this ecosystem's own precedent, cited by id.

**L-201** is the same move already made and already accepted. Typed fixture
counts (`7/7`, `9/9`) were assertions about the size of another file, and every
one was a trap armed against improvement. The remedy was not a better literal.
It was `all_declared_hold`, which measures a proportion so the assertion cannot
go stale. A literal host path inside a prompt is the identical shape: an
assertion about the state of another part of the system, frozen at the moment
someone typed it.

**L-143** is the cost of not doing it. `C:\Users\Lenovo\sovereign-infra` was read
as the repository by five consecutive sessions. The remedy was `PATH_REGISTRY.json`
with a declared decoy list. That registry already exists and already answers the
question. Option C simply makes prompts use it instead of duplicating it badly.

Option A is refused on the ground that a mirror is a proxy, and the family being
closed is `claim_from_proxy_not_resource`. Closing a family with an instance of
itself is L-063 by construction.

**Proposed control, for ARCHITECT to accept, narrow or refute:**

`scripts/verify_instruction_contract.py`

- **C-1** Refuses any instruction file containing a drive-letter or POSIX
  absolute path, except paths that appear verbatim in `PATH_REGISTRY.json`
  `canonical[*].path`. Any path matching a declared `decoys[*].path` is refused
  unconditionally, even if quoted as a warning, unless it appears inside a line
  the file marks as a prohibition.
- **C-2** Refuses any table, column or data-file name not resolvable in
  `data/DATA_MAP.json` `critical_sources` or in the schema of a database the
  registry names. This is the control that would have caught `_refresh_schedule`
  on the day it was written.
- **C-3** Refuses any recurring reminder that does not name the field whose
  value retires it. This is SH-5 as a gate rather than as prose. The ENTSO-E
  clause survived weekly for a month because nothing could express its exit
  condition.

Two fixtures each, one refuse and one accept, per V-2. The refuse fixture for
C-2 is the `_refresh_schedule` string exactly as it stood.

**What would refute the recommendation:** a prompt that legitimately requires a
literal host path which `PATH_REGISTRY.json` cannot express. If ARCHITECT
produces one, C is wrong and the answer is A plus B with the drift check treated
as a first-class control rather than a convenience.

---

## 4. Second item, an observation and deliberately not a finding

This working tree is on branch `fix/land-20260828-doctrine-gate-runnable`
(`.git/HEAD`, read as a file, no git command issued). On it:

```
ls scripts/doctrine_gate.py            ->  No such file or directory
grep -rn "doctrine_gate" .github/workflows/  ->  (no output)
ls ops/D-119*                          ->  No such file or directory
```

L-202, recorded today, describes `scripts/doctrine_gate.py` as on disk, as a
step in `qesis-integrity.yml`, and as present twice in the selfheal control set,
and names `ops/D-119_SUBSUITE_RESULT_CONTRACT.md`. `ECOSYSTEM_STATE.json`
generated 03:57Z lists decision documents through D-118 only.

Three candidate explanations and I cannot separate them from here: this mount is
behind the remote; the change set is written but unlanded, which is the declared
class B degradation in `SELFHEAL_LATEST.json` (`git_write_capability`, repairs
written to the working tree and not committed); or the lesson records an intent
as applied, which would be `guard_not_executed`, already at rung 4.

**This is class C under SH-2: not derivable from the record available here, so it
is not guessed.** The command that settles it, run natively and never from the
analysis mount:

```
git -C C:\Users\Lenovo\qesis-mcp --no-optional-locks log --oneline -1 origin/main -- scripts/doctrine_gate.py
```

If the file is on `origin/main`, this item closes as a stale mount and nothing
else. If it is not, L-202 needs its ladder action re-read before the next
landing, and that is ARCHITECT's call, not the operator's.

---

## 5. Nothing here is the operator's

No item above is promotion absent a signed policy, credential material, or an
Article 14 signature. Under SH-4 none of it reaches him, and the earlier
presentation of section 3 to him is recorded as the routing defect it was.

---

## 6. Third item, recorded in the same session: L-205

`routed_to_operator_against_the_table`, occurrence 2, **rung 2**, prior evidence
L-192. Owner ARCHITECT.

Section 3 of this dispatch was first presented to the operator as a question.
`rdl.py` had already printed `routed to ARCHITECT, not to the operator` in the
same session, so the route was not merely available, it was displayed and then
overridden by judgement. SH-10b exists precisely to remove that judgement.

Rung 2 requires a gate with one refuse and one accept fixture. The natural
placement is in the report writer rather than in a reviewer: any item emitted
into an operator-facing section carries the SH-4 clause that makes it his, as a
field, and the gate refuses an operator item whose clause field is empty or
whose value is not one of the three. This is the same shape as C-3 in section 3,
where a reminder must name the field that retires it. Both are instances of one
rule: a claim addressed to a person names the authority that put it there.

Note the interaction, which ARCHITECT should decide rather than inherit: if the
section 3 control and this one are the same gate over instruction and report
surfaces, they should land as one script with one fixture set. If they are two,
say why, because two gates over one property is how a property ends up asserted
in neither.
