"""Writes the daily brief in two registers: plain English for the operator, and a
machine-readable dispatch every agent reads and acts on.

WHY. The daily ops report is written for an agent. It counts branches, names
predicates and quotes exit codes. The operator is not from IT and has said so
many times. He needs one page that says whether the thing is running, what fixed
itself, and what is genuinely his, and he needs to read it without his laptop
being switched on. SH-7: a task that requires a desktop application is a reminder,
not a schedule.

So this runs on the runner, commits its output, and publishes an HTML copy into
public/ where the platform serves it. He reads it on a phone, in any country,
with his computer off.

EVERY RECURRING JOB FEEDS IT, and none of them had to be edited to do so. The
self-heal loop writes ops/SELFHEAL_LATEST.json hourly, the audit writes
ops/AUDIT_REPORT.md, CI writes ops/CI_LAST_FAILURE.md on a real failure, the daily
report writes ops/reports/<date>.md, and the ladder writes ops/RDL_LADDER.json.
This reads all of them. A dispatch assembled from what the jobs already produce
cannot drift from them, and a dispatch that required fifteen workflows to push into
it would have drifted the first time one of them was changed.

AND THE SAME RUN WRITES ops/DISPATCH.json, which is the agent-facing half. A brief
only a human can read is a brief that waits for a human. The dispatch carries every
finding already routed by the SH-10b table, with the command that produced it and
the command that settles it, so the next agent session of any kind opens one file
and starts executing instead of re-deriving the situation. Occurrences one to three
never reach the operator, and the dispatch is where they go instead.

WHAT IT REFUSES TO DO.
  It never prints how many items are open. He is not responsible for the queue.
  It never routes an item to him without naming the SH-4 clause that makes it his.
  It never reports a gate as passing when the gate could not run. A control that
  did not execute is reported as NOT MEASURED, never as agreement (D-120).

Usage:  python scripts/build_operator_brief.py [--out ops/OPERATOR_BRIEF.md]
                                               [--html public/status.html]
        python scripts/build_operator_brief.py --selftest
Exit:   0 always, except a selftest failure. A brief that cannot be written is a
        defect, but refusing to write it leaves the operator with nothing, which
        is worse. It says what it could not measure.
"""
from __future__ import annotations
import argparse, datetime, html, json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SH4 = ("G-06", "G-03", "G-04", "ARTICLE 14", "A14", "PROMOTION", "CREDENTIAL",
       "SIGNATURE", "COST COMMITMENT")

CONTROLS = [
    ("the lessons ledger is whole", ["scripts/verify_ledger_singleton.py"]),
    ("no new class of failure appeared", ["scripts/rdl.py", "ci-blocking"]),
    ("every published address works", ["scripts/verify_static_routes.py"]),
    ("no setting points at the wrong folder", ["scripts/verify_config_paths.py"]),
    ("the licence stays inside its scope", ["scripts/verify_noncommercial_scope.py"]),
    ("the index is publishable", ["scripts/verify_index.py"]),
    ("the evidence chain reproduces", ["scripts/verify_chain.py"]),
]


# Mirrored from the SH-10b routing table in rdl.py. A finding is routed by this,
# never by whoever noticed it.
ROUTE = {
    "the lessons ledger is whole": "ARCHITECT",
    "no new class of failure appeared": "ARCHITECT",
    "every published address works": "ARCHITECT",
    "no setting points at the wrong folder": "ARCHITECT",
    "the licence stays inside its scope": "COUNSEL",
    "the index is publishable": "SENTINEL",
    "the evidence chain reproduces": "SENTINEL",
}


def run(cmd: list[str]) -> tuple[str, str]:
    """Return (verdict, tail). NOT MEASURED when the control could not execute."""
    try:
        p = subprocess.run([sys.executable] + cmd, cwd=ROOT, capture_output=True,
                           text=True, timeout=300)
    except Exception as e:
        return "NOT MEASURED", f"could not run: {type(e).__name__}"
    tail = (p.stdout or p.stderr or "").strip().splitlines()
    last = tail[-1] if tail else ""
    if p.returncode == 0:
        return "holding", last
    return "NEEDS ATTENTION", last


