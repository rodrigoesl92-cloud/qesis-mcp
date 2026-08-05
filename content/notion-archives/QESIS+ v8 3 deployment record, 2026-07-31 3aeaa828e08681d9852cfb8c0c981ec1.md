# QESIS+ v8.3 deployment record, 2026-07-31

**Status: shipped to `main`, not yet promoted to the production alias.** Read the Blocker section before assuming v8.3 is public.

Written for the agent registry and the next operator session. Everything below was measured, not inferred.

## What shipped

| Repository | Branch | Commit | State |
| --- | --- | --- | --- |
| `qesis-mcp` (public) | `main` | `6088303` then merge `cad235f` | pushed, CI green |
| `qesis-mcp` (public) | `main` | `cec097c` | pushed, [DEPLOY.md](http://DEPLOY.md) correction |
| `sovereign-infra` (private) | `fix/render-gates-d049` | `1e5918e` | pushed, 25 files |

PR [#7](https://github.com/rodrigoesl92-cloud/qesis-mcp/pull/7) carries the full reasoning.

## The substantive change

v8.3 replaces CRD with RGD (Region Density) under D-049, advancing the composite to `QESIS_THEORY_v3`. The axis never measured reliance or density; it is a normalised count of cloud regions and is now named as one. Tier assignment is stated as a rule and applied deterministically, correcting 9 in-population states whose labels had been assigned by eye, including Germany, France and the United Kingdom, which the rule makes ACTIVE rather than EPIS.

The index carries a named human approval: `R. Batista Silva`, `2026-07-31T00:09:47Z`, ratifying D-050 and D-051. No agent signed it.

## Four defects found while committing it

The local propagation run reported all seven surfaces consistent at v8.3. It checks that a surface carries the vintage string, not that the artefact is coherent, so none of these were visible to it. This is the governing lesson again: a check that reads a stored claim is not a check.

1. **Lineage described the wrong generation.** `lineage.formula_id` said `QESIS_THEORY_v2` while `composite_model` said v3. Hard gate failure R1.10. It also still named `build_index.py` and the v8.2 build stamp, and that script emits v8.2 with CRD, so re-running the named generator would have regressed the index. Lineage now names the transform that produced v8.3 and carries `derived_from` with the v8.2 SHA-256.
2. **The MCP server was broken against its own index.** `server.py` still declared `CRD` in `AXES`, so `qesis_compare_countries` would have raised `KeyError` on all 35 states and `qesis_rank_countries` would have rejected `RGD`. This is the shipped product, not a script.
3. **The gate self-test was crashing, not passing.** `m_inversion` injected defects over a literal axis list containing `CRD` and died with `KeyError` before reaching its assertion. The mutation suite had silently stopped proving the gate catches dominance inversion.
4. **RGD was never range-checked.** `verify_index.py` held the same stale literal, and its soft check reads `.get(axis)`, so a renamed axis returns `None` and is skipped rather than flagged. Quieter than a crash and longer-lived.

A fifth, smaller one: the `.gitignore` rule for superseded inputs was a literal filename, so `qesis_v8.2_superseded.json` and the v8.3 candidate were staged for the public repo when the vintage advanced. Now globs. A rule's scope has to travel with it.

## Verification

Green in GitHub Actions and locally: `verify_index` 16 of 16, `test_gate` 9 of 9 behaviours, `smoke_server`, `coupling` reproducing published values, `build_eval --check`, `build_landing --check`, `test_http` answering MCP over HTTP at v8.3.

## Blocker: promotion, not the build

`qesis-mcp.vercel.app` still serves **v8.2**. This is not a build failure and not a code problem.

The merge built clean in three seconds. The deployment reports `state: READY`, `target: production`, and is the project's `latestDeployment`. The production alias was never moved onto it. The GitHub commit status carries the only hint: `Checks for Deployment have failed`. A deployment whose checks fail is still built and still READY, and the alias simply is not assigned. Promotion is what publishes.

Two deployments now sit in this state:

- `dpl_F4hDwDyTpjzqcg4iSZzqhd4BeocW` (merge `cad235f`)
- `dpl_EZQcLJJvPDBN33iEJQeSpk8GVMng` (`cec097c`)

Two candidate causes, both project-level Vercel configuration, neither reachable from the repository or the Vercel MCP connector:

1. **A blocking check.** Vercel supports checks that block production alias assignment (`vercel project checks --blocks deployment-alias`). This matches the status message exactly.
2. **A paused project.** The API returns `"live": false`. Pausing "disables auto-assigning custom production domains".

### The action that closes it

Either promote directly:

```
vercel promote dpl_EZQcLJJvPDBN33iEJQeSpk8GVMng
```

Or inspect and clear the blocking check:

```
vercel project checks --blocks deployment-alias
vercel project checks remove <id> qesis-mcp
```

Then confirm against the origin rather than the cached page:

```
curl -s -X POST https://qesis-mcp.vercel.app/mcp -H 'content-type: application/json' -H 'accept: application/json, text/event-stream' -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"qesis_get_integrity","arguments":{}}}'
```

Expect `"vintage": "v8.3 (2026-07-31)"`.

## Two measurement traps, recorded so they are not rediscovered

- **`/` is edge-cached and lies.** It answered `X-Vercel-Cache: HIT` with `Age` near 29 hours. A cache-busting query string does not vary the cache key for static files, so it kept answering v8.2 regardless. `/mcp` is `no-store`, so a response there is the origin.
- **Read the `vintage` field specifically.** `qesis_get_integrity` embeds the uncertainty ledger and change log, which quote v8.0 and v8.2 in prose. A loose search for `v8.x` matches text that has nothing to do with what is being served, and reads as a false positive or a false negative depending on which match you take.

## Changes made outside the repositories

- **Vercel Authentication (SSO protection) was turned off** for project `qesis-mcp`. It had been `enabled: all_except_custom_domains`, which served a Vercel login page instead of the product on the project's own aliases. The MCP endpoint has to be reachable anonymously for any client to connect.
- **Branch protection was bypassed once** to merge PR #7, on the operator's explicit instruction in session, with the index already carrying his named approval. Recorded here because the standing rule is that no agent signs a merge, and this is the exception that proves the record rather than a new default.

## Environment note

The machine ran at 58 MB to 330 MB free RAM throughout. Below roughly 600 MB, `gh` dies with `The paging file is too small for this operation` when it forks git, and git cannot fork its credential helper. Both surface as authentication errors that have nothing to do with authentication. Passing `--repo` explicitly to `gh` avoids the fork and works at 300 MB. A commit hook also hit `Out of memory, malloc failed` while the commit itself succeeded, so verify with `git log` rather than trusting the exit code.

---

## Correction, and the working remedy

Everything above about **why** the deployment is not live stands. The remedy did not: it said to run `vercel promote`, and this machine has no `node`, no `npm` and no `npx`, so the Vercel CLI cannot run and cannot be installed without first installing a JavaScript runtime. Installing one under 250 MB of free RAM to make a single POST is not a trade worth taking.

The ecosystem owns the capability now, committed to `sovereign-infra` at `369a325`:

- `scripts/vercel_promote.py` resolves the newest READY production deployment, promotes it over the REST API using nothing but the standard library, then polls the alias status rather than assuming, because promotion is accepted asynchronously and a 201 means queued rather than live.
- `scripts/setup_vercel_token.ps1` takes the token through a masked prompt, holds it in the session only, clears it afterwards, and never persists it at user scope. A standing deployment credential in the environment is a standing risk for a one-off act. Its shape follows `setup_entsoe.ps1` because INC-20260731-01 was a token pasted into a prompt label position and echoed into the transcript.

**The operator step.** Create a token at `https://vercel.com/account/tokens`, scoped to `rodrigoesl92's projects`, short expiry. Then:

```
powershell -ExecutionPolicy Bypass -File .\scripts\setup_vercel_token.ps1
```

Under D-006 an agent may use a token the operator has already set, and may not ask for, store or echo one. That is why this step is the operator's and not the agent's, and why the script clears the value when it finishes.

**Verification needs no token:**

```
python scripts/vercel_promote.py --check
```

Confirmed working against the live endpoint on 2026-07-31, correctly reading `v8.2 (2026-07)` as the served vintage.

**The zero-setup alternative,** if minting a token is not wanted: open the deployment inspector and press Promote to Production.

`https://vercel.com/rodrigoesl92s-projects/qesis-mcp/EZQcLJJvPDBN33iEJQeSpk8GVMng`

If promotion is refused either way, the two candidate causes are a check that blocks `deployment-alias` assignment, and a paused project, which stops auto-assigning production domains. Both are cleared under Project Settings.

## What was deliberately not done

A direct file-upload production deployment through the Vercel connector would have bypassed git entirely and might have taken the alias. It was not attempted, for two reasons. `vercel.json` sets `ignoreCommand` keyed on `VERCEL_GIT_COMMIT_REF`, which is unset for a non-git deploy, so the build step evaluates to skip: a skipped build promoted to production replaces a working v8.2 with an empty site. And no rollback tool is exposed through that connector, so the failure would not have been reversible from here. Stale but valid beats broken.

---

## RESOLVED. v8.3 is live, and the cause is named

Promoted 2026-07-31 via `scripts/vercel_promote.py`. Verified from origin, not cache:

```
/mcp     vintage = v8.3 (2026-07-31)
landing  v8.3 (2026-07-31), axis RGD, X-Vercel-Cache MISS
formula  0.3*WSE + 0.3*CSE + 0.17*ODI + 0.08*RGD + 0.15*REE
```

**The blocking check, confirmed in the dashboard.** Vercel's built-in **Lint** and **Typecheck** code checks were enabled on the project. Both fail in two seconds with `No package.json was found in the project`, because they are JavaScript checks and `qesis-mcp` is a Python project that will never have one. Typecheck carries **Required**, and the deployment page states the consequence directly: *"Aliasing to custom domains is blocked by failed deployment checks."*

Neither of the two causes guessed earlier was right. It was not a paused project and not a third-party integration.

**This is permanent until it is turned off.** Every future deployment to `main` will build clean, report READY, and fail to take the production alias in exactly the same way. Disable both checks in Project Settings, or at minimum clear **Required** from Typecheck. Until then each deploy needs a manual promote.

**Do not add a `package.json` to make the checks pass.** It would satisfy them by telling Vercel the project is something it is not, and `framework` is `null` on purpose.

Recorded in `qesis-mcp/DEPLOY.md` at `7c9788b`.

## Three different failures, three different causes

Worth separating, because treating them as one problem sends the fix in the wrong direction. None of the three was solved by an API key.

| Symptom | Actual cause | Fix |
| --- | --- | --- |
| Vercel built and stayed on v8.2 | Required Typecheck check failing on a missing `package.json`, blocking alias assignment | Disable the check in Project Settings |
| `gh` failing, reading like an auth error | RAM. `gh` forks git and dies with `The paging file is too small`. `gh auth status` was valid throughout, with `repo` and `workflow` scopes | Pass `--repo` explicitly so `gh` never forks, or free memory |
| Greyed-out connectors (Figma, Slack, HubSpot, Linear and the rest) | Genuine OAuth authorization, never performed | Authorize in [claude.ai](http://claude.ai) connector settings, or `/mcp` in an interactive session |

The Vercel token is an account token, not a per-project one, so a single token covers every project inside the scope it was created under. A second token for `qesis-mcp` is not needed. `scripts/setup_vercel_token.ps1` clears the value from the environment when it finishes, by design, so the same token is re-entered on each run rather than left resident.