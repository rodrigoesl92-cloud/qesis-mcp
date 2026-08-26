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

  C-4 LOCAL SET REACHABILITY. Every script in the selfheal control set is
      tracked, or untracked and not ignored (the lander's `git add -A` will
      stage it), or absent from this repository (out of scope, reported by
      name). Only IGNORED-on-disk fails: that is the L-135 class, a file git
      silently skips. Index membership alone was the wrong predicate (L-173).

  C-5 REQUIREMENTS INSTALL IS GUARDED OR SATISFIED. Every `pip install -r X`
      in a workflow names a file that exists in THIS repository, or the same
      `run:` block guards it with `[ -f X ]` (or `test -f X`). selfheal.yml is
      paired byte-identical into sovereign-infra, which has no requirements.txt;
      the unguarded step failed there in eight seconds every hour and the loop
      never reached a control (L-175). Third occurrence of the family
      paired_what_is_not_pairable (L-170, L-171), so this check is a release
      blocker: both integrity workflows run this gate, and the gate runs its
      own fixtures before it judges anything (V-2).

Usage:  python scripts/verify_workflow_contract.py [--quiet]
        python scripts/verify_workflow_contract.py --selftest
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
    "build_ops_report.py": "a generator, not a gate. It reports the control set and cannot "
    "also be a member of it without asserting its own output. The gate it depends on, "
    "verify_ledger_singleton.py, IS in CONTROLS and is where a ledger defect fails.",
    "rdl.py": "the ladder executor. `rdl.py ci-blocking` is a RELEASE gate and belongs in "
    "qesis-integrity.yml, not in the hourly loop. A family at rung 3 stays at rung 3 until "
    "its gate lands, so putting it in CONTROLS would escalate on every run, and L-063 says "
    "an escalation that fires every cycle has been switched off without anyone deciding to "
    "switch it off. The loop reports the ladder; the release refuses on it.",
    # The evidence plane's own CI scripts (sovereign-infra/compliance.yml). One
    # runner and one contract serve both repositories, so the contract has to
    # know both script sets or it fails the repository it never visited (L-171).
    "build_concordance.py": "a generator with a --check mode, run by compliance.yml (G-02). "
    "A concordance drift is a build-time finding against the served index, which the "
    "evidence plane does not carry, so the hourly loop cannot evaluate it there.",
    "scan_credentials.py": "sovereign-infra's history-aware credential scan. It runs `git log`, "
    "and the loop may execute on the analysis mount, where any git command takes and "
    "abandons .git/index.lock (L-122, L-123). It runs on the runner in compliance.yml, where "
    "git is safe, and its findings are class C there exactly as verify_secrets is here.",
}
# git_unlock.py was briefly listed above and removed the same session: no
# workflow runs it, so an exemption for it is dead, and C-3's own message is
# right that a dead exemption hides the next real one. It is a host-side repair
# invoked by the lander, which is not CI. L-048: the target state for EXEMPT is
# empty, and it does not get padded with entries that were never needed.


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


def ignored_by_git(rel: str) -> bool | None:
    """Would `git add -A` skip this path? True ignored, False not, None unknown.

    THE RESOURCE, NOT THE PROXY (L-173). Whether CI will have a file is decided
    by two things: it is tracked, or it is untracked and NOT ignored, in which
    case the lander's `git add -A` stages it. Membership in the index is a proxy
    for the second case and a wrong one: a control script added in this change
    set is never in the index before the lander stages it, so a C-4 that read
    only `git ls-files` refused every new control script forever, exactly the
    gate no correct action can satisfy (SH-10f). `git check-ignore` reads the
    ignore rules and writes nothing.
    """
    import subprocess
    try:
        r = subprocess.run(["git", "check-ignore", "-q", "--", rel], cwd=ROOT,
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode == 0:
        return True
    if r.returncode == 1:
        return False
    return None


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


#: C-5. `pip install ... -r FILE` or `--requirement FILE`, one capture: the file.
REQ_RE = re.compile(r"\bpip\s+install\b[^\n]*?\s(?:-r|--requirement)[\s=]+([^\s;&|)]+)")


def run_blocks(text: str) -> list[tuple[int, str]]:
    """Every `run:` block in a workflow as (line number, body text).

    A scalar `run: cmd` is one line. A literal or folded `run: |` block is every
    following line indented deeper than the `run` key, blank lines included. The
    key's column is what ends the block, not the first blank line: the block
    reader that stopped at a blank line is the L-134 shape, a parser that reads
    part of a structure and reports confidently on all of it.
    """
    lines = text.splitlines()
    blocks: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)(-\s+)?run:\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        key_col = len(m.group(1)) + (len(m.group(2)) if m.group(2) else 0)
        rest = m.group(3).strip()
        if rest and not rest[0] in "|>":
            blocks.append((i + 1, rest))
            i += 1
            continue
        body: list[str] = []
        j = i + 1
        while j < len(lines):
            line = lines[j]
            if not line.strip():
                body.append("")
                j += 1
                continue
            if len(line) - len(line.lstrip()) <= key_col:
                break
            body.append(line)
            j += 1
        blocks.append((i + 1, "\n".join(body)))
        i = j
    return blocks