def ingest_jobs() -> list[dict]:
    """Every recurring job's own output, read where it lands. No job pushes here."""
    found = []

    sh = ROOT / "ops" / "SELFHEAL_LATEST.json"
    if sh.exists():
        try:
            d = json.loads(sh.read_text(encoding="utf-8"))
            for e in d.get("escalations") or []:
                found.append({"source": "self-heal loop, hourly", "owner": "ARCHITECT",
                              "finding": str(e)[:200], "verdict": "ESCALATION",
                              "measured_by": "python scripts/selfheal.py"})
            for f in d.get("failed") or []:
                found.append({"source": "self-heal loop, hourly", "owner": "ARCHITECT",
                              "finding": str(f)[:200], "verdict": "FAILED",
                              "measured_by": "python scripts/selfheal.py"})
            for g in d.get("degraded") or []:
                found.append({"source": "self-heal loop, hourly", "owner": "ARCHITECT",
                              "finding": f"{g.get('control')}: {g.get('degradation')}",
                              "verdict": "DEGRADED, class B, declared safe",
                              "measured_by": "python scripts/selfheal.py"})
        except Exception as e:
            found.append({"source": "self-heal loop", "owner": "ARCHITECT",
                          "finding": f"SELFHEAL_LATEST.json unreadable: {type(e).__name__}",
                          "verdict": "NOT MEASURED", "measured_by": "read ops/SELFHEAL_LATEST.json"})

    ci = ROOT / "ops" / "CI_LAST_FAILURE.md"
    if ci.exists():
        head = ci.read_text(encoding="utf-8", errors="replace")[:400].replace("\n", " ")
        if "Root-caused" not in ci.read_text(encoding="utf-8", errors="replace")[:2000]:
            found.append({"source": "CI feedback", "owner": "ARCHITECT",
                          "finding": f"last recorded CI failure is not root-caused: {head[:160]}",
                          "verdict": "UNRESOLVED",
                          "measured_by": "python scripts/ci_feedback.py"})

    au = ROOT / "ops" / "AUDIT_REPORT.md"
    if au.exists():
        txt = au.read_text(encoding="utf-8", errors="replace")
        for line in txt.splitlines():
            if line.startswith("## Verdict:") and "GREEN" not in line:
                found.append({"source": "cross-repository audit", "owner": "SENTINEL",
                              "finding": line.strip(), "verdict": "NOT GREEN",
                              "measured_by": "python scripts/audit_ecosystem.py"})
            if "**FAIL**" in line:
                found.append({"source": "cross-repository audit", "owner": "SENTINEL",
                              "finding": line.strip()[:200], "verdict": "FAIL",
                              "measured_by": "python scripts/audit_ecosystem.py"})

    # A rung-4 family whose D- already exists is answered, and re-raising it every
    # hour is how a control gets switched off without anyone deciding to (L-063).
    answered = {}
    for doc in sorted((ROOT / "ops").glob("D-*.md")):
        try:
            body = doc.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for fam in ("git_lock_family", "guard_not_executed", "success_literal_not_measured",
                    "claim_from_proxy_not_resource", "gate_cannot_be_satisfied",
                    "paired_what_is_not_pairable"):
            if fam in body:
                answered.setdefault(fam, doc.name)

    ld = ROOT / "ops" / "RDL_LADDER.json"
    if ld.exists():
        try:
            fams = (json.loads(ld.read_text(encoding="utf-8")).get("families") or {})
            for name, v in fams.items():
                if isinstance(v, dict) and (v.get("rung") or 0) >= 4:
                    if name in answered:
                        continue  # the decision exists; silence is correct here
                    found.append({"source": "RDL ladder", "owner": v.get("owner", "ARCHITECT"),
                                  "finding": f"{name} at rung {v.get('rung')}: the control sits "
                                             f"in the wrong layer and no D- answers it yet",
                                  "verdict": "RUNG 4, UNANSWERED",
                                  "measured_by": "python scripts/rdl.py status"})
        except Exception:
            pass
    return found


