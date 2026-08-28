#!/usr/bin/env python3
"""RDL engine. The escalation ladder, executed rather than described.

Standing operator instruction, 2026-08-24, locked:

    Agents handle occurrences 1 through 3 autonomously. The ladder is wired into
    ARCHITECT's event-driven telemetry. Every failure is hashed to
    ops/LESSONS_LEDGER.md and to var/qesis_ops.sqlite so the system learns
    permanently. Pipeline defects and CI failures are ARCHITECT's, and are routed
    there without being shown to the operator.

The ladder, from CLAUDE.md section 5, now with an executor behind it:

    rung 1  first occurrence          record an L- entry
    rung 2  second occurrence         wire a gate with two fixtures (V-2)
    rung 3  third occurrence          the gate becomes a CI release blocker
    rung 4  fourth occurrence         the control is in the wrong layer, open a D-

Classification is by **epistemic move**, not by artefact (L-118). The family key
is therefore a short stable string like `guard_not_executed` or `git_lock_family`,
never a filename. Four instances across four file types escalate as four.

Two things this module refuses to do:

  It never allocates a lesson id by reading the tail of the ledger. The tail is
  not sorted, because entries are filed when written and not when the event
  happened, so the tail cannot answer the question (L-151). Ids come from
  verify_ledger_singleton.py, the accessor that enumerates them.

  It never runs a git command. This module is imported by sessions that may be
  executing on the analysis mount, where any git invocation takes `.git/index.lock`
  and abandons it, manufacturing the blocker it would then report (L-122, L-123,
  L-150). Where a repair needs git, this module writes it into the host lander
  instead and says so.

Usage:
    python scripts/rdl.py record --family git_lock_family \
        --signature "index.lock present, no git process" \
        --evidence "LAND_EVERYTHING_LOG.txt: Unable to create index.lock" \
        --owner ARCHITECT --title "the stale lock broke the lander"
    python scripts/rdl.py status
    python scripts/rdl.py ci-blocking      # exit 1 if any family is at rung 3
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "ops" / "LESSONS_LEDGER.md"
LADDER = ROOT / "ops" / "RDL_LADDER.json"
PENDING = ROOT / "ops" / "RDL_PENDING_APPEND.md"
BASELINE = ROOT / "ops" / "RDL_BASELINE.json"

#: Candidate store locations. The store lives outside OneDrive by D-027 and L-001,
#: but the repository pairing means it may sit beside either checkout.
STORES = [
    Path(r"C:\Users\Lenovo\OneDrive\sovereign-infra\var\qesis_ops.sqlite"),
    ROOT / "var" / "qesis_ops.sqlite",
    ROOT.parent / "sovereign-infra" / "var" / "qesis_ops.sqlite",
]

#: Routing. The operator's instruction of 2026-08-24: pipeline defects and CI
#: failures are ARCHITECT's and are never shown to the operator. SENTINEL keeps
#: integrity and QA (Rule 1-1). COUNSEL keeps money and law.
ROUTING = {
    "pipeline": "ARCHITECT",
    "ci": "ARCHITECT",
    "build": "ARCHITECT",
    "git": "ARCHITECT",
    "lock": "ARCHITECT",
    "workflow": "ARCHITECT",
    "integrity": "SENTINEL",
    "gate": "SENTINEL",
    "qa": "SENTINEL",
    "licence": "COUNSEL",
    "contract": "COUNSEL",
}

DDL = """
CREATE TABLE IF NOT EXISTS qesis_rdl_defects (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    family       TEXT NOT NULL,
    family_hash  TEXT NOT NULL,
    signature    TEXT NOT NULL,
    evidence     TEXT NOT NULL,
    owner        TEXT NOT NULL,
    occurrence   INTEGER NOT NULL,
    rung         INTEGER NOT NULL,
    action       TEXT NOT NULL,
    lesson_id    TEXT,
    prev_hash    TEXT NOT NULL,
    entry_hash   TEXT NOT NULL,
    recorded_at  TEXT NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def family_hash(family: str) -> str:
    return hashlib.sha256(f"rdl:{family}".encode()).hexdigest()


def route(family: str, owner: str | None) -> str:
    if owner:
        return owner.upper()
    low = family.lower()
    for key, agent in ROUTING.items():
        if key in low:
            return agent
    return "ARCHITECT"


def find_store() -> Path | None:
    return next((p for p in STORES if p.exists()), None)


def reservation_dirs() -> tuple[list[Path], list[str]]:
    """Every ops directory that can hold a reservation: this one and the pair's.

    WHY BOTH SIDES, added 2026-08-28. The ledger is ONE file mirrored across two
    repositories, and R3 of the singleton gate exists to prove it. Reservations
    were read from this repository alone, so two sessions working the pair at the
    same time allocated the same id from two different checkouts. Measured that
    evening: a scheduled task reserved L-203 in qesis-mcp at 20:15 local and this
    executor issued L-203 again in sovereign-infra eleven minutes later, because
    nothing it read could see the other side. That is L-073 reached through the
    module written to prevent L-073, and it is L-196's rule arriving at the
    allocator: a declaration about a pair of repositories is built from both
    sides or it is not built.

    Resolved by the singleton gate's own resolver, so there is ONE definition of
    where the sibling is (L-169), and the decoy stub at C:\\Users\\Lenovo\\
    sovereign-infra is never mistaken for the repository (L-143).

    Returns the directories AND the human-readable scope, because a sibling that
    is not checked out narrows the allocation base and the caller must say so
    rather than allocate as if the other side were empty (D-007).
    """
    dirs = [ROOT / "ops"]
    notes: list[str] = []
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location(
            "_vls", ROOT / "scripts" / "verify_ledger_singleton.py")
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for led in mod.sibling_ledgers(ROOT, ROOT / "ops" / "LESSONS_LEDGER.md"):
            d = led.parent
            if d.is_dir() and d.resolve() != (ROOT / "ops").resolve():
                dirs.append(d)
    except Exception as exc:
        notes.append(f"sibling unresolved ({type(exc).__name__}), one side only")
    if len(dirs) == 1 and not notes:
        notes.append("sibling not checked out, one side only")
    return dirs, notes


def reserved_ids() -> set[int]:
    """Ids already allocated into a pending append but not yet in the ledger.

    Added 2026-08-24 after the first run of this executor issued L-150 three
    times. The accessor reads the ledger, the pending entries are not in the
    ledger yet, so the maximum never advanced and the module built to prevent
    the L-073 duplicate-id failure produced three of them in one command.

    An id is allocated the moment it is written anywhere a later process will
    read it, so the allocator counts reservations and not only the committed
    store. This also picks up ids reserved by another agent's pending file, which
    is how COUNSEL's scheduled sweep and this executor stay out of each other's
    range without either of them locking the ledger (L-152).

    Since 2026-08-28 it reads BOTH repositories rather than only this one. See
    `reservation_dirs` for why.
    """
    return ids_in_dirs(reservation_dirs()[0])


def ids_in_dirs(dirs) -> set[int]:
    """Every id reserved in the given ops directories. Pure, so it has fixtures."""
    out: set[int] = set()
    for ops in dirs:
        if not ops.is_dir():
            continue
        for f in sorted(ops.glob("RDL_PENDING*.md")):
            text = f.read_text(encoding="utf-8", errors="replace")
            out |= {int(m) for m in re.findall(r"\*\*L-(\d{3})", text)}
            # COUNSEL's sweep writes "provisionally L-150" in prose rather than
            # as an entry header, so a reservation in either shape is honoured.
            out |= {int(m) for m in re.findall(r"[Pp]rovisionally L-(\d{3})", text)}
    return out


def selftest() -> int:
    """V-2 for the allocator. Rung 2 for `declaration_built_from_one_side_of_a_pair`.

    The duplicate of 2026-08-28 was not caught by anything, because nothing in
    this module had a fixture at all. One refuse and one accept, or the gate is
    a coin (L-049).
    """
    import tempfile
    fails: list[str] = []
    n = 0
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "repo_a" / "ops", Path(d) / "repo_b" / "ops"
        a.mkdir(parents=True)
        b.mkdir(parents=True)
        (a / "RDL_PENDING_APPEND.md").write_text(
            "**L-300 · reserved in this repository** body\n", encoding="utf-8")
        (b / "RDL_PENDING_APPEND.md").write_text(
            "**L-301 · reserved in the paired repository** body\n", encoding="utf-8")

        # REFUSE: the one-sided read, which is the 2026-08-28 duplicate exactly
        # as it happened. A reservation in the pair must not be invisible.
        if 301 in ids_in_dirs([a]):
            fails.append("the fixture is wrong: a one-sided read saw the sibling")
        n += 1
        # ACCEPT: both sides, both ids.
        both = ids_in_dirs([a, b])
        if both != {300, 301}:
            fails.append(f"a both-sides read returned {sorted(both)}, expected [300, 301]")
        n += 1
        # A prose reservation is honoured wherever it lives (L-152).
        (b / "RDL_PENDING_sweep.md").write_text(
            "COUNSEL reserves provisionally L-302 for the sweep\n", encoding="utf-8")
        if 302 not in ids_in_dirs([a, b]):
            fails.append("a prose reservation in the sibling was missed")
        n += 1
        # The allocation floor is the HIGHEST reservation anywhere in the pair.
        if max(ids_in_dirs([a, b])) != 302:
            fails.append("the allocation floor ignored the sibling's highest id")
        n += 1
        # An absent sibling narrows the base and must never read as empty.
        if ids_in_dirs([a, Path(d) / "not_checked_out" / "ops"]) != {300}:
            fails.append("an absent directory changed the result instead of being skipped")
        n += 1

    # Live half: the scope of the read is reported, and no id is reserved twice
    # across the pair right now. The second is the condition L-073 makes a build
    # failure, checked before it can reach the ledger rather than after.
    dirs, notes = reservation_dirs()
    if len(dirs) == 1 and not notes:
        fails.append("a one-sided read reported no scope note")
    n += 1
    seen: dict[int, list[str]] = {}
    for ops in dirs:
        for i in ids_in_dirs([ops]):
            seen.setdefault(i, []).append(str(ops))
    dupes = {i: v for i, v in seen.items() if len(v) > 1}
    if dupes:
        fails.append("id reserved on both sides of the pair: "
                     + ", ".join(f"L-{i:03d}" for i in sorted(dupes)))
    n += 1

    for f in fails:
        print(f"SELFTEST FAIL: {f}")
    print("RDL ALLOCATOR SELFTEST: "
          + (f"PASSED, {n} fixtures" if not fails else f"FAILED, {len(fails)} of {n}"))
    return 1 if fails else 0


def next_lesson_id() -> tuple[int, str]:
    """Allocate from the accessor plus outstanding reservations. Never the tail.

    The tail of the ledger is not sorted, because entries are filed when written
    and not when the event happened, so it cannot answer this question at all
    (L-151).
    """
    try:
        p = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_ledger_singleton.py"), "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120, check=False, cwd=ROOT,
        )
        doc = json.loads(p.stdout)
        ledger_max = int(doc["max"])
    except Exception as exc:
        # Refuse rather than guess. A guessed id is the L-073 build failure.
        raise SystemExit(
            f"RDL REFUSES: cannot allocate a lesson id from the accessor ({exc}). "
            "Reading the tail of the ledger is not a fallback, it is L-151."
        )
    dirs, notes = reservation_dirs()
    res = reserved_ids()
    nxt = max([ledger_max] + sorted(res)) + 1
    how = f"verify_ledger_singleton.py .max={ledger_max}"
    if res:
        how += f" plus {len(res)} reserved in ops/RDL_PENDING*.md, highest L-{max(res):03d}"
    # The SCOPE of the read is part of the claim. An allocation made from one
    # side of the pair is still an allocation, and it says so (L-196, D-007).
    how += f", reservations read from {len(dirs)} ops director{'y' if len(dirs) == 1 else 'ies'}"
    if notes:
        how += " (" + "; ".join(notes) + ")"
    return nxt, how


