# Session record, 2026-08-26: the STIR directive, and the two defects it exposed in me

**ARCHITECT and COUNSEL. Supersedes nothing; extends `ops/HANDOVER_2026-08-26.md`.**
Every claim carries the reader that produced it, per D-118 rule 1. Values read
from a caching tool do not appear here at all.

---

## 1. The correction that matters most

An earlier draft of this record said the deployment plane lagged `main` by two
landings and placed "promote 654c950" on the operator. **That was false.**

| Value | Read from | By | Result |
|---|---|---|---|
| `deployment_commit` | serving plane, live origin | Chrome bridge, `qesis-mcp.vercel.app/health` | `654c950df4f481ed0be6628b2abf6f2cccbd31dc`, equal to `main` |
| production deployment | serving plane | Vercel API `list_deployments` | `dpl_Fh1SThbR3iZxE7xZd1Q8imakjHZq`, READY, target production, on `654c950` |
| `main` | delivery plane | `api.github.com/repos/.../commits/main` | `654c950df4f4`, 2026-08-26T10:31:06Z |
| open pull requests | delivery plane | GitHub, both repositories | **zero.** PR 43, the first runner landing, is closed |
| chain | serving plane | same `/health` read | 754 entries, VERIFIED, 0 link breaks |

The false value came from `WebFetch`, which caches for fifteen minutes per URL.
A cached response is a proxy. Asserting it as the resource is
`claim_from_proxy_not_resource`, tenth occurrence, recorded as **L-182**, and
the cost was not a wrong sentence but an item placed on a person that nobody
needed to do. That is L-147 arriving through a different door, and the operator
was right to refuse it.

**Nothing about promotion is outstanding. `654c950` is live and serving v9.0.**

## 2. The second defect, found while checking the first

`verify_action_pinning.py` reported SEC-1 PASS, 18 of 18 pinned. True of
`qesis-mcp`, false of the ecosystem: the gate does not exist in
`sovereign-infra`, where five `uses:` lines carried mutable tags.

| File | Line | Was | Now |
|---|---|---|---|
| `claude.yml` | 43 | `actions/checkout@v4` | `@34e114876b0b11c390a56381ad16ebd13914f8d5` |
| `claude.yml` | 48 | `anthropics/claude-code-action@v1` | `@1f291e1cfe0f5fc21db2aef19af844591600ade7` |
| `compliance.yml` | 29 | `actions/checkout@v4` | `@34e114876b0b11c390a56381ad16ebd13914f8d5` |
| `compliance.yml` | 31 | `actions/setup-python@v5` | `@a26af69be951a213d495a4c3e4e4022e16d87065` |
| `promote-production.yml` | 20 | `actions/checkout@v4` | `@34e114876b0b11c390a56381ad16ebd13914f8d5` |

Every SHA resolved by command against `api.github.com/git/ref/tags`, none
guessed (L-110). `checkout` and `setup-python` use the pins already proven by
SEC-1 in `qesis-mcp`, so both repositories carry the same pin (G-01).

**The vector, demonstrated on this repository rather than cited from a report:**
`actions/checkout@v4` resolved to `34e11487...` when `qesis-mcp` pinned it and
resolves to `11d5960a...` today. Same reference, different code, different day.
That is the Datadog State of DevSecOps 2026 finding reproduced locally, and it
is why SEC-1 exists.

Recorded as **L-181**, `guard_not_executed`, eighth occurrence. The gate is now
paired into `sovereign-infra` and wired into its integrity workflow. Fixture
pair, measured: **exit 1** against the tree as installed, **exit 0** against the
tree with `ops/pending_workflows` installed, 14 of 14 pinned.

## 3. D-118, the standing remedy

Both defects are one move: a claim made about a resource from something that is
not the resource. Ten occurrences. Rung 4 says the control sat in the wrong
layer, and it did, every time, because the control was a habit inside a session
and a habit dies with the session.

`ops/SOURCE_PRECEDENCE.json` makes the hierarchy **data**:

- **Precedence, ratified by the decision holder.** Our documentation, then the
  sources this ecosystem has adopted, then sources the decision holder delivers
  directly, then the open web. Nothing lower overturns anything higher without
  an RDL entry saying so. Nothing from the open web is ever tier 1.
- **Four planes, one authoritative non-caching reader each.** Artefact, evidence,
  delivery, serving.
- **`WebFetch` is forbidden on the two remote planes**, with its reason, its
  evidence and its permitted use recorded beside the prohibition.
