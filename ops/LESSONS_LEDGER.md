# LESSONS_LEDGER, pointer, not a ledger

**Do not append to this file.**

The canonical Reflective Defect Learning ledger for the whole STIR / QESIS+
ecosystem is:

```
C:\Users\Lenovo\sovereign-infra\ops\LESSONS_LEDGER.md
```

## Why this file is empty of lessons

Until 2026-08-09 this path held an independent ledger. It issued the id
**L-068** to an entry dated 2026-08-03 while the canonical ledger had already
issued **L-068** to a different entry dated 2026-08-01. Two files, one
identifier, two meanings. An RDL store whose primary key collides cannot be
cited and is not memory, only text.

The entry that lived here has been migrated to the canonical ledger and re-issued
as **L-075**, with its origin recorded in the entry itself. The collision and its
rule are recorded as **L-073**.

## The rule this file enforces

Per `CLAUDE.md` §0 Rule P-3 and ledger entry L-073:

- The lesson ledger is single-instance with one named canonical location.
- Any second copy is a pointer file containing the path and nothing else.
- Ids are issued by appending to the canonical file, never by counting.
- A duplicate `L-` id is a build failure, not an editorial matter.

Retrieval order for any agent session is fixed in `CLAUDE.md` §4 Rule G-2:
`Digital Twin R&D/` → `sovereign-infra/ops/` → served surface (`mcp__qesis__*`)
→ open web.