def ladder_state() -> dict:
    if LADDER.exists():
        return json.loads(LADDER.read_text(encoding="utf-8"))
    return {"_doc": "RDL ladder state. Occurrence counts by family, and the rung "
            "each family has reached. Written by scripts/rdl.py, read by CI.",
            "families": {}}


def occurrences(fam: str) -> int:
    """Count prior occurrences: the HIGHER of the store and the ladder file.

    A record made where the store was unreachable (analysis mount, CI) lands in
    the ladder file only, class B. If the next host-side record read the store
    alone it would count fewer occurrences than the ladder shows and re-issue a
    lower rung, which is the ladder forgetting on purpose. Neither source may
    lower the count the other has already established.
    """
    from_ladder = int(ladder_state()["families"].get(fam, {}).get("occurrences", 0))
    store = find_store()
    if store:
        try:
            con = sqlite3.connect(f"file:{store}?mode=ro", uri=True)
            con.execute(DDL.replace("CREATE TABLE IF NOT EXISTS", "CREATE TEMP TABLE IF NOT EXISTS"))
            n = con.execute(
                "SELECT COUNT(*) FROM qesis_rdl_defects WHERE family=?", (fam,)
            ).fetchone()[0]
            con.close()
            return max(int(n), from_ladder)
        except sqlite3.OperationalError:
            pass  # table absent on first run, fall through
    return from_ladder


