# Session record, 2026-08-27c: the address is live, the gate asserts it, and the audit stops blaming the tree

**ARCHITECT. Follows the landing of PR 81 and PR 47.**
Every claim carries the reader that produced it, per D-118 rule 1.

---

## 1. qesis.eu serves, measured

The operator made `qesis.eu` the primary domain on the Vercel project and removed
the `www` alias from the platform.

| Value | Reader | Result |
|---|---|---|
| `https://qesis.eu/health` | Vercel API fetch, 14:04Z | **200** |
| `deployment_commit` | that payload | `550ee76a447461dbf1d07dc7f2d604c43347ab53`, equal to `main` |
| `index_sha256` | that payload | `8009815e4c19...`, the attested artefact |
| chain | that payload | VERIFIED, 754 entries, 0 link breaks |
| `www.qesis.eu` | direct UDP query to `a.regfish-ns.net` at 178.21.144.21 | NXDOMAIN, and no longer published |

The 308 into nothing is gone. `scripts/verify_public_domain.py` run live now prints
PASS for both published addresses.

## 2. The declaration follows the platform

`www.qesis.eu` left `canonical` in `data/domains.json` and entered a new
`retired` list. Retired names stay declared so a historical reference is not an
undeclared literal, and are excluded from `canonical` so no control asserts an
address nobody serves. `verify_domains.py` reads both; `verify_public_domain.py`
reads `canonical` only.

Two gates were retyping that name and both were repaired to read the declaration
rather than a copy of it: `test_http.py` asserted the rebinding guard accepts
`www.qesis.eu`, which is a Host the guard had correctly stopped allowing, and
`test_routes.py` used it as its synthetic Host. **The preflight caught both,
before anything was pushed.** L-089 is the rule and this is the second time in
one day that a retyped literal cost a build.

## 3. The live assertion is wired

`production-integrity-probe.yml` gains a step that runs
`verify_public_domain.py` against every address in `canonical`, hop by hop,
refusing a redirect into a host with no DNS record. `probe` is an owned check,
so the audit asserts it and `gh_ops.py runner-merge` will not merge a runner
landing while it is red.

**It is in the probe and not in the required integrity gate, deliberately.** The
required gate decides whether a change may land. Making every landing depend on
a third party answering in the next twenty seconds converts somebody else's bad
minute into a blocked release, which is a worse failure than the one being
prevented. The fixtures run in the required gate; the live assertion runs in the
probe, hourly and on every push, where a transient failure is information rather
than a blockade.

`scripts/verify_public_domain.py --selftest` is now a `selfheal.py` control
rather than an exemption, because the script runs in CI (L-183).

## 4. The audit was blaming the tree for the machine

The 13:35Z audit reported two FAIL rows and printed **NOT GREEN** on a healthy
tree. Both rows carry `exit 3221225773`. That is `0xC000012D`, NTSTATUS
**STATUS_COMMITMENT_LIMIT**: the machine ran out of virtual memory. The gates
never reached a verdict.

Corroborated three ways: the same step passed inside the same lander run eleven
minutes earlier on the identical tree; CI run 33078066776 passed on the identical
commit; and both scripts exit 0 when run on this tree with memory available,
`verify_index.py` reporting 30 checks, 0 failed, 0 warnings.

**This is D-116 inverted.** That decision exists because an exit code was read as
a result. Here a machine fault was read as a refusal, and the cost is the same
shape: the operator went looking for a defect in a change set that had none.

`scripts/audit_ecosystem.py` now has `classify`. An exit code the gate chooses
(0, 1, 2, 3) is a verdict about the tree. Anything else is **CRASH**, reported
with the abnormal termination named where it is known, and the audit reads
**INCONCLUSIVE** rather than NOT GREEN. A crash is never PASS and still exits
non zero, because a gate that did not run has not said anything. Nine fixtures,
three of them over `classify` itself. Recorded as **L-193**.

**What this does not fix.** The laptop still runs out of memory during a full
audit, and that is the verification tax the operator has been describing. The
honest remedy is not a bigger container in another cloud: it is that a full
ecosystem audit belongs on a runner and not on the operator's machine, which is
a change to `AUDIT_ECOSYSTEM.bat` and the workflows, and it is the next
ARCHITECT item rather than something to slip into this landing.

## 5. Control set, this tree

```
test_gate.py                              97/97   exit 0   "Gate is trustworthy"
verify_public_domain.py --selftest         7/7    exit 0
verify_public_domain.py  (live)            2/2 addresses PASS
audit_ecosystem.py --selftest              9/9    exit 0
verify_domains.py                                 exit 0
verify_workflow_contract.py               31 CI scripts, 19 controls, 17 exemptions
preflight.py  (qesis-mcp)                 23/23   PREFLIGHT PASSED
preflight.py  (sovereign-infra)           10/10   PREFLIGHT PASSED
rdl.py ci-blocking                                6 accepted, 0 regressions
```

---
Decision holder: Rodrigo Batista Silva. Author for copyright purposes, and the
only signature on this record.
Prepared by: Claude, Cowork session of 2026-08-27, acting under CLAUDE.md and
sovereign-infra/ops/GOVERNANCE.md. Machine attribution under R-1: data, not
authorship, and not a claim of any right.
Landed by: pending.
