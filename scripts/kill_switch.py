"""Article 14 Decision 5. The stop control, as a lever rather than a signature.

WHY THIS EXISTS AS CODE
    Decision 5 is "revocation protocol and emergency kill-switch parameters",
    risk CRITICAL, and the register's clearing order puts it first because a stop
    control that arrives after autonomy is theatre. The failure analysis is the
    argument: the term CON * RET * HIT * MCP survives the consistency cutoff at
    0.822 WITH the human gate present, so human oversight is a damper and not an
    immunity, and the damper is exactly what autonomous promotion removes.

    Signing Decision 5 without shipping the switch would sign a promise. This is
    the switch.

TWO CHANNELS, AND THE ORDER MATTERS
    1. Environment: QESIS_KILL_SWITCH=1. Settable as a GitHub repository variable
       from a phone, with no clone, no git and no laptop. This is the emergency
       channel and it is checked FIRST, because an emergency control that
       requires a working development environment is not an emergency control.
    2. File: ops/KILL_SWITCH.json with engaged=true. Versioned, reviewable, and
       it carries who engaged it and why. This is the deliberate channel.

    Either engages. BOTH must be clear to proceed. A control that can be
    satisfied by whichever channel happens to be quieter is not a control.

WHAT IT STOPS, AND WHAT IT DELIBERATELY DOES NOT
    Engaged, the loop performs no repair, lands no commit and permits no
    promotion, and vercel_gate refuses the build so production keeps serving the
    last deployment it could verify.

    It does NOT take the endpoint down. An instrument that cannot verify itself
    should keep showing the last thing it could verify rather than go dark or go
    wrong, which is the same reasoning vercel_gate already applies to a failing
    gate set. Taking production down is a separate act with a separate blast
    radius and it is not delegated to a boolean.

Usage:
    python scripts/kill_switch.py            report state, exit 0 clear, 3 engaged
    python scripts/kill_switch.py --require  exit non-zero if engaged, for CI
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SWITCH = ROOT / "ops" / "KILL_SWITCH.json"
ENV_VAR = "QESIS_KILL_SWITCH"
ENGAGED_EXIT = 3


def state() -> tuple[bool, str, dict]:
    """Returns (engaged, channel, detail). Environment is checked first."""
    env = os.environ.get(ENV_VAR, "").strip().lower()
    if env in ("1", "true", "yes", "on"):
        return True, "environment", {
            "variable": ENV_VAR, "value": env,
            "note": "Emergency channel. Set as a repository variable or a runner "
                    "environment variable. Clear it to release."}

    if SWITCH.exists():
        try:
            d = json.loads(SWITCH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            # An unparseable kill switch is treated as ENGAGED. A stop control
            # that fails open is not a stop control, and a corrupt file is
            # exactly the state in which someone wants everything to halt.
            return True, "file", {"error": f"unparseable, failing safe: {exc}"}
        if d.get("engaged") is True:
            return True, "file", d
        return False, "file", d

    return False, "absent", {
        "note": "No ops/KILL_SWITCH.json and no environment variable. Nothing is halted."}


def main() -> int:
    engaged, channel, detail = state()
    if engaged:
        print(f"KILL SWITCH ENGAGED via {channel}")
        for k, v in detail.items():
            print(f"  {k}: {v}")
        print("\nThe loop performs no repair, lands no commit and permits no")
        print("promotion. Production keeps serving its last verified deployment.")
        return ENGAGED_EXIT if "--require" in sys.argv else ENGAGED_EXIT
    print(f"kill switch clear (channel checked: environment, then {channel})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
