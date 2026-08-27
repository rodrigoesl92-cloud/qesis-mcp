# D-118: agentic observability. The reader is part of the claim

**Status:** decided 2026-08-26, ARCHITECT and COUNSEL, at rung 4 of the RDL
family `claim_from_proxy_not_resource` (L-161, L-162, L-173, L-174, L-179,
L-180; this occurrence **L-182**), and at rung 4 of `guard_not_executed`
(L-154, L-169, L-178; this occurrence **L-181**).
**Ratified by** the decision holder on 2026-08-26 as the standing evidence
hierarchy for this ecosystem.
**Authority:** CLAUDE.md Rule V-1, D-115 (a control queries the thing it
asserts), D-116 rule 1 (a verdict is a predicate over a parsed value), G-01b
(four planes), SEC-1 (pinned actions), Article 12 of Regulation (EU) 2024/1689
(automated record keeping).

## What happened, twice, on one day

**L-182.** A session reported the serving plane as `deployment_commit 24a6a80`
against `main` at `654c950`, concluded that the deployment lagged by two
landings, and escalated "promote 654c950" to the operator under G-06 limit 2.
Read from the browser against the live origin, the same endpoint returns
`deployment_commit 654c950df4f481ed0be6628b2abf6f2cccbd31dc`, equal to `main`,
with chain 754. The Vercel API shows `dpl_Fh1SThbR3iZxE7xZd1Q8imakjHZq`, READY,
target production, on that commit. The earlier value came from a fetch tool
whose own documentation states that responses are cached for fifteen minutes
per URL.

The sentence was wrong. That is the small part. The large part is that a person
was handed an item that had already been done, by an agent whose whole reason
for existing is to keep that from happening. Three consecutive reports doing
that is L-147, and the operator was right about it then and right about it now.

**L-181.** `verify_action_pinning.py` reported SEC-1 PASS, 18 of 18 pinned, and
the statement was true of `qesis-mcp` and false of the ecosystem. The gate does
not exist in `sovereign-infra`, where five `uses:` lines carried mutable tags,
one of them a third-party action running in a privileged context. The mutability
is not theoretical: `actions/checkout@v4` resolved to `34e11487...` when
`qesis-mcp` pinned it and resolves to `11d5960a...` today. The same reference,
different code, different day.

**The single move behind both.** A claim was made about a resource from
something that was not the resource. A cache instead of an origin. One
repository instead of the pair. This family has now been recorded ten times.
Rung 4 says the control is in the wrong layer, and it has been in the wrong
layer every time, because the control was always a habit inside a session and a
habit dies with the session that had it.

## Decision

1. **The reader is part of the claim.** Every asserted value carries its plane
   and the reader that produced it, in the form `<value> read from <plane> by
   <reader> at <utc>`. A value with no reader named is not an observation, it is
   a recollection.

2. **The hierarchy is data, not advice.** `ops/SOURCE_PRECEDENCE.json` declares
   the four evidence tiers, the four planes, the authoritative reader for each
   plane, and the readers that are forbidden on the remote planes. Advice in a
   prompt is deletable and unenforceable. Data has a gate:
   `scripts/verify_reading_contract.py`, RC-1 to RC-6, twelve fixtures, one
   refusal per rule, paired into both repositories. This is the same move R1.26
   already makes for the fsQCA reading flags, applied to evidence itself.

3. **Precedence, ratified.** Our documentation first, then the sources this
   ecosystem has already adopted, then sources the decision holder delivers
   directly, then the open web. Nothing at a lower tier overturns a higher one
   without an RDL entry that says so, and nothing found on the open web is ever
   promoted to tier 1.

4. **Caching readers are forbidden on the remote planes.** `WebFetch` may read
   prose a human will read. It may never be the source of a value that appears
   in a report. The delivery plane is read by `gh_ops.py proof` or by the
   browser bridge against `api.github.com` and `github.com`; the serving plane
   by the browser bridge against the live origin or by the Vercel API. A value
   that reaches a report from a caching reader anyway carries the word cached
   beside it or does not appear. RC-2 and RC-3 refuse a contract that says
   otherwise.

5. **A gate is paired into every repository whose files it judges, in the same
   change set that writes it.** Before reporting any control as passing, state
   which repositories it ran in. `verify_action_pinning.py` and
   `verify_reading_contract.py` are now in both.

6. **Before an item is placed on the operator, the state that makes it
   necessary is read from the resource, in that turn.** Not from a report, not
   from a handover, not from a cache. If the resource cannot be reached from
   where the agent is, the item is not raised: the command that settles it is
   named instead, and the agent says it could not run it. SH-4 lists three
   admissible escalations and none of them survives a stale premise.

7. **A tool boundary is not a governance clause and is not written as one.**
   Where an agent cannot act because a tool refuses, the report says which tool
   refused and what it refused. The Chrome bridge reads a GitHub settings page
   and is blocked from writing to one; that is the reason the Actions setting is
   the operator's, and G-03 by analogy is the second reason, not the first.

## What this costs, and why it is worth it

Reading the resource every time is slower than trusting a report. The DORA 2026
work names the general form of this: AI generation without automated
verification produces a verification tax, and the J-curve dip is what happens
when generated volume queues in front of manual review. Every gate in these two
repositories exists to keep that queue empty. A gate is cheaper than the review
it replaces, and much cheaper than the trust it replaces.

## What would falsify this decision

An asserted value that carried its plane and its reader and was still wrong.
That would mean the reader itself is unsound, and the remedy would move to
requiring two independent readers per remote plane rather than one. Nothing
observed so far requires that.

---
Decision holder: Rodrigo Batista Silva. Author for copyright purposes, and the
only signature on this record.
Prepared by: Claude, Cowork session of 2026-08-26, acting under CLAUDE.md and
sovereign-infra/ops/GOVERNANCE.md. Machine attribution under R-1: data, not
authorship, and not a claim of any right.
Established from: browser read of https://qesis-mcp.vercel.app/health against
the live origin; Vercel list_deployments for prj_qp1c8sgZNJi2XUGcbVfzLN5QVT2r;
api.github.com commits/main for qesis-mcp; the pull request lists of both
repositories, zero open; `grep -rn uses:` filtered to lines without a 40 hex
SHA over both workflow directories; `verify_action_pinning.py` exit 1 on the
tree as installed and exit 0 on the tree with ops/pending_workflows installed;
`verify_reading_contract.py --selftest` 12 of 12; `test_gate.py` 84 of 84.
Landed by: pending.