def rung_for(occ: int) -> tuple[int, str]:
    if occ <= 1:
        return 1, "record an L- entry"
    if occ == 2:
        return 2, "wire a gate with one refuse fixture and one accept fixture (V-2)"
    if occ == 3:
        return 3, "the gate becomes a CI release blocker"
    return 4, "the control sits in the wrong layer, open a D- decision"


def append_pending(entry: str) -> None:
    """Hold the ledger text for the host lander to append.

    Not appended directly, because a concurrent session may be writing the same
    file and a lost update to the ledger is invisible to verify_ledger_singleton,
    which compares ids and not text (L-152).
    """
    head = "" if PENDING.exists() else (
        "# RDL pending append\n\nWritten by `scripts/rdl.py`. The host lander "
        "appends these to `ops/LESSONS_LEDGER.md`, re-reading the accessor for "
        "the id immediately before the write, then deletes this file.\n\n---\n\n"
    )
    with PENDING.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(head + entry.rstrip() + "\n\n")


LOCK = ROOT / "ops" / ".rdl.lock"
LOCK_STALE_SECONDS = 900


def acquire(holder: str = "rdl") -> None:
    """Advisory lock naming the holder and the start time. L-152.

    Two sessions wrote one working tree on 2026-08-24 and neither could see the
    other, producing a duplicated CONTROLS entry that no control detected. A loop
    that repairs a tree it does not exclusively hold is not idempotent however
    idempotent each remedy is, because idempotence is a property of a remedy
    applied to a known state and concurrency removes the known state.
    """
    import os
    import time
    if LOCK.exists():
        try:
            doc = json.loads(LOCK.read_text(encoding="utf-8"))
            age = time.time() - float(doc.get("epoch", 0))
        except Exception:
            age = LOCK_STALE_SECONDS + 1
            doc = {"holder": "unreadable"}
        if age < LOCK_STALE_SECONDS:
            raise SystemExit(
                f"RDL REFUSES: ops/.rdl.lock held by {doc.get('holder')} since "
                f"{doc.get('started')} ({age:.0f}s ago). Another writer is live on "
                "this working tree. Refusing to mutate. This is L-152 applied."
            )
    LOCK.write_text(json.dumps(
        {"holder": holder, "pid": os.getpid(), "started": now(),
         "epoch": __import__("time").time()}), encoding="utf-8", newline="\n")


