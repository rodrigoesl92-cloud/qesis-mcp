# Session record, 2026-08-27b: the two red checks, and what the RDL said about them

**ARCHITECT and COUNSEL. Follows the successful landing of PR 80 and PR 46.**
Every claim carries the reader that produced it, per D-118 rule 1.

---

## 1. The landing closed

| Value | Plane | Reader | Result |
|---|---|---|---|
| qesis-mcp main | delivery | lander `gh_ops.py proof`, 11:5xZ | `e7647fbe6f48`, PR 80 merged by rebase |
| sovereign-infra main | delivery | same | `3dfc8d70686b`, PR 46 merged by rebase |
| ledger | evidence | `rdl_append.py` then the singleton gate | L-185 to L-188 appended, sha256 `1c3a98557be80bab`, both copies |
| audit | all four planes | `audit_ecosystem.py` | VERDICT GREEN, every predicate holds |
| chain | serving | the audit's store read | 754 entries, 0 breaks |

## 2. The request, and why it was refused as written

The brief asked for the Dockerfile memory limits, port configuration and EU
authentication parameters "we established two weeks ago", to be applied to a
Cloud Run deployment in `europe-west1`.

**The RDL was queried first, and it says the opposite.**

- **L-044, 2026-07-29.** A five service cloud migration was proposed to solve a
  memory problem. Cloud Run was priced out explicitly: it "could not move
  without the data, and moving the data was the paid item". The rule is that
  each service is priced against the specific failure it removes.
- **D-113, ACCEPTED and signed by the operator 2026-08-19**, eight days ago and
  inside the window the brief remembers. Option A, migrate the runtime to an
  EU-jurisdiction provider, was **refused**. The adopted decision is one line:
  **"Adopt the current posture explicitly, and instrument it. Do not migrate."**

So there is no historical Cloud Run solution to retrieve. There is a signed
decision not to have one. Delivering a Dockerfile and a `cloudbuild.yaml` would
have adopted a substrate dependency the operator refused, without a decision
number, which is precisely L-045, the lesson D-113 exists to close.

## 3. What is actually failing, measured

Both repositories, read from disk: **no Dockerfile, no `cloudbuild.yaml`, no
`.gcloudignore`, no GCP workflow, no `Procfile`, and no `main.py`, `app.py`,
`wsgi.py` or `asgi.py`.** `docker-compose.yml` is a local pgvector Postgres for
development and `Dockerfile.postgres` is its image. The served entrypoint is
`api/index.py`, a Vercel serverless function, which never listens on a port
because Vercel does not ask it to.

Nothing in either repository can produce a container. So nothing in either
repository produces those two checks. They are Cloud Build triggers in Google
Cloud project `5c4e8a9a-723a-453e-80d`, connected to the repository outside it.

**The `gh_ops.py` fixtures written on 2026-08-26 already use
`cloudrun-qesis-europe-west1` as the canonical example of a check the repository
does not own.** The integration predates this landing, has been red throughout,
and was never declared. Recorded as **L-190**, `dependency_not_declared`, and
opened as `ACT-7` on D-113.

## 4. Why it fails in 17 seconds, and what is not claimed

Seventeen and twenty seconds is build-phase timing. A source deploy with no
Dockerfile falls to buildpack detection, and Python buildpack detection needs an
entrypoint this repository does not carry. It fails before any container image
exists.

**A container that does not exist cannot be OOMKilled**, so no memory limit
fixes this, and no port setting does either. That is the load-bearing point and
it is measured from the absent files rather than from the failure text.

**What is not claimed.** The build log itself was not read. The Chrome bridge
returned a script injection timeout on seven consecutive attempts against
`github.com` this session, and `gh` is absent from the analysis VM, so no
authoritative reader for that log was available. Reported as a tool boundary per
D-118 rule 7 rather than dressed as a finding: the exact failure string is one
click away on either **Details** link and would confirm or refute the paragraph
above. Everything else here is measured.

## 5. The defect this exposed in the ecosystem, and the gate that closes it

The commit page showed **7 successful and 2 failing**. The proof block printed
six owned check names, named neither failure, and the audit concluded GREEN.

Both were correct. D-116 rule 3 says a check the repository does not own must
not block, and neither does. But "must not block" had been quietly implemented
as "must not be mentioned", and those are different claims. The operator read a
GREEN verdict against a page reading 7/9 and reasonably concluded the ecosystem
was hiding a backend failure from him.

That is **L-189**, `scope_of_verdict_not_stated`: a verdict over a filtered set
that does not name what it filtered is read at the reader's scope, not at its
own. It is L-179 inverted, silence read as absence rather than as success.

**Shipped in the same change set.** `gh_ops.py foreign_checks` inventories every
check on a commit the ecosystem does not own. `proof` prints them under a
heading that says they are reported and never asserted, with a count of how many
are not passing, and a line naming what an undeclared writer to commit status
is. Five fixtures hold it: a foreign check is listed whatever its conclusion,
every foreign check is listed rather than the first, an owned check never
appears in the inventory, a foreign check carries its own state, and an empty
inventory prints nothing. `test_gate.py` is 92 of 92.

The verdict is unchanged. It still turns on owned checks only. What changed is
that it can no longer be read as broader than it is.

## 5b. While looking at the noise, the actual outage

The two red checks were noise. The public endpoint was down, and every gate was
green, and the two facts have the same cause.

**Measured 2026-08-27T12:40Z, against `a.regfish-ns.net` at 178.21.144.21, the
zone's own authoritative nameserver, by direct UDP query. Not a resolver cache.**

| Name | Type | Result |
|---|---|---|
| `qesis.eu` | A | `216.198.79.1`, the Vercel apex address |
| `qesis.qesis.eu` | CNAME | `4419ea408f5d2543.vercel-dns-017.com` |
| `www.qesis.eu` | CNAME and A | **NXDOMAIN. The name does not exist in the published zone** |

And the serving plane, read through the Vercel API:

- `https://qesis.eu/health` returns **308 Permanent Redirect** to
  `https://www.qesis.eu/health`.
- `https://qesis.qesis.eu/health` returns **200**, `deployment_commit`
  `e7647fbe6f48`, `index_sha256` `8009815e4c19...`, chain VERIFIED, 754 entries,
  0 link breaks, database connected.

**So the application is perfect and the front door is a dead end.** Everyone who
types the domain is redirected to a hostname with no DNS record. The Vercel
project carries `www.qesis.eu`, `qesis.qesis.eu` and `qesis.eu` as attached
domains, so the platform side is complete; the registrar zone holds two records
and `www` is not one of them. The registrar's change log shows a `www` CNAME
created 05.08 and modified 08.08, and the authoritative answer today is
NXDOMAIN, so the 08.08 change is where it went.

The registrar dashboard recorded **1377 queries and 768 errors in 24 hours**
against this one domain. That error rate is the outage, counted by the registrar,
for nineteen days.

**Why no gate saw it.** `production-integrity-probe.yml` probes
`qesis-mcp.vercel.app`. That is the platform alias, it was healthy throughout,
and it is not the address on the business card. A surface was added and its
control was not. Recorded as **L-191**,
`surface_added_without_its_control`.

**The control shipped in this change set.** `scripts/verify_public_domain.py`
follows each published address hop by hop and refuses a redirect into a host with
no DNS record, which is precisely the shape of this defect. `assess` is a pure
function over the hop chain, so it runs with no network and no credential, and
seven fixtures hold it, including the live defect as it stood. Run live against
the tree today it prints:

```
FAIL  https://qesis.eu/health
      qesis.eu 308 -> www.qesis.eu (no DNS)
```

**Deliberately not yet wired into the required gate.** The address it asserts is
currently a dead end, and a gate that blocks every landing until a DNS record
appears is a worse failure than the one it reports. It is in `test_gate.py` as
fixtures now and flips to a live assertion in the landing after the record
exists. That is a decision recorded, not a step forgotten.

## 5c. The two ways to fix it, and neither is a container

**Recommended, and it needs no DNS change at all.** Make `qesis.eu` the primary
domain on the Vercel project so it serves directly instead of redirecting to
`www`. The apex already resolves and the deployment behind it is the landed
commit. One setting, no zone edit, no DNSSEC exposure, and `qesis.eu` is the
better canonical for this brand than `www.qesis.eu` anyway.

