#!/usr/bin/env python3
"""Full ecosystem audit. Every row carries the command that produced it, the
value it returned, and the PREDICATE that turned the value into a verdict.

Runs on the host. Writes ops/AUDIT_REPORT.md in BOTH repositories, so the result
is a file the operator can open and a file the next session reads, rather than a
sentence in a chat window that nobody can check.

D-116, and the defect that forced it (L-172). The first version of this audit
printed PASS for "main check conclusions" because `gh api` exited 0, while the
value it had just fetched read `qesis-integrity: failure`. It printed PASS for
"open pull requests" while listing a CONFLICTING one. `success` is a status of
the operation, not of the result (V-5). So every row here is one of two kinds:

    gate         a script whose exit code IS its contract; exit 0 means the
                 property holds, because the script was built to that rule
    measurement  a value fetched from a resource, with an explicit predicate
                 over the PARSED value; the fetch's exit code decides nothing

A measurement whose value cannot be parsed is FAIL, never PASS. A measurement
with no predicate is INFO and cannot make the verdict green or red.

Covers, in this order:
  A  local gates in both repositories, including preflight (CI's own step list)
     and the self-heal loop in dry-run (what the `heal` check will do)
  B  the operational store: chain recomputed link by link, Article 14, tasks
  C  GitHub: open pull requests and their real mergeStateStatus, the required
     status checks on main read from the branch ruleset and evaluated against
     the check runs, open issues
  D  Vercel: the live /health payload evaluated field by field, and whether the
     commit production serves IS main
  E  the verdict, computed from the rows and from nothing else

Exit 0 only when no row is FAIL. Anything else exits 1 and the report names the
predicate that failed.

Usage:  python scripts/audit_ecosystem.py [--skip-slow]
        python scripts/audit_ecosystem.py --selftest
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

QESIS = Path(r"C:\Users\Lenovo\qesis-mcp")
INFRA = Path(r"C:\Users\Lenovo\OneDrive\sovereign-infra")
STORE = INFRA / "var" / "qesis_ops.sqlite"
OWNER = "rodrigoesl92-cloud"
HEALTH = "https://qesis-mcp.vercel.app/health"
LANDING = "https://qesis-mcp.vercel.app/"

rows: list[dict] = []
ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def owned_checks(root: Path) -> set[str]:
    """The check-run names this repository's own workflows produce (gh_ops.py)."""
    try:
        return _load("_gh_ops", ROOT / "scripts" / "gh_ops.py").owned_check_names(root)
    except Exception:
        return set()


def doctrine_hits(text: str) -> list[str]:
    """Blocking writing-doctrine hits in a report text, as 'rule@line' strings.

    The report is prose that compliance.yml scans with qesis_agents/style.py in
    the evidence plane; it must pass the gate it will meet (L-178). The doctrine
    module is used when it is reachable; otherwise the em dash rule, the one
    that fired, is applied directly so the check never silently vanishes.
    """
    for cand in (ROOT / "qesis_agents" / "style.py", INFRA / "qesis_agents" / "style.py",
                 QESIS / "qesis_agents" / "style.py"):
        if cand.exists():
            try:
                style = _load("_style", cand)
                return [f"{h.get('rule')}@{h.get('line')}" for h in style.scan(text)["blocking"]]
            except Exception:
                break
    import re
    return [f"em_dash@{i}" for i, line in enumerate(text.splitlines(), 1)
            if re.search(r"(?<![0-9])[\u2014\u2013](?![0-9])", line)]


def _sh(cmd, cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout,
                           shell=isinstance(cmd, str))
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as exc:
        return 127, f"{type(exc).__name__}: {exc}"


def row(label: str, cmd, cwd: Path, code: int, tail: list[str], verdict: str, basis: str) -> dict:
    r = {"label": label, "cmd": cmd if isinstance(cmd, str) else " ".join(map(str, cmd)),
         "exit": code, "tail": tail, "cwd": str(cwd), "verdict": verdict, "basis": basis}
    rows.append(r)
    print(f"  [{verdict:4s}] {label}   exit {code}")
    return r


def gate(label: str, cmd, cwd: Path, timeout: int = 600) -> dict:
    """A script whose exit code is its contract."""
    code, out = _sh(cmd, cwd, timeout)
    return row(label, cmd, cwd, code, out.splitlines()[-8:],
               "PASS" if code == 0 else "FAIL", "gate: exit code is the contract")