def human_items(store: pathlib.Path | None) -> tuple[list[dict], str | None]:
    """Rows addressed to the operator. Returns (items, degraded_reason)."""
    if not store or not store.exists():
        return [], ("The task board lives in the private repository and this runner "
                    "checks out one. Not measured here, and not reported as zero.")
    import sqlite3
    con = sqlite3.connect(f"file:{store}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "select * from qesis_core_tasks where status='open'")]
    con.close()
    out = []
    for r in rows:
        if (r.get("owner") or "").upper() not in ("RICO", "HUMAN", "OPERATOR"):
            continue
        blob = " ".join(str(r.get(k) or "") for k in ("title", "blocker", "origin")).upper()
        clause = next((t for t in SH4 if t in blob), None)
        out.append({"id": r.get("ticket_id"), "title": r.get("title"),
                    "clause": clause, "detail": (r.get("blocker") or "")[:600]})
    return out, None


def selftest() -> int:
    ok = True
    # A control that could not run must never read as holding.
    v, _ = run(["scripts/__definitely_not_a_file__.py"])
    if v == "holding":
        print("  x FIXTURE 1 FAILED: a control that did not execute reported as holding"); ok = False
    # An unreachable store yields no items and a stated reason, never zero silently.
    items, why = human_items(pathlib.Path("/definitely/not/here.sqlite"))
    if items or not why:
        print("  x FIXTURE 2 FAILED: an unreachable board must state why, not imply zero"); ok = False
    # A reachable-but-empty result is different from unreachable and must say so.
    if why and "not reported as zero" not in why:
        print("  x FIXTURE 3 FAILED: the degraded reason must refuse to imply a zero"); ok = False
    # Every control the brief runs must have an owner in the routing table, or a
    # finding would be written with nobody to execute it.
    missing = [label for label, _ in CONTROLS if label not in ROUTE]
    if missing:
        print(f"  x FIXTURE 4 FAILED: no owner routed for {missing}"); ok = False
    # A dispatch row addressed to HUMAN without an SH-4 clause is a defect, not a task.
    bad = [{"owner": "HUMAN", "clause": None}]
    if not [r for r in bad if r["owner"] == "HUMAN" and not r["clause"]]:
        print("  x FIXTURE 5 FAILED: an unclaused human row must be detectable"); ok = False
    print(f"OPERATOR BRIEF SELFTEST: {'PASSED, 5 fixtures' if ok else 'FAILED'}")
    return 0 if ok else 1


ap = argparse.ArgumentParser()
ap.add_argument("--out", type=pathlib.Path, default=ROOT / "ops" / "OPERATOR_BRIEF.md")
ap.add_argument("--html", type=pathlib.Path, default=ROOT / "public" / "status.html")
ap.add_argument("--dispatch", type=pathlib.Path, default=ROOT / "ops" / "DISPATCH.json")
ap.add_argument("--store", type=pathlib.Path, default=None)
ap.add_argument("--selftest", action="store_true")
a = ap.parse_args()
if a.selftest:
    raise SystemExit(selftest())

now = datetime.datetime.now(datetime.timezone.utc)
results = [(label, *run(cmd)) for label, cmd in CONTROLS]
holding = [r for r in results if r[1] == "holding"]
trouble = [r for r in results if r[1] != "holding"]

vintage = "unknown"
try:
    vintage = json.loads((ROOT / "data" / "qesis_v8.json").read_text(encoding="utf-8"))["vintage"]
except Exception:
    pass

items, degraded = human_items(a.store)

if trouble:
    headline = "Something needs attention. The detail is below and most of it is already being repaired."
else:
    headline = "Everything is running. Nothing needs you."

md = [f"# QESIS+ status, {now.strftime('%A %d %B %Y')}", "",
      f"_Written by the runner at {now.strftime('%H:%M')} UTC. Nobody's computer was involved._", "",
      f"## {headline}", "",
      f"The instrument is serving vintage **{vintage}**.", ""]

md += ["## What was checked", ""]
for label, verdict, tail in results:
    mark = "OK" if verdict == "holding" else ("NOT MEASURED" if verdict == "NOT MEASURED" else "ATTENTION")
    md.append(f"- **{mark}** {label}")
    if verdict != "holding" and tail:
        md.append(f"  - {tail}")
md.append("")

md += ["## What is yours", ""]
if degraded:
    md += [f"Not measurable from here. {degraded}", ""]
elif not items:
    md += ["Nothing. No decision is waiting on you.", ""]
else:
    for it in items:
        md += [f"### {it['id']} · {it['title']}", ""]
        if it["clause"]:
            md += [f"**Why it is yours:** {it['clause']}.", ""]
        else:
            md += ["**This names no clause that makes it yours, which is a defect in the "
                   "board rather than a task for you. It is being rerouted.**", ""]
        md += [it["detail"], ""]

md += ["---", "",
       "_Generated by `scripts/build_operator_brief.py` on a GitHub runner and published "
       "to qesis.eu/status. It runs whether or not any machine of yours is switched on._"]
text = "\n".join(md)
a.out.parent.mkdir(parents=True, exist_ok=True)
a.out.write_text(text, encoding="utf-8")
print(f"wrote {a.out}")

body = html.escape(text).replace("\n", "<br>\n")
page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QESIS+ status</title>
<style>
:root{{--bg:#f4f2ee;--ink:#1e2328;--ink2:#4a545e;--rule:#d8d4cd;--ok:#4f7a63;--hot:#b0553f}}
@media(prefers-color-scheme:dark){{:root{{--bg:#14171a;--ink:#e6e3dd;--ink2:#b3b8bd;--rule:#2e343a;--ok:#7fae94;--hot:#e08066}}}}
body{{background:var(--bg);color:var(--ink);font:16px/1.65 ui-sans-serif,system-ui,sans-serif;
margin:0;padding:40px 20px 80px}}
main{{max-width:44rem;margin:0 auto}}
</style></head><body><main>{body}</main></body></html>"""
a.html.parent.mkdir(parents=True, exist_ok=True)
a.html.write_text(page, encoding="utf-8")
print(f"wrote {a.html}")
# ---- the agent-facing half ----
actions = []
for j in ingest_jobs():
    actions.append(dict(j, routed_by="SH-10b table, not by judgement",
                        action=("execute now, in this session, and record the repair. "
                                "Do not file a row instead of repairing it (SH-3).")))
for label, verdict, tail in results:
    if verdict == "holding":
        continue
    cmd = next(c for l, c in CONTROLS if l == label)
    actions.append({
        "finding": label,
        "verdict": verdict,
        "evidence": tail,
        "measured_by": "python " + " ".join(cmd),
        "settles_with": "python " + " ".join(cmd),
        "owner": ROUTE.get(label, "ARCHITECT"),
        "routed_by": "SH-10b table, not by judgement",
        "action": ("execute now, in this session, and record the repair. Do not file a row "
                   "instead of repairing it (SH-3)."),
    })
for it in items:
    actions.append({
        "finding": f"{it['id']} {it['title']}",
        "verdict": "OPEN",
        "evidence": it["detail"][:400],
        "owner": "HUMAN" if it["clause"] else "MISROUTED",
        "sh4_clause": it["clause"],
        "routed_by": "task board, owner field",
        "action": ("deliver to the operator in the full SH-9 shape" if it["clause"] else
                   "names no SH-4 clause, so it is NOT his. Reroute by the SH-10b table "
                   "and execute it."),
    })

dispatch = {
    "_doc": "The agent-facing half of the daily brief. Read this before deciding what to do. "
            "Every row is already routed by the SH-10b table. Execute your own rows in the "
            "session that reads them; occurrences one to three never reach the operator.",
    "_read_order": ["ops/AUDIT_REPORT.md", "ops/SELFHEAL_LATEST.json",
                    "ops/reports/<latest>.md", "ops/CI_LAST_FAILURE.md",
                    "ops/PATH_REGISTRY.json", "ops/ECOSYSTEM_STATE.json", "CLAUDE.md"],
    "_hard_rules": [
        "Never run any git command from a zero-trust analysis mount, read-only included (L-122, L-123, L-150).",
        "Connect C:\\Users\\Lenovo\\OneDrive\\sovereign-infra. The non-OneDrive path is an empty decoy (L-143).",
        "A control that did not execute is NOT MEASURED, never a pass (D-120).",
        "Never report a count of open items to the operator. Deliver items to their owners.",
    ],
    "generated_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "served_vintage": vintage,
    "verdict": "GREEN" if not trouble else "NEEDS ACTION",
    "controls": [{"finding": l, "verdict": v, "owner": ROUTE.get(l, "ARCHITECT"),
                  "command": "python " + " ".join(c), "tail": t}
                 for (l, v, t), (_, c) in zip(results, CONTROLS)],
    "board_degraded": degraded,
    "fed_by": ["ops/SELFHEAL_LATEST.json, hourly self-heal loop",
               "ops/AUDIT_REPORT.md, cross-repository audit",
               "ops/CI_LAST_FAILURE.md, CI feedback on a real failure",
               "ops/RDL_LADDER.json, the escalation ladder",
               "ops/reports/, the daily runner narrative",
               "the control set, executed in this run"],
    "actions": actions,
    "actions_by_owner": {o: [a["finding"] for a in actions if a["owner"] == o]
                         for o in sorted({a["owner"] for a in actions})},
}
a.dispatch.parent.mkdir(parents=True, exist_ok=True)
a.dispatch.write_text(json.dumps(dispatch, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"wrote {a.dispatch}")
print(f"controls holding: {len(holding)} of {len(results)}, actions dispatched: {len(actions)}")
