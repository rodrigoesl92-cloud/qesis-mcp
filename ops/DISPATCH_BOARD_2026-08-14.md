# Dispatch board, 2026-08-14

**Author: COUNSEL. Standing pairing: COUNSEL detects and reports, ARCHITECT fixes.
Every finding below is a hypothesis ARCHITECT may refute, and every remedy gets the
same hostile reading as the original defect (R-2).**

Read order used: `qesis-mcp/CLAUDE.md`, then `sovereign-infra/ops/GOVERNANCE.md`,
then `ops/D-110_KG_FSQCA_ASSESSMENT.md` once, then the evidence plane
(`data/axes/`, `ops/`, `sovereign-infra/ops/analysis/`). The served index
`data/qesis_v8.json` was treated as a summary, not as the data.

---

## 0. Headline: two of the eight briefed tasks are wrong as briefed

The brief is a brief, not a spec, and it was tested before it was run. SEC-1
describes a state of the repository that ceased to be true on 2026-08-13. KG-1
cites fixture evidence that does not exist. Both corrections are below with the
command that produced them. Running SEC-1 as written would have had ARCHITECT
rebuild a scanner that already exists and already works, which is the most
expensive class of error available here: reporting verified work as broken.

---

## 1. The board

| Id | Agent | Gate | Blocks / blocked by | State after review |
|---|---|---|---|---|
| **A-3** | ARCHITECT, SENTINEL confirms | new pre-commit content + one refuse fixture | blocks nothing, blocked by nothing | **NEW, promoted above SEC-1.** Documented gate is not the gate on disk |
| **MDA-1** | ARCHITECT wires, SENTINEL gates | new `R1.28`, two fixtures | blocks nothing, blocked by nothing | **CONFIRMED, worse than briefed** |
| **SEC-1** | ARCHITECT, then HUMAN for the two SHAs | `scripts/verify_action_pinning.py`, already written | blocked by GitHub ref API on the last two | **RESTATED. 8 of 10 already pinned, scanner already exists, not wired** |
| **KG-1** | ARCHITECT | `build_graph.py --check` in CI | blocks KG-5, KG-2 | **PARTIALLY REFUTED.** Build and `--check` verified. Fixtures do not exist |
| **KG-5** | ARCHITECT | plane declaration in `EDGE_SCHEMA` + two fixtures | blocked by KG-1 | **CONFIRMED, narrower than briefed.** Domain/range already blocks it structurally; the plane is prose only |
| **KG-3 / PUB-1** | ANALYST, then SENTINEL | `verify_served_contract` | blocks KG-2's honest caption | **CONFIRMED OPEN** |
| **AUDIT-1** | SENTINEL | `licence_audit` / `integrity_audit` | blocks nothing | **CONFIRMED, path stale, and a second instance found on the same line** |
| **KG-2** | ARCHITECT | render gates, U-04 scope sentence | blocked by KG-1 and KG-3 | **ACCEPTED WITH OBJECTION.** V4 is the wrong host |
| **KG-4** | SCOUT | none yet, sourcing discipline applies | blocks any D-110 fsQCA limb | **UNCHANGED, correctly scoped** |

Parallel groups, given the blocking column:

- **Wave 1, simultaneous, nothing blocks them:** A-3, MDA-1, SEC-1, KG-1, AUDIT-1, KG-4.
- **Wave 2, after KG-1 lands:** KG-5, and KG-3.
- **Wave 3, after KG-1 and KG-3:** KG-2.

KG-4 runs in parallel across all waves and gates nothing in this cycle.

---

## 2. Findings, each with the command that produced it

### A-1. SEC-1's premise is false as of 2026-08-13. Highest-value correction in this review.

The brief states: "All ten `uses:` lines across .github/workflows/*.yml carry
mutable tags."