def requirement_findings(wf_name: str, text: str, root: Path) -> list[str]:
    """C-5 over one workflow text against one repository root. Pure."""
    out: list[str] = []
    for lineno, body in run_blocks(text):
        for m in REQ_RE.finditer(body):
            req = m.group(1).strip("'\"")
            if "$" in req or "{{" in req:
                continue  # an expression; not decidable here, and not a literal claim
            if (root / req).exists():
                continue
            guard = re.compile(r"(?:\[\[?\s*-[fes]\s+" + re.escape(req) + r"\s*\]\]?|\btest\s+-[fes]\s+"
                               + re.escape(req) + r"\b)")
            if guard.search(body):
                continue
            out.append(f"C-5 {wf_name}:{lineno} installs `-r {req}` and this repository has no "
                       f"{req}; the step runs unguarded and fails before any control runs. "
                       f"Guard the block with `[ -f {req} ]` or add the file. A workflow paired "
                       f"into a repository must not assume that repository's files (L-175).")
    return out


def selftest() -> int:
    """V-2 fixtures for C-5: one refuse, two accept. Run before every judgement."""
    import tempfile
    root = Path(tempfile.mkdtemp())
    unguarded = ("jobs:\n  j:\n    steps:\n      - name: Install runtime\n"
                 "        run: python -m pip install --quiet -r requirements.txt\n"
                 "      - run: echo done\n")
    guarded = ("jobs:\n  j:\n    steps:\n      - name: Install runtime\n"
               "        run: |\n"
               "          if [ -f requirements.txt ]; then\n"
               "            python -m pip install --quiet -r requirements.txt\n"
               "          fi\n"
               "      - run: echo done\n")
    cases = [
        ("C-5 refuses an unguarded `-r requirements.txt` where the file is absent",
         len(requirement_findings("w.yml", unguarded, root)) == 1),
        ("C-5 accepts the same install inside `[ -f requirements.txt ]`",
         requirement_findings("w.yml", guarded, root) == []),
    ]
    (root / "requirements.txt").write_text("", encoding="utf-8")
    cases.append(("C-5 accepts an unguarded install where the file exists",
                  requirement_findings("w.yml", unguarded, root) == []))
    ok = all(v for _, v in cases)
    for name, v in cases:
        print(f"  {'PASS' if v else 'FAIL'}  {name}")
    print(f"workflow contract selftest: {sum(v for _, v in cases)}/{len(cases)} fixtures "
          + ("hold" if ok else "FAILED"))
    return 0 if ok else 1


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
    if "--selftest" in sys.argv:
        return selftest()
    # The gate proves its own fixtures before it judges the repository. A gate
    # whose fixtures fail has no standing to pass anything (V-2), and running
    # them here means the evidence plane, which has no test_gate.py, proves
    # them in its own CI too.
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        st = selftest()
    if st != 0:
        print(buf.getvalue(), end="")
        print("WORKFLOW CONTRACT FAILED: the gate's own fixtures do not hold")
        return 1
    fails: list[str] = []
    if not WORKFLOWS.is_dir():
        print("FAIL .github/workflows is not a directory")
        return 1

    controls = local_controls()
    tracked, mode = tracked_scripts()
    ci_scripts: set[str] = set()
    will_stage: list[str] = []

    def reach_status(name: str, mode: str) -> str:
        """absent | ignored | will_stage, for a script git does not track."""
        if not (ROOT / "scripts" / name).exists():
            return "absent"
        if mode != "git ls-files":
            return "will_stage"  # no git here; on disk is all that can be known
        ign = ignored_by_git(f"scripts/{name}")
        return "ignored" if ign else "will_stage"

    for wf in sorted(WORKFLOWS.glob("*.yml")):
        text = wf.read_text(encoding="utf-8")
        perms = declared_permissions(text)

        # C-5
        fails.extend(requirement_findings(wf.name, text, ROOT))

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
                    status = reach_status(name, mode)
                    if status == "absent":
                        fails.append(f"C-2 {wf.name}:{lineno} references scripts/{name}, "
                                     "which does not exist at all")
                    elif status == "ignored":
                        fails.append(f"C-2 {wf.name}:{lineno} references scripts/{name}, "
                                     "which exists on disk, is NOT TRACKED, and is IGNORED "
                                     "by .gitignore: `git add -A` will skip it and CI will "
                                     "not have it (L-135). `git check-ignore -v` names the rule.")
                    else:
                        will_stage.append(name)
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
    #
    # Two conditions, and only one is a finding. ON DISK BUT UNTRACKED is the
    # L-135 class: local green, CI red, nothing said so. ABSENT ENTIRELY is
    # scope: one control set serves both repositories, and selfheal.py's
    # controls_present() reports an absent script as out of scope rather than
    # as a failure. The first version of this check conflated the two and
    # produced twelve findings in sovereign-infra for scripts that gate the
    # served index and have never belonged there (L-171). Scope is reported
    # by name, so it is never silent, and never failed, so it is never noise.
    out_of_scope: list[str] = []
    for name in sorted(controls):
        if name in tracked:
            continue
        status = reach_status(name, mode)
        if status == "ignored":
            fails.append(f"C-4 scripts/{name} is in the selfheal control set, is on disk, "
                         "is NOT TRACKED, and is IGNORED by .gitignore, so `git add -A` "
                         "skips it and CI cannot run it (L-135). `git check-ignore -v` names the rule.")
        elif status == "absent":
            out_of_scope.append(name)
        else:
            will_stage.append(name)

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
        if out_of_scope:
            print(f"     scope: {len(out_of_scope)} control script(s) absent from this "
                  "repository, out of scope here per selfheal.controls_present(): "
                  + ", ".join(out_of_scope))
        if will_stage:
            print(f"     untracked, not ignored: {len(will_stage)} script(s) on disk that "
                  "`git add -A` will stage, so CI will have them once this change set lands: "
                  + ", ".join(sorted(set(will_stage))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