def measure(label: str, cmd, cwd: Path, predicate, timeout: int = 120, parse=json.loads) -> tuple[dict, object]:
    """A fetched value with an explicit predicate. Returns (row, parsed value)."""
    code, out = _sh(cmd, cwd, timeout)
    if code != 0:
        return row(label, cmd, cwd, code, out.splitlines()[-6:], "FAIL",
                   "measurement: the fetch itself failed, value unreadable"), None
    try:
        value = parse(out)
    except Exception as exc:
        return row(label, cmd, cwd, code, [f"unparseable: {exc}"] + out.splitlines()[-4:], "FAIL",
                   "measurement: value unparseable, never PASS by default"), None
    verdict, basis, lines = predicate(value)
    return row(label, cmd, cwd, code, lines, verdict, "measurement: " + basis), value


# ----------------------------------------------------------------------------- A
def section_a(skip_slow: bool) -> None:
    print("\nA. Local gates, both repositories")
    for repo in (QESIS, INFRA):
        if not repo.exists():
            row(f"{repo.name} present", f"test -d {repo}", repo, 1, ["repository not found"],
                "FAIL", "gate: the canonical path must exist (ops/PATH_REGISTRY.json)")
            continue
        py = "python"
        checks = [
            ("ledger mirror in sync", "scripts/ledger_sync.py --check"),
            ("ledger singleton", "scripts/verify_ledger_singleton.py"),
            ("ledger fixtures", "scripts/verify_ledger_singleton.py --selftest"),
            ("ecosystem bootstrap", "scripts/build_ecosystem_state.py --check"),
            ("ecosystem fixtures", "scripts/build_ecosystem_state.py --selftest"),
            ("RDL delta gate", "scripts/rdl.py ci-blocking"),
            ("workflow contract", "scripts/verify_workflow_contract.py"),
            ("self-heal fixtures", "scripts/selfheal.py --selftest"),
            # The lander is judged too (L-176, L-177): it must parse nothing,
            # read its landing from the manifest and restore only the delta.
            ("lander contract", "scripts/verify_lander_contract.py"),
            ("landing base fixtures", "scripts/landing_base.py --selftest"),
            ("landing manifest fixtures", "scripts/landing_manifest.py --selftest"),
        ]
        for name, script in checks:
            if (repo / script.split()[0]).exists():
                gate(f"{repo.name}: {name}", f"{py} {script}", repo)
        if skip_slow:
            continue
        if (repo / "scripts/preflight.py").exists():
            gate(f"{repo.name}: preflight, CI's own steps", f"{py} scripts/preflight.py", repo, 1200)
        if (repo / "scripts/selfheal.py").exists():
            gate(f"{repo.name}: self-heal loop, dry run (the `heal` check)",
                 f"{py} scripts/selfheal.py --dry-run", repo, 1200)


# ----------------------------------------------------------------------------- B
def section_b() -> None:
    print("\nB. Operational store")
    if not STORE.exists():
        row("store reachable", str(STORE), INFRA, 1, ["store not found"], "FAIL",
            "measurement: the store must exist at its canonical path")
        return
    tmp = Path.home() / "qesis_audit_copy.sqlite"
    try:
        shutil.copy(STORE, tmp)
        con = sqlite3.connect(tmp)
        cur = con.cursor()
        n, mx = cur.execute(
            "SELECT COUNT(*), MAX(timestamp) FROM qesis_audit_compliance_log").fetchone()
        chain = cur.execute(
            "SELECT seq, prev_hash, entry_hash FROM qesis_audit_compliance_log ORDER BY seq"
        ).fetchall()
        breaks = sum(1 for i in range(1, len(chain)) if chain[i][1] != chain[i - 1][2])
        held = cur.execute("SELECT COUNT(*) FROM qesis_audit_compliance_log "
                           "WHERE hitl_required=1 AND hitl_approved=0").fetchone()[0]
        opent = cur.execute("SELECT COUNT(*) FROM qesis_core_tasks "
                            "WHERE closed_at IS NULL").fetchone()[0]
        con.close()
        tmp.unlink(missing_ok=True)
        row("compliance chain", "sqlite recompute link by link", INFRA, 0 if breaks == 0 else 1,
            [f"{n} entries, max {mx}", f"{breaks} linkage breaks",
             f"{held} Article 14 executions held", f"{opent} open tasks"],
            "PASS" if breaks == 0 else "FAIL",
            "predicate: every prev_hash equals the previous entry_hash (0 breaks)")
        print(f"         chain {n} entries, {breaks} breaks, {held} held, {opent} open tasks")
    except Exception as exc:
        row("store readable", "sqlite3", INFRA, 1, [str(exc)], "FAIL",
            "measurement: the store could not be read")


