# Endpoint declaration, made in the Default, not yet propagated

**2026-08-14 · qesis-mcp · branch `claude/ecosystem-default-implementation-91u838`**

## Status, stated plainly

This change was **made in the Default**. It is implemented in `qesis-mcp` only.
It is **not** yet implemented throughout the ecosystem repositories and domains,
and nothing in this repository makes it binding anywhere else. This file exists
so that the gap is a recorded item rather than an assumption that the pattern
spread on its own.

Per L-054, a rule held only in prose has been described, not applied. What
follows below the line is described. What is above it is applied and gated.

## What was applied here

| Artefact | Role |
|---|---|
| `data/endpoints.json` | The single declaration of every outbound MCP endpoint this repository dials |
| `qesis_endpoints.py` | The only sanctioned reader of that declaration |
| `scripts/verify_endpoints.py` | The gate that makes the declaration binding, codes `E1.0`, `E1.1`, `E1.2` |
| `scripts/test_gate.py::check_endpoints` | One fixture the gate must accept, three it must refuse (V-2) |
| `.github/workflows/qesis-integrity.yml` | The gate runs on every push and every pull request |

Two literals were removed from the code path: `infrastructure_mcp.py:7` and
`test_client.py:7`, both `local_endpoint = "http://127.0.0.1:8000/sse"`. The
untracked root file `horizon_endpoint = http127.0.0.1800.txt` was deleted after
its content was migrated into the declaration, including the operator
instruction it carried, which was the half that had been lost.

## The defect, in measured terms

The horizon endpoint existed in three places. Two were identical string literals
in Python modules. The third was an untracked text file at the repository root
and was the only copy that recorded the operating instruction: the port moves
between runs, so the value to use is the one the server prints in the terminal,
not the one written in the source.

`ops/SESSION_REPORT_2026-08-08.md` line 135 listed that file among repository
litter. The listing was correct that the file did not belong at the root. It was
wrong to conclude anything further without opening it, and the effect was that
the instruction it carried was discarded while the two stale literals were kept.

Separating what was true from what was assumed:

- **True.** Three copies of one value existed. One file was misplaced at the root.
- **Assumed.** That a file which looks like litter carries nothing. It carried
  the only statement of how the value is meant to be obtained.

This is the L-089 failure family, one identity declared in several places with
nothing asserting the copies agree, applied to an outbound address rather than
an inbound one. Under the RDL escalation ladder that is the second rung, so the
remedy is a gate with two fixtures rather than a note. It has four.

**Candidate rule, for the canonical ledger:** a value that an operator must
supply at run time is declared once, with its environment variable named beside
its default, and a gate refuses the literal anywhere else. Deleting a stray file
is not the same act as reading it.

## Ledger registration is OUTSTANDING

`ops/LESSONS_LEDGER.md` in this repository is a pointer file and explicitly
refuses appends. Ids are issued by appending to the canonical ledger at
`sovereign-infra/ops/LESSONS_LEDGER.md`, never by counting, and a duplicate `L-`
id is a build failure (L-073).

That repository was **not reachable from this session**, so no id was issued and
none was invented. The lesson above is unregistered. Registering it is the first
propagation item, and until it happens the rule is described here and gated only
in `qesis-mcp`.

## Propagation items

| # | Where | What must happen | Owner |
|---|---|---|---|
| P-1 | `sovereign-infra/ops/LESSONS_LEDGER.md` | Issue the next `L-` id for the rule above. Do not reuse an id and do not count to guess one | ARCHITECT |
| P-2 | `sovereign-infra` | Port `endpoints.json`, the resolver and `verify_endpoints.py`. The evidence plane dials outbound services too, and this gate does not run there | ARCHITECT |
| P-3 | `my-agent/` | Audit for endpoint literals. It carries its own `CLAUDE.md` and `AGENTS.md` and was not covered by this change set | ARCHITECT |
| P-4 | Domains | `data/domains.json` declares inbound identity, `data/endpoints.json` declares outbound. Decide whether they merge into one identity declaration or stay deliberately separate, and record the reason either way | ARCHITECT, then SENTINEL |
| P-5 | Ecosystem CI | The gate is wired into `qesis-integrity.yml` in this repository only. Every repository that dials an MCP endpoint needs it as a required check | SENTINEL |
| P-6 | `ops/SESSION_REPORT_2026-08-08.md` | Annotate line 135. The litter listing is the proximate cause of the instruction being lost and currently reads as a clean disposal | ARCHITECT |

## G-01 pairing

This change touches no vintage, axis definition, provenance or citation
metadata, so Rule 2-1 does not require a paired landing in `sovereign-infra`.
It is recorded as single repository by scope, not by exemption. P-2 remains
open on its own merits: the pattern belongs in both planes, and the reason it is
not there yet is that the session had no access to that repository, which is a
reachability fact and not a design decision.

## What would falsify the claim that this is fixed

Running `python scripts/verify_endpoints.py` from a checkout in which a new
outbound MCP endpoint has been added at a call site, and seeing it pass. The
gate reads `*.py`, `*.ts`, `*.yml` and `*.yaml`. It does **not** read prose, so
an endpoint that exists only in a Markdown runbook or a stray text file at the
root is still invisible to it, which is precisely how this defect began. That
limit is stated rather than closed, and closing it is not part of this change.