```
$ grep -rn "uses:.*@[0-9a-f]\{40\}" .github/workflows/*.yml | wc -l
8

$ python scripts/verify_action_pinning.py ; echo $?
  8 pinned to a 40-char SHA, 2 not, 10 uses: lines
SEC-1 FAIL. Resolve each with, and never guess a SHA:
  gh api repos/<owner>/<repo>/commits/<tag> --jq .sha
  FAIL production-probe.yml: actions/github-script@v7 is a mutable tag
  FAIL production-probe.yml: actions/github-script@v7 is a mutable tag
1
```

Eight of ten are pinned. The scanner the brief asks ARCHITECT to build already
exists, already fails strict, and already returns the correct non-zero exit code.
`ops/MODELING_LAYERS_MDA.md` line 134 records the remediation, its date, both
resolved SHAs, and the reason the last two are open: the GitHub ref API did not
return a ref and **a supply-chain SHA is never guessed**.

The residual is therefore narrower and harder than the brief assumed. It is not an
edit ARCHITECT can make. It needs an authenticated `gh api` call or a human, and
until then the honest control is the explicit `--allow-unresolved
actions/github-script` declaration the scanner already supports, which makes the
exception visible rather than silent.

**What is actually open under SEC-1:** the scanner is wired into nothing.

```
$ grep -rn "verify_action_pinning\|build_graph" .github/workflows/*.yml
(no output)
```

**Restated SEC-1 for ARCHITECT.** Wire `verify_action_pinning.py` into
`qesis-integrity.yml`. Do not re-pin what is pinned. Do not guess the two
`github-script` SHAs. Escalate the two unresolved refs to HUMAN as a one-line
request naming the command, not the value.

### A-2. The pre-commit gate SEC-1 targets does not exist in this repository.

```
$ cd qesis-mcp && git config core.hooksPath
(empty)
$ ls .git/hooks/ | grep -v sample
(no output)

$ cd sovereign-infra && git config core.hooksPath
.githooks
```

`qesis-mcp` has no hooks path and no installed hooks. The workflows live in
`qesis-mcp`. "Add a pinning scan to the pre-commit gate" therefore names a layer
that does not exist in the repository that holds the artefact. CI is the only
enforceable layer available today, which is why the restatement above targets CI.

### A-3. sovereign-infra's documented pre-commit gate is not the gate on disk. NEW, and the most serious item on this board.

`sovereign-infra/CLAUDE.md` states: "The pre-commit gate is a credential scan plus
`SENTINEL doctrine_audit`. Both must be clean."

```
$ grep -n -i "credential\|secret\|doctrine\|style" .githooks/pre-commit .githooks/pre-push
(no output)

$ cat .githooks/pre-commit
# ... branch warning on main/master/production (warns, does not block)
# ... D-107 duplicate ticket id check on ops/TICKETS.json (blocks)
exit 0
```

There is no credential scan in the pre-commit hook. There is no `doctrine_audit`
in it either. The hook warns on branch and blocks on duplicate ticket ids. Both of
those are real controls and both are well argued in their comments. Neither is the
control the governance document says is there.

This is the `L-082` to `L-094` family exactly: a control is real only at the layer
it is applied. It ranks above SEC-1 on this board because the project's own record
carries four credential exposures, and the standing memory of that episode
concludes that the absence of CI in `sovereign-infra` was the root cause. A
reviewer reading `CLAUDE.md` would mark the credential control closed. It is not
closed. It was never open at that layer.

**Counter-argument, stated before it is asked for.** It is possible the credential
scan was deliberately moved to CI or to a wrapper script and the `CLAUDE.md` line
is merely stale prose rather than a missing control. I could not find it in
`.githooks/`. That is the limit of what this command proves, and ARCHITECT may
refute it by naming the layer where the scan actually runs. If it runs nowhere,
the finding stands at full severity. If it runs somewhere, the finding degrades to
a documentation defect and `CLAUDE.md` gets the correction. Either way the prose
and the disk must be made to agree.

### A-4. MDA-1 confirmed, and it is worse than briefed.