# ----------------------------------------------------------------------------- C
def required_contexts(slug: str) -> tuple[list[str], str]:
    """The status checks the branch ruleset on main requires, by name."""
    code, out = _sh(["gh", "api", f"repos/{slug}/rules/branches/main"], QESIS, 120)
    if code != 0:
        return [], f"ruleset unreadable: {out.splitlines()[0] if out else ''}"
    try:
        rules = json.loads(out)
    except Exception as exc:
        return [], f"ruleset unparseable: {exc}"
    ctx: list[str] = []
    for r in rules:
        if r.get("type") == "required_status_checks":
            for c in (r.get("parameters") or {}).get("required_status_checks", []):
                if c.get("context"):
                    ctx.append(c["context"])
    return ctx, "ruleset"


def section_c() -> dict:
    print("\nC. GitHub, fetched now")
    facts: dict = {}
    for repo in ("qesis-mcp", "sovereign-infra"):
        slug = f"{OWNER}/{repo}"

        def pr_pred(prs):
            lines = [f"PR {p['number']} head {p['headRefName']} {p.get('mergeable')} "
                     f"{p.get('mergeStateStatus')}" for p in prs] or ["0 open pull requests"]
            dirty = [str(p["number"]) for p in prs if (p.get("mergeStateStatus") or "").upper() == "DIRTY"]
            if dirty:
                return ("FAIL", f"no open pull request may be DIRTY; PR {', '.join(dirty)} "
                        "conflicts and auto-merge can never fire on it (L-165)", lines)
            if prs:
                return ("INFO", f"{len(prs)} open, none DIRTY. Open is unlanded work, not a "
                        "defect; the lander merges or closes it", lines)
            return ("PASS", "0 open pull requests", lines)

        _, prs = measure(f"{repo}: open pull requests",
                         ["gh", "pr", "list", "--repo", slug, "--state", "open", "--limit", "50",
                          "--json", "number,headRefName,mergeable,mergeStateStatus"],
                         QESIS, pr_pred)
        facts[f"{repo}_open_prs"] = prs or []

        _, commit = measure(f"{repo}: main",
                            ["gh", "api", f"repos/{slug}/commits/main"], QESIS,
                            lambda c: ("INFO", "recorded for the deployment comparison",
                                       [f"main {c.get('sha','')[:12]}  "
                                        f"{(c.get('commit',{}).get('message','') or '').splitlines()[0][:70]}"]))
        facts[f"{repo}_main_sha"] = (commit or {}).get("sha", "")

        contexts, how = required_contexts(slug)
        facts[f"{repo}_required"] = contexts

        def checks_pred(doc, contexts=contexts, how=how):
            if not isinstance(doc, dict) or "check_runs" not in doc:
                return ("FAIL", "the check-runs payload has no check_runs key; unreadable, never PASS",
                        [str(doc)[:120]])
            runs = doc.get("check_runs") or []
            latest: dict[str, dict] = {}
            for cr in runs:
                name = cr.get("name", "")
                key = cr.get("completed_at") or cr.get("started_at") or ""
                if name not in latest or key > (latest[name].get("completed_at") or latest[name].get("started_at") or ""):
                    latest[name] = cr
            lines = [f"required by {how}: " + (", ".join(contexts) if contexts else "none readable")]
            failed = []
            for c in contexts:
                cr = latest.get(c)
                concl = (cr or {}).get("conclusion") or ((cr or {}).get("status") or "never reported")
                lines.append(f"REQUIRED {c}: {concl}")
                if concl != "success":
                    failed.append(f"{c}={concl}")
            # D-116 rule 6 (L-179): a check produced by a workflow THIS repository
            # owns is asserted whether or not the ruleset requires it. Only a
            # check from an integration the ecosystem does not own is INFO.
            # Not finished at read time is reported, never failed; no run on this
            # commit is reported, never failed (schedule- and path-triggered jobs).
            owned = owned_checks(root_for) - set(contexts)
            lines.append("owned by this repository's workflows: " + (", ".join(sorted(owned)) or "none readable"))
            for name in sorted(owned):
                cr = latest.get(name)
                if cr is None:
                    lines.append(f"OWNED {name}: no run on this commit")
                    continue
                if (cr.get("status") or "") != "completed":
                    lines.append(f"OWNED {name}: {cr.get('status')} (not finished at read time; rerun the audit)")
                    continue
                concl = cr.get("conclusion") or "no conclusion"
                lines.append(f"OWNED {name}: {concl}")
                if concl != "success":
                    failed.append(f"{name}={concl} (owned, not required)")
            for name, cr in sorted(latest.items()):
                if name not in contexts and name not in owned:
                    lines.append(f"informational {name[:60]}: {cr.get('conclusion') or cr.get('status')}")
            if not contexts:
                # Fall back to the names the ecosystem owns, and say so.
                owned = {n: cr for n, cr in latest.items()
                         if any(k in n.lower() for k in ("integrity", "heal", "guard", "binding"))}
                bad = [f"{n}={cr.get('conclusion')}" for n, cr in owned.items() if cr.get("conclusion") != "success"]
                if bad:
                    return ("FAIL", "ruleset unreadable, so every ecosystem-owned check on main must be "
                            "success; not: " + ", ".join(bad), lines)
                return ("PASS" if owned else "FAIL",
                        "ruleset unreadable; every ecosystem-owned check on main is success"
                        if owned else "no check on main could be evaluated", lines)
            if failed:
                return ("FAIL", "every REQUIRED status check and every completed check this repository "
                        "OWNS must be success on main (D-116 rules 5 and 6); not: " + ", ".join(failed), lines)
            return ("PASS", f"all {len(contexts)} required check(s) and every completed owned check on "
                    "main are success; integrations the ecosystem does not own (e.g. Cloud Build) "
                    "are informational", lines)

        root_for = QESIS if repo == "qesis-mcp" else INFRA
        measure(f"{repo}: required and owned checks on main",
                ["gh", "api", f"repos/{slug}/commits/main/check-runs?per_page=100"],
                QESIS, checks_pred)

        measure(f"{repo}: open issues",
                ["gh", "issue", "list", "--repo", slug, "--state", "open", "--json", "number,title"],
                QESIS, lambda issues: ("INFO", f"{len(issues)} open issue(s), recorded",
                                       [f"#{i['number']} {i.get('title','')[:70]}" for i in issues]
                                       or ["0 open issues"]))
    return facts