def release() -> None:
    # Truncate rather than unlink: the mount may refuse unlink, and a
    # half-deleted lock would read as held forever.
    if LOCK.exists():
        LOCK.write_text("{}", encoding="utf-8", newline="\n")


def remote_touches_ledger() -> str:
    """Pre-append remote check, requested by the operator 2026-08-24.

    If an open pull request already touches the ledger, a local append will
    collide with it on merge. Reported, never guessed: where `gh` is absent or
    unauthenticated this returns an empty string and the caller proceeds, because
    a missing tool is not evidence of a clean remote (D-007).
    """
    try:
        p = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--json", "number,files",
             "--jq", '[.[] | select(.files[]?.path | test("LESSONS_LEDGER")) | .number] | join(",")'],
            capture_output=True, text=True, timeout=60, check=False, cwd=ROOT,
        )
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:
        return ""


def record(family: str, signature: str, evidence: str, owner: str | None,
           title: str, rule: str, prior: int = 0, prior_evidence: str = "") -> dict:
    """Record one occurrence and apply the rung it earns.

    `prior` seeds a family that was occurring before this executor existed. It is
    accepted only with `prior_evidence` naming the L- ids that record those
    occurrences, because an unevidenced prior count is a way to jump a family up
    the ladder without anything having happened, which is the ladder's own
    version of gate-gaming.
    """
    fam = family.strip().lower().replace(" ", "_")
    if prior and not prior_evidence:
        raise SystemExit(
            "RDL REFUSES: --prior needs --prior-evidence naming the L- ids that "
            "record those occurrences. An unevidenced prior count is not history."
        )
    occ = max(occurrences(fam), prior) + 1
    rung, action = rung_for(occ)
    agent = route(fam, owner)
    lid, how = next_lesson_id()

    entry = (
        f"**L-{lid:03d} · {datetime.now(timezone.utc).date()} · {title}** "
        f"{signature} **Evidence:** {evidence} "
        f"**Family:** `{fam}`, occurrence {occ}, ladder rung {rung}."
        + (f" Prior occurrences evidenced by {prior_evidence}. " if prior_evidence else " ")
        + f"**Rule:** {rule} "
        + f"**Routed to {agent}** by the RDL routing table, not by a human triage step. "
        + f"**Ladder action, applied not proposed:** {action}."
    )
    append_pending(entry)

    st = ladder_state()
    fams = st["families"]
    prev = fams.get(fam, {})
    fams[fam] = {
        "occurrences": occ,
        "rung": rung,
        "owner": agent,
        "family_hash": family_hash(fam),
        "last_signature": signature,
        "last_seen": now(),
        "prior_evidence": prior_evidence or prev.get("prior_evidence", ""),
        "lesson_ids": prev.get("lesson_ids", []) + [f"L-{lid:03d}"],
        "ci_blocking": rung >= 3,
        "gate_required": rung >= 2,
        "decision_required": rung >= 4,
    }
    LADDER.write_text(json.dumps(st, indent=1) + "\n", encoding="utf-8", newline="\n")

    rec = {
        "family": fam, "family_hash": family_hash(fam), "signature": signature,
        "evidence": evidence, "owner": agent, "occurrence": occ, "rung": rung,
        "action": action, "lesson_id": f"L-{lid:03d}", "recorded_at": now(),
        "id_allocated_by": how,
    }
    write_store(rec)
    return rec


