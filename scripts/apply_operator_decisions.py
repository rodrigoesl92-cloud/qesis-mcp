#!/usr/bin/env python3
"""Apply the operator's signed decisions of 2026-08-24 to the operational store.

Runs on the host from the lander. Never on the analysis mount: the store is
SQLite and a write from a filesystem that cannot hold a lock cleanly is the D-027
and L-001 failure, so this refuses rather than corrupting.

Two decisions reach the store. Both were put to the operator as numbered items
with a recommendation, and both were approved verbatim on 2026-08-24.

  Decision 5   79 held Article 14 executions cleared by TWO standing rulings
               rather than 79 signatures. D-053 permits disposal on the
               equivalence class of agent, operation and input_hash, and records
               the ruling_vintage under which the ruling was made.

  Decision 7   ENTSO-E task 1a48c78d closed. The operator confirms access works.
               INC-20260731-01 recorded access provided on 2026-08-01 and the
               task was never closed, which was a status contradiction rather
               than a measurement blocker.

Idempotent. Safe to run twice, because it will be (L-108).

Usage:
    python scripts/apply_operator_decisions.py            # apply
    python scripts/apply_operator_decisions.py --dry-run
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORES = [
    Path(r"C:\Users\Lenovo\OneDrive\sovereign-infra\var\qesis_ops.sqlite"),
    ROOT / "var" / "qesis_ops.sqlite",
    ROOT.parent / "sovereign-infra" / "var" / "qesis_ops.sqlite",
]

SIGNER = "R. Batista Silva"
WHEN = "2026-08-24"
ENTSOE_TASK = "1a48c78d-6bcb-4ffc-aa96-8b1beb3e243f"

#: The two standing rulings. Each names the class it disposes of and the reason,
#: and each carries the canonical vintage it was made under, so D-053 inheritance
#: expiry works exactly as it does for every other ruling.
RULINGS = [
    {
        "agent": "HERALD",
        "action": "artifact_ladder",
        "decision": "APPROVED",
        "reason": (
            "Standing ruling under D-053, signed 2026-08-24. The HERALD "
            "artifact_ladder class is drafting output that stops at the gate and "
            "publishes nothing on its own; publication remains a separate act "
            "under G-06 and is not granted here. The prior ruling read 'regenerate "
            "at v8.2' and expired on the canonical vintage change, which is the "
            "mechanism working rather than failing. Re-issued at the current "
            "canonical vintage on the equivalence class of agent, operation and "
            "input_hash, not on individual rows."
        ),
    },
    {
        "agent": "COUNSEL",
        "action": "triage_contract",
        "decision": "APPROVED",
        "reason": (
            "Standing ruling under D-053, signed 2026-08-24. The COUNSEL "
            "triage_contract class produces a draft for a human professional to "
            "review and grants no authority to execute, spend or bind. The prior "
            "ruling read 'acceptance fixture, not a real contract' and expired on "
            "the canonical vintage change. Re-issued at the current canonical "
            "vintage on the equivalence class."
        ),
    },
]


def find_store() -> Path | None:
    return next((p for p in STORES if p.exists()), None)


def canonical_vintage() -> str:
    """Derived from the artefact that carries it, never hardcoded. L-050."""
    import json
    for cand in ("data/qesis_v8.json", "data/index.json"):
        p = ROOT / cand
        if p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            for k in ("vintage", "canonical_vintage"):
                if isinstance(d, dict) and d.get(k):
                    return str(d[k])
                meta = d.get("meta") or d.get("provenance") or {}
                if isinstance(meta, dict) and meta.get(k):
                    return str(meta[k])
    raise SystemExit(
        "REFUSED: cannot derive the canonical vintage from the served index. A "
        "ruling with a hardcoded or missing vintage cannot expire correctly under "
        "D-053, so it is not written at all."
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    store = find_store()
    if store is None:
        print("REFUSED: the operational store is not reachable from here. "
              "Nothing applied, nothing imputed.")
        return 1

    vintage = canonical_vintage()
    print(f"store: {store}")
    print(f"canonical vintage, derived from the index: {vintage}")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    con = sqlite3.connect(store, timeout=20)
    cur = con.cursor()

    # ---- Decision 5: two standing rulings over 79 held executions ----
    total = 0
    for r in RULINGS:
        held = cur.execute(
            "SELECT COUNT(*) FROM qesis_audit_compliance_log "
            "WHERE hitl_required=1 AND hitl_approved=0 AND agent_name=? AND action_type=?",
            (r["agent"], r["action"]),
        ).fetchone()[0]
        print(f"  {r['agent']} {r['action']}: {held} held")
        total += held
        if a.dry_run or held == 0:
            continue
        # The chain triggers permit an UPDATE that touches only the approval
        # fields. Anything else is rejected by the database itself, which is the
        # Article 12 no-retroactive-rewrite control, and this stays inside it.
        cur.execute(
            "UPDATE qesis_audit_compliance_log SET hitl_approved=1, approved_by=?, "
            "approved_at=?, hitl_decision=?, hitl_reason=?, ruling_vintage=? "
            "WHERE hitl_required=1 AND hitl_approved=0 AND agent_name=? AND action_type=?",
            (SIGNER, stamp, r["decision"], r["reason"], vintage, r["agent"], r["action"]),
        )
        print(f"    ruled {cur.rowcount} row(s) {r['decision']} at {vintage}")

    remaining = cur.execute(
        "SELECT COUNT(*) FROM qesis_audit_compliance_log "
        "WHERE hitl_required=1 AND hitl_approved=0"
    ).fetchone()[0]
    print(f"  held before: {total} in these two classes. Held after, all classes: "
          f"{remaining if not a.dry_run else 'unchanged, dry run'}")
    if remaining and not a.dry_run:
        rows = cur.execute(
            "SELECT agent_name, action_type, COUNT(*) FROM qesis_audit_compliance_log "
            "WHERE hitl_required=1 AND hitl_approved=0 GROUP BY 1,2"
        ).fetchall()
        print("  NOT covered by these two rulings, reported rather than swept:")
        for ag, act, n in rows:
            print(f"    {ag} {act}: {n}")

    # ---- Decision 7: close the ENTSO-E task ----
    row = cur.execute(
        "SELECT status, closed_at FROM qesis_core_tasks WHERE task_id=?", (ENTSOE_TASK,)
    ).fetchone()
    if row is None:
        print(f"  ENTSO-E task {ENTSOE_TASK[:8]}: not found, nothing done")
    elif row[1]:
        print(f"  ENTSO-E task {ENTSOE_TASK[:8]}: already closed at {row[1]}")
    elif a.dry_run:
        print(f"  ENTSO-E task {ENTSOE_TASK[:8]}: would close, status {row[0]}")
    else:
        cur.execute(
            "UPDATE qesis_core_tasks SET status='closed', closed_at=?, "
            "blocker='Closed 2026-08-24 on the operator confirming access works. "
            "INC-20260731-01 recorded access provided 2026-08-01 and the task was "
            "never closed; the 24 day overdue reading was a status contradiction, "
            "not a measurement blocker. ESE draws on ERAA and sits outside the "
            "composite.' WHERE task_id=?",
            (stamp, ENTSOE_TASK),
        )
        print(f"  ENTSO-E task {ENTSOE_TASK[:8]}: CLOSED, {cur.rowcount} row")

    if a.dry_run:
        con.rollback()
        print("DRY RUN: rolled back, nothing written.")
    else:
        con.commit()
        print("COMMITTED.")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