# ----------------------------------------------------------------------------- D
def section_d(facts: dict) -> None:
    print("\nD. Vercel, the design endpoint")
    main_sha = facts.get("qesis-mcp_main_sha", "")

    def health_pred(h):
        chain = h.get("chain") or {}
        lines = [f"status {h.get('status')}  vintage {h.get('vintage')}  chain {chain.get('status')} "
                 f"{chain.get('entries')} entries {chain.get('link_breaks')} breaks",
                 f"deployment_commit {str(h.get('deployment_commit',''))[:12]}  main {main_sha[:12]}",
                 f"tools {h.get('tool_count')}  database {h.get('database')}"]
        bad = []
        if h.get("status") != "ok":
            bad.append(f"status={h.get('status')}")
        if chain.get("status") != "VERIFIED":
            bad.append(f"chain={chain.get('status')}")
        if chain.get("link_breaks") not in (0, None):
            bad.append(f"link_breaks={chain.get('link_breaks')}")
        if chain.get("attestation_agrees") is False:
            bad.append("attestation_agrees=false")
        if main_sha and h.get("deployment_commit") and h["deployment_commit"] != main_sha:
            bad.append("production serves a commit that is not main (the merge is the deploy; "
                       "either the deploy has not happened or main moved)")
        if bad:
            return ("FAIL", "; ".join(bad), lines)
        return ("PASS", "status ok, chain VERIFIED with 0 breaks, attestation agrees, and "
                "deployment_commit equals main", lines)

    measure("live /health", ["curl.exe", "-s", "--max-time", "25", HEALTH], QESIS, health_pred, 60)
    measure("landing page HTTP",
            ["curl.exe", "-s", "-o", "NUL", "-w", "%{http_code}", "--max-time", "25", LANDING],
            QESIS, lambda code: (("PASS" if code == "200" else "FAIL"),
                                 f"HTTP {code}, predicate: 200", [f"HTTP {code}"]),
            60, parse=lambda s: s.strip())


