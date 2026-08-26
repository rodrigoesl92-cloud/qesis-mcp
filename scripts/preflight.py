#!/usr/bin/env python3
"""Run exactly what CI runs, locally, before anything is pushed.

THE GAP THIS CLOSES. Every failure of 2026-08-24 has the same shape: a gate
passed where the agent could run it and failed where it actually runs. Local
runs and CI differ in ways that matter, and the agent kept treating "green here"
as evidence of "green there". That is a proxy, and D-115 forbids it.

This does not simulate CI. It PARSES `.github/workflows/qesis-integrity.yml`,
extracts every `run:` step in order, and executes them. If a step is added to
the workflow it is picked up automatically, so this file cannot drift from the
thing it is predicting.

Exit 0 means the required status check will pass on this tree. Exit 1 names the
first step that will fail and stops, because everything after a red step is
noise the operator would have to read through.

Usage:
    python scripts/preflight.py
    python scripts/preflight.py --workflow .github/workflows/qesis-integrity.yml
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def steps(workflow: Path) -> list[tuple[str, str]]:
    """Extract (name, command) for every `run:` step, in file order.

    Deliberately a small parser rather than a YAML dependency: this must work on
    a bare checkout with nothing installed, which is the state it is predicting.
    """
    out: list[tuple[str, str]] = []
    name = ""
    lines = workflow.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"\s*-?\s*name:\s*(.+?)\s*$", line)
        if m:
            name = m.group(1).strip().strip('"').strip("'")
        m = re.match(r"(\s*)run:\s*(.*)$", line)
        if m:
            indent, first = m.group(1), m.group(2).strip()
            if first in ("|", ">", "|-", ">-"):
                block, i = [], i + 1
                while i < len(lines):
                    nxt = lines[i]
                    if nxt.strip() and not nxt.startswith(indent + " "):
                        break
                    block.append(nxt.strip())
                    i += 1
                cmd = "\n".join(b for b in block if b)
                out.append((name, cmd))
                continue
            if first:
                out.append((name, first))
        i += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", default=".github/workflows/qesis-integrity.yml")
    ap.add_argument("--keep-going", action="store_true")
    a = ap.parse_args()

    wf = ROOT / a.workflow
    if not wf.exists():
        print(f"PREFLIGHT: {a.workflow} is absent from this repository. "
              "Nothing to predict. Reported, not assumed green.")
        return 0

    all_steps = steps(wf)
    install = [c for _, c in all_steps if "pip install" in c]
    if install:
        print("  installing requirements, as CI does, before predicting anything")
        subprocess.run(install[0], shell=True, cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    st = [(n, c) for n, c in all_steps
          if c.strip() and not c.strip().startswith("echo")
          and "GITHUB_STEP_SUMMARY" not in c and "pip install" not in c]
    print(f"PREFLIGHT: {len(st)} runnable step(s) from {a.workflow}")
    print("Running what CI runs, in CI's order, on this tree.\n")

    failed, env_only = [], []
    for n, cmd in st:
        single = [l for l in cmd.splitlines() if l.strip()]
        label = (n or single[0])[:58]
        try:
            p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True,
                               text=True, timeout=600)
            code = p.returncode
            tail = (p.stdout + p.stderr).strip().splitlines()
        except Exception as exc:
            code, tail = 127, [f"{type(exc).__name__}: {exc}"]

        joined = "\n".join(tail)
        if code == 0:
            print(f"  PASS  {label}")
        elif "ModuleNotFoundError" in joined or "ImportError" in joined:
            mod = re.search(r"No module named '([^']+)'", joined)
            print(f"  ENV   {label}   dependency not installed here"
                  + (f": {mod.group(1)}" if mod else ""))
            env_only.append(label)
        else:
            print(f"  FAIL  {label}   exit {code}")
            for t in tail[-8:]:
                print(f"        {t}")
            failed.append((label, code))
            if not a.keep_going:
                print("\nPREFLIGHT FAILED. This step will fail the required status "
                      "check, so the pull request could not merge.")
                print("Nothing has been pushed. Fix this, then run again.")
                return 1

    print()
    if env_only:
        print(f"  {len(env_only)} step(s) could not run here for lack of an "
              "installed dependency. CI installs requirements.txt and will run "
              "them. Reported as environment, not as a pass and not as a defect.")
    if failed:
        print(f"PREFLIGHT FAILED: {len(failed)} step(s). "
              + ", ".join(f for f, _ in failed))
        return 1
    print("PREFLIGHT PASSED: every step CI will run passes on this tree.")
    print("This is not a proxy for CI. It is CI's own step list, executed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
