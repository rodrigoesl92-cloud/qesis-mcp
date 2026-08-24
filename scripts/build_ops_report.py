#!/usr/bin/env python3
"""Generate the daily ops report from measured state. Stdlib only.

Runs on a GitHub Actions runner under SH-7, and locally with the same output.

Doctrine this file is written to obey:
  V-1  a claim about system state carries the command that produced it
  V-5  `success` is a status of the operation, not of the result; assert counts
  D-007 a gap is reported with its cause, never imputed and never a silent zero
  L-015 no em dash in prose
  SH-3 solve, do not report: this file states who owns each item, and an item is
       only marked for the operator when a clause makes it his

Scope is ONE repository. What this runner cannot see is named in the report
rather than reported as zero.

Usage:
    python scripts/build_ops_report.py --out ops/reports/2026-08-24.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# L-015, the em dash is banned in prose. Written as a codepoint on purpose: a
# literal here would be the one em dash in the repository, and D-049 reduces
# scripts to their string literals before the doctrine scan reads them, so the
# enforcer would be the only thing the enforcement finds.
BANNED = "\u2014"


def sh(*args: str) -> tuple[int, str]:
    """Run a command in the repository root and return code plus stripped output."""
    try:
        p = subprocess.run(
            args, cwd=ROOT, capture_output=True, text=True, timeout=120, check=False
        )
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as exc:  # pragma: no cover
        return 127, f"{type(exc).__name__}: {exc}"


def git(*args: str) -> str:
    return sh("git", *args)[1]


def repo_state() -> dict:
    head = git("rev-parse", "--abbrev-ref", "HEAD")
    base = "origin/main" if git("rev-parse", "--verify", "-q", "origin/main") else "main"
    counts = git("rev-list", "--left-right", "--count", f"{base}...HEAD")
    behind, ahead = (counts.split() + ["?", "?"])[:2]
    porcelain = [l for l in git("status", "--porcelain").splitlines() if l.strip()]
    return {
        "head": head,
        "base": base,
        "ahead": ahead,
        "behind": behind,
        "modified": [l for l in porcelain if not l.startswith("??")],
        "untracked": [l for l in porcelain if l.startswith("??")],
        "last_commits": git("log", "-5", "--date=iso", "--pretty=%h %ad %s").splitlines(),
        "base_head": git("log", "-1", "--date=iso", "--pretty=%h %ad %s", base),
    }


def selfheal_state() -> dict:
    p = ROOT / "ops" / "SELFHEAL_LATEST.json"
    if not p.exists():
        return {"present": False, "why": f"{p.relative_to(ROOT)} absent from this checkout"}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"present": False, "why": f"unparseable: {exc}"}
    return {
        "present": True,
        "generated_utc": d.get("generated_utc"),
        "mode": d.get("mode"),
        "controls": len(d.get("controls", [])),
        "passed": sum(1 for c in d.get("controls", []) if c.get("status", "").startswith("PASS")),
        "repaired": len(d.get("repaired", [])),
        "degraded": [x.get("control") for x in d.get("degraded", [])],
        "escalations": len(d.get("escalations", [])),
        "failed": [c.get("name") for c in d.get("controls", []) if c.get("status") == "FAIL"],
    }


def ledger_state() -> dict:
    code, out = sh(sys.executable, "scripts/verify_ledger_singleton.py", "--json")
    try:
        return json.loads(out)
    except Exception:
        return {"status": "UNKNOWN", "rules": {"R0": out[:300]}, "degraded": []}


def served_vintage() -> str:
    for cand in ("data/qesis_v8.json", "data/index.json"):
        p = ROOT / cand
        if p.exists():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            for k in ("vintage", "canonical_vintage"):
                if isinstance(d, dict) and d.get(k):
                    return f"{d[k]} (from {cand})"
                meta = d.get("meta") or d.get("provenance") or {}
                if isinstance(meta, dict) and meta.get(k):
                    return f"{meta[k]} (from {cand})"
    return "not determinable from this checkout"


def schedules() -> list[str]:
    out = []
    wf = ROOT / ".github" / "workflows"
    for f in sorted(wf.glob("*.yml")) if wf.exists() else []:
        t = f.read_text(encoding="utf-8", errors="replace")
        crons = re.findall(r"cron:\s*[\"']([^\"']+)[\"']", t)
        if crons:
            out.append(f"{f.name}: {', '.join(crons)}")
    return out


def build(today: str) -> str:
    r = repo_state()
    sh_ = selfheal_state()
    led = ledger_state()
    repo = ROOT.name

    L = []
    A = L.append
    A(f"# QESIS+ Daily Ops Report: {today}")
    A("")
    A(
        f"Generated on the runner by `.github/workflows/daily-ops-report.yml` under SH-7. "
        f"Repository `{repo}`. No human ran this and none was asked to."
    )
    A("")
    A("**Scope, declared.** This runner sees one repository. The thesis governance folder, "
      "the operational SQLite store and the OneDrive mounts are not reachable from here, so "
      "`_GOVERNANCE`, `_DATABASE`, the compliance chain and the Article 14 queue are OUT OF "
      "SCOPE in this report and are not reported as zero. D-007: withheld with cause.")
    A("")

    # 1
    A("## 1. What ran")
    A("")
    if sh_["present"]:
        A(f"**Self-heal:** `{sh_['generated_utc']}`, mode {sh_['mode']}. "
          f"{sh_['passed']} of {sh_['controls']} controls passed, {sh_['repaired']} repaired, "
          f"{sh_['escalations']} escalations, {len(sh_['failed'])} failed"
          + (f" ({', '.join(sh_['failed'])})" if sh_["failed"] else "")
          + (f". Degraded: {', '.join(sh_['degraded'])}." if sh_["degraded"] else "."))
    else:
        A(f"**Self-heal: no artefact.** {sh_['why']}")
    A("")
    A("**Declared schedules in this repository:**")
    A("")
    for s in schedules() or ["none declared"]:
        A(f"- `{s}`")
    A("")

    # 2
    A("## 2. What changed")
    A("")
    A(f"HEAD `{r['head']}`, **{r['ahead']} ahead of {r['base']}, {r['behind']} behind**. "
      f"{r['base']} at `{r['base_head']}`.")
    A("")
    A(f"Working tree: **{len(r['modified'])} modified, {len(r['untracked'])} untracked.**")
    if r["untracked"]:
        A("")
        A("Untracked, therefore unhashed, unlineaged and on one disk only:")
        A("")
        for u in r["untracked"][:15]:
            A(f"- `{u[3:]}`")
        if len(r["untracked"]) > 15:
            A(f"- and {len(r['untracked']) - 15} more")
    A("")
    A("Last five commits:")
    A("")
    for c in r["last_commits"]:
        A(f"- `{c}`")
    A("")
    A(f"Served vintage: {served_vintage()}.")
    A("")

    # 3
    A("## 3. Staleness and gaps")
    A("")
    A(f"**Lessons ledger singleton: {led.get('status')}.** "
      f"{led.get('entries', '?')} entries, {led.get('unique', '?')} unique, "
      f"max L-{led.get('max', 0):03d}, sha256 `{str(led.get('sha256', ''))[:16]}`.")
    A("")
    for rule, msg in (led.get("rules") or {}).items():
        A(f"- {rule}: {msg}")
    for deg in led.get("degraded") or []:
        A(f"- {deg['rule']} DEGRADED: {deg['why']}")
    A("")
    A("Out of scope from this runner and therefore NOT measured today: the Article 14 queue, "
      "the compliance chain length, the operational task board, `_GOVERNANCE` and `_DATABASE` "
      "drift, and the ENTSO-E task. Each lives behind a mount this job does not have. They are "
      "named so their absence is visible rather than silent.")
    A("")

    # 4
    A("## 4. Lessons")
    A("")
    A(f"Ledger stands at {led.get('unique', '?')} unique ids, max L-{led.get('max', 0):03d}. "
      "Declared absent ids are listed in `ops/LEDGER_GAPS.json` with an owner and a closing "
      "condition; R2 of the singleton gate fails the build on any absent id that is not "
      "declared there.")
    A("")

    # 5
    A("## 5. Next actions")
    A("")
    items = []
    if led.get("status") != "PASS":
        items.append(
            "**Ledger singleton is failing.** "
            + "; ".join(f"{k}: {v}" for k, v in led.get("rules", {}).items() if "no " not in v)
            + ". Owner: ARCHITECT. This is repairable without the operator."
        )
    if int(r["ahead"] or 0) > 0:
        items.append(
            f"**{r['ahead']} commits sit ahead of {r['base']} on `{r['head']}`.** Under G-06 an "
            "agent MAY merge a remediation pull request once its checks pass, by "
            "`gh pr merge --rebase`. This is not an operator action unless it promotes."
        )
    if r["untracked"]:
        items.append(
            f"**{len(r['untracked'])} untracked paths carry no hash and no lineage.** Commit or "
            "record them withdrawn. Owner: ARCHITECT."
        )
    if sh_.get("failed"):
        items.append(f"**Self-heal controls failing: {', '.join(sh_['failed'])}.** Owner: SENTINEL.")
    if not items:
        items.append("**Nothing in this repository requires action.** Zero is zero.")
    for n, it in enumerate(items[:3], 1):
        A(f"{n}. {it}")
    A("")
    A("**Operator actions.** Only three classes reach the operator under SH-4: promotion absent "
      "a signed policy (G-06 limit 2), credential material in either direction (G-03, G-04), and "
      "an Article 14 signature. Nothing else in this report is his. If an item above is written "
      "as his and does not fall in one of those three, that is a defect in this generator.")
    A("")
    A("---")
    A("")
    A(f"_Generated at {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')} by "
      f"`scripts/build_ops_report.py` on the runner. Read-only except this file. Zeros are zeros._")

    text = "\n".join(L) + "\n"
    if BANNED in text:  # L-015, enforced here rather than described
        raise SystemExit("DOCTRINE FAILURE: em dash in generated prose (L-015)")
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--date", default=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args()
    text = build(a.date)
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(ROOT)}, {len(text)} chars, {text.count(chr(10))} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
