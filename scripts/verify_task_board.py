"""Refuses a task board that hands the operator work no clause makes his.

L-208. Four rows sat open for a month whose closing condition the record already
proved, and ten of thirteen open rows were addressed to the operator. A board
with no drain is a generator of false findings: a row once written stays true
forever, and every session reads it and hands it back to him.

SH-4 admits exactly three classes to the operator: promotion absent a signed
policy (G-06 limit 2), credential material in either direction (G-03, G-04), and
an Article 14 signature. An open row addressed to him that names none of the
three is routed by the SH-10b table instead, and this gate says so.

assess() is pure over a list of rows so both fixtures run without a database.
Where the store is unreachable the gate degrades rather than escalating, because
a runner checks out one repository and the store is not in it (D-007).

Usage:  python scripts/verify_task_board.py [--selftest]
Exit:   0 board is sound or store unreachable - 1 a row violates SH-4
"""
from __future__ import annotations
import argparse, json, pathlib, sqlite3, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HUMAN = {"RICO", "HUMAN", "OPERATOR"}
SH4 = ("G-06", "G-03", "G-04", "ARTICLE 14", "A14", "PROMOTION", "CREDENTIAL", "SIGNATURE")


def assess(rows: list[dict]) -> list[str]:
    """One finding per open operator row that names no SH-4 clause."""
    findings = []
    for r in rows:
        if (r.get("status") or "").lower() != "open":
            continue
        if (r.get("owner") or "").upper() not in HUMAN:
            continue
        blob = " ".join(str(r.get(k) or "") for k in ("title", "blocker", "origin")).upper()
        if not any(tok in blob for tok in SH4):
            findings.append(
                f"{r.get('ticket_id') or r.get('task_id')}: open and addressed to the "
                f"operator, and names no SH-4 clause. Either name the clause that makes "
                f"it his, or route it by the SH-10b table. "
                f"({(r.get('title') or '')[:70]})"
            )
    return findings


def selftest() -> int:
    must_refuse = [{"ticket_id": "QT-9001", "owner": "RICO", "status": "open",
                    "title": "Install an SDK and authenticate", "blocker": "", "origin": ""}]
    must_accept = [{"ticket_id": "QT-9002", "owner": "RICO", "status": "open",
                    "title": "Sign the held decision", "blocker": "Article 14 signature", "origin": ""},
                   {"ticket_id": "QT-9003", "owner": "ARCHITECT", "status": "open",
                    "title": "anything at all", "blocker": "", "origin": ""}]
    ok = True
    if len(assess(must_refuse)) != 1:
        print("  x FIXTURE 1 FAILED: an unclaused operator row was accepted"); ok = False
    if assess(must_accept):
        print("  x FIXTURE 2 FAILED: a claused row or an agent row was refused"); ok = False
    print(f"TASK BOARD SELFTEST: {'PASSED, 2 fixtures' if ok else 'FAILED'}")
    return 0 if ok else 1


ap = argparse.ArgumentParser()
ap.add_argument("--selftest", action="store_true")
ap.add_argument("--store", type=pathlib.Path, default=None)
args = ap.parse_args()
if args.selftest:
    raise SystemExit(selftest())

store = args.store
if store is None:
    try:
        reg = json.loads((ROOT / "ops" / "PATH_REGISTRY.json").read_text(encoding="utf-8"))
        store = pathlib.Path(reg["canonical"]["operational-store"]["path"])
    except Exception:
        store = ROOT.parent / "sovereign-infra" / "var" / "qesis_ops.sqlite"

if not pathlib.Path(store).exists():
    print(f"TASK BOARD CHECK DEGRADED: store not reachable from here ({store})")
    print("  Class B. The store is in the private repository and a runner checks out one.")
    print("  Reported, not imputed (D-007). Zero rows is not the same as no board.")
    raise SystemExit(0)

con = sqlite3.connect(f"file:{store}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute("select * from qesis_core_tasks")]
con.close()

op = [r for r in rows if (r.get("status") or "").lower() == "open"]
mine = [r for r in op if (r.get("owner") or "").upper() in HUMAN]
print(f"{len(rows)} row(s), {len(op)} open, {len(mine)} addressed to the operator")
findings = assess(rows)
if findings:
    print("\nTASK BOARD CHECK FAILED")
    for f in findings:
        print(f"  x {f}")
    raise SystemExit(1)
print("\nTASK BOARD CHECK PASSED: every open operator row names the clause that makes it his.")