# ----------------------------------------------------------------------------- E
def render_report(rows: list[dict], stamp: str) -> str:
    """The report text. Prose in it meets the writing doctrine it will be gated by."""
    bad = [r for r in rows if r["verdict"] == "FAIL"]
    info = [r for r in rows if r["verdict"] == "INFO"]
    lines = [
        "# QESIS+ full ecosystem audit",
        "",
        f"Generated {stamp} by `scripts/audit_ecosystem.py`.",
        "Every row carries the command that produced it, the exit code it returned, and",
        "the predicate that decided its verdict. An exit code alone never decides a",
        "measurement (D-116, V-5). Nothing here is asserted; V-1.",
        "",
        f"## Verdict: {'GREEN' if not bad else 'NOT GREEN, ' + str(len(bad)) + ' failing'}"
        + (f" ({len(info)} informational)" if info else ""),
        "",
        "| # | check | verdict | exit | basis |",
        "|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(f"| {i} | {r['label']} | **{r['verdict']}** | {r['exit']} | {r['basis'][:110]} |")
    lines += ["", "## Output of every check", ""]
    for i, r in enumerate(rows, 1):
        lines += [f"### {i}. {r['label']}  ({r['verdict']}, exit {r['exit']})", "",
                  f"`{r['cmd']}`  in `{r['cwd']}`", "", f"Basis: {r['basis']}", "", "```"]
        lines += r["tail"] or ["(no output)"]
        lines += ["```", ""]
    if bad:
        lines += ["## What is failing", ""]
        for r in bad:
            # No em dash: this line is prose and compliance.yml's doctrine gate
            # refused the report on main for exactly that character (L-178).
            lines.append(f"- **{r['label']}**: {r['basis']}"
                         + (f", last line: `{r['tail'][-1][:160]}`" if r["tail"] else ""))
        lines.append("")
    return "\n".join(lines) + "\n"


def write_report() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = render_report(rows, stamp)
    hits = doctrine_hits(text)
    if hits:
        # The report meets the gate it will be scanned by, or it says so as a
        # FAIL row of its own and the verdict cannot be GREEN (L-178). The hit
        # is named by rule and line, never quoted, so the row cannot re-offend.
        row("audit report meets the writing doctrine", "scripts/audit_ecosystem.py", QESIS, 1,
            [f"blocking: {', '.join(hits[:8])}"], "FAIL",
            "gate: qesis_agents/style.py blocking hits over the rendered report must be zero (W-1, L-178)")
        text = render_report(rows, stamp)
    bad = [r for r in rows if r["verdict"] == "FAIL"]
    for repo in (QESIS, INFRA):
        if repo.exists():
            (repo / "ops").mkdir(exist_ok=True)
            (repo / "ops" / "AUDIT_REPORT.md").write_text(text, encoding="utf-8", newline="\n")
            print(f"\nwrote {repo / 'ops' / 'AUDIT_REPORT.md'}")
    return 1 if bad else 0


def selftest() -> int:
    """V-2 fixtures for the report writer (L-178) and the owned-check reader (L-179)."""
    fail_row = {"label": "x: a failing gate", "cmd": "python scripts/x.py", "exit": 1,
                "tail": ["last line of output"], "cwd": "C:/x", "verdict": "FAIL",
                "basis": "gate: exit code is the contract"}
    text = render_report([fail_row], "2026-08-26T00:00:00Z")
    offending = text.replace(", last line:", " \u2014 last line:")
    cases = [
        ("report writer: a FAIL row with a tail renders without an em dash",
         "\u2014" not in text and ", last line: `last line of output`" in text),
        ("report writer: the doctrine check refuses a rendered em dash",
         any(h.startswith("em_dash") for h in doctrine_hits(offending))),
        ("report writer: the doctrine check accepts the rendered report",
         doctrine_hits(text) == []),
    ]
    import tempfile
    root = Path(tempfile.mkdtemp())
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "c.yml").write_text(
        "name: Continuous compliance verification\non: [push]\njobs:\n  verify:\n"
        "    runs-on: ubuntu-latest\n    steps:\n      - run: true\n  heal:\n    name: Self-heal\n"
        "    runs-on: ubuntu-latest\n    steps:\n      - run: true\n", encoding="utf-8")
    owned = owned_checks(root)
    cases.append(("owned checks: job ids and job names are read from the workflow files",
                  {"verify", "heal", "Self-heal"} <= owned))
    for name, ok in cases:
        print(f"  {'PASS' if ok else 'FAIL'}  audit: {name}")
    n = sum(ok for _, ok in cases)
    print(f"audit selftest: {n}/{len(cases)} fixtures " + ("hold" if n == len(cases) else "FAILED"))
    return 0 if n == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-slow", action="store_true",
                    help="skip preflight and the self-heal dry run (minutes each)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    print("QESIS+ FULL ECOSYSTEM AUDIT")
    print("=" * 60)
    section_a(a.skip_slow)
    section_b()
    facts = section_c()
    section_d(facts)
    code = write_report()
    print("=" * 60)
    print("VERDICT: " + ("GREEN, every predicate holds."
                         if code == 0 else
                         "NOT GREEN. ops/AUDIT_REPORT.md names every failing predicate."))
    return code


if __name__ == "__main__":
    sys.exit(main())