**Or, add the missing record.** `www.qesis.eu` CNAME to the target Vercel shows
for that domain in the project's domain settings. Do not copy the target from
`qesis.qesis.eu`: Vercel issues a distinct hostname per domain, and
`4419ea408f5d2543.vercel-dns-017.com` belongs to that name. `cname.vercel-dns.com`
is the documented universal alternative where the per-domain value is not shown.

Both acts are credentialed and therefore human under G-03. The operator's
authorisation to work inside the DNS is recorded and it changes what can be
monitored, not who holds the key: no plaintext credential passes through an
agent in either direction, which is the standing rule after four exposures on
this project. If DNS automation is wanted later, the token belongs in the CI
secret store, installed by the operator, and the ecosystem reads the zone
through it. Reading the zone needs no credential at all and now happens in a
control.

## 5d. The retrieval, done properly the second time

The operator pressed twice for the historical Cloud Run configuration. The first
search stopped at `ops/`, `CODEBOOK.md`, `README.md` and the index of one
repository and reported nothing, which is L-188 repeating inside the same
session. The second search went where D-118 rule 9 says to go and found the
document.

**`sovereign-infra/ops/GCP_RUNBOOK.md`, authority D-043, dated 2026-07-29**,
indexed in the operational store as asset `QES-A0106`. It was located through
the store's own retrieval table rather than by guessing filenames: the chunk row
names the path, and the earlier `grep` had timed out against the 12 MB SQLite in
the same tree before reaching it.

**What the historical solution actually says**, quoted from its own table:

| Service | Verdict | Reason given |
|---|---|---|
| Cloud Storage | **connect** | solves the real failure, roughly free at this volume |
| Cloud Build | **skip** | duplicates a GitHub Actions pipeline that already runs free and green |
| Cloud Run | **defer** | the runtime reads the local corpus and writes the local compliance chain, so moving the server without the data gains nothing |

Section 9 is explicit: "It does not move compute, does not create a database,
does not install an agent in Google Cloud. The runtime stays local and
sovereign."

**So the retrieval succeeded and returned no memory limits, no port
configuration and no Cloud Run region parameters, because none were ever
established.** What was established, and is running, is Cloud Storage in
`europe-west3` under project `qesis-sovereign-infra`, with the identifiers fixed
in `qesis_agents/cloud.py` lines 32 to 36.

**And the failing checks match neither identifier.** They name
`project-5c4e8a9a-723a-453e-80d` and `europe-west1` against a canonical
`qesis-sovereign-infra` and `europe-west3`. This is not a misconfigured version
of the connection this ecosystem declared. It is a second connection, in another
project, in another region, that D-043 declined to make.

**The real defect is that this was already known and never made runnable.**
`HANDOVER_2026-08-24.md` line 101 says disconnect the trigger.
`HANDOVER_2026-08-26.md` line 138 says it again. The 2026-08-27 report says it a
third time. Three statements, zero commands, and an instruction repeated long
enough starts being remembered as a solution that was implemented. That is
**L-192**, `instruction_repeated_instead_of_delivered`, and the remedy is
`sovereign-infra/ops/GCP_DISCONNECT_TRIGGERS.md`: the exact `gcloud` calls to
list and delete both triggers, the GitHub App step that removes write access to
commit status, and `gh_ops.py proof` as the after check, whose foreign inventory
goes from two lines to none.

## 6. The disposition, and it is the operator's

`ACT-7` on D-113. Two options, and the reasoning is L-044's.

**Disconnect the triggers.** Removes the failure completely, costs nothing,
deploys nothing that was ever deployed. This is the recommendation.

**Or declare and build.** If an institutional licence requires EU residency,
D-113 names that as a reason to reopen the page. It then needs a row in the
footprint table, a container this ecosystem actually builds and gates, a
decision on which surface the chain binds, and a bill. It is a decision, not a
configuration, and it does not begin with a Dockerfile.

Human under G-03 either way: the Google Cloud account and the GitHub integration
settings are both credentialed, and the Chrome bridge classifier refuses writes
to settings pages.

---
Decision holder: Rodrigo Batista Silva. Author for copyright purposes, and the
only signature on this record.
Prepared by: Claude, Cowork session of 2026-08-27, acting under CLAUDE.md and
sovereign-infra/ops/GOVERNANCE.md. Machine attribution under R-1: data, not
authorship, and not a claim of any right.
Landed by: pending.