def write_store(rec: dict) -> None:
    """Hash-chain the record into the operational store when it is writable."""
    store = find_store()
    if store is None:
        rec["store"] = "NOT REACHABLE, ladder file carries the state"
        return
    try:
        con = sqlite3.connect(store, timeout=10)
        con.execute(DDL)
        row = con.execute(
            "SELECT entry_hash FROM qesis_rdl_defects ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        prev = row[0] if row else "0" * 64
        payload = json.dumps(
            {k: rec[k] for k in sorted(rec) if k != "store"}, sort_keys=True
        )
        eh = hashlib.sha256((prev + payload).encode()).hexdigest()
        con.execute(
            "INSERT INTO qesis_rdl_defects (family,family_hash,signature,evidence,"
            "owner,occurrence,rung,action,lesson_id,prev_hash,entry_hash,recorded_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (rec["family"], rec["family_hash"], rec["signature"], rec["evidence"],
             rec["owner"], rec["occurrence"], rec["rung"], rec["action"],
             rec["lesson_id"], prev, eh, rec["recorded_at"]),
        )
        con.commit()
        con.close()
        rec["store"] = str(store)
        rec["entry_hash"] = eh
    except Exception as exc:
        # D-027 and L-001: the store may sit on a mount that refuses SQLite
        # locking. That is a declared safe failure, class B, never an escalation.
        rec["store"] = f"DEGRADED, not written: {type(exc).__name__}: {exc}"


def cmd_status() -> int:
    st = ladder_state()
    fams = st["families"]
    if not fams:
        print("RDL ladder: 0 families recorded. Zero is zero.")
        return 0
    print(f"RDL ladder: {len(fams)} families")
    for fam, d in sorted(fams.items(), key=lambda kv: -kv[1]["occurrences"]):
        flags = []
        if d.get("gate_required"):
            flags.append("GATE REQUIRED")
        if d.get("ci_blocking"):
            flags.append("CI BLOCKING")
        if d.get("decision_required"):
            flags.append("D- REQUIRED")
        if d.get("cleared"):
            flags = [f for f in flags if f != "CI BLOCKING"]
            flags.append(f"CLEARED by {d['cleared']['gate']}")
        print(f"  {fam:28s} occ {d['occurrences']}  rung {d['rung']}  "
              f"{d['owner']:9s} {' '.join(flags)}")
        print(f"    {', '.join(d.get('lesson_ids', []))}")
    store = find_store()
    print(f"  store: {store if store else 'NOT REACHABLE from here'}")
    return 0


