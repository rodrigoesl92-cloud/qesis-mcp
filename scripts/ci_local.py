"""Run the REAL CI step list locally, in order. End the local-green CI-red class.

WHY A CONTRACT GATE WAS NOT ENOUGH
    `verify_workflow_contract.py` compares NAMES: it asserts that the scripts CI
    runs also appear in the local control set. That catches drift in the lists
    and catches nothing about behaviour. CI ran and failed in 13 seconds while
    the local set reported 55 of 55, because the two were never the same
    EXECUTION, only the same inventory.

    Comparing inventories is how you discover that both lists mention
    `verify_index.py`. It is not how you discover that CI dies before reaching
    it. This runs the steps.

WHAT IT DOES
    Parses .github/workflows/*.yml, takes each job's steps in declared order,
    and executes every `run:` block in the repository root with the same shell
    semantics CI uses. `uses:` steps are reported as SKIPPED with their action
    name, because checkout and setup-python have no local equivalent and
    pretending otherwise would be the same lie in the other direction.

    It stops at the FIRST failure and prints that step's name, its command and
    its output, which is the thing three rounds of repair-by-hypothesis never
    had.

WHAT IT CANNOT DO, STATED SO THE RESULT IS NOT OVERREAD
    It cannot reproduce a failure caused by the runner environment itself: a
    network refusal during pip install, a missing repository secret, a
    permission the local shell has and the runner token does not. Where every
    step passes here and CI still fails, that difference IS the diagnosis and it
    is a much smaller search space than the whole workflow.

Usage:
    python scripts/ci_local.py                      run qesis-integrity.yml
    python scripts/ci_local.py --workflow selfheal  run a named workflow
    python scripts/ci_local.py --list               list steps without running
    python scripts/ci_local.py --skip-install       skip pip, for a fast loop
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def load_steps(path: Path) -> list[tuple[str, str, str]]:
    """Return [(job, step_name, command_or_uses)] in declared order.

    Parsed with PyYAML when available and with a deliberate line reader when it
    is not, because this script has to work in exactly the environments where
    dependencies are the thing under suspicion. A diagnostic that needs the
    runtime it is diagnosing is not a diagnostic.
    """
    try:
        import yaml
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        out: list[tuple[str, str, str]] = []
        for job, spec in (doc.get("jobs") or {}).items():
            for st in (spec.get("steps") or []):
                name = st.get("name") or st.get("uses") or "(unnamed)"
                if "run" in st:
                    out.append((job, name, st["run"]))
                elif "uses" in st:
                    out.append((job, name, f"USES::{st['uses']}"))
        return out
    except ImportError:
        pass

    out, job, name, buf, indent = [], "?", None, [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if m:
            job = m.group(1)
        m = re.match(r"^\s+- name:\s*(.+?)\s*$", line)
        if m:
            if name and buf:
                out.append((job, name, "\n".join(buf)))
            name, buf, indent = m.group(1).strip('"\''), [], None
            continue
        m = re.match(r"^\s+- uses:\s*(\S+)", line)
        if m:
            if name and buf:
                out.append((job, name, "\n".join(buf)))
                name, buf = None, []
            out.append((job, m.group(1), f"USES::{m.group(1)}"))
            continue
        m = re.match(r"^(\s+)run:\s*\|?\s*(.*)$", line)
        if m:
            indent = len(m.group(1)) + 2
            if m.group(2).strip():
                buf.append(m.group(2))
            continue
        if indent is not None and line.startswith(" " * indent):
            buf.append(line[indent:])
        elif indent is not None and line.strip():
            if name and buf:
                out.append((job, name, "\n".join(buf)))
            name, buf, indent = None, [], None
    if name and buf:
        out.append((job, name, "\n".join(buf)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", default="qesis-integrity")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--skip-install", action="store_true")
    ap.add_argument("--keep-going", action="store_true")
    a = ap.parse_args()

    wf = WORKFLOWS / f"{a.workflow}.yml"
    if not wf.exists():
        print(f"FAIL no such workflow: {wf}")
        print("available: " + ", ".join(p.stem for p in sorted(WORKFLOWS.glob('*.yml'))))
        return 1

    steps = load_steps(wf)
    print(f"ci_local: {wf.name}, {len(steps)} steps\n")
    if a.list:
        for job, name, cmd in steps:
            kind = "uses" if cmd.startswith("USES::") else "run "
            print(f"  [{kind}] {job}: {name}")
        return 0

    env = dict(os.environ)
    env.setdefault("GITHUB_STEP_SUMMARY", os.devnull)
    env.setdefault("CI", "true")

    # PLATFORM. This ran on Linux and was shipped to a Windows operator, where
    # `bash -lc` routes through WSL, WSL has no `python` on PATH, and every step
    # died with exit 127 before reaching a single gate. A diagnostic that cannot
    # run where the operator runs is not a diagnostic, and building it on the
    # wrong platform is the same defect it exists to catch, one layer up (L-137).
    is_windows = os.name == "nt"

    #: Constructs that only a POSIX shell understands. On Windows these are
    #: reported NOT RUNNABLE rather than executed and misreported, because a step
    #: that fails for a shell reason would read as a gate failure and send the
    #: next reader hunting the wrong thing. Honest refusal beats a wrong answer.
    posix_only = ("<<'", '<<"', "set -euo", "set -e", "${{", "$GITHUB", "&&", "||", "|")

    def run_step(cmd: str):
        """Execute one workflow `run:` block with the platform's own shell."""
        if is_windows:
            if any(tok in cmd for tok in posix_only) or "\n" in cmd.strip():
                return None, "POSIX shell constructs; not runnable on Windows"
            # `python` resolves through whatever launcher is first on PATH. Use
            # the interpreter that is running THIS script, so the local run and
            # the check it reports on cannot diverge on interpreter version.
            # A FUNCTION replacement, never a string. re.sub parses a string
            # replacement as a TEMPLATE, and a Windows interpreter path contains
            # backslash escapes: C:\\Users\\... makes `\\U` and the call dies with
            # `bad escape \\U`. Written on Linux where sys.executable is
            # /usr/bin/python3 and no backslash exists, so it could not fail
            # there and could not do anything else here (L-139).
            native = re.sub(r"^\s*python\b", lambda _m: f'"{sys.executable}"',
                            cmd.strip())
            return subprocess.run(native, cwd=ROOT, env=env, shell=True,
                                  capture_output=True, text=True, timeout=900), None
        return subprocess.run(["bash", "-lc", cmd], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=900), None

    failures = 0
    for job, name, cmd in steps:
        if cmd.startswith("USES::"):
            print(f"  ..  SKIP  {name}   (action, no local equivalent)")
            continue
        if a.skip_install and "pip install" in cmd:
            print(f"  ..  SKIP  {name}   (--skip-install)")
            continue

        t0 = time.time()
        r, skip_reason = run_step(cmd)
        dt = time.time() - t0
        if r is None:
            print(f"  ..  SKIP  {name}   ({skip_reason})")
            continue
        ok = r.returncode == 0
        print(f"  {'ok ' if ok else 'X  '} {name}   ({dt:.1f}s, exit {r.returncode})")
        if not ok:
            failures += 1
            print("\n" + "=" * 70)
            print(f"FIRST FAILING STEP: {job} / {name}")
            print("=" * 70)
            print("COMMAND:")
            for l in cmd.splitlines():
                print(f"  {l}")
            print("\nOUTPUT (last 60 lines):")
            for l in (r.stdout + r.stderr).splitlines()[-60:]:
                print(f"  {l}")
            print("=" * 70)
            if not a.keep_going:
                print("\nStopped at the first failure, which is what CI does. Pass")
                print("--keep-going to see every failing step in one pass.")
                return 1

    if failures:
        print(f"\n{failures} step(s) failed")
        return 1
    print(f"\nAll runnable steps passed. If CI still fails, the difference is the")
    print("runner ENVIRONMENT rather than the step list: a network refusal during")
    print("install, a missing repository secret, or a token permission this shell")
    print("has and the runner does not. That is the diagnosis, and it is a much")
    print("smaller search space than the workflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
