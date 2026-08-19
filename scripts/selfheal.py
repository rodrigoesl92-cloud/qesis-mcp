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
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPS = ROOT / "ops"
REPORT = OPS / "SELFHEAL_LATEST.json"


# ── the control set. V-4: audit the set, never one member of it. ────────────
CONTROLS = [
    ("verify_index",           ["scripts/verify_index.py"]),
    ("verify_chain",           ["scripts/verify_chain.py"]),
    ("verify_vintage_pairing", ["scripts/verify_vintage_pairing.py"]),
    ("verify_axis_sfc",        ["scripts/verify_axis_sfc.py", "--quiet"]),
    ("verify_action_pinning",  ["scripts/verify_action_pinning.py"]),
    ("build_graph_check",      ["scripts/build_graph.py", "--check"]),
    ("build_percolation_check", ["scripts/build_percolation_block.py", "--check"]),
    ("self_exposure_check",    ["scripts/self_exposure.py", "--check"]),
    ("build_eval_check",       ["scripts/build_eval.py", "--check"]),
    ("build_landing_check",    ["scripts/build_landing.py", "--check"]),
    ("test_gate",              ["scripts/test_gate.py"]),
]


# ── the remedy registry. This IS the autonomy boundary, and it is data. ─────
#
# class A  the record already declares the remedy. Apply it, record it, continue.
# class B  no declared remedy, but the safe degradation is declared. Refuse and
#          degrade rather than guess. This is BIG withholding generalised: a
#          value that cannot be established is withheld, never imputed (D-007).
# class C  cannot be derived from the record. Escalate with the command that
#          would settle it, never with a guess.
REMEDIES = {
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
    "verify_action_pinning": {
        "class": "C",
        "why": "Resolving an action tag to a commit SHA requires an authenticated "
               "API call, and a supply-chain SHA is NEVER guessed. The runner "
               "names the command and refuses the value, exactly as it does for a "
               "credential.",
        "escalate_with": "gh api repos/<owner>/<repo>/commits/<tag> --jq .sha",
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
    probe = ROOT / ".git" / f".selfheal_probe_{int(datetime.now().timestamp())}"
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
    signed = (OPS / "G-07_PROMOTION_POLICY_SIGNED.json")
    if not signed.exists():
        return False, ("promotion policy unsigned. Article 14 Decision 25 and "
                       "G-07 section 4 are the instrument. Escalating instead.")
    if state["failed"] or state["escalations"]:
        return False, "control set not fully green"
    return True, "policy signed and predicate holds"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()

    now = datetime.now(timezone.utc).isoformat()
    state = {"generated_utc": now, "mode": ("report-only" if args.report_only
                                            else "dry-run" if args.dry_run else "repair"),
             "controls": [], "repaired": [], "degraded": [], "escalations": [],
             "failed": [], "benign": []}

    print(f"selfheal {now}  mode={state['mode']}\n")

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
        print(f"  !!  git writes UNSAFE here: {gw_why}")
        print(f"      repairs land in the working tree, commit from the host")
        if strays:
            print(f"      {len(strays)} stray tmp_obj_* in .git/objects, "
                  f"clear with: git prune ; git gc")
    print()

    for name, cmd in CONTROLS:
        script = ROOT / cmd[0]
        if not script.exists():
            state["controls"].append({"name": name, "status": "ABSENT"})
            print(f"  ..  {name:24s} absent from this checkout")
            continue
        rc, out = run(cmd)
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

        if rem["class"] == "A":
            if args.dry_run or args.report_only:
                print(f"      class A, would run {rem['run'][0]}")
                state["repaired"].append({"control": name, "applied": False,
                                          "would_run": rem["run"][0], "why": rem["why"]})
                continue
            rc2, _ = run(rem["run"])
            ok = rc2 == 0
            if ok and rem.get("reverify"):
                ok = run(cmd)[0] == 0
            state["repaired"].append({"control": name, "applied": True, "ok": ok,
                                      "ran": rem["run"][0], "why": rem["why"]})
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

    green = not state["failed"] and not state["escalations"]
    state["verdict"] = ("GREEN" if green and not state["degraded"] else
                        "DEGRADED" if green else "ESCALATED")

    if not args.report_only:
        REPORT.write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")

    print(f"\n  verdict {state['verdict']}   repaired {len(state['repaired'])}   "
          f"degraded {len(state['degraded'])}   escalations {len(state['escalations'])}")
    print(f"  promotion: {'PROCEED' if ok_promote else 'HELD'}  ({why})")
    for e in state["escalations"]:
        print(f"    [{e['severity']}] {e['control']}: {e['command']}")

    # Exit non-zero only on escalation. A repaired or safely degraded run is the
    # loop working, not the loop failing, and a scheduler that pages on both
    # trains the operator to ignore it.
    return 1 if state["escalations"] or state["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
