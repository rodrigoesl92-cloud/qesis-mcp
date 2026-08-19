"""Close the "green locally, red in CI" class. Third occurrence in one week.

THE RECURRENCE THIS EXISTS TO END
    2026-08-13, 2026-08-15 and 2026-08-19: a change set passed every local gate
    and failed in Actions. Each was diagnosed and fixed individually, which is
    why it happened three times. The instances differ; the class does not.

    Local and CI run DIFFERENT SETS and nothing asserted they should agree.
    `scripts/selfheal.py` holds one list, `.github/workflows/*.yml` holds
    another, and neither could see the other. Under D-112 this is one family,
    "a property asserted without executing the check that would falsify it",
    and the escalation ladder says the third occurrence makes it a blocker.

WHAT IT ASSERTS, AND WHY EACH IS EARNED

  C-1 PERMISSION CONTRACT. A step that runs `git push`, `git commit`,
      `gh pr create` or `gh issue create` needs the matching `permissions:`
      block. `selfheal.yml` declared `contents: read` while its own step pushed
      a branch and opened a pull request, which is the 2026-08-19 failure
      exactly. GitHub reports this as a runtime 403 in a log nobody reads, and
      the declaration sits three lines above the step that contradicts it.

  C-2 SCRIPT EXISTENCE. Every `python scripts/X.py` in a workflow names a file
      that exists at this commit. A workflow referencing a script that a rename
      moved fails at the step rather than at review.

  C-3 SET PARITY. Every verification script CI runs appears in the local control
      set, or is declared exempt with a reason. This is the one that closes the
      class: without it, the two lists drift silently and the drift is only
      discovered by a red check.

      Silence is not an exemption. An exemption is a named entry with a stated
      reason, and the target state for EXEMPT is empty (L-048).

Usage:  python scripts/verify_workflow_contract.py [--quiet]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

#: Commands that mutate, mapped to the permission each requires.
NEEDS = {
    r"\bgit\s+push\b": ("contents", "write"),
    r"\bgit\s+commit\b": ("contents", "write"),
    r"\bgh\s+pr\s+create\b": ("pull-requests", "write"),
    r"\bgh\s+pr\s+merge\b": ("pull-requests", "write"),
    r"\bgh\s+issue\s+create\b": ("issues", "write"),
    r"github\.rest\.issues\.create": ("issues", "write"),
    r"github\.rest\.pulls\.create": ("pull-requests", "write"),
}

#: CI steps that verify something but deliberately do NOT belong to the local
#: loop. Each carries the reason. Target state for this dict is empty.
EXEMPT = {
    "smoke_server.py": "needs the MCP runtime installed; the loop runs where it may not be",
    "test_http.py": "binds a port; unsuitable for a loop that may run on a mount",
    "test_routes.py": "asserts vercel.json rewrites against routes, a deploy-shaped check",
    "verify_served_contract.py": "imports server.py, which needs mcp and pydantic",
    "prove_axis_sfc_contract.py": "falsification suite for the SFC contract, run at build not at heal",
    "coupling.py": "recomputes published coupling values, expensive and not a drift check",
    "verify_dashboard.py": "pre-build surface check, runs in vercel_gate rather than the loop",
    "verify_domains.py": "inbound identity, asserted at build",
    "verify_endpoints.py": "outbound endpoints, asserted at build",
    "verify_release.py": "release binding workflow, not a continuous control",
    "prove_release_gate.py": "falsification suite for the release binding, run at release not at heal",
    "selfheal.py": "IS the loop. A control set that contains its own runner recurses.",
    "verify_production.py": "probes the live endpoint; the loop reads committed artefacts",
}


def local_controls() -> set[str]:
    """Script basenames in scripts/selfheal.py CONTROLS.

    Parsed from the source rather than imported, because importing selfheal
    executes its module level and this gate must run before that is safe.
    """
    src = (ROOT / "scripts" / "selfheal.py")
    if not src.exists():
        return set()
    text = src.read_text(encoding="utf-8")
    # Split on the CLOSING bracket at column zero, not on the first "]" found.
    # Every entry in CONTROLS is itself a list, so the naive split truncated the
    # block after the first entry and reported nine controls as missing. The
    # gate was right that something was wrong and wrong about what. A parser
    # that reads one entry and reports on all of them produces confident
    # nonsense, which is worse than failing to parse (L-134).
    block = text.split("CONTROLS = [", 1)[-1].split("\n]", 1)[0]
    return set(re.findall(r"scripts/([A-Za-z0-9_]+\.py)", block))


def tracked_scripts() -> tuple[set[str], str]:
    """Scripts git actually carries, and how that was established.

    THE WHOLE MONTH IN ONE FUNCTION. Local gates read the WORKING TREE; CI reads
    the COMMIT. Any file present locally and absent from the commit makes local
    green and CI red, and nothing in this repository asserted the difference.

    On 2026-08-19 `.gitignore` line 79, `*SECRET*`, swallowed
    scripts/verify_no_plaintext_secrets.py. `git add -A` skipped it without a
    word, `git status --short` hides ignored files, the commit shipped without
    it, and CI died in thirteen seconds running a step whose script was not
    there. The secrets gate was excluded by the secrets ignore rule (L-135).

    `git ls-files` reads the index and never writes it, so it takes no lock and
    is safe on an analysis mount (L-123). Where git is unavailable, as in the
    Vercel pre-build gate, the mode is reported rather than silently downgraded:
    a check that quietly answers a weaker question is how this started.
    """
    import subprocess
    try:
        r = subprocess.run(["git", "ls-files", "scripts"], cwd=ROOT,
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return ({line.rsplit("/", 1)[-1] for line in r.stdout.split() if line},
                    "git ls-files")
    except (OSError, subprocess.SubprocessError):
        pass
    return ({p.name for p in (ROOT / "scripts").glob("*.py")}, "filesystem fallback")


def workflow_steps(text: str) -> list[tuple[int, str]]:
    return [(i, l) for i, l in enumerate(text.splitlines(), 1)]


def declared_permissions(text: str) -> dict[str, str]:
    """Top-level `permissions:` block. Job-level blocks override and are read too."""
    perms: dict[str, str] = {}
    in_block = False
    for line in text.splitlines():
        if re.match(r"^\s*permissions:\s*$", line):
            in_block = True
            continue
        if in_block:
            # A blank line or a comment inside the block is not the end of the
            # block. Three separate parser defects in this one gate had the same
            # shape: an unexpected but valid line was read as end-of-structure,
            # and the gate then reported confidently on a structure it had only
            # partly read. A parser that stops early does not fail, it lies
            # (L-134).
            bare = line.strip()
            if not bare or bare.startswith("#"):
                continue
            # Strip a trailing comment before matching. `issues: write  # note`
            # is a correct declaration and the first version of this regex read
            # it as no declaration at all.
            line = re.sub(r"\s+#.*$", "", line)
            m = re.match(r"^\s+([a-z-]+):\s*([a-z]+)\s*$", line)
            if m:
                # A later, wider grant wins: write beats read.
                k, v = m.group(1), m.group(2)
                if perms.get(k) != "write":
                    perms[k] = v
                continue
            in_block = False
    return perms


def main() -> int:
    quiet = "--quiet" in sys.argv
    fails: list[str] = []
    if not WORKFLOWS.is_dir():
        print("FAIL .github/workflows is not a directory")
        return 1

    controls = local_controls()
    tracked, mode = tracked_scripts()
    ci_scripts: set[str] = set()

    for wf in sorted(WORKFLOWS.glob("*.yml")):
        text = wf.read_text(encoding="utf-8")
        perms = declared_permissions(text)

        for lineno, line in workflow_steps(text):
            # C-1
            for pattern, (scope, level) in NEEDS.items():
                if re.search(pattern, line):
                    have = perms.get(scope)
                    if have != level:
                        fails.append(
                            f"C-1 {wf.name}:{lineno} runs a command needing "
                            f"`{scope}: {level}` and the workflow declares "
                            f"`{scope}: {have or 'nothing'}`")
            # C-2 and C-3
            for m in re.finditer(r"python\s+scripts/([A-Za-z0-9_]+\.py)", line):
                name = m.group(1)
                if name not in tracked:
                    on_disk = (ROOT / "scripts" / name).exists()
                    why = ("exists on disk but is NOT TRACKED, so CI will not have "
                           "it. Check `git check-ignore -v` before assuming a "
                           "rename is needed." if on_disk else
                           "does not exist at all")
                    fails.append(f"C-2 {wf.name}:{lineno} references scripts/{name}, "
                                 f"which {why}")
                ci_scripts.add(name)

    # C-3, reconciliation
    for name in sorted(ci_scripts):
        if name in controls or name in EXEMPT:
            continue
        fails.append(
            f"C-3 scripts/{name} runs in CI and is absent from the selfheal "
            f"control set. Add it to CONTROLS, or declare it in EXEMPT with a "
            f"reason. Silence is not an exemption.")

    # C-4. Every script the LOCAL control set depends on must be tracked too.
    # A control that runs locally from an untracked file is a control CI does
    # not have, and the loop would report green on a set the runner cannot run.
    for name in sorted(controls):
        if name not in tracked:
            fails.append(f"C-4 scripts/{name} is in the selfheal control set and "
                         f"is NOT TRACKED. The loop runs it locally and CI cannot.")

    # A dead exemption hides the next real one, so it is a finding. It is scoped
    # to exemptions whose script EXISTS: an exemption naming a script that is not
    # in this checkout says nothing about drift, it says the checkout is partial,
    # and firing on it made the accept fixture fail for a reason unrelated to
    # what the fixture was testing. A check that fails a fixture for the wrong
    # reason teaches nothing when it passes.
    stale = sorted(n for n in (set(EXEMPT) - ci_scripts)
                   if (ROOT / "scripts" / n).exists())
    for name in stale:
        fails.append(f"C-3 scripts/{name} exists and is declared EXEMPT, and no "
                     f"workflow runs it. A dead exemption hides the next real one.")

    if fails:
        print(f"WORKFLOW CONTRACT FAILED: {len(fails)} finding(s)")
        for f in fails:
            print(f"  {f}")
        return 1
    if not quiet:
        print(f"OK   workflow contract holds: {len(ci_scripts)} CI scripts, "
              f"{len(controls)} local controls, {len(EXEMPT)} declared exemptions, "
              f"tracked via {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
