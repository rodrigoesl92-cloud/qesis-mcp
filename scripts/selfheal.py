"""G-07. The autonomous remediation loop.

The ecosystem runs continuously and repairs itself. This is the runner that does
it. It executes the declared control set, classifies every failure against the
remedy registry, applies what the record already authorises, records the lesson,
and escalates only what cannot be derived from the record.

THE DESIGN CLAIM, STATED SO IT CAN BE ATTACKED
  Most defects in this ecosystem are not novel. They are a known family arriving
  on a new surface, and the correct action is written down before the defect
  happens: a gate exists, a threshold is declared, a doctrine names the refusal.
  Where that is true no human is needed and asking one is waste. Where it is not
  true, an agent inventing a remedy is the failure this whole project exists to
  catch, so it refuses, degrades safely, and says so.

  The registry below is the boundary between those two cases. It is data, not
  judgement, and it is auditable by reading it.

WHAT THIS RUNNER WILL NOT DO, AND WHY IT IS NOT TIMIDITY
  It does not promote to production (G-06 limit 2). It does not touch credential
  material in either direction (G-03, G-04). It does not sign an Article 14
  decision (the register holds 25 and none is signed by an agent). Those three
  are not agent policy. They are the operator's standing rules, and a runner that
  quietly widened them would be the exact defect class it exists to close.

  Under G-07 the first of those becomes a POLICY the operator signs once, after
  which promotion proceeds automatically whenever the policy predicate holds.
  That is Human-on-the-Loop applied to promotion, exactly as G-06 applied it to
  merge. The predicate is `promotion_policy` below. Until it is signed it
  evaluates to False and the runner escalates instead.

Usage:
    python scripts/selfheal.py                 diagnose, repair, report
    python scripts/selfheal.py --dry-run       diagnose and report, change nothing
    python scripts/selfheal.py --report-only   emit the report, run no remedy
    python scripts/selfheal.py --selftest      V-2 fixtures for the runner itself
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPS = ROOT / "ops"
REPORT = OPS / "SELFHEAL_LATEST.json"


# ── the control set. V-4: audit the set, never one member of it. ────────────
#: The capability probe's filename. Fixed, never timestamped (L-142).
PROBE_NAME = ".selfheal_probe"

CONTROLS = [
    ("verify_index",           ["scripts/verify_index.py"]),
    ("verify_chain",           ["scripts/verify_chain.py"]),
    ("verify_vintage_pairing", ["scripts/verify_vintage_pairing.py"]),
    ("verify_axis_sfc",        ["scripts/verify_axis_sfc.py", "--quiet"]),
    ("verify_action_pinning",  ["scripts/verify_action_pinning.py"]),
    ("verify_secrets",         ["scripts/verify_no_plaintext_secrets.py", "--quiet"]),
    ("verify_workflow",        ["scripts/verify_workflow_contract.py", "--quiet"]),
    # L-146, L-147. The ledger existed in two repositories and the copies named
    # two different lessons under L-119 and L-120 for four days. L-073 has made a
    # duplicate id a build failure since it was written and nothing failed,
    # because no control had ever been pointed at the ledger itself. R3 degrades
    # when the sibling repository is not checked out, which is the normal state
    # under CI and is not an escalation.
    ("verify_ledger_singleton", ["scripts/verify_ledger_singleton.py", "--quiet"]),
    ("kill_switch",            ["scripts/kill_switch.py"]),
    ("build_graph_check",      ["scripts/build_graph.py", "--check"]),
    ("build_percolation_check", ["scripts/build_percolation_block.py", "--check"]),
    ("self_exposure_check",    ["scripts/self_exposure.py", "--check"]),
    ("build_eval_check",       ["scripts/build_eval.py", "--check"]),
    ("build_landing_check",    ["scripts/build_landing.py", "--check"]),
    # Runs in CI through production-integrity-probe.yml, so it is in the control
    # set and not in EXEMPT (L-183). Fixtures here, live assertion there: the
    # self-heal loop must not go red because a third party had a bad minute.
    ("public_domain",         ["scripts/verify_public_domain.py", "--selftest"]),
    # Every model, every session type, reads ops/ECOSYSTEM_STATE.json and
    # ops/PATH_REGISTRY.json before asserting anything. Those files are only
    # trustworthy if a stale copy fails the build, so the check joins the set.
    ("ecosystem_state_check",  ["scripts/build_ecosystem_state.py", "--check"]),
    # C-3 set parity, and both of these are controls in their own right rather
    # than exemptions. `gh_ops.py runner-merge --selftest` decides over canned
    # values, so it runs with no network and no credential, which is the only
    # form in which a gate over a merge can run at all (G-03, G-04). The reading
    # contract is the same shape: data on disk, a predicate over it, an exit
    # code. Both entered CI with D-117 and D-118 and both belong in the set the
    # loop re-runs, not in EXEMPT, whose target state is empty (L-048).
    ("runner_merge_selftest",  ["scripts/gh_ops.py", "runner-merge", "--selftest"]),
    ("reading_contract",       ["scripts/verify_reading_contract.py", "--quiet"]),
    ("test_gate",              ["scripts/test_gate.py"]),
]


def controls_present(root: Path = ROOT) -> list:
    """The controls whose script actually exists in THIS repository.

    ONE runner serves both repositories. qesis-mcp holds 59 scripts and gates the
    served index; sovereign-infra holds 42 and is the evidence plane. Running the
    full list in the evidence plane fails on nineteen scripts that were never
    supposed to be there, which is what happened on 2026-08-24 when the qesis-mcp
    workflow was paired across as if it were a governance document.

    A control whose script is absent is REPORTED as out of scope, never silently
    dropped and never counted as a pass. D-007: withheld with cause. The
    promotion predicate reads this list, so a missing script cannot inflate a
    green run into a promotion.
    """
    have, absent = [], []
    for name, cmd in CONTROLS:
        target = root / cmd[0]
        (have if target.exists() else absent).append((name, cmd))
    if absent:
        print(f"  scope: {len(absent)} control(s) out of scope in this repository, "
              "script not present: " + ", ".join(n for n, _ in absent))
    return have


def load_kill_switch(root: Path = ROOT) -> tuple[bool, str, dict]:
    """Article 14 Decision 5, read wherever the runner is.

    L-171. `scripts/kill_switch.py` was loaded unconditionally, and it existed in
    one repository only. In sovereign-infra the runner died on a FileNotFoundError
    before reading a single control, the `heal` job failed on every hourly run,
    and the failure read as an escalation when it was a crash. ONE runner serves
    both repositories (see controls_present), so the stop control must be read
    the same way everywhere: the module when it is present, the emergency
    environment channel directly when it is not, and the absence reported as a
    degradation rather than swallowed. A stop control that fails closed (crash)
    is as useless as one that fails open: nothing reads a crashed runner.
    """
    import importlib.util as _ilu
    import os
    script = root / "scripts" / "kill_switch.py"
    if script.exists():
        _spec = _ilu.spec_from_file_location("_ks", script)
        _ks = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_ks)
        return _ks.state()
    env = os.environ.get("QESIS_KILL_SWITCH", "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True, "environment", {"variable": "QESIS_KILL_SWITCH", "value": env,
                                     "note": "read directly; scripts/kill_switch.py absent here"}
    switch = root / "ops" / "KILL_SWITCH.json"
    if switch.exists():
        try:
            d = json.loads(switch.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return True, "file", {"error": f"unparseable, failing safe: {exc}"}
        return bool(d.get("engaged") is True), "file", d
    return False, "absent", {
        "degraded": "kill_switch_module_absent",
        "note": "scripts/kill_switch.py and ops/KILL_SWITCH.json are both absent from this "
                "checkout. The environment channel was read directly and is clear. Pair "
                "the switch into this repository; a stop control that exists in one "
                "repository of a pair stops half the ecosystem."}


def _assert_controls_unique(controls=None) -> None:
    """L-152, exposure 1. Two sessions both added verify_ledger_singleton to
    CONTROLS on 2026-08-24 and the list held it twice. That raises no syntax
    error, runs the gate twice, and double counts it in the totals the G-07
    section 4.1 promotion predicate reads, which "every control returns PASS"
    then satisfies twice. Nothing in the ecosystem detected it. This does."""
    names = [n for n, _ in (CONTROLS if controls is None else controls)]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise SystemExit(
            "SELFHEAL REFUSES: duplicate control(s) in CONTROLS: "
            + ", ".join(dupes)
            + ". A duplicated control inflates the count the promotion predicate "
              "reads. L-152."
        )


_assert_controls_unique()


# ── the remedy registry. This IS the autonomy boundary, and it is data. ─────
#
# class A  the record already declares the remedy. Apply it, record it, continue.
# class B  no declared remedy, but the safe degradation is declared. Refuse and
#          degrade rather than guess. This is BIG withholding generalised: a
#          value that cannot be established is withheld, never imputed (D-007).
# class C  cannot be derived from the record. Escalate with the command that
#          would settle it, never with a guess.
REMEDIES = {
    "ecosystem_state_check": {
        "class": "A",
        "why": "The state and path files are derived from the repository and "
               "recompute nothing. A drift means the artefact stopped deriving, "
               "and regenerating is the declared remedy and is idempotent.",
        "run": ["scripts/build_ecosystem_state.py"],
        "reverify": True,
    },
    "build_graph_check": {
        "class": "A",
        "why": "The graph is derived from the index and from nothing else, so a "
               "mismatch means the artefact stopped deriving. Rebuilding is the "
               "declared remedy and it is idempotent by construction.",
        "run": ["scripts/build_graph.py"],
        "reverify": True,
    },
    "build_percolation_check": {
        "class": "A",
        "why": "Same shape. The block reads the evidence file and recomputes "
               "nothing, so a rebuild cannot introduce a number.",
        "run": ["scripts/build_percolation_block.py"],
        "reverify": True,
    },
    "self_exposure_check": {
        "class": "A",
        "why": "The instrument's own exposure is derived from a declared substrate "
               "table and recomputes nothing. A drift means the table moved and the "
               "artefact did not, which is D-113 losing its evidence.",
        "run": ["scripts/self_exposure.py"],
        "reverify": True,
    },
    "build_eval_check": {
        "class": "A",
        "why": "The eval set is generated from the index. The v8.0 set was "
               "hand-written and began failing correct answers the moment the "
               "index was corrected, which is why it is generated now.",
        "run": ["scripts/build_eval.py"],
        "reverify": True,
    },
    "build_landing_check": {
        "class": "A",
        "why": "The page is generated from the index and must not state a number "
               "the index no longer holds.",
        "run": ["scripts/build_landing.py"],
        "reverify": True,
    },
    "verify_index": {
        "class": "C",
        "why": "A failing index gate means a served number disagrees with its own "
               "axes, or a declared control was removed. Neither has a mechanical "
               "remedy: rebuilding would overwrite the evidence of the defect. "
               "This is the one failure where speed is the enemy.",
        "escalate_with": "python scripts/verify_index.py   (read the R-code it names)",
    },
    "verify_chain": {
        "class": "C",
        "why": "A broken hash chain is an EU AI Act Article 12 record-keeping "
               "failure. It is never repaired by an agent, because a chain an "
               "agent can rewrite is not a chain.",
        "escalate_with": "python scripts/verify_chain.py",
        "severity": "CRITICAL",
        # Both verifiers document exit 2 as COULD NOT CHECK, distinct from exit 1,
        # a break. In sovereign-infra the store is var/qesis_ops.sqlite, which is
        # gitignored by D-027, so every runner checkout exits 2. Reading that as
        # a CRITICAL break escalated on every hourly run, which is the escalation
        # that fires every cycle and gets ignored (L-063, SH-5). Withheld with
        # cause instead (D-007): the chain is verified where the store is.
        "degrade_on_exit": {2: "store_not_reachable_from_this_checkout"},
    },
    "verify_vintage_pairing": {
        "class": "B",
        "why": "Either the register lacks a row for the served vintage, or the "
               "tail disagrees with it. Both are recordable without inventing a "
               "vintage: the safe degradation is to refuse the promotion and "
               "leave the register untouched, never to write the missing row, "
               "because a row written by the process that failed the check is "
               "the check answering itself.",
        "degrade": "block_promotion",
    },
    "verify_axis_sfc": {
        "class": "B",
        "why": "A withheld axis reporting a status that disagrees with its "
               "measured coverage. The declared degradation is WITHHELD WITH "
               "CAUSE. Values are withheld, never imputed (D-007).",
        "degrade": "withhold_with_cause",
    },
    "verify_workflow": {
        "class": "C",
        "why": "A workflow whose declared permissions disagree with what its "
               "steps do, or whose script set has drifted from the local control "
               "set, is a governance defect rather than a drifted artefact. "
               "Rewriting a permissions block automatically would let the loop "
               "widen its own authority, which is the one thing G-07 refuses "
               "outright.",
        "escalate_with": "python scripts/verify_workflow_contract.py",
        "severity": "HIGH",
    },
    "verify_secrets": {
        "class": "C",
        "why": "A reachable secret is never remediated by an agent. Deleting the "
               "line does not un-disclose the value, and cloud sync retains "
               "provider-side history that survives local deletion, so rotation "
               "is the only remedy and rotation is a human act (G-03, G-04).",
        "escalate_with": "python scripts/verify_no_plaintext_secrets.py",
        "severity": "CRITICAL",
    },
    "kill_switch": {
        "class": "B",
        "why": "A non-zero exit here means the switch is engaged, which is the "
               "operator's decision working rather than a defect. The loop halts "
               "before this registry is consulted; the entry exists so the "
               "control appears in the reported set rather than being invisible "
               "when it is doing its job.",
        "degrade": "halt",
    },
    "verify_action_pinning": {
        "class": "C",
        "why": "Resolving an action tag to a commit SHA requires an authenticated "
               "API call, and a supply-chain SHA is NEVER guessed. The runner "
               "names the command and refuses the value, exactly as it does for a "
               "credential.",
        "escalate_with": "gh api repos/<owner>/<repo>/commits/<tag> --jq .sha",
    },
    "verify_ledger_singleton": {
        "class": "A",
        "run": ["scripts/ledger_sync.py"],
        "reverify": True,
        "remedy_scope": "R3 mirror drift that is MECHANICAL: an entry present in one "
                        "copy only, or a line-ending or trailing-newline difference. "
                        "scripts/ledger_sync.py takes the union by id and writes every "
                        "copy in one canonical form. It REFUSES (exit 2, nothing written) "
                        "a duplicate id, a prelude that differs, or the same id carrying "
                        "two texts, so those reach the escalation below through the "
                        "failed reverify rather than being guessed at. L-169.",
        "why": "A duplicate lesson id has been a build failure since L-073, and "
               "the ledger is the canonical record every later session reads as "
               "fact. There is no mechanical remedy: renumbering an id strands "
               "every document that cites it, which is the same harm G-02 gives "
               "the concordance to prevent, and merging two entries under one id "
               "destroys the one of them that was not a copy. An undeclared gap "
               "is settled by writing the reason into ops/LEDGER_GAPS.json, and "
               "the reason is knowledge the runner does not have. Withheld with "
               "cause rather than imputed (D-007).",
        "escalate_with": "python scripts/verify_ledger_singleton.py   "
                         "(R1 duplicate, R2 undeclared gap, R3 sibling drift)",
        "severity": "HIGH",
    },
    "test_gate": {
        "class": "C",
        "why": "The gate self-test failing means a control stopped catching what "
               "it claims to catch. Repairing the gate automatically would let "
               "the runner decide what counts as caught, which is the system "
               "grading its own homework (L-072).",
        "escalate_with": "python scripts/test_gate.py",
        "severity": "CRITICAL",
    },
}

#: Known-environmental, never a defect. Checked against its clause, not assumed
#: (V-3). CI installs requirements.txt before the gates; a local shell may not.
#:
#: Matched PER FAILING BEHAVIOUR, not per run. Matching per run would let one
#: environmental miss mark a whole suite benign, and refusing to match at all
#: would escalate CRITICAL on every cycle for a condition nobody can fix locally.
#: A check whose false positives are routine has been switched off without anyone
#: deciding to switch it off (L-063), and a scheduler is where that happens
#: fastest, because nobody reads the ninetieth identical alert.
BENIGN = [
    ("test_gate", "verifier cannot run",
     "Local runtime lacks mcp/pydantic, so verify_served_contract cannot import "
     "server.py. CI installs requirements.txt before the gates."),
    ("test_gate", "skipped: build idempotence",
     "Canonical sources are operator-local and absent from a public checkout."),
]

#: Output lines that mark a failed behaviour inside a suite that reports a ratio.
FAIL_MARKERS = ("  X   ", "  X  ")


def git_writes_safe() -> tuple[bool, str]:
    """Preflight. Can this filesystem complete a git write, not merely start one?

    Measured 2026-08-15 on the analysis mount: `git add -A` staged ZERO files and
    left FORTY `tmp_obj_*` files in `.git/objects`. Git writes an object to a
    temporary name and renames it into place, and this mount permits the create
    and refuses the unlink and the rename. So the command reports warnings,
    exits zero, changes nothing, and litters the object store.

    That is the worst available failure mode: it looks like it worked, it did
    not, and it left damage behind. A blocked write is safe because it is
    visible. A half-write is not.

    The probe is create-then-unlink inside `.git`, because unlink is the
    capability that actually fails. Probing for write permission alone would
    return True here and be wrong, which is L-118 family B: a claim about a
    resource made from a proxy for that resource rather than from the resource.

    Measured again 2026-08-15, and the second measurement is the important one:
    the operator cleared `.git/index.lock` and it reappeared within a minute,
    timestamped one minute after an agent `git status` and OWNED BY THE SANDBOX
    USER. The lock was never stale. Every git command run from this mount creates
    one and cannot unlink it, so the agent was manufacturing the blocker it kept
    reporting, then telling the operator to clear it (L-123).

    Therefore the rule this function enforces is stronger than "warn before
    writing": where this returns False, **no git command is run from here at
    all**, including read-only ones, because `status`, `add` and `diff` all take
    the index lock and all leave it behind.
    """
    # FIXED name, not a timestamped one. L-142: the first version stamped the
    # probe with `int(datetime.now().timestamp())`, so on the one filesystem the
    # probe exists to detect, every run created a file it could not remove and
    # fourteen accumulated inside `.git`. A diagnostic whose failure path grows
    # without bound is L-063 arriving from the other side: not an alarm nobody
    # reads, litter nobody attributes. A fixed name overwrites its predecessor,
    # so the leak is bounded at one file and the create-then-unlink probe still
    # measures exactly the capability that fails, which is UNLINK (L-122).
    probe = ROOT / ".git" / PROBE_NAME
    if not (ROOT / ".git").is_dir():
        return False, "no .git directory reachable from here"
    try:
        probe.write_text("probe", encoding="utf-8")
    except OSError as exc:
        return False, f"cannot create inside .git: {exc.strerror}"
    try:
        probe.unlink()
    except OSError as exc:
        return False, (f"can create but CANNOT UNLINK inside .git: {exc.strerror}. "
                       f"Git writes will half-complete and litter .git/objects. "
                       f"Leftover probe: {probe.name}")
    return True, "git writes complete on this filesystem"


def run(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run([sys.executable, *[str(ROOT / c) if c.endswith(".py") else c
                                          for c in cmd]],
                       capture_output=True, text=True, cwd=ROOT, timeout=600)
    return r.returncode, (r.stdout + r.stderr)


def benign_reasons(name: str, out: str) -> tuple[bool, list[str]]:
    """True only when EVERY failing behaviour in the output is a declared benign.

    Returns (all_benign, reasons). A suite with one environmental miss and one
    real miss is not benign, and the distinction has to be made line by line or
    it is not being made at all.
    """
    failing = [l for l in out.splitlines()
               if any(l.startswith(m) for m in FAIL_MARKERS)]
    if not failing:
        return False, []
    reasons, unexplained = [], []
    for line in failing:
        hit = next((why for n, needle, why in BENIGN
                    if n == name and needle in line), None)
        if hit:
            reasons.append(f"{line.strip()[:70]} -> {hit}")
        else:
            unexplained.append(line.strip()[:90])
    if unexplained:
        return False, [f"UNEXPLAINED: {u}" for u in unexplained]
    return True, reasons


def promotion_policy(state: dict) -> tuple[bool, str]:
    """G-07. Promotion proceeds automatically only when the operator has signed
    the policy AND the predicate holds. Unsigned, this is always False.

    The predicate is deliberately narrow. Promotion is what publishes, and the
    Article 14 failure analysis found `CON * RET * HIT * MCP` surviving the
    consistency cutoff at 0.822 WITH the human gate present. Human oversight is a
    damper, not an immunity, which is the argument for a kill switch independent
    of the approval gate rather than redundant with it. A promotion policy that
    fires on anything less than a fully green control set removes the damper
    without replacing it.
    """
    # Article 14 Decision 5 outranks Decision 25. A signed promotion policy does
    # not survive an engaged kill switch, and the order of these two checks is
    # the whole content of "the stop control clears first".
    engaged, channel, _ = load_kill_switch()
    if engaged:
        return False, f"KILL SWITCH ENGAGED via {channel}. Decision 5 outranks Decision 25."

    signed = (OPS / "G-07_PROMOTION_POLICY_SIGNED.json")
    if not signed.exists():
        return False, ("promotion policy unsigned. Article 14 Decision 25 and "
                       "G-07 section 4 are the instrument. Escalating instead.")
    if state["failed"] or state["escalations"]:
        return False, "control set not fully green"

    # A class B degradation whose DECLARED degradation is block_promotion must
    # block it. Without this the policy read only failures and escalations, so
    # verify_vintage_pairing could degrade to block_promotion and promotion would
    # proceed anyway: the registry declared a consequence and the policy did not
    # read it. That is a rule described and not applied (L-054), committed inside
    # the function whose entire job is to apply rules.
    blockers = [d["control"] for d in state["degraded"]
                if d.get("degradation") == "block_promotion"]
    if blockers:
        return False, ("declared block_promotion degradation on "
                       + ", ".join(blockers))
    return True, "policy signed and predicate holds"



def action_gap(state: dict) -> dict:
    """The agentic action gap, instrumented on what this loop already emits.

    Forrester, Mind The Agentic Action Gap (2026), defines the gap as the distance
    between an agent-generated insight and a value-driving action, measured on
    friction, time to action, and adoption. The loop was already emitting the
    numerator and the denominator of all three and aggregating none of them, so
    this is instrumentation rather than a new measurement.

    Friction is the count of findings that cannot be executed without a human:
    class C escalations plus unclassified failures. That is the count the loop
    exists to drive to zero.

    The empty denominator is deliberately null and not 1.0. A run with no findings
    has no execution rate, and a loop that reports a perfect rate on an empty
    denominator is asserting rather than measuring (L-055).
    """
    detected = [c for c in state["controls"] if c.get("status") == "FAIL"]
    applied = [r for r in state["repaired"] if r.get("applied")]
    held = [r for r in applied if r.get("ok")]
    times = [r["seconds_to_action"] for r in applied
             if r.get("seconds_to_action") is not None]
    return {
        "definition": "Forrester, Mind The Agentic Action Gap (2026). Framework "
                      "applied; the report itself is a single-use reprint and is "
                      "neither redistributed nor indexed (SA-007).",
        "friction_points": len(state["escalations"]) + len(state["failed"]),
        "friction_is": "class C escalations plus unclassified failures, which are "
                       "exactly the findings a human must execute",
        "time_to_action_seconds": {
            "measured_repairs": len(times),
            "total": round(sum(times), 3) if times else 0.0,
            "slowest": round(max(times), 3) if times else 0.0,
            "note": "null in dry-run and report-only mode, where nothing is applied",
        },
        "unmodified_execution_rate": (round(len(held) / len(detected), 4)
                                      if detected else None),
        "unmodified_execution_is": f"{len(held)} repairs held over "
                                   f"{len(detected)} findings this run",
        "empty_denominator_reads_as": "null, never 1.0",
    }


def selftest() -> int:
    """V-2 for the runner itself, added at rung 2 of paired_what_is_not_pairable.

    ACCEPT: a checkout that carries only part of the control set and no kill
    switch module. The runner must enumerate what is present, report the rest as
    out of scope, read the stop control without crashing, and honour the
    environment channel directly.
    REFUSE: a duplicated control name, which inflates the count the promotion
    predicate reads (L-152).
    """
    import os
    import tempfile
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "partial-checkout"
        (root / "scripts").mkdir(parents=True)
        (root / "ops").mkdir()
        (root / "scripts" / "verify_ledger_singleton.py").write_text("", encoding="utf-8")
        have = controls_present(root)
        if [n for n, _ in have] != ["verify_ledger_singleton"]:
            fails.append(f"partial checkout enumerated {[n for n, _ in have]}")
        engaged, channel, detail = load_kill_switch(root)
        if engaged or channel != "absent" or not detail.get("degraded"):
            fails.append(f"absent kill switch was not reported as a degradation: {channel} {detail}")
        os.environ["QESIS_KILL_SWITCH"] = "1"
        try:
            engaged, channel, _ = load_kill_switch(root)
        finally:
            os.environ.pop("QESIS_KILL_SWITCH", None)
        if not engaged or channel != "environment":
            fails.append("environment channel was not honoured without the module")
        (root / "ops" / "KILL_SWITCH.json").write_text('{"engaged": true}', encoding="utf-8")
        engaged, channel, _ = load_kill_switch(root)
        if not engaged or channel != "file":
            fails.append("file channel was not honoured without the module")
        (root / "ops" / "KILL_SWITCH.json").write_text("{broken", encoding="utf-8")
        engaged, _, _ = load_kill_switch(root)
        if not engaged:
            fails.append("an unparseable switch file failed open")
    try:
        _assert_controls_unique([("a", ["x.py"]), ("a", ["y.py"])])
        fails.append("a duplicated control name was accepted")
    except SystemExit:
        pass
    for f in fails:
        print(f"SELFTEST FAIL: {f}")
    print("SELFHEAL SELFTEST: " + ("PASSED, 6 fixtures" if not fails else "FAILED"))
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    now = datetime.now(timezone.utc).isoformat()
    state = {"generated_utc": now, "mode": ("report-only" if args.report_only
                                            else "dry-run" if args.dry_run else "repair"),
             "controls": [], "repaired": [], "degraded": [], "escalations": [],
             "failed": [], "benign": []}

    print(f"selfheal {now}  mode={state['mode']}\n")

    # Decision 5 before everything. A loop that checks its stop control after it
    # has started repairing has not got a stop control, it has got a regret.
    ks_engaged, ks_channel, ks_detail = load_kill_switch()
    state["kill_switch"] = {"engaged": ks_engaged, "channel": ks_channel, "detail": ks_detail}
    if isinstance(ks_detail, dict) and ks_detail.get("degraded"):
        state["degraded"].append({"control": "kill_switch",
                                  "degradation": ks_detail["degraded"],
                                  "why": ks_detail["note"]})
        print(f"  !!  kill switch: {ks_detail['note']}")
    if ks_engaged:
        state["verdict"] = "HALTED"
        state["promotion"] = {"proceed": False,
                              "reason": f"kill switch engaged via {ks_channel}"}
        print(f"  !!  KILL SWITCH ENGAGED via {ks_channel}. No repair, no commit, no promotion.")
        print("      Production keeps serving its last verified deployment.")
        if not args.report_only:
            REPORT.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")
        # Exit 0. An engaged switch is the operator's decision working, not a
        # failure, and paging on it would train him to ignore the page (L-063).
        return 0

    # Preflight before any control runs. A loop that cannot land its own repair
    # must know that before it starts repairing, not after.
    gw_ok, gw_why = git_writes_safe()
    state["git_writes"] = {"safe": gw_ok, "detail": gw_why}
    if not gw_ok:
        state["degraded"].append({
            "control": "git_write_capability", "degradation": "host_only_git",
            "why": ("Repairs are written to the working tree and NOT committed "
                    "from here. " + gw_why + " Class B: the safe failure mode is "
                    "declared, so the loop degrades and continues rather than "
                    "escalating. The work is not lost, it is unlanded, and those "
                    "are different states (L-062).")})
        strays = list((ROOT / ".git" / "objects").glob("*/tmp_obj_*"))
        if strays:
            state["degraded"][-1]["stray_objects"] = len(strays)
        # The loop reports the litter git leaves and must report its own on the
        # same line of reasoning, or it is holding the tool to a standard it
        # exempts itself from. L-142.
        probes = sorted(p.name for p in (ROOT / ".git").glob(".selfheal_probe*"))
        legacy = [n for n in probes if n != PROBE_NAME]
        if probes:
            state["degraded"][-1]["stray_probes"] = len(probes)
            state["degraded"][-1]["legacy_probes"] = len(legacy)
        print(f"  !!  git writes UNSAFE here: {gw_why}")
        print(f"      repairs land in the working tree, commit from the host")
        if strays:
            print(f"      {len(strays)} stray tmp_obj_* in .git/objects, "
                  f"clear with: git prune ; git gc")
        if legacy:
            print(f"      {len(legacy)} legacy timestamped probe(s) in .git from "
                  f"before L-142, clear from the HOST with: "
                  f"Remove-Item .git\\.selfheal_probe_*")
    print()

    for name, cmd in controls_present():
        script = ROOT / cmd[0]
        if not script.exists():
            state["controls"].append({"name": name, "status": "ABSENT"})
            print(f"  ..  {name:24s} absent from this checkout")
            continue
        rc, out = run(cmd)
        _t_detect = time.monotonic()
        all_benign, reasons = (benign_reasons(name, out) if rc != 0 else (False, []))
        if all_benign:
            # Every failing behaviour is a declared environmental condition. The
            # control is reported PASS WITH BENIGN, never silently PASS: a
            # suppression nobody can see is a suppression nobody can audit.
            rc = 0
        status = ("PASS" if rc == 0 and not all_benign else
                  "PASS_WITH_BENIGN" if rc == 0 else "FAIL")
        state["controls"].append({"name": name, "status": status, "exit": rc,
                                  "tail": out.strip().splitlines()[-1:] or [""]})
        if reasons:
            state["benign"].append({"control": name, "all_benign": all_benign,
                                    "detail": reasons})
        print(f"  {'ok ' if rc == 0 else 'X  '} {name:24s} {status}")
        if rc == 0:
            continue

        rem = REMEDIES.get(name)
        if rem is None:
            state["failed"].append({"control": name,
                                    "why": "no registry entry. Unclassified "
                                           "failures are never repaired blind."})
            print(f"      UNCLASSIFIED. Not repaired. Registry has no entry.")
            continue

        # A documented "could not check" exit is a declared safe failure mode,
        # not the failure the control exists to catch. Class B by the record.
        deg = (rem.get("degrade_on_exit") or {}).get(rc)
        if deg:
            state["controls"][-1]["status"] = "DEGRADED"
            state["degraded"].append({"control": name, "degradation": deg,
                                      "why": f"exit {rc} is documented by the control as "
                                             "'could not check', not as a finding. Withheld "
                                             "with cause, never imputed (D-007)."})
            print(f"      class B degraded safely: {deg}")
            continue

        if rem["class"] == "A":
            if args.dry_run or args.report_only:
                print(f"      class A, would run {rem['run'][0]}")
                state["repaired"].append({"control": name, "applied": False,
                                          "would_run": rem["run"][0], "why": rem["why"],
                                          "seconds_to_action": None})
                continue
            rc2, _ = run(rem["run"])
            ok = rc2 == 0
            if ok and rem.get("reverify"):
                ok = run(cmd)[0] == 0
            state["repaired"].append({"control": name, "applied": True, "ok": ok,
                                      "ran": rem["run"][0], "why": rem["why"],
                                      "seconds_to_action": round(time.monotonic() - _t_detect, 3)})
            print(f"      class A repaired via {rem['run'][0]}: "
                  f"{'reverified' if ok else 'STILL FAILING, escalating'}")
            if not ok:
                state["escalations"].append({"control": name,
                                             "why": "declared remedy did not clear it",
                                             "command": " ".join(cmd)})

        elif rem["class"] == "B":
            state["degraded"].append({"control": name, "degradation": rem["degrade"],
                                      "why": rem["why"]})
            print(f"      class B degraded safely: {rem['degrade']}")

        else:
            state["escalations"].append({
                "control": name, "severity": rem.get("severity", "HIGH"),
                "why": rem["why"], "command": rem.get("escalate_with", " ".join(cmd))})
            print(f"      class C ESCALATION [{rem.get('severity','HIGH')}]")

    ok_promote, why = promotion_policy(state)
    state["promotion"] = {"proceed": ok_promote, "reason": why}

    state["action_gap"] = action_gap(state)

    green = not state["failed"] and not state["escalations"]
    state["verdict"] = ("GREEN" if green and not state["degraded"] else
                        "DEGRADED" if green else "ESCALATED")

    if not args.report_only:
        REPORT.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")

    print(f"\n  verdict {state['verdict']}   repaired {len(state['repaired'])}   "
          f"degraded {len(state['degraded'])}   escalations {len(state['escalations'])}")
    _ag = state["action_gap"]
    _rate = _ag["unmodified_execution_rate"]
    print(f"  action gap: friction {_ag['friction_points']}   "
          f"time to action {_ag['time_to_action_seconds']['total']}s over "
          f"{_ag['time_to_action_seconds']['measured_repairs']} repairs   "
          f"unmodified execution {'n/a (no findings)' if _rate is None else f'{_rate:.0%}'}")
    print(f"  promotion: {'PROCEED' if ok_promote else 'HELD'}  ({why})")
    for e in state["escalations"]:
        print(f"    [{e['severity']}] {e['control']}: {e['command']}")

    # Exit non-zero only on escalation. A repaired or safely degraded run is the
    # loop working, not the loop failing, and a scheduler that pages on both
    # trains the operator to ignore it.
    return 1 if state["escalations"] or state["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
