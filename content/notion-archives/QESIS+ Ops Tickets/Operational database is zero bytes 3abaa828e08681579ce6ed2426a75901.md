# Operational database is zero bytes

Closed: 28 July 2026
Evidence: Rebuilt from the versioned CSV layer: 44 tables plus _lineage, 2,511 rows, PRAGMA integrity_check ok, clean close with no journal; live copy at sovereign-infravarqesis.sqlite outside OneDrive, byte-identical snapshot in _DATABASE, both SHA-256 5e8b21b2; registered QES-A0061
Log ref: L-013, L-017, D-027
Opened: 28 July 2026
Owner: ORCHESTRATOR
Ref: OPS-5
Report: 2026-07-28
Severity: SEV2
Source log: Lessons ledger
Status: Closed

Diagnosis corrected. The file was not a dehydrated cloud placeholder: it had zero blocks allocated, a forced read did not hydrate it, and writing SQLite to that path fails with disk I/O error because the sync-backed mount does not honour the locking and rename semantics SQLite requires. Pinning would not have fixed it.

Two orphan journal files quarantined to _DATABASE_quarantine2026-07-28, not deleted.