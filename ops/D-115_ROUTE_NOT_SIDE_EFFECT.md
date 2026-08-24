# D-115: a control asserting an authorised route queries the route, never a correlated side effect

**Status:** APPROVED and EXECUTED
**Date opened:** 2026-08-24, by L-161 at the fourth rung
**Date approved:** 2026-08-24
**Approved by:** R. Batista Silva
**Authored by:** COUNSEL. Wired by ARCHITECT. Confirmed by SENTINEL.

---

## What happened

`branch-guard.yml` exists to detect an unauthorised write to `main`. It
classified how a commit arrived by counting parents:

```
if [ "$parents" -ge 2 ]; then route="pull_request_merge"
else route="direct_push"
fi
```

Only the **merge-commit** strategy produces two parents. A **rebase** merge
replays the commit onto `main` with **one** parent and the original subject, and
a **squash** merge produces one parent as well. G-06 Rule 2-4 mandates rebase and
forbids squash, because squash strands the commit hashes the lineage register
cites.

So under this ecosystem's own governance, **every correctly executed merge landed
as `direct_push` and opened an audit issue.** `sovereign-infra` issue 37, for
commit `3a81552`, is the first instance and it would have recurred on every merge
thereafter. An alarm that fires on every correct action is switched off by
whoever tires of it first, which is L-063 reached by construction.

## The ruling

**Parent count is a proxy for "arrived through a pull request", and it is the
wrong proxy.** The authoritative answer is held by the forge, so the control asks
the forge:

```
gh api repos/{repo}/commits/{sha}/pulls --jq '[.[] | select(.merged_at != null)] | length'
```

Any associated merged pull request means authorised, whatever the merge strategy.
The two cheap checks are kept ahead of it as fast paths, because a two-parent
commit and a `Merge pull request` subject are both sufficient on their own.

**Where the API cannot be reached the control reports and does not downgrade.**
An unreachable API is not evidence of an authorised route. D-007 generalised:
withheld with cause, never imputed.

## Why this is a fourth-rung decision and not a fix

This is the fourth instance of one epistemic move: **a claim about a resource
made from a proxy for that resource rather than from the resource itself.**

- **L-104** declared `sovereign-infra` unreachable on one empty grep, while the
  repository had been read from twice in the same session.
- **L-111** allocated lesson ids by counting forward from memory instead of
  reading the store.
- **L-143** read an empty connected folder as a failed repository, when the
  repository was reachable under a different path.
- **L-161** read parent count as merge provenance.

Four instances across four surfaces, which under D-112 escalate as four, because
the family key is the epistemic move and not the artefact. The control sits in
the wrong layer: V-1 requires a claim to carry the command that produced it, and
what was missing is that **the command must probe the thing asserted, not
something correlated with it.**

## Scope

Binds every control that classifies an action as authorised or unauthorised.
Before merge, before promotion, before publication. Where the authoritative
record is held by an external system, the control queries that system and
degrades visibly when it cannot.

## Falsifier

If a control is added that decides authorisation from a locally computed
property, when the authoritative record is held elsewhere and is queryable, this
decision is not applied.

*Status:* EXECUTED in `.github/workflows/branch-guard.yml`, paired across both
repositories. *Approved by:* R. Batista Silva, 2026-08-24.