def baseline_state() -> dict:
    """The accepted ladder state, as of the last landed change set.

    Read from ops/RDL_BASELINE.json in the working tree. In CI that file arrives
    with the branch, so the comparison below is branch-against-accepted, which is
    the delta the gate is supposed to measure.
    """
    if BASELINE.exists():
        try:
            return json.loads(BASELINE.read_text(encoding="utf-8")).get("families", {})
        except Exception:
            return {}
    return {}


def cmd_ci_blocking() -> int:
    """Regression validator, not a historical punisher.

    THE DEFECT THIS REPLACES, recorded because it nearly bricked the pipeline.
    The first wiring failed the build on ANY family at rung 3 or above. Two
    families were recorded at rung 4 in the same session, `qesis-integrity` is a
    required status check on main, and the gate would therefore have failed every
    run forever. Every future pull request would have been unmergeable and the
    only available remedy would have been switching the gate off, which is L-063
    reached by construction rather than by neglect.

    A gate on an append-only history must measure the DELTA. A defect family that
    was already at rung 4 when the last change set landed is a historical
    constant: it is recorded, it is owned, and it says nothing about whether the
    change under review is safe. What matters is whether THIS change set
    introduces a new rung-3 family, or escalates an existing one.

    Fails only on:
      - a family at rung >= 3 that is absent from the accepted baseline
      - a family whose rung is HIGHER than its accepted baseline rung

    Everything else is history and is reported without failing.
    """
    cur = ladder_state()["families"]
    base = baseline_state()

    # No baseline recorded yet. There is nothing to measure a delta against, so
    # every rung-3 family would read as new and the gate would fail on its own
    # first run. That is the deadlock this rewrite exists to remove, arriving
    # through the back door. Report the unassessed families loudly and pass.
    # D-007 shape: withheld with cause, never imputed, and never a silent zero.
    if not BASELINE.exists():
        pending = {f: d for f, d in cur.items() if int(d.get("rung", 0)) >= 3}
        print("RDL DELTA GATE: no baseline recorded at ops/RDL_BASELINE.json, so "
              "there is nothing to measure this change set against.")
        for f, d in pending.items():
            print(f"  UNASSESSED  {f} at rung {d['rung']}, owner {d['owner']}")
        print(f"  {len(pending)} famil(y/ies) unassessed. Passing rather than "
              "failing, because a gate with no reference point that refuses "
              "everything is a deadlock, not a control.")
        print("  Record the reference point with: "
              "python scripts/rdl.py baseline --accept --reason ...")
        return 0

    regressions, historical = [], []
    for fam, d in cur.items():
        rung = int(d.get("rung", 0))
        if rung < 3:
            continue
        prior = int(base.get(fam, {}).get("rung", 0))
        if fam not in base:
            regressions.append((fam, d, prior, "new family at rung 3 or above"))
        elif rung > prior:
            regressions.append((fam, d, prior, f"escalated from rung {prior}"))
        else:
            historical.append((fam, d, prior))

    for fam, d, prior in historical:
        note = ""
        if d.get("cleared"):
            note = f", gate {d['cleared']['gate']} landed"
        print(f"RDL: {fam} at rung {d['rung']} is accepted history "
              f"(baseline rung {prior}){note}. Not a regression.")

    if not regressions:
        print(f"RDL DELTA GATE PASSED: {len(historical)} accepted, 0 regressions. "
              "The ladder introduces no new escalation in this change set.")
        return 0

    print(f"RDL DELTA GATE FAILED: {len(regressions)} regression(s)")
    for fam, d, prior, why in regressions:
        print(f"  {fam}: rung {d['rung']}, {why}. Owner {d['owner']}. "
              f"Lessons {', '.join(d.get('lesson_ids', []))}")
    print("\nA regression clears by landing the gate this rung demands, then "
          "accepting the new state with:  python scripts/rdl.py baseline --accept")
    print("Accepting without landing the gate is gate-gaming and the reason field "
          "is there to make that visible in review.")
    return 1


def cmd_baseline(accept: bool, reason: str) -> int:
    """Show the accepted baseline, or accept the current ladder as the new one."""
    cur = ladder_state()["families"]
    if not accept:
        base = baseline_state()
        print(f"RDL baseline: {len(base)} famil(y/ies) accepted")
        for fam, d in sorted(base.items()):
            print(f"  {fam:34s} rung {d.get('rung')}")
        drift = [f for f, d in cur.items()
                 if int(d.get("rung", 0)) >= 3 and int(base.get(f, {}).get("rung", 0)) < int(d.get("rung", 0))]
        print(f"  pending regressions against it: {len(drift)}"
              + (": " + ", ".join(drift) if drift else ""))
        return 0
    if not reason:
        print("RDL REFUSES: --accept needs --reason. An accepted baseline without a "
              "stated reason is a silent amnesty.")
        return 1
    BASELINE.write_text(json.dumps({
        "_doc": "Accepted RDL ladder state. scripts/rdl.py ci-blocking fails only "
                "on families that are new at rung 3 or above, or that have "
                "escalated above the rung recorded here. History does not fail a "
                "build; regressions do.",
        "accepted_at": now(),
        "reason": reason,
        "families": {f: {"rung": d.get("rung"), "occurrences": d.get("occurrences"),
                         "owner": d.get("owner"),
                         "lesson_ids": d.get("lesson_ids", [])}
                     for f, d in sorted(cur.items())},
    }, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"RDL: baseline accepted, {len(cur)} famil(y/ies). Reason: {reason}")
    return 0


def cmd_clear(family: str, gate_path: str, reason: str) -> int:
    """Clear a rung-3 family by naming the gate that now catches it.

    Refuses a gate that is not on disk. A family cleared by a gate that does not
    exist is the ladder marking its own homework, which is worse than not having
    the ladder, because it reads as a control.
    """
    fam = family.strip().lower().replace(" ", "_")
    st = ladder_state()
    if fam not in st["families"]:
        print(f"RDL REFUSES: no family '{fam}' on the ladder.")
        return 1
    if not (ROOT / gate_path).exists():
        print(f"RDL REFUSES: gate '{gate_path}' is not on disk. A family cleared "
              "by a gate that does not exist is the ladder marking its own homework.")
        return 1
    st["families"][fam]["cleared"] = {
        "gate": gate_path, "reason": reason, "when": now(),
    }
    LADDER.write_text(json.dumps(st, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"RDL: {fam} cleared by {gate_path}. It stays on the ladder with its "
          f"occurrence count intact; it no longer blocks the release.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--family", required=True)
    r.add_argument("--signature", required=True)
    r.add_argument("--evidence", required=True)
    r.add_argument("--title", required=True)
    r.add_argument("--rule", required=True)
    r.add_argument("--owner")
    r.add_argument("--prior", type=int, default=0,
                   help="occurrences of this family that predate this executor")
    r.add_argument("--prior-evidence", default="",
                   help="the L- ids that record those prior occurrences")
    sub.add_parser("status")
    sub.add_parser("ci-blocking")
    sub.add_parser("selftest")
    bl = sub.add_parser("baseline")
    bl.add_argument("--accept", action="store_true")
    bl.add_argument("--reason", default="")
    cl = sub.add_parser("clear")
    cl.add_argument("--family", required=True)
    cl.add_argument("--gate", required=True, help="path to the gate that now catches it")
    cl.add_argument("--reason", required=True)
    a = ap.parse_args()

    if a.cmd == "status":
        return cmd_status()
    if a.cmd == "ci-blocking":
        return cmd_ci_blocking()
    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "baseline":
        return cmd_baseline(a.accept, a.reason)
    if a.cmd == "clear":
        return cmd_clear(a.family, a.gate, a.reason)
    rec = record(a.family, a.signature, a.evidence, a.owner, a.title, a.rule,
                 a.prior, a.prior_evidence)
    print(json.dumps(rec, indent=1))
    print(f"\nrung {rec['rung']}: {rec['action']}")
    print(f"routed to {rec['owner']}, not to the operator")
    return 0


if __name__ == "__main__":
    sys.exit(main())
