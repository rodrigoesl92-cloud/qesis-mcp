"""qesis_mcp: Sovereign Substrate Intelligence as an MCP server.

Exposes the QESIS+ v8.0 index (Batista Silva, 2026) so any MCP-capable AI
client (Claude.ai, Claude Code, enterprise agents) can query substrate
sovereignty data as a first-class tool.

Tiering: without QESIS_LICENSE_KEY in the environment the server runs in
DEMO mode (top-10 ranking depth, scores rounded to integers, component
audit locked). Any non-empty key unlocks the institutional vintage.

Run (local stdio):      python server.py
Run (remote, HTTP):     python server.py --http   (streamable HTTP on :8000)
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

DATA_PATH = Path(__file__).parent / "data" / "qesis_v8.json"
# C-01. The chain attestation is a separate artefact on purpose. It is produced by
# an independent verifier in sovereign-infra, never by the process that appends to
# the chain and never by the process that writes the index. Keeping it out of the
# index is what stops the index builder from becoming a second self-reporter.
CHAIN_PATH = Path(__file__).parent / "data" / "chain_attestation.json"
# The spine is the evidence; the attestation is a second opinion about it. Both
# are committed, so this process can recompute the first and check the second
# against it rather than repeating either.
SPINE_PATH = Path(__file__).parent / "data" / "chain_spine.jsonl"
LICENSED = bool(os.environ.get("QESIS_LICENSE_KEY", "").strip())

DATA: dict = {}
_INDEX_SHA256: str | None = None
_CHAIN_CACHE: tuple[str, dict] | None = None

GENESIS = "0" * 64
# Restated from the documented definition, not imported from
# scripts/verify_chain.py. That verifier restates it rather than importing from
# the producer for the same reason: two independent restatements that agree are
# evidence, one shared import that agrees with itself is not. This is the third
# restatement and it is held to the same rule.
LINK_RULE = "sha256(prev_hash | input_hash | output_hash | timestamp)"


def _link(prev: str, input_hash: str, output_hash: str, timestamp: str) -> str:
    return hashlib.sha256(
        f"{prev}|{input_hash}|{output_hash}|{timestamp}".encode("utf-8")
    ).hexdigest()


def _recompute_chain(raw: bytes) -> dict:
    """Recompute every link from the committed spine. Raises if it cannot."""
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("the committed spine is empty")
    # A chain with a hole in it can still have every remaining link recompute,
    # so the sequence is checked separately from the hashes. Deleting an entry
    # and repointing its neighbour is only visible here.
    expected_seq = list(range(rows[0]["seq"], rows[0]["seq"] + len(rows)))
    dense = [r["seq"] for r in rows] == expected_seq
    breaks: list[int] = []
    prev = GENESIS
    for r in rows:
        if r["prev_hash"] != prev:
            breaks.append(r["seq"])
        if r["entry_hash"] != _link(prev, r["input_hash"], r["output_hash"], r["timestamp"]):
            breaks.append(r["seq"])
        prev = r["entry_hash"]
    return {
        "entries": len(rows),
        "link_breaks": len(breaks),
        "head_sha256": rows[-1]["entry_hash"],
        "genesis_sha256": rows[0]["entry_hash"],
        "sequence_dense": dense,
        "broken_at": breaks[:8] or None,
    }


def _refresh() -> dict:
    """Reload the index when the file on disk changes.

    The server is long-lived: a stdio host keeps it resident for the whole
    session. Without this, regenerating the index leaves every client reading
    the previous generation from memory while the corrected file sits on disk,
    which is the hardest class of drift to notice because both look right.

    The reload is also the reason G-01b exists. Any process that writes this
    file changes what is served, immediately, with no release event in between.
    That is convenient locally and it means `served` and `committed` can differ
    in either direction, so the hash below is taken on every load and published:
    a reader identifies the served bytes rather than trusting a vintage label.
    """
    global DATA, _INDEX_SHA256
    try:
        raw = DATA_PATH.read_bytes()
    except OSError:
        return DATA
    # Keyed on content, not on mtime. The mtime version missed a change: two
    # writes landing inside one filesystem timestamp tick left this process
    # serving the first while publishing a hash computed from it, which under
    # G-01b is worse than publishing no hash at all. Hashing 76 KB costs a
    # fraction of a millisecond and the JSON parse is still skipped when the
    # bytes are unchanged, so the fast path stays fast.
    digest = hashlib.sha256(raw).hexdigest()
    if digest != _INDEX_SHA256:
        DATA = json.loads(raw.decode("utf-8"))
        _INDEX_SHA256 = digest
        print(f"[qesis] loaded {DATA.get('vintage')} "
              f"({len(DATA.get('countries', {}))} states) "
              f"sha256 {digest[:12]}", file=sys.stderr)
    return DATA


def _chain() -> dict:
    """The chain state, recomputed in this process from the committed spine.

    Never fabricates a verdict. An unreadable spine is reported as unverified, because
    the failure this exists to prevent is a chain figure nobody can contradict, and
    a default of `0 link breaks` would recreate it in a worse form.

    This used to return the attestation file verbatim. That was still a number the
    reader had to take on trust: a deployment serving a stale or hand-edited
    attestation would answer `604 entries, 0 link breaks` just as confidently as a
    correct one, and nothing reachable over HTTP would disagree. The links are now
    recomputed from `chain_spine.jsonl` on the deployment that is answering, and the
    independent attestation is checked against that result rather than reported in
    place of it. Disagreement is published under `attestation.agrees`; it is never
    resolved silently in favour of either side.

    C-01 still holds. This process neither appends to the chain nor writes the index,
    so recomputing here is not self-reporting: it reads a committed artefact any
    reader can recompute with `python scripts/verify_chain.py`.
    """
    global _CHAIN_CACHE
    try:
        raw = SPINE_PATH.read_bytes()
    except OSError as exc:
        return {
            "status": "UNVERIFIED",
            "reason": f"no readable spine at {SPINE_PATH.name}: {type(exc).__name__}",
            "effect": "Do not cite a chain height or a link-break count from this "
                      "deployment. None is being asserted.",
        }
    # Keyed on content for the same reason as the index: two writes inside one
    # filesystem timestamp tick would otherwise leave a cached verdict describing
    # bytes that are no longer there.
    digest = hashlib.sha256(raw).hexdigest()
    if _CHAIN_CACHE is not None and _CHAIN_CACHE[0] == digest:
        return _CHAIN_CACHE[1]

    try:
        computed = _recompute_chain(raw)
    except (ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        return {
            "status": "UNVERIFIED",
            "reason": f"the spine did not parse: {type(exc).__name__}: {exc}",
            "effect": "Do not cite a chain height or a link-break count from this "
                      "deployment. None is being asserted.",
        }

    intact = computed["link_breaks"] == 0 and computed["sequence_dense"]
    out = {
        "status": "VERIFIED" if intact else "BROKEN",
        **computed,
        "spine_sha256": digest,
        "link_rule": LINK_RULE,
        "computed": ("Recomputed from data/chain_spine.jsonl by the process answering "
                     "this request, not read from a stored figure."),
        "reproduce": ("python scripts/verify_chain.py recomputes the same links from "
                      "the same committed spine and exits non-zero if they disagree."),
    }

    # The second opinion, kept separate and never merged into the numbers above.
    try:
        att = json.loads(CHAIN_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        out["attestation"] = {
            "present": False,
            "reason": f"no readable attestation at {CHAIN_PATH.name}: {type(exc).__name__}",
            "effect": "The recomputation above stands on its own; the independent "
                      "cross-check does not.",
        }
    else:
        disagreements = {
            k: {"attestation": att.get(k), "spine": computed[k]}
            for k in ("entries", "link_breaks", "head_sha256", "genesis_sha256")
            if att.get(k) != computed[k]
        }
        out["attestation"] = {
            "present": True,
            "agrees": not disagreements,
            "verifier": att.get("verifier"),
            "verified_at_utc": att.get("verified_at_utc"),
            "verified_from": att.get("verified_from"),
            "independence": att.get("independence"),
        }
        if disagreements:
            out["status"] = "DISPUTED"
            out["attestation"]["disagreements"] = disagreements
            out["attestation"]["effect"] = (
                "The committed attestation does not follow from the committed spine. "
                "Cite neither until that is resolved; one of the two artefacts is wrong.")

    _CHAIN_CACHE = (digest, out)
    return out


def _provenance() -> dict:
    """Which bytes are being served, and whether they are pinned to a release.

    G-01b. A vintage string is a label, not a fingerprint: two different builds
    of v8.4 shipped on 2026-08-01, one with a flattened lineage and one with it
    repaired, and both answered `v8.4 (2026-08-01)`. Anything comparing vintage
    strings to decide whether a promotion took effect would have seen no
    difference. The sha256 of the served file is the thing that distinguishes
    them, so it is published.

    On a Vercel deployment the commit is known from the build environment, so a
    reader can check out that commit, hash `data/qesis_v8.json` and get this
    number. On the local stdio plane there is no commit: the file comes from a
    working tree that any process may have written since. That case says so
    rather than leaving the reader to assume a release happened.
    """
    commit = (os.environ.get("VERCEL_GIT_COMMIT_SHA") or "").strip()
    if commit:
        return {
            "plane": "deployment",
            "index_sha256": _INDEX_SHA256,
            "deployment_commit": commit,
            "verify": ("git checkout <deployment_commit> && sha256sum "
                       "data/qesis_v8.json must equal index_sha256"),
        }
    return {
        "plane": "working tree",
        "index_sha256": _INDEX_SHA256,
        "deployment_commit": None,
        "warning": ("Served from a working tree, not from a promoted commit. "
                    "These bytes may be uncommitted. Match index_sha256 against "
                    "a commit before citing anything from this process."),
    }


def _contract(tool: str, served: dict) -> dict:
    """Does this process actually serve the vintage it is announcing?

    `_refresh()` reloads the index when the file changes; this module is read
    once at process start. A resident host therefore advances its vintage string
    the moment the data lands and keeps running whatever code it started with.
    That is how v8.4 was announced by a process serving neither `chain` nor
    `citation_concordance`, which are the two things v8.4 adds.

    A stale process now says so in its own payload rather than answering as
    though nothing were missing. The limit is worth stating plainly: this can
    only report a contract it knows about, so it protects every vintage after
    the one that introduced it and could not have caught the incident that
    prompted it.
    """
    declared = ((DATA.get("served_contract") or {}).get("tools") or {}).get(tool)
    if not declared:
        return {"status": "UNDECLARED",
                "note": f"the index declares no contract for {tool}"}
    missing = [f for f in declared if f not in served]
    if not missing:
        return {"status": "SATISFIED", "declared": len(declared)}
    return {
        "status": "STALE_RUNTIME",
        "declared": len(declared),
        "missing": missing,
        "effect": (f"This process loaded {DATA.get('vintage')} from disk but is "
                   f"running older code, so it is announcing a vintage it only "
                   f"partly implements. Restart the server before citing anything "
                   f"that depends on the missing fields."),
    }


_refresh()
AXES = ["WSE", "CSE", "REE", "FPE", "ODI", "RGD", "ESE"]
AXIS_NAMES = {
    "WSE": "Water Stress Exposure", "CSE": "Cable Stress Exposure",
    "REE": "Rare Earth Element Stress", "FPE": "Foreign Platform Exposure",
    "ODI": "Operator Dependency Index", "RGD": "Region Density",
    "ESE": "Electricity Stress Exposure",
}

def _allowed_hosts() -> list[str]:
    """Hosts accepted by the DNS-rebinding guard on the HTTP transport.

    The guard stays on. It defaults to refusing every Host it was not told
    about, which rejected the production domain with HTTP 421 until this was
    configured. Matching is exact, apart from a ':*' port wildcard, so Vercel
    preview deployments cannot be covered by a static list: their hostname
    changes per deploy. Vercel exports it as VERCEL_URL, so read it.
    """
    hosts = [h.strip() for h in os.environ.get("QESIS_ALLOWED_HOSTS", "").split(",")
             if h.strip()]
    if not hosts:
        # Both production names are allowed so the project can be renamed in
        # Vercel without a code change and without a window where the landing
        # page works and /mcp answers 421 to every client. An allowed host that
        # nobody is serving costs nothing: the guard checks the inbound Host
        # against this list, it does not advertise it.
        #
        # The custom domains are named explicitly and not left to VERCEL_*.
        # VERCEL_PROJECT_PRODUCTION_URL resolves to the SHORTEST production
        # domain, which is `qesis.eu`, while the domain that actually serves
        # traffic is `www.qesis.eu` (qesis.eu answers 308 to it). Relying on that
        # variable alone would have left every real request arriving on a Host
        # the guard had never been told about, so /mcp would have answered 421
        # from a deployment whose build, routes and tools were all correct.
        hosts = ["qesis.eu", "www.qesis.eu",
                 "qesis-mcp.vercel.app", "qesis.vercel.app",
                 "localhost", "localhost:*",
                 "127.0.0.1", "127.0.0.1:*", "0.0.0.0:*"]
    for var in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
        v = os.environ.get(var, "").strip()
        if v and v not in hosts:
            hosts.append(v)
    return hosts


_HOSTS = _allowed_hosts()

# stateless_http and json_response are required for serverless hosting: each
# invocation is a fresh process, so a session-bound transport has nothing to
# resume and a long-lived SSE stream has nowhere to live. Neither setting
# affects the stdio transport used locally.
mcp = FastMCP(
    "qesis_mcp",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_HOSTS,
        allowed_origins=[f"https://{h}" for h in _HOSTS if not h.endswith(":*")]
                        + [f"http://{h}" for h in _HOSTS if h.startswith(("localhost", "127."))],
    ),
)


def _tier_note() -> str:
    return "" if LICENSED else (
        "\n\n[DEMO TIER] Scores rounded; depth limited. Set QESIS_LICENSE_KEY "
        "for the institutional vintage (full precision, component audit, exports)."
    )


def _score(v):
    if v is None:
        return None
    return v if LICENSED else round(v)


def _country_or_error(iso: str):
    c = DATA["countries"].get(iso.upper())
    if not c:
        valid = ", ".join(sorted(DATA["countries"]))
        raise ValueError(f"Unknown ISO3 '{iso}'. Valid codes: {valid}")
    return c


class CountryInput(BaseModel):
    """Input for a single-country lookup."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    iso3: str = Field(..., description="ISO3 country code, e.g. 'DEU', 'ESP', 'GBR'",
                      min_length=3, max_length=3)


class RankInput(BaseModel):
    """Input for ranking countries."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    axis: str = Field(default="composite",
                      description="What to rank by: 'composite' or one of WSE, CSE, REE, FPE, ODI, RGD, ESE")
    top_n: int = Field(default=10, ge=1, le=35, description="How many countries to return")
    ascending: bool = Field(default=False, description="False = most exposed first (default)")


class CompareInput(BaseModel):
    """Input for comparing two countries."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    iso3_a: str = Field(..., min_length=3, max_length=3, description="First ISO3 code")
    iso3_b: str = Field(..., min_length=3, max_length=3, description="Second ISO3 code")


class PathwayInput(BaseModel):
    """Input for pathway queries."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    iso3: Optional[str] = Field(default=None, min_length=3, max_length=3,
                                description="Optional ISO3 filter: return only pathways this country belongs to")


@mcp.tool(name="qesis_get_country", annotations={
    "title": "Get country substrate profile", "readOnlyHint": True,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def qesis_get_country(params: CountryInput) -> str:
    """Full substrate sovereignty profile for one country: seven axis scores
    (0-100 stress), composite exposure, BIG coverage flags, fidelity to the
    planetary-safe reference state where computed, and pathway memberships.

    Returns JSON. Axis legend: WSE water, CSE submarine cable, REE rare
    earths, FPE foreign platform share, ODI hyperscaler operator
    concentration, RGD normalised cloud region count, ESE electricity
    stress. RGD is algebraically coupled to ODI: see rgd_method.warning
    before reporting any ODI-RGD relationship as empirical."""
    _refresh()
    c = _country_or_error(params.iso3)
    iso = params.iso3.upper()
    paths = [p["id"] for p in DATA["fsqca"]["pathways"] if iso in p["members"]]
    out = {
        "iso3": iso, "name": c["name"], "vintage": DATA["vintage"],
        "axes": {k: _score(v) for k, v in c["axes"].items()},
        "composite_exposure": _score(c["composite"]),
        "composite_status": c.get("composite_status"),
        "coverage": c.get("coverage"),
        "big_flags": c["big_flags"] or "none, full coverage",
        "fidelity": DATA["fidelity"]["scores"].get(iso),
        "pathway_memberships": paths or "none at >0.5 membership",
        # Operator concentration at full resolution alongside the ordinal axis
        # the composite still consumes. Both are published; neither is hidden.
        "odi_continuous": c.get("odi_continuous"),
        "fsqca_conditions": c.get("fsqca_conditions"),
    }
    if c.get("composite") is None:
        finding = next((e for e in DATA.get("epis_findings", [])
                        if e["iso3"] == iso), None)
        out["epis_finding"] = finding["finding"] if finding else (
            "Composite withheld under the BIG coverage gate.")
        # C-02. The coverage arithmetic says the composite is withheld; the cause
        # says why the coverage is missing. A caller who meets the gap here should
        # not have to open the methodology to learn that Singapore and Taiwan are
        # absent for entirely different reasons.
        if finding and finding.get("withholding_cause"):
            out["withholding_cause"] = finding["withholding_cause"]
            out["cause_statement"] = finding["cause_statement"]
    return json.dumps(out, indent=1) + _tier_note()


@mcp.tool(name="qesis_rank_countries", annotations={
    "title": "Rank countries by exposure", "readOnlyHint": True,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def qesis_rank_countries(params: RankInput) -> str:
    """Rank the 35-state sample by composite exposure or by any single axis.
    Demo tier returns at most 10 rows. Countries with a BIG coverage flag on
    the requested axis are listed separately rather than silently dropped."""
    _refresh()
    axis = params.axis.upper() if params.axis.lower() != "composite" else "composite"
    if axis != "composite" and axis not in AXES:
        raise ValueError(f"axis must be 'composite' or one of {AXES}")
    rows, flagged = [], []
    for iso, c in DATA["countries"].items():
        v = c["composite"] if axis == "composite" else c["axes"][axis]
        if v is None:
            flagged.append(iso)
        else:
            rows.append((iso, c["name"], v))
    rows.sort(key=lambda r: r[2], reverse=not params.ascending)
    limit = params.top_n if LICENSED else min(params.top_n, 10)
    body = [{"rank": i + 1, "iso3": r[0], "name": r[1], axis: _score(r[2])}
            for i, r in enumerate(rows[:limit])]
    out = {"ranked_by": AXIS_NAMES.get(axis, "composite exposure"),
           "ranked_n": len(rows), "sample_n": len(DATA["countries"]),
           "results": body}
    if flagged:
        # An unranked state is a published finding, never a silent omission and
        # never a zero pushed to the bottom of the table.
        findings = {e["iso3"]: e["finding"] for e in DATA.get("epis_findings", [])}
        out["big_epistemic_gaps"] = [
            {"iso3": i, "name": DATA["countries"][i]["name"],
             "coverage": DATA["countries"][i].get("coverage"),
             "finding": findings.get(i, "Value withheld under the BIG coverage gate.")}
            for i in flagged]
    return json.dumps(out, indent=1) + _tier_note()


@mcp.tool(name="qesis_compare_countries", annotations={
    "title": "Compare two countries", "readOnlyHint": True,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def qesis_compare_countries(params: CompareInput) -> str:
    """Side-by-side substrate comparison of two countries with per-axis
    deltas and the binding constraint (highest-stress axis) of each."""
    _refresh()
    a, b = _country_or_error(params.iso3_a), _country_or_error(params.iso3_b)
    ia, ib = params.iso3_a.upper(), params.iso3_b.upper()
    table, deltas = {}, {}
    for ax in AXES:
        va, vb = a["axes"][ax], b["axes"][ax]
        table[ax] = {ia: _score(va), ib: _score(vb)}
        if va is not None and vb is not None:
            deltas[ax] = _score(round(va - vb, 1))
    bind = lambda c: max((ax for ax in AXES if c["axes"][ax] is not None),
                         key=lambda ax: c["axes"][ax])
    out = {
        "comparison": table, "delta_a_minus_b": deltas,
        "composite": {ia: _score(a["composite"]), ib: _score(b["composite"])},
        "binding_constraint": {ia: bind(a), ib: bind(b)},
    }
    return json.dumps(out, indent=1) + _tier_note()


@mcp.tool(name="qesis_get_coupling", annotations={
    "title": "Two-tier substrate coupling", "readOnlyHint": True,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def qesis_get_coupling() -> str:
    """The headline finding: substrate entanglement is geopolitical, not
    universal. Returns the two-tier von Neumann coupling ratios (global
    n=32 vs import-dependent core n=26), key cross-axis correlations, and
    the interpretation."""
    _refresh()
    return json.dumps(DATA["coupling"], indent=1) + _tier_note()


@mcp.tool(name="qesis_get_pathways", annotations={
    "title": "fsQCA pathways to sovereignty loss", "readOnlyHint": True,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def qesis_get_pathways(params: PathwayInput) -> str:
    """Configurational (fsQCA) pathways to high sovereignty vulnerability:
    declared model, necessity results, solution statistics, outcome
    calibration anchors with the anti-circularity test, and the five
    pathway terms with consistency/coverage and member states. Optionally
    filtered to one country's memberships."""
    _refresh()
    fs = dict(DATA["fsqca"])
    if params.iso3:
        iso = params.iso3.upper()
        _country_or_error(iso)
        fs = {**fs, "pathways": [p for p in fs["pathways"] if iso in p["members"]],
              "filtered_for": iso}
    return json.dumps(fs, indent=1) + _tier_note()


