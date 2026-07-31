# Deploying QESIS+

The public surface is two things served from one Vercel project: a static
landing page generated from the index, and a remote MCP endpoint.

| path | what | served by |
|---|---|---|
| `/` | landing page, generated from `data/qesis_v8.json` | `public/index.html` |
| `/mcp` | streamable HTTP MCP endpoint | `api/index.py` |

## One deployable branch

`vercel.json` sets `ignoreCommand` so Vercel skips the build for any ref other
than `main`. Vercel runs that command before building and treats **exit 0 as
skip, exit 1 as build**, which reads backwards until you have been caught by it
once.

Without this, every feature branch produced a preview URL answering alongside
production, and it stopped being obvious which address was the index.

`vercel.json` cannot carry comments. Vercel validates it against a strict
schema and rejects unknown top-level keys, including a `"//"` comment key. That
rejection surfaces on the pull request as three separate "Deployment failed"
checks linking to the project-configuration docs, with no build log, which is
why this note exists rather than a comment in the file.

## One project is attached to this repository

This was three until 2026-07-31. `rodrigoesl92-cloud-qesis-mcp` and `site` are
gone, and the API now returns a single project, `qesis-mcp`
(`prj_qp1c8sgZNJi2XUGcbVfzLN5QVT2r`), holding `qesis-mcp.vercel.app`. That is
the canonical address. Each attached project used to build every push, so one
commit produced three deployments and three status checks.

Deleting a project cannot be done from the repository: it is Vercel dashboard
only, under Project Settings, Advanced, Delete Project.

## A READY production deployment is not necessarily the live one

Observed on 2026-07-31 and worth stating, because every obvious signal said the
release had shipped. The v8.3 merge to `main` built clean in three seconds, the
deployment reported `state: READY` and `target: production`, and it was the
project's `latestDeployment`. `qesis-mcp.vercel.app` went on serving v8.2.

The GitHub commit status carried the only hint: `Checks for Deployment have
failed`. A deployment whose checks fail is still built and still READY, and the
production alias simply is not moved onto it. Promotion, not the build, is what
publishes.

**The cause, confirmed in the dashboard.** Vercel's built-in **Lint** and
**Typecheck** code checks were enabled on this project. Both fail in two seconds
with `No package.json was found in the project`, because they are JavaScript
checks and this is a Python project that will never have one. Typecheck is
marked **Required**, and the deployment page states the consequence plainly:

> Aliasing to custom domains is blocked by failed deployment checks.

So the block is permanent and applies to every future deployment, not just the
v8.3 one. The API does not surface it: `get_deployment` reports `READY` and
`target: production` with no hint, and the only machine-readable signal is the
GitHub commit status string. Turn both checks off in Project Settings, or at
minimum clear **Required** from Typecheck. Until that is done, every deploy to
`main` needs a manual promote:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\setup_vercel_token.ps1
```

That lives in `sovereign-infra`, is stdlib only, and exists because there is no
`node`, `npm` or `npx` on the build machine, so every CLI-shaped remedy in
Vercel's own documentation is unusable here.

Do not "fix" this by adding a `package.json`. It would make the checks pass by
telling Vercel the project is something it is not, and `framework` is currently
`null` on purpose.

Two traps sit on top of that when you go to confirm it:

- `/` is a static asset and is edge-cached. It answered `X-Vercel-Cache: HIT`
  with `Age` near 29 hours, and a cache-busting query string does not vary the
  key for static files, so it kept answering v8.2 from the edge regardless.
  Check `/mcp` instead: it is `no-store`, so a response there is the origin.
- Read the `vintage` field specifically. `qesis_get_integrity` embeds the
  uncertainty ledger and change log, which quote older vintages in prose, so a
  loose search for `v8.x` matches text that has nothing to do with what is
  being served.

## Deployment protection

Preview deployments sit behind Vercel SSO by default and answer `401` with a
`Protected deployment` body. That is correct for previews and fatal for the MCP
endpoint, which has to be reachable anonymously for a client to connect.

Confirm under Project Settings, Deployment Protection that **Vercel
Authentication is off for Production**. Production was already public on
2026-07-29; the check matters after any settings change.

## Host allowlist

The MCP transport runs DNS-rebinding protection, which refuses any `Host` it was
not told about and answers `421`. `server.py` allows the production domain,
localhost, and whatever `VERCEL_URL` holds, because preview hostnames change per
deployment and matching is exact apart from a `:*` port wildcard.

To serve a custom domain, set `QESIS_ALLOWED_HOSTS` in the Vercel project
environment as a comma-separated list. It replaces the defaults entirely.

That replacement has a consequence worth knowing before you debug the wrong
thing. On 2026-07-31, `qesis-mcp.vercel.app/mcp` answered normally while
`qesis-mcp-rodrigoesl92s-projects.vercel.app/mcp` answered `421`. Both are
aliases of the same project and the same deployment. `_allowed_hosts()` falls
back to `VERCEL_URL`, `VERCEL_BRANCH_URL` and `VERCEL_PROJECT_PRODUCTION_URL`
only when `QESIS_ALLOWED_HOSTS` is empty, so setting it in the project
environment silently drops every alias not named in it. A `421` on one alias
and `200` on another is that variable, not a broken deployment.

## Verify a deployment

```bash
curl -s https://qesis-mcp.vercel.app/ -o /dev/null -w '%{http_code}\n'

curl -s -X POST https://qesis-mcp.vercel.app/mcp \
  -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Eight tools should come back. A `401` means deployment protection is on, a `421`
means the Host is not allowed, and a `404` on `/mcp` means the rewrite did not
apply and the function did not build.

Locally, `python scripts/test_http.py` drives the same ASGI app in-process and
checks the two failures that broke the first wiring: the session manager never
starting when a host sends no lifespan events, and the rebinding guard rejecting
the production Host.
