# QESIS+ session close 2026-07-31: v8.3 serving, three release claims corrected, six commits still off main

File this under the Command Board. Per QT-0010 the integration can read that wiki but not write into it, so this is created at workspace level.

## Verdict

**Service OPERATIONAL. Repository topology is the open problem, not the service.**

## Verified live this session

| Surface | Result |
| --- | --- |
| `qesis-mcp.vercel.app/` | HTTP 200, 0.34s, v8.3 (2026-07-31), axis RGD |
| `qesis-mcp.vercel.app/mcp` | HTTP 200, `tools/list` answers |
| chain | 604 entries, 0 link breaks, head `06fc6d1a` |
| Article 14 queue | 0 held |
| acceptance battery | 7 of 7 |
| `qesis-mcp` | `9161795` on `main`, synchronised |
| `sovereign-infra` | `1339a5e` on `fix/render-gates-d049` |

## Three claims in the afternoon release summary that did not survive checking

1. **"Both working trees clean" is false on inspection, true in substance.** `qesis-mcp` showed 366 insertions and 366 deletions across three files, an exactly symmetric diff. `git diff --ignore-all-space` is empty. Pure CRLF churn: worktree CRLF, HEAD LF, `core.autocrlf` unset on a repository written by both Windows and a Linux mount. Repaired with `.gitattributes` in both repositories. Recorded as **L-063**.
2. **"Pushed `1339a5e`" is true and it went to the wrong branch.** `origin/main` is at `cf80cbb`, six commits behind. The render-gate repair, D-051, the v8.3 propagation, the promote script and the deployment record all sit on `fix/render-gates-d049`. `main` is what any clone reads as the description of the system. Recorded as **L-062**.
3. **"/mcp 200" was asserted, not tested.** It is 200 under the correct header. A bare request returns 406, which is correct MCP streamable-HTTP behaviour and not a fault. A monitor without `Accept: application/json, text/event-stream` will report the service down while it is up.

## Blocker, operator only

`.git/index.lock` is present in both repositories and cannot be removed from the analysis sandbox: the FUSE mount returns `Operation not permitted`. Reads only warn, so this stays invisible until a write is attempted and then every commit fails.

## Two actions that are yours and are not agent-actionable

1. **Clear the lock, renormalise, land on `main`.** Six commits, no conflicts expected, `main` is a strict ancestor.
2. **INC-20260731-01: revoke the exposed ENTSO-E token, do not reissue.** `_SCHEMA\ENTSO-E API KEY.txt` was still on disk in a synced folder at 13:08 today. No agent opened it and none will. Nothing in the ecosystem consumes it and `refresh_audit` is CLEAN without it, which is exactly why this keeps getting deferred.

## Ticket state

11 open, down from 13. Closed with on-disk evidence per D-028: QT-0006 (ENTSO-E token, superseded), QT-0007 (Article 14 drafts, cleared).

By owner: RICO 8 open, ARCHITECT 2, COUNSEL 1. Oldest open HIGH-risk item is QT-0001, warehouse header promotion, due 2026-08-03.

## Ledger

At 63 lessons. Added today: L-058 through L-063. The through-line across all six is one defect wearing different clothes: a property declared in one place and enforced in none. A decision without its propagation, a version constant outliving its artifact, a test writing to production, a gate measuring the wrong property, a commit on the wrong branch, a diff that is not a diff.

## The line worth carrying

A deployment can be green, READY, production-targeted and still not be serving. Build success and service delivery are separate states and only the second is availability.

Today added the smaller sibling: a commit can be real, pushed and reachable and still not be on the branch that describes the system.