- **Nineteen registered sources**, APA, each with the use it is admitted for.

`scripts/verify_reading_contract.py` is its gate. RC-1 to RC-6, **12 fixtures,
one refusal per rule**, exit 0, paired into both repositories, wired into
`test_gate.py` and into the delivered `sovereign-infra` integrity workflow. The
contract cannot be quietly relaxed: removing `WebFetch` from the forbidden
table, admitting a cached reader, or promoting a source to tier 1 each fail a
named fixture.

## 4. Everything from the first half of this session, still standing

`gh_ops.py runner-merge`, 12 fixtures, paired; the hourly sweep in the delivered
`selfheal.yml`; **D-117** and **L-180**; `public/blueprint.html`, the three-phase
causal surface, 3 fixtures; `AUTHORS.md` rewritten with the machine-assistance
disclosure; the COUNSEL memo on authorship, copyright and the signature
convention; the signature block now on every decision record.

## 5. Full control set, this tree, exit codes measured

```
test_gate.py                              84/84   exit 0   "Gate is trustworthy"
gh_ops.py runner-merge --selftest         12/12   exit 0
verify_reading_contract.py --selftest     12/12   exit 0
build_blueprint.py --selftest              3/3    exit 0
verify_action_pinning.py  (delivered)     14/14   exit 0
verify_action_pinning.py  (as installed)          exit 1   the hole is real
rdl.py ci-blocking                                exit 0   0 regressions
preflight.py            (sovereign-infra)  7/7    exit 0
selfheal.py             (qesis-mcp)       16 controls PASS, 0 escalations
verify_reading_contract.py, both repos            exit 0   RC PASS
```

## 6. One item is the operator's. One, and here is exactly why

**qesis-mcp, Settings > Actions > General > Workflow permissions: tick "Allow
GitHub Actions to create and approve pull requests".**

Read from the resource, not assumed: the settings page reports
`actions_workflow_permission_can_approve_pr` **unchecked** and
`actions_default_workflow_permissions` set to **read**. Corroborated
independently: the `ops/report-2026-08-26` branch exists in `qesis-mcp` (it has
a Vercel preview deployment authored by `qesis-ops[bot]`) and `qesis-mcp` has
zero pull requests, so the runner pushed a branch and could not open one. That
is L-174 still running in that repository.

**Why it is not mine.** Two reasons, in the order they actually bind. First, a
tool boundary: the Chrome bridge reads that settings page and its classifier
refuses to write to it. I attempted the write and it was denied; that is a fact
about the tool, not a governance clause, and D-118 rule 7 now requires it to be
reported as one. Second, G-03 and G-04 by analogy, because the tick widens what
the Actions token may do.

**Tick only that checkbox.** Leave the default token at read. Every workflow
here declares its own `permissions:` block, which overrides the default, so
raising the default buys nothing and widens everything.

**If you decline:** the hourly sweep is harmless and idempotent, it prints zero
open pull requests and exits 0. The cost is that class A repairs and daily
reports in `qesis-mcp` keep needing a click.

## 7. What is not done, and what is only latent

- **The change set is on disk and not landed.** One double-click of
  `LAND_EVERYTHING_FINAL.bat`. `LANDING_MANIFEST.json` is written, branch
  `feat/land-20260826-runner-merge-and-blueprint`.
- **Two workflows in `sovereign-infra` declare no `permissions:` block at all**:
  `claude.yml` and `promote-production.yml`, the second being the promotion
  runner. They inherit the repository default. Pinning was applied; the
  permissions block was not, because narrowing the token on the promotion
  workflow could stop promotion working and that is not a change to make in the
  same landing that pins it. Named here as the next ARCHITECT item, not as the
  operator's.
- **The delivered workflows are not installed** until the lander's step 0a runs.
  Until then SEC-1 fails in `sovereign-infra` by design, and that failure is the
  gate telling the truth.

## 8. The computer-use boundary, measured this session

I attempted to run the lander myself rather than hand it over. Recorded so the
next session does not rediscover it:

| Application | Tier | What that allows |
|---|---|---|
| `Git CMD` | **full** | see, click AND type. The one that can run the lander |
| `Terminal`, `Git Bash`, `Visual Studio Code` | click | see and left-click only, no typing |
| `PowerShell`, `File Explorer` | not grantable | resolve to nothing and cannot be requested |