```
$ python -c "import json; d=json.load(open('data/qesis_v8.json')); print(d['effective_weights']['finding'])"
Nominal and realised weights diverge. WSE realises roughly 1.8x its declared
weight. ODI, RGD and REE together carry 40% of nominal weight and realise close to
zero. REE is simultaneously quasi-necessary under fsQCA (consistency 0.916) and
effectively weightless in the composite built from the same data.

$ python -c "... d['fsqca']['necessity']['REE'] ..."
{"necessity_consistency": 0.7033, "necessity_coverage": 0.5763,
 "erratum": {"withdrawn_value": 0.916, "withdrawn_from": ["data/qesis_v8.json", ...]}}
```

The brief says one served block cites live what another withdraws. Correct, and
the sharper statement is this: the withdrawal record **names the file the live
citation sits in**. `withdrawn_from` lists `data/qesis_v8.json`, and the withdrawn
value is still being asserted in the present tense inside `data/qesis_v8.json`.
The artefact refutes itself in one hop.

`fsqca.necessity_verdict` is unambiguous and is worth quoting to whoever wires
this, because it explains why a bare threshold would not have caught it: REE
"scores 0.7268 against the negated outcome, higher than against the outcome, so it
tracks the absence of the result more closely than the result."

`R1.23` reads `citation_concordance.resolution_bindings` and does not reach
`effective_weights`. **Specification for the new gate, `R1.28`:** no prose field
anywhere in the payload may assert a numeric value that appears in any
`erratum.withdrawn_value` whose `withdrawn_from` includes that payload. Refuse
fixture: the current `effective_weights.finding` verbatim. Accept fixture: the
same sentence rewritten to cite 0.7033 with the D-109 conjunctive verdict, or to
attribute 0.916 explicitly to withdrawn thesis section 4.5 in the past tense.

Note for whoever writes the replacement sentence: the *substantive* finding
survives. REE being weightless in the composite is untouched. Only the necessity
limb is withdrawn. Do not delete the paragraph; correct its citation.

### A-5. KG-1 partially refuted. The build is sound. The fixtures are not there.

```
$ python scripts/build_graph.py --check ; echo $?
OK   graph matches a fresh build at v9.0 (2026-08-13)
0

$ python -c "... len(nodes), len(edges) ..."
nodes 68 edges 175
```

68 nodes and 175 edges confirmed, `--check` idempotent, exit 0. Node kinds: State
35, LandingCity 15, Axis 6, Provider 4, CableSourceDataset 3, WithholdingCause 2,
Vintage 2, CableNetwork 1.

The fixture claim does not hold.

```
$ grep -c -i "graph" scripts/test_gate.py
0
```

`scripts/build_graph.py` line 209 says: "Fixtures live in `scripts/test_gate.py`;
this is the assertion they exercise." `test_gate.py` contains zero occurrences of
the string "graph", case insensitive. Its 22 mutation fixtures run `R1.3` through
`R1.26` against the index. None touches the graph.

So the graph gate is a gate whose docstring names fixtures that do not exist. That
is the same failure shape as A-1 and A-3, committed in the file whose entire
argument is that typed edges make commitments explicit, and it is the second
second-order defect in `build_graph.py` inside two revisions. R-2 earned: the
moment of highest risk is immediately after a correction.

**KG-1 restated.** Wire `build_graph.py --check` into `qesis-integrity.yml` beside
`build_eval --check`, **and** land the two fixtures in `test_gate.py` in the same
change set, or delete the sentence at line 209. Wiring the CI step without the
fixtures satisfies the brief and leaves the lie in place.

### A-6. KG-5 confirmed, but narrower than briefed. Say so, or ARCHITECT will rebuild working code.

`validate()` already enforces domain and range on every edge from `EDGE_SCHEMA`.
Because `CHOKEPOINT_IN` is declared `LandingCity -> CableNetwork`, a
`CableSourceDataset` node structurally cannot appear on it today. The typing
control exists and works.

What does not exist is the *plane*. `EDGE_SCHEMA` declares only domain and range:

```
{"HOSTS_REGION_OF": {"domain": "State", "range": "Provider"},
 "CSE_VALUE_SOURCED_FROM": {"domain": "State", "range": "CableSourceDataset"},
 "CHOKEPOINT_IN": {"domain": "LandingCity", "range": "CableNetwork"}, ...}
```

There is no `plane: physical | provenance` field. The distinction that the whole
D-110 revision B correction turns on lives in Python comments at lines 39 to 42,
133, 173 and 193, and in prose in the assessment. A rule held only in prose has
been described, not applied (L-054). The brief is right about the principle and
wrong to imply nothing is wired.

**KG-5 restated.** Add `"plane"` to every `EDGE_SCHEMA` entry. Have `validate()`
refuse any edge whose plane is `physical` and whose domain or range resolves to a
node kind declared as a provenance artefact. Two fixtures: refuse a
`CSE_VALUE_SOURCED_FROM` edge retyped as physical, accept the current graph.

### A-7. AUDIT-1 confirmed. The path is stale and there is a second instance on the same line.

```
$ ls ops/ | grep -i audit
DEPLOYMENT_AUDIT_2026-08-02.md

$ git log --oneline --all -- 'ops/v9.0_FINAL_AUDIT.md' | head -1
c4b24a7 fix(ui): restore classic dashboard design, rename audit to DEPLOYMENT_AUDIT_2026-08-02.md per step 1
```

`ops/v9.0_FINAL_AUDIT.md` does not exist. It was renamed at `c4b24a7`. The
standing item in `CLAUDE.md` names a path that has not existed since that commit,
which is itself a `L-074` breach: a document that does not name its live path
sends the next reader to nothing.

The claim survives in the renamed file and the finding stands on the merits:

```
$ grep -n -i "emodnet" ops/DEPLOYMENT_AUDIT_2026-08-02.md
5:* **Data Pipelines**: ENTSO-E, Ember, and EMODnet verified ACTIVE.

$ python -c "... emodnet_cse_evidence.json['reproduction_verdict'] ..."
{"qesis_states_sourced_by_emodnet": 12, "coverage": 0.3429, "big_gate": 0.75,
 "passes_big_gate": false, ...}
```

Coverage 0.3429 against a 0.75 gate, `passes_big_gate: false`, and the file's own
verdict is NOT REPRODUCIBLE at Spearman -0.467. ACTIVE is a property of a
connection, not of a result (L-055).

**Second instance, not in the brief.** The same line certifies **ENTSO-E** ACTIVE.
`ops/INC-20260731-01.md` is open and the standing position is that the ENTSO-E
token is deferred, not held. One line therefore commits the L-055 error twice. Any
restatement SENTINEL writes must cover both, not just EMODnet.

**Disposition for SENTINEL:** restate, do not close. Suggested wording: "ENTSO-E,
Ember and EMODnet connectors were reachable on 2026-08-02. Reachability is not
reproduction. EMODnet returns coverage 0.3429 against the 0.75 BIG gate and a NOT
REPRODUCIBLE verdict; see `data/axes/emodnet_cse_evidence.json`."

### A-8. KG-3 / PUB-1 confirmed open.

```
$ python -c "... json.dumps(qesis_v8).lower().count(t) ..."
percolation      -> 0
porthcurno       -> 0
giant_component  -> 0
articulation     -> 0
emodnet          -> 39
```

The percolation evidence is not on the served surface in any form. EMODnet appears
39 times as a source label, but its reproduction verdict does not. The finding
carried by `cse_percolation.json` is therefore unpublished: twelve targeted
removals cost 31 cities between them, the thirteenth, Porthcurno in the United
Kingdom, severs 278, against random removal of 88 cities costing 14 percent of the
giant component. Robust-yet-fragile, confirmed and audited in the evidence plane.

This is **not** a ledger gap and is not to be filed as one. The disposition is
already audited. PUB-1 is a publication task, not a remediation.

### A-9. KG-2 accepted with a design objection.

