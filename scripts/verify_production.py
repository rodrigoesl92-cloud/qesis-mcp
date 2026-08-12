"""Measures PRODUCTION. Never the deployment URL -- that URL served correctly
for two days while production was dark.

The expected chain figure is read from the committed attestation, not written
here as a literal. It was `== 604` until 2026-08-06, by which time the live log
had reached 651 and the committed spine was 47 entries stale: the number in this
file would have kept asserting 604 long after 604 stopped being true, and would
have failed a correct deployment or passed a stale one depending only on which
way the drift ran. A gate that hardcodes the value it is checking is a stored
claim, not a measurement.

Usage:
    python scripts/verify_production.py <expected_index_sha> <expected_commit>
Exit: 0 all checks pass · 1 any check fails or production is unreachable
"""
import json
import pathlib
import sys
import urllib.request
from pathlib import Path
_DOMAINS = json.loads((Path(__file__).resolve().parent.parent / 'data' / 'domains.json').read_text(encoding='utf-8'))


if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(2)

sha, commit = sys.argv[1], sys.argv[2]

att_path = pathlib.Path(__file__).resolve().parent.parent / "data" / "chain_attestation.json"
try:
    att = json.loads(att_path.read_text(encoding="utf-8"))
    expected_entries = att["entries"]
    expected_breaks = att["link_breaks"]
except Exception as e:                                             # noqa: BLE001
    print(f"FAIL  cannot read the committed attestation: {e}")
    print("      Without it there is no independent figure to hold production to.")
    sys.exit(1)

# /health, not /api/health. Vercel's filesystem router owns /api/* and preempts
# vercel.json rewrites, so a route under that namespace with no matching file is
# unreachable however correctly it is registered. /mcp works for the same reason
# in reverse: it sits outside /api/.
HEALTH = _DOMAINS["probe_base"]

try:
    h = json.load(urllib.request.urlopen(HEALTH, timeout=25))
except Exception as e:                                             # noqa: BLE001
    print(f"FAIL  production unreachable at {HEALTH}: {e}")
    sys.exit(1)

chain = h.get("chain", {}) or {}
checks = {
    "status ok":     h.get("status") == "ok",
    "commit bound":  h.get("deployment_commit") == commit,
    "index matches": h.get("index_sha256") == sha,
    f"chain {expected_entries} entries, {expected_breaks} breaks":
                     chain.get("entries") == expected_entries
                     and chain.get("link_breaks") == expected_breaks,
    "eight tools":   h.get("tool_count") == 8,
}
for name, ok in checks.items():
    print(("PASS  " if ok else "FAIL  ") + name)

passed = sum(1 for v in checks.values() if v)
print(f"\nRESULT: {passed} passed, {len(checks) - passed} failed")
sys.exit(0 if passed == len(checks) else 1)