@mcp.tool(name="qesis_get_component_audit", annotations={
    "title": "ESE component audit trail", "readOnlyHint": True,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def qesis_get_component_audit(params: CountryInput) -> str:
    """[Institutional tier] The full audit trail behind a country's scores:
    ESE components (carbon intensity from Ember, industrial electricity price
    from IEA/Eurostat, SAIDI grid reliability from World Bank), the CSE
    component split, REE base and stress vintages, the ODI construction with
    its operator shares, and the composite recomputed from the published axes
    so the headline number can be checked line by line."""
    _refresh()
    if not LICENSED:
        return ("LOCKED. Component-level audit requires the institutional "
                "license (QESIS_LICENSE_KEY). The demo tier exposes scores and "
                "methodology; the audit trail is the paid layer. Contact: "
                "see repository README.")
    c = _country_or_error(params.iso3)
    iso = params.iso3.upper()
    model = DATA.get("composite_model") or {}
    W = model.get("weights") or {}
    # Recompute in front of the caller rather than restating the stored value.
    terms, recomputed = {}, None
    if all(c["axes"].get(a) is not None for a in W):
        terms = {a: round(W[a] * c["axes"][a], 3) for a in W}
        recomputed = round(sum(terms.values()), 1)
    return json.dumps({
        "iso3": iso, "name": c["name"], "vintage": DATA["vintage"],
        "composite": {
            "served": c["composite"], "recomputed_from_axes": recomputed,
            "reproduces": (recomputed == c["composite"]),
            "weighted_terms": terms, "weights": W,
            "coverage": c.get("coverage"), "status": c.get("composite_status"),
        },
        "ese": {"score": c["axes"]["ESE"], "components": c["ese_components"],
                "method": DATA["ese_method"]},
        "axis_provenance": c.get("audit"),
        "odi_continuous": c.get("odi_continuous"),
        "odi_method": DATA.get("odi_method"),
        "fsqca_conditions": c.get("fsqca_conditions"),
        "csove": c.get("csove"),
        "lineage": DATA.get("lineage"),
    }, indent=1)


@mcp.tool(name="qesis_get_integrity", annotations={
    "title": "Index integrity and lineage", "readOnlyHint": True,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def qesis_get_integrity() -> str:
    """Which generation of the index is being served, how the composite is
    derived, every state whose composite is withheld under BIG and why, the
    verified state of the EU AI Act Art. 12 hash chain, and the concordance
    between published thesis figures and the numbers served here. Query this
    before citing any number: it answers 'is what I am reading reproducible'
    without requiring access to the build machine."""
    _refresh()
    C = DATA["countries"]
    W = (DATA.get("composite_model") or {}).get("weights") or {}
    drift = []
    for iso, c in C.items():
        if c["composite"] is None or any(c["axes"].get(a) is None for a in W):
            continue
        calc = round(sum(W[a] * c["axes"][a] for a in W), 1)
        if abs(calc - c["composite"]) > 0.051:
            drift.append({"iso3": iso, "served": c["composite"], "recomputed": calc})
    out = {
        "vintage": DATA["vintage"], "supersedes": DATA.get("supersedes"),
        # G-01b. The vintage names a generation; this identifies the bytes.
        "provenance": _provenance(),
        "composite_model": DATA.get("composite_model"),
        "lineage": DATA.get("lineage"),
        "self_check": {
            "states": len(C),
            "ranked": sum(1 for c in C.values() if c["composite"] is not None),
            "withheld_epis": sum(1 for c in C.values() if c["composite"] is None),
            "composites_reproducing_from_axes": drift == [],
            "drift": drift or "none",
        },
        # C-01. Read from an independent verifier's output, never written by the
        # process that appends to the chain. The spine it was computed from is
        # committed, so a reader can recompute every link rather than trust this.
        "chain": _chain(),
        "epis_findings": DATA.get("epis_findings"),
        # C-02. Two distinct causes sit behind three withholdings, and the codes
        # are published beside the findings so the difference is legible.
        "withholding_causes": DATA.get("withholding_causes"),
        "uncertainty_ledger": DATA.get("uncertainty_ledger"),
        # C-04. Served before anyone concludes a thesis figure and this index
        # disagree because one of them is wrong.
        "citation_concordance": DATA.get("citation_concordance"),
        "coupling_exclusions": {
            "excluded_from_global": DATA["coupling"].get("excluded_from_global"),
            "excluded_from_core": DATA["coupling"].get("excluded_from_core"),
            "rule": DATA["coupling"].get("exclusion_rule"),
        },
    }
    # Reported last, over the response that was actually built, so it describes
    # what this process serves rather than what the source says it should.
    out["contract"] = _contract("qesis_get_integrity", out)
    return json.dumps(out, indent=1) + _tier_note()


@mcp.tool(name="qesis_get_methodology", annotations={
    "title": "Methodology and provenance", "readOnlyHint": True,
    "destructiveHint": False, "idempotentHint": True, "openWorldHint": False})
async def qesis_get_methodology() -> str:
    """Framework documentation: the seven axes, the Binary Integrity Guard
    (BIG) coverage discipline, fidelity construction, ESE composite method,
    data sources, and citation. Use this before interpreting any score."""
    _refresh()
    return json.dumps({
        "framework": "QESIS+ (Quantitative Epistemic Sovereignty Index Stack), STIR composite",
        "axes": AXIS_NAMES,
        "big_protocol": ("Coverage >= 0.75 required to rank (DORM); below it the gap is "
                         "published as a finding (EPIS), never imputed; INFR marks "
                         "inferred vulnerability under data opacity. From v8.1 the gate "
                         "also binds the composite: a state missing a weighted axis "
                         "returns no composite rather than a number resting on a zero."),
        "composite_model": DATA.get("composite_model"),
        "fidelity": DATA["fidelity"],
        "ese_method": DATA["ese_method"],
        "odi_method": DATA.get("odi_method"),
        "vintage": DATA["vintage"],
        "citation": {
            "work": "Batista Silva, R. (2026). Liquid Sovereignty. ESIC/LSE.",
            "dataset": f"Sovereign_Infra_Intelligence {DATA['vintage']}.",
            "supersedes": ("Metadata through v8.0 carried an earlier working title, "
                           "'Ontological Blind-Spots'. That citation is withdrawn."),
            "subtitle_status": ("Short form served here. The full subtitle is set by "
                                "the deposited thesis record and is not asserted from "
                                "this dataset; confirm against the deposit before "
                                "quoting it in a publication."),
        },
        "license": DATA["license"],
    }, indent=1)


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
