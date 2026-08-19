# Handoff, 2026-08-15: land the change set, and verify what I could not

**COUNSEL. Read section 0 before running anything.**

---

## 0. What is verified and what is not

The sandbox shell wedged partway through this session, three identical
`process already running` failures, and I stopped rather than retry into a
fourth. That divides the work in two and the division is the point of this
section.

| Item | State | Evidence |
|---|---|---|
| PUB-1 percolation block | **verified** | `build_percolation_block.py --check` returned OK |
| KG-1 graph fixtures | **verified** | `test_gate.py` 44/45, accept plus three refuse |
| EMO-1 verdict restatement | **verified** | graph rebuilt, live verdict read from evidence |
| `verify_index` / `verify_chain` / pairing | **verified** | 30 checks, 752 entries, tail agrees |
| **KG-5 plane** | **WRITTEN, NOT RUN** | shell died before `build_graph.py` executed |
| **AUDIT-1 restatement** | written, verifiable by reading | no execution required |
| **MAP-1** | **not started** | see section 4 |

KG-5 is untested code. Under V-2 an unrun gate is a claim merely asserted, and
under L-118 family A a guard never executed against the state it would meet is
the single most repeated defect in this ledger. I am not going to write the
fourth instance of it into a handoff and call it done. Section 2 is the command
that settles it, and it must run before the commit in section 1, not after.

---

## 1. Verify KG-5, then commit

Run this first. If it fails, fix or revert KG-5 and commit the rest.

```powershell
cd C:\Users\Lenovo\qesis-mcp
python scripts\build_graph.py
python scripts\test_gate.py
python scripts\build_percolation_block.py --check
python scripts\verify_index.py
```

Expected, and each is falsifiable:

- `build_graph.py` prints 68 nodes and 175 edges. The counts must not move.
  KG-5 adds a declaration and a refusal, not an edge.
- `test_gate.py` reports **45/46**, one more than yesterday's 44/45, with the
  new line `caught: graph: physical edge resolves to a provenance kind`.
- The persistent single failure is `contract: verifier cannot run, server.py
  does not import: ModuleNotFoundError`. That is the local environment lacking
  `mcp` and `pydantic`. CI installs `requirements.txt` before the gates. It is
  not a defect and it has been checked against its clause (V-3).

If `test_gate.py` reports 44/46 rather than 45/46, the new fixture is not
catching and KG-5 is wrong. Do not commit it. The likely cause is that
`PROVENANCE_KINDS` does not match the kinds actually emitted; the graph emits
`CableSourceDataset`, `Vintage` and `WithholdingCause`, and those are the three
declared.

### The commit

```powershell
cd C:\Users\Lenovo\qesis-mcp
git status --short
git add .gitignore CLAUDE.md `
        .github\workflows\qesis-integrity.yml `
        data\axes\emodnet_cse_evidence.json data\qesis_graph.json `
        data\qesis_percolation.json `
        ops\LESSONS_LEDGER.md ops\D-112_RDL_TAXONOMY_ADR.md `
        ops\SCOUT_INTAKE_2026-08-15_UN_COMTRADE_SDI.md `
        ops\DEPLOYMENT_AUDIT_2026-08-02.md `
        ops\HANDOFF_2026-08-15_LAND_AND_VERIFY.md `
        scripts\build_graph.py scripts\build_percolation_block.py `
        scripts\test_gate.py
git commit -m "feat(PUB-1,KG-1,KG-5,EMO-1): publish percolation, land graph fixtures, plane the ontology

PUB-1. data/qesis_percolation.json publishes the cable percolation finding,
read from data/axes/cse_percolation.json and recomputing nothing. Porthcurno
severs 278 cities at removal 13; targeted 0.3465 against random 0.6732 at the
same 13 removals. The single-step severance and the half-collapse threshold at
removal 19 are published as the separate quantities they are. Three limitations
and a falsifier travel with it. Sibling artefact, so index_sha256 does not move
and no vintage bumps (L-117).

KG-1. Four fixtures in test_gate.py::check_graph, one accept and three refuse.
build_graph.py --check wired into qesis-integrity.yml. The docstring that named
these fixtures for two revisions is now falsifiable by grep.

KG-5. EDGE_SCHEMA declares a plane per edge type: physical, provenance,
analytic. validate() refuses a physical edge whose RESOLVED endpoint is a
provenance kind, which is the case domain and range cannot catch. Fifth fixture.