Access to `Git CMD` was granted and the application was opened. It could not be
brought to the front, for two reasons in sequence: an elevated
`Administrator: Windows PowerShell` window was running, and Windows UIPI refuses
input from a lower-integrity process to a higher one; and every click requires
the frontmost application to be in the session allowlist, which makes focusing a
background window circular whenever the operator's own foreground application is
not granted.

**The consequence, in one sentence:** Git CMD is already open on the taskbar, and
clicking it once, or closing any elevated PowerShell window, is enough for the
next attempt to type the lander path and run it.

This is a tool boundary and is written as one, per D-118 rule 7. It is not a
governance clause and it does not make the landing the operator's under SH-4.

## 9. The lander refused, twice over, and both refusals were right

The 16:18:42Z click of revision 6 aborted at preflight, before anything was
committed, pushed or opened. Two separate defects, one mine and one older than
this session, and the change set is better for both.

### L-183, mine. A gate verified against the tree before its own input existed

`verify_workflow_contract.py` reads `.github/workflows`. This change set
delivers five workflow files to `ops/pending_workflows`, and step 0a is what
installs them. I ran the gate against the tree where step 0a had not yet run,
it passed, and I recorded that pass as evidence about the tree the lander would
judge. Step 0a installed them and the same gate found **C-3**: `gh_ops.py` now
runs in CI and was absent from the self-heal control set.

What makes it a defect rather than an oversight: the technique was already in
my hands in the same session. SEC-1 was proven by building a temp tree with the
delivered workflows installed and running the gate there. The sibling gate did
not get the same treatment.

**Repair.** `runner_merge_selftest` and `reading_contract` are now entries in
`selfheal.py` CONTROLS, not entries in EXEMPT, because both decide over values
on disk with no network and no credential and are therefore controls in their
own right. `EXEMPT`'s target state is empty (L-048) and it stays that way.

### L-184, older than this session. The working tree carried an unlanded edit to the released index

`data/qesis_v8.json` on disk hashed to `bbfc66a7594f`. The blob at `main`
hashes to `8009815e4c19`, which is the artefact bound in the chain spine and the
`index_sha256` production serves. The whole difference was **one extra element**
in `served_contract.tools.qesis_get_integrity`, the string
`field_no_code_builds`, present locally and absent from `main`.

Every gate that reads the working tree passed on it: `verify_index`,
`verify_served_contract`, `verify_vintage_pairing`, `coupling`, every build
check. They passed because the working tree was self-consistent, and a
self-consistent working tree is exactly what a silent local mutation looks like.
The only rule that compares the disk against something the disk cannot edit is
**C5 of `verify_chain.py`**, and C5 was the one chain rule with no fixture in
`test_gate.py`. C1, C2 and C3 had fixtures. The rule that mattered did not.

**Repair.** The index is restored to the blob at `main`, verified by hash
(`8009815e4c19132048bf285c`), and `check_chain_binding()` now carries the accept
and refuse pair C5 was missing. `test_gate.py` is 86 of 86.

The orphan field is recorded here rather than discarded: if
`field_no_code_builds` was intended, it needs a change set of its own that
lands the declaration and re-binds the artefact through
`sovereign-infra/scripts/bind_release.py`. It is not smuggled in under a
landing that never mentioned it.

### How the reference was read without running git

`git` may not be run from the analysis mount at all, read-only included, because
`status`, `add` and `diff` each take `.git/index.lock` and this mount cannot
unlink it (L-122, L-123, L-150, SH-10c). The blob was read instead with
`dulwich`, a pure-Python git object reader: refs, commit, tree, blob, no index,
no lock, no command. The restore was then verified by SHA-256 against the bound
artefact, so its correctness is proven rather than trusted.

### Full CI step list, executed here after the repairs

```
qesis-mcp        23 of 23 preflight steps PASS, index still 8009815e after the run
sovereign-infra  10 of 10 preflight steps PASS, including the three added this session
test_gate.py     86 of 86, "Gate is trustworthy"
rdl.py ci-blocking  6 accepted, 0 regressions
```

---
Decision holder: Rodrigo Batista Silva. Author for copyright purposes, and the
only signature on this record.
Prepared by: Claude, Cowork session of 2026-08-26, acting under CLAUDE.md and
sovereign-infra/ops/GOVERNANCE.md. Machine attribution under R-1: data, not
authorship, and not a claim of any right.
Established from: the readers named in section 1 and the exit codes in section
5, each run in this session. No git command was run from the analysis mount. No
credential was read, written or requested. No value in this record came from a
caching reader.
Landed by: pending.
