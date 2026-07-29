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

## Three projects are attached to this repository

Only one should be. As of 2026-07-29 the Vercel dashboard shows:

| project | domain | verdict |
|---|---|---|
| `qesis-mcp` | `qesis-mcp.vercel.app` | **keep**, this is the canonical address |
| `rodrigoesl92-cloud-qesis-mcp` | auto-generated | delete, duplicate of the same repo |
| `site` | `site-nine-eta-99.vercel.app` | delete, no production deployment, never finished |

Each attached project builds every push, so one commit produced three
deployments and three status checks. Deleting a project cannot be done from the
repository: it is Vercel dashboard only, under Project Settings, Advanced,
Delete Project.

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