EMO-1. The EMODnet evidence file carried its withdrawn verdict in the top-level
field with the supersession nested inside it, and two consumers served the
retracted claim. Verdict restated live, previous retained, no number changed.
build_graph.py now reads the verdict rather than retyping it.

D-112. ADR opened by L-118, fourth rung: classify RDL defects by epistemic move
under an availability test. Proposed, unsigned. No agent signs.

SCOUT intake on UN Comtrade for the SDI axis. Coverage clears BIG. The binding
finding is architectural: single-version policy, no archive of earlier releases,
against an index that pins every source by SHA and invites re-derivation.

AUDIT-1 restated, not closed. ACTIVE is a property of a connection.

Refs L-055 L-054 L-117 L-118 D-110 D-112"
git push -u origin feat/d110-kg-rev-b
```

### Assert the landing, per L-080

Do not proceed on a green push message.

```powershell
cd C:\Users\Lenovo\qesis-mcp
git fetch origin
$local  = git rev-parse HEAD
$remote = git rev-parse origin/feat/d110-kg-rev-b
if ($local -eq $remote) { Write-Host "LANDED $local" -ForegroundColor Green }
else { Write-Host "NOT LANDED local=$local remote=$remote" -ForegroundColor Red }
```

---

## 2. SI-1: the host-side check no agent can run

```powershell
Get-ChildItem C:\Users\Lenovo\sovereign-infra -Force | Select-Object Name, Length | Format-Table
cd C:\Users\Lenovo\sovereign-infra ; git rev-parse --abbrev-ref HEAD ; git log --oneline -3
```

Three outcomes and they are not the same:

1. **Files present.** The mount was stale. Nothing is wrong with the repository
   and SI-1 closes as a mount artefact.
2. **Empty and `.git` present.** A checkout emptied the working tree. `git
   restore .` recovers it.
3. **Empty and no `.git`.** The local clone is gone. The remote still resolves
   `sovereign_infra_commit 7a9da8c6` through `verify_vintage_pairing`, so
   `git clone` recovers it, and the only loss is anything uncommitted.

Do not let me guess between these. I read it empty at the mount and that is a
measurement about the mount, not about the repository (L-104).

---

## 3. D-112: sign or refuse

`ops/D-112_RDL_TAXONOMY_ADR.md`. Three options, recommendation is Option B,
classify by epistemic move under the availability test: the entry must name the
specific command that was available and not run, or it moves to the control-gap
track. Option C is rejected because a second authoritative taxonomy without a
precedence rule is the D-103 / CONC-1 / R1.28 / EMO-1 pattern volunteered.

Two decisions, not one:

1. Accept, refuse, or amend the taxonomy change.
2. Rule on the `D-` namespace drift. `citation_concordance.id_namespace`
   declares D-001 to D-099 as decisions and D-101 upward as v6.6-lineage
   defects, while D-108 through D-112 are decisions sitting in the defect range.
   Either the rule is amended to match practice, or the four are renumbered.
   Renumbering breaks citations, so amending the rule is the cheaper correct
   answer, and it should say why the ranges stopped meaning what they said.

No agent signs a `D-`.

---

## 4. MAP-1: specified, not written

`data/DATA_MAP.json` records absolute roots under
`/sessions/trusting-brave-fermat/mnt/`, which resolve in exactly one session.
The map is declared `read_before` any statement containing missing, absent or
unreachable, and it cannot support those statements from any other session. The
control built to remedy L-104 and L-105 carries the L-104 defect.

Not written this session, deliberately. I already have one untested change in
this set and adding a second while the shell is down would put two unrun
controls in one commit.

**Specification for ARCHITECT:**

1. `scripts/build_data_map.py` stores paths **relative to the repository root**
   and drops the absolute `roots` block, or keeps it clearly marked as
   informational and generator-local.
2. The reader resolves the root at read time from its own location.
3. A build-time assertion refuses any recorded path matching `/sessions/` or a
   session identifier, with two fixtures: one path it must refuse and one it
   must accept. Without the assertion this recurs the first time a generator
   runs somewhere new, which is how it happened.

---

## 5. Standing, unchanged

`main` is Human-on-the-Loop. This branch is `feat/*`, so the pre-push hook
permits it. An agent may merge a paired remediation pull request by `gh pr merge
--rebase` once checks pass, never squash, because squash strands the hashes the
lineage register cites. Promotion to production is a human act and no amendment
reaches it. Nothing in this change set touches `data/qesis_v8.json`, so
`index_sha256` does not move and **no promotion is required**.