V4 is the coupling matrix, a six by six axis to axis structure. V5 is pathways.
The conjunctive result is a **state-level** set intersection, `SOLE_PROVIDER` and
`CHOKEPOINT_IN`, and its cardinality is **0**. Putting a state-level empty set on
an axis-level matrix is a category error dressed as a feature, and rendering an
empty set on the hero-adjacent views risks reading as a rendering failure rather
than as a result.

**Counter-proposal for ARCHITECT to accept or refute:** the null belongs in V6, the
provenance strip, or as an explicit callout under V2 geography where states are
already the unit. If it goes on V4 or V5 regardless, it must render as a named
null with the U-04 scope sentence attached, never as an empty region.

The U-04 sentence is already carried correctly in the artefact and must travel
verbatim with every use:

> SOLE_PROVIDER means only one hyperscaler operates a cloud region on that state's
> territory, weighted one unit per active region because availability-zone counts
> are missing for 27 of 35 states (U-04). It is jurisdictional single-sourcing, not
> a claim about where that state's workloads run.

---

## 3. Refused, and recorded as refused rather than deferred

No agent reopens these in a later session.

1. **Autonomous mutating pull requests.** G-06 plus Article 14. An agent may merge
   a paired remediation PR by `gh pr merge --rebase` once checks pass. It may not
   push to `main` and may not promote.
2. **Per-instance fsQCA diagnosis.** fsQCA is cross-case. A live sub-graph is n=1.
   D-110 F-4.
3. **Automated fuzzy calibration of graph metrics.** Anchors are part of the
   result and there is no anchor theory for graph features. D-110 F-3. This is
   D-103 at machine speed.

---

## 4. RDL, drafted not filed, and why

Three lessons are earned by this review. They are drafted here and **not** appended
to `sovereign-infra/ops/LESSONS_LEDGER.md` by COUNSEL.

The reason is doctrinal, not timid. Step 5 of the RDL protocol requires the control
to be wired in the same change set, because a rule held only in prose has been
described, not applied. Appending three lessons tonight with no control attached
would commit, in the ledger, the exact defect the review is reporting three times
over. ARCHITECT lands each lesson with its gate, atomically, and SENTINEL confirms.
COUNSEL detects and reports. Ledger ids are assigned at that point, not reserved
here.

| Draft | Rule, one imperative sentence | Control that must land with it |
|---|---|---|
| Stale-brief | Before acting on a task brief, run the command that would falsify its premise, and report the refutation before the remedy. | The board itself; no code control needed |
| Phantom-fixture | A docstring naming a fixture file is a claim, and it fails the build unless the named file contains the fixture. | Grep assertion in `test_gate.py` over every `Fixtures live in` string |
| Documented-not-installed | A governance document asserting a hook is checked against `core.hooksPath` and the hook body, or it is not asserted. | Startup assertion in `qesis_agents status` |

---

## 5. Boundaries this board inherits and does not relax

No agent pushes directly to `main`. No agent promotes to production. Merges of
paired remediation PRs use `gh pr merge --rebase`, never squash, because squash
strands the commit hashes the lineage register cites. No credential moves in either
direction, including for the purpose of testing whether one is dead; an agent names
the environment variable and refuses the value. Every mutating command names its
repository explicitly and the confirmation read back is the remote, not the exit
code. No em dash in prose, and `SENTINEL doctrine_audit` runs as the last act of
writing.

---

## 6. What I could not verify, stated rather than assumed

- Whether the credential scan in A-3 runs at some layer I did not open. I searched
  `.githooks/` in `sovereign-infra` and the hooks path in both repositories. I did
  not enumerate CI in `sovereign-infra`, and standing memory records that
  `sovereign-infra` has no CI at all, which if true makes the finding worse rather
  than better. ARCHITECT should confirm or refute directly.
- Whether the two `actions/github-script` SHAs are resolvable today. The API did
  not return a ref on 2026-08-13 per `MODELING_LAYERS_MDA.md`. I did not retry,
  because retrying it from an agent session and acting on the result is the exact
  shape of guessing a supply-chain SHA.
