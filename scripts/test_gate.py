"""Mutation test for the integrity gate.

A gate is only worth its exit code if it fails when it should. This injects one
defect at a time into a copy of the served index and asserts the gate catches
it. The Singapore case is the v8.0 defect itself, replayed.

Usage:  python scripts/test_gate.py
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import pathlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts" / "verify_index.py"
BASE = json.loads((ROOT / "data" / "qesis_v8.json").read_text(encoding="utf-8"))


def run_gate(doc) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False)
        p = fh.name
    try:
        r = subprocess.run([sys.executable, str(GATE), "--json", p, "--quiet"],
                           capture_output=True, text=True)
        return r.returncode, (r.stdout + r.stderr)
    finally:
        Path(p).unlink(missing_ok=True)


# ── mutations: (name, mutator, expected substring in failure output) ────────
def m_drift(d):
    """A composite silently disagrees with its own axes."""
    d["countries"]["DEU"]["composite"] = 99.9
    return d


def m_singapore(d):
    """The v8.0 defect: emit a number over a BIG-flagged axis."""
    sgp = d["countries"]["SGP"]
    sgp["composite"] = 1.7
    sgp["composite_status"] = "DORM"
    d["epis_findings"] = [e for e in d["epis_findings"] if e["iso3"] != "SGP"]
    return d


def m_inversion(d):
    """Dominance inverted without breaking arithmetic elsewhere."""
    # Axes come from the declared model, never a hardcoded list: v8.3 renamed
    # CRD to RGD and a literal list silently crashed this case instead of
    # exercising it. A self-test that cannot run proves less than no self-test.
    W = d["composite_model"]["weights"]
    for a in W:
        d["countries"]["GBR"]["axes"][a] = max(
            d["countries"]["GBR"]["axes"][a], d["countries"]["CHE"]["axes"][a])
    d["countries"]["GBR"]["composite"] = round(
        sum(W[a] * d["countries"]["GBR"]["axes"][a] for a in W), 1)
    d["countries"]["CHE"]["composite"] = d["countries"]["GBR"]["composite"] + 5.0
    return d


def m_weights(d):
    """Weights quietly stop summing to 1."""
    d["composite_model"]["weights"]["WSE"] = 0.40
    return d


def m_lineage(d):
    """Served rows can no longer be traced to a generation."""
    d["lineage"].pop("sources", None)
    return d


def m_silent_exclusion(d):
    """Coupling drops states without naming them."""
    d["coupling"].pop("excluded_from_global", None)
    return d


def m_citation(d):
    """A superseded citation returns to a public surface."""
    d["fidelity"]["citation"] = "Ontological Blind-Spots: Hybrid War..."
    return d


def m_generic_withholding(d):
    """The v8.3 defect: three withholdings, one label, two real causes.

    Reverting to the generic string is the exact regression C-02 exists to
    prevent, and it is invisible in every other check because the arithmetic
    it reports is correct.
    """
    for e in d["epis_findings"]:
        e.pop("withholding_cause", None)
        e.pop("cause_statement", None)
    return d


def m_undeclared_cause(d):
    """A cause code appears that the codebook never declared."""
    d["epis_findings"][0]["withholding_cause"] = "GEOPOLITICAL"
    return d


def m_dangling_erratum(d):
    """A concordance row points at an erratum that does not exist."""
    d["citation_concordance"]["rows"][0]["erratum"] = "D-999"
    return d


def m_silent_concordance_row(d):
    """A row is present but says nothing about the figure's standing."""
    d["citation_concordance"]["rows"][0]["status"] = ""
    return d


def m_undated_roadmap(d):
    """A scoped roadmap item loses its date and becomes an open promise again."""
    for u in d["uncertainty_ledger"]["entries"]:
        if u.get("target_vintage"):
            u.pop("target_date", None)
    return d


def m_conc1_replay(d):
    """CONC-1 replayed: the re-run is complete and the row still says pending.

    This is the v8.6 defect itself, not an invented one. It is the fixture
    R1.23 must refuse. (L-074.)
    """
    for r in d["citation_concordance"]["rows"]:
        if r.get("erratum") == "D-103":
            r["status"] = "withdrawn pending re-run"
    return d


def m_conc1_erratum_replay(d):
    """The same contradiction carried by the erratum block instead of the row."""
    for e in d["citation_concordance"]["errata"]:
        if e.get("id") == "D-103":
            e["status"] = "OPEN, blocks the Phase 1 gate"
    return d


def m_unbound_erratum(d):
    """An erratum is neither bound nor excused, so the gate cannot see it."""
    cc = d["citation_concordance"]
    cc["unbound_errata"] = [u for u in cc.get("unbound_errata", [])
                            if u.get("erratum") != "D-105"]
    return d


def m_excuse_without_reason(d):
    """An erratum is 'declared' unbound with an empty reason, which says nothing."""
    for u in d["citation_concordance"].get("unbound_errata", []):
        if u.get("erratum") == "D-104":
            u["reason"] = "   "
    return d


def m_conc2_replay(d):
    """CONC-2 replayed: a NECESSARY label the declared rule does not produce.

    WSE returns consistency_N 0.7896, below the 0.90 bar, so under D-109 its
    label is LABEL-DECLINED. Asserting NECESSARY beside the measures is the
    v8.7 defect itself. R1.24 recomputes rather than reads.
    """
    d["fsqca"]["necessity_gate"]["WSE"]["verdict"] = "NECESSARY"
    return d


def m_necessity_threshold_dropped(d):
    """A condition stops declaring the consistency bar, so the rule cannot apply."""
    d["fsqca"]["necessity_gate"]["WSE"]["thresholds"].pop(
        "consistency_N_publishable", None)
    return d


def m_prose_contradicts_labels(d):
    """The quotable sentence disagrees with the labels beside it."""
    g = d["fsqca"]["necessity_gate"]["CABLE"]
    g["thresholds"]["consistency_N_publishable"] = 0.10   # make CABLE clear the bar
    g["verdict"] = "NECESSARY"
    return d                                              # verdict still says none is


def m_flag_without_statement(d):
    """A governance flag arrives as a bare value, so the reader learns nothing."""
    d["agent_reading_contract"]["flags"]["theory_informed_limitation"]["statement"] = ""
    return d


def m_flag_dropped(d):
    """The trilemma demotion is quietly removed while the block stays populated."""
    d["agent_reading_contract"]["flags"].pop("trilemma_status", None)
    return d


def m_flag_outside_vocabulary(d):
    """A flag takes a value its own declared vocabulary does not allow."""
    d["agent_reading_contract"]["flags"]["trilemma_status"]["value"] = "structural"
    return d


CASES = [
    ("composite drift (DEU)",        m_drift,               "R1.4"),
    ("Singapore: number over gap",   m_singapore,           "R1.5"),
    ("dominance inversion",          m_inversion,           "R1.7"),
    ("weights stop summing to 1",    m_weights,             "R1.3"),
    ("lineage sources removed",      m_lineage,             "R1.8"),
    ("unnamed coupling exclusions",  m_silent_exclusion,    "R1.12"),
    ("superseded citation returns",  m_citation,            "R1.16"),
    ("withholding loses its cause",  m_generic_withholding, "R1.17"),
    ("undeclared cause code",        m_undeclared_cause,    "R1.17"),
    ("concordance row dangles",      m_dangling_erratum,    "R1.19"),
    ("concordance row says nothing", m_silent_concordance_row, "R1.20"),
    ("roadmap item loses its date",  m_undated_roadmap,     "R1.21"),
    ("erratum neither bound nor excused", m_unbound_erratum, "R1.22"),
    ("unbound excuse carries no reason",  m_excuse_without_reason, "R1.22"),
    ("CONC-1: row pending, re-run done", m_conc1_replay,    "R1.23"),
    ("CONC-1: erratum OPEN, re-run done", m_conc1_erratum_replay, "R1.23"),
    ("CONC-2: label the rule denies",  m_conc2_replay,        "R1.24"),
    ("necessity threshold undeclared", m_necessity_threshold_dropped, "R1.24"),
    ("prose contradicts the labels",   m_prose_contradicts_labels, "R1.25"),
    ("flag without its statement",     m_flag_without_statement, "R1.26"),
    ("limitation flag dropped",        m_flag_dropped,        "R1.26"),
    ("flag outside its vocabulary",    m_flag_outside_vocabulary, "R1.26"),
]


CHAIN_GATE = ROOT / "scripts" / "verify_chain.py"
SPINE = ROOT / "data" / "chain_spine.jsonl"
ATTESTATION = ROOT / "data" / "chain_attestation.json"


def run_chain_gate(rows, att) -> tuple[int, str]:
    d = Path(tempfile.mkdtemp())
    (d / "s.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n", encoding="utf-8")
    (d / "a.json").write_text(json.dumps(att), encoding="utf-8")
    r = subprocess.run([sys.executable, str(CHAIN_GATE), "--spine", str(d / "s.jsonl"),
                        "--attestation", str(d / "a.json"), "--quiet"],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def check_chain(results: list[tuple[str, bool]]) -> None:
    """The chain figure must be contradictable, or C-01 changed nothing.

    Before C-01 the served `604 entries, 0 link breaks` came from the runtime
    that appends to the chain. Moving it to an attestation only helps if the
    attestation can be caught disagreeing with the spine it claims to summarise.
    """
    if not (SPINE.exists() and ATTESTATION.exists()):
        results.append(("chain artefacts present", False))
        return
    spine = [json.loads(l) for l in SPINE.read_text(encoding="utf-8").splitlines() if l.strip()]
    att = json.loads(ATTESTATION.read_text(encoding="utf-8"))

    rc, _ = run_chain_gate(spine, att)
    results.append(("chain baseline reproduces", rc == 0))

    mid = len(spine) // 2
    tampered = [dict(r) for r in spine]
    tampered[mid]["entry_hash"] = "0" * 64
    removed = [dict(r) for r in spine[:mid] + spine[mid + 1:]]
    for name, rows, a, expect in [
        ("chain: entry count edited", spine, {**att, "entries": 999}, "C3"),
        ("chain: head rewritten", spine, {**att, "head_sha256": "f" * 64}, "C3"),
        ("chain: a link tampered", tampered, att, "C2"),
        ("chain: an entry removed", removed, att, "C1"),
    ]:
        rc, out = run_chain_gate(rows, a)
        results.append((f"caught: {name}", rc != 0 and expect in out))


PAIRING_GATE = ROOT / "scripts" / "verify_vintage_pairing.py"
REGISTER = ROOT / "data" / "vintage_lineage.json"


def check_pairing(results: list[tuple[str, bool]]) -> None:
    """G-01 is a rule about two repositories, so its check must refuse silence.

    The interesting failure is not a missing register. It is a register that
    carries a row for the served vintage and says nothing in it, which reads as
    compliance while recording none.
    """
    if not REGISTER.exists():
        results.append(("vintage register present", False))
        return
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    served = BASE["vintage"]

    def run(r) -> tuple[int, str]:
        d = Path(tempfile.mkdtemp())
        (d / "r.json").write_text(json.dumps(r), encoding="utf-8")
        p = subprocess.run([sys.executable, str(PAIRING_GATE), "--register",
                            str(d / "r.json"), "--quiet"], capture_output=True, text=True)
        return p.returncode, (p.stdout + p.stderr)

    rc, _ = run(reg)
    results.append(("pairing baseline passes", rc == 0))

    dropped = {**reg, "entries": [e for e in reg["entries"] if e["vintage"] != served]}
    unpaired, silent, duped = (json.loads(json.dumps(reg)) for _ in range(3))
    for r, mut in ((unpaired, "pair"), (silent, "summary"), (duped, "dupe")):
        row = next(e for e in r["entries"] if e["vintage"] == served)
        if mut == "pair":
            row["sovereign_infra_commit"] = None
            row["single_repo_reason"] = None
        elif mut == "summary":
            row["summary"] = ""
        else:
            r["entries"].append(dict(row))

    # `pending` expires when the vintage stops being the served one. Without
    # this case the placeholder satisfies the pairing check forever, which is
    # how a temporary hole becomes the permanent state of a register.
    stale = json.loads(json.dumps(reg))
    stale["entries"].append({
        "vintage": "v8.9 (2099-01-01)", "qesis_mcp_commit": "pending",
        "sovereign_infra_commit": "pending", "single_repo_reason": None,
        "summary": "a later vintage, so the served one is not this row"})
    # R1.28, added 2026-08-14 (L-117). The register TAIL announces a vintage the
    # index does not serve. This survived a merge and a promotion with every other
    # gate green, because the pairing gate read the register and never compared its
    # tail to the served vintage. A vintage is defined by its payload, not by
    # scaffolding beside it. The ACCEPT fixture is the unmodified register, which
    # "pairing baseline passes" above already exercises.
    phantom_tail = json.loads(json.dumps(reg))
    phantom_tail["entries"].append({
        "vintage": "v99.9 (2099-01-01)", "qesis_mcp_commit": None,
        "sovereign_infra_commit": None, "single_repo_reason": "fixture",
        "summary": "phantom tail, the index never served this"})

    old_pending = json.loads(json.dumps(reg))
    for e in old_pending["entries"]:
        if e["vintage"] != served:
            e["qesis_mcp_commit"] = "pending"
            e["sovereign_infra_commit"] = "pending"
            break

    for name, r, expect in [
        ("pairing: vintage unrecorded", dropped, "G1.1"),
        ("pairing: one repo, no reason", unpaired, "G1.2"),
        ("pairing: row says nothing", silent, "G1.3"),
        ("pairing: duplicate rows", duped, "G1.4"),
        ("pairing: pending outlives its vintage", old_pending, "G1.2"),
        ("pairing: register tail is a phantom vintage", phantom_tail, "register tail is"),
    ]:
        rc, out = run(r)
        results.append((f"caught: {name}", rc != 0 and expect in out))


CONTRACT_GATE = ROOT / "scripts" / "verify_served_contract.py"
INDEX = ROOT / "data" / "qesis_v8.json"


def check_contract(results: list[tuple[str, bool]]) -> None:
    """Replay the v8.4 incident: data announcing a vintage the code half-serves.

    The index reloads on file change and the module does not, so a resident
    process can advance its vintage string while running older code. That is
    not hypothetical; it is what happened, on a public endpoint, and nothing
    failed. This is the check that makes it fail.
    """
    # Bytes, not text, and this is not a detail. read_text applies universal
    # newlines, so a file written with CRLF came back as LF and the restore
    # below wrote LF over it. Running this suite therefore rewrote the published
    # artefact: on 2026-08-07 it silently moved the v8.5 index from d423c9e9 to
    # f2a29747 after the label had already been bound, breaking N1 by way of the
    # test that exists to protect it. A check that mutates the artefact it is
    # checking must restore it byte for byte or it is a defect wearing a gate.
    original = INDEX.read_bytes()

    def run() -> tuple[int, str]:
        r = subprocess.run([sys.executable, str(CONTRACT_GATE), "--quiet"],
                           capture_output=True, text=True, cwd=str(ROOT))
        return r.returncode, (r.stdout + r.stderr)

    try:
        rc, out = run()
        if rc == 2:
            # Exit 2 is "could not check", and it must never be mistaken for a
            # caught defect. CI proved that the hard way: the runtime was
            # installed after this suite ran, server.py would not import, and
            # the removed-declaration case passed anyway because an unimportable
            # runtime and a removed declaration both exit 2. Two of three cases
            # failed loudly and the third passed for the wrong reason, which is
            # the more dangerous half. Refuse to run the mutations at all rather
            # than report results that mean nothing.
            results.append((f"contract: NOT CHECKED, verifier cannot run "
                            f"({out.strip().splitlines()[-1][:70] if out.strip() else 'no output'})",
                            False))
            return
        results.append(("contract baseline: every declared field served", rc == 0))

        d = json.loads(original)
        d["served_contract"]["tools"]["qesis_get_integrity"].append("field_no_code_builds")
        INDEX.write_bytes((json.dumps(d, indent=1, ensure_ascii=False) + "\n")
                          .encode("utf-8"))
        rc, out = run()
        results.append(("caught: contract: data ahead of code", rc == 1 and "K3" in out))

        d = json.loads(original)
        d.pop("served_contract", None)
        INDEX.write_bytes((json.dumps(d, indent=1, ensure_ascii=False) + "\n")
                          .encode("utf-8"))
        rc, out = run()
        # A vintage that promises nothing must not read as a vintage that keeps
        # every promise. Exit 2, and it must be 2 for the declared reason rather
        # than because the verifier fell over on the way in.
        results.append(("caught: contract: declaration removed",
                        rc == 2 and "declares no served_contract" in out))
    finally:
        INDEX.write_bytes(original)
        # Assert the restore, rather than trust it. This is the line that would
        # have caught the lossy restore the moment it was introduced.
        results.append((
            "contract: the published index is restored byte for byte",
            INDEX.read_bytes() == original))


ENDPOINT_GATE = ROOT / "scripts" / "verify_endpoints.py"


def check_endpoints(results: list[tuple[str, bool]]) -> None:
    """V-2 for verify_endpoints.py: one fixture it must accept, three it must refuse.

    Built in a temporary tree rather than by mutating the repository, because
    the interesting refusal is an undeclared literal and writing one into the
    working tree to prove a point is how a fixture becomes a defect.

    The case that matters most is the second: a literal that AGREES with the
    declaration today. A gate that only refuses disagreement certifies the state
    of one afternoon. The horizon endpoint's three copies all agreed with each
    other on the day they were written, and the copy that carried the operator
    instruction was still the one no consumer read.
    """
    if not ENDPOINT_GATE.exists():
        results.append(("endpoint gate present", False))
        return

    # The fixture values are READ from the declaration, never retyped here.
    # Two reasons. The gate refuses endpoint literals in *.py and this file is
    # *.py, so a retyped fixture makes the self-test fail the gate it is testing.
    # The better reason is L-014's shape: a fixture holding its own copy of the
    # value under test stops exercising the real case the moment the declaration
    # moves, and goes on passing while it does.
    decl = json.loads((ROOT / "data" / "endpoints.json").read_text(
        encoding="utf-8"))
    declared_url = decl["endpoints"]["horizon"]["default"]
    # An address that is well formed and NOT declared. Derived so it stays
    # undeclared however the declaration changes.
    undeclared_url = declared_url.replace("://", "://x-", 1) + "-undeclared"

    def run(consumer: str | None, declaration: dict | None) -> tuple[int, str]:
        d = Path(tempfile.mkdtemp())
        (d / "data").mkdir()
        if declaration is not None:
            (d / "data" / "endpoints.json").write_text(
                json.dumps(declaration), encoding="utf-8")
        if consumer is not None:
            (d / "consumer.py").write_text(consumer, encoding="utf-8")
        p = subprocess.run([sys.executable, str(ENDPOINT_GATE), "--root", str(d),
                            "--quiet"], capture_output=True, text=True)
        return p.returncode, (p.stdout + p.stderr)

    clean = "from qesis_endpoints import resolve\nurl = resolve('horizon').url\n"
    rc, out = run(clean, decl)
    results.append(("endpoints: resolved consumer passes", rc == 0))

    for name, consumer, declaration, expect in [
        ("endpoints: declared value retyped at call site",
         f'ep = "{declared_url}"\n', decl, "E1.1"),
        ("endpoints: undeclared endpoint dialled",
         f'ep = "{undeclared_url}"\n', decl, "E1.2"),
        ("endpoints: declaration absent", clean, None, "E1.0"),
    ]:
        rc, out = run(consumer, declaration)
        results.append((f"caught: {name}", rc != 0 and expect in out))


GRAPH_BUILDER = ROOT / "scripts" / "build_graph.py"


def run_graph_validate(mutate=None) -> tuple[bool, list[str]]:
    """Drive build_graph.validate() directly, optionally on a mutated graph.

    Imported rather than shelled out because validate() is the assertion under
    test and running the CLI would test the CLI. The import is guarded: a public
    checkout without the builder skips rather than fails, the same posture
    check_idempotent takes for build_index.py.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("_bg", GRAPH_BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    g = mod.build()
    if mutate is not None:
        g = mutate(g)
    fails = mod.validate(g)
    return (not fails), fails


def g_retype_provenance_as_physical(g):
    """KG-5 refuse fixture. Retype a provenance edge onto the physical plane.

    This is the D-110 revision A defect replayed: CSE_VALUE_SOURCED_FROM said
    "one dataset supplied this value" and was read as "one cable route". A
    provenance edge wearing a physical edge's clothes. The graph must refuse it.
    """
    for e in g["edges"]:
        if e["type"] == "CSE_VALUE_SOURCED_FROM":
            e["type"] = "CHOKEPOINT_IN"
            return g
    raise AssertionError("fixture is vacuous: no CSE_VALUE_SOURCED_FROM edge "
                         "exists to retype, so this case proves nothing")


def g_physical_edge_onto_provenance_kind(g):
    """KG-5 refuse fixture. A physical edge whose endpoint resolves to a
    provenance kind, with domain and range left consistent.

    This is the case domain and range cannot catch. Retype a CableSourceDataset
    node as a LandingCity and CHOKEPOINT_IN still satisfies its declaration:
    source is a LandingCity, target is a CableNetwork, every field agrees. The
    graph now asserts that a dataset is a place where cables land. Only the plane
    rule refuses it, and it refuses on the RESOLVED endpoint rather than on the
    declaration, which is why the check is worth having.
    """
    ds = next((n for n in g["nodes"] if n["kind"] == "CableSourceDataset"), None)
    net = next((n for n in g["nodes"] if n["kind"] == "CableNetwork"), None)
    if ds is None or net is None:
        raise AssertionError("fixture is vacuous: needs a CableSourceDataset and "
                             "a CableNetwork node to construct the defect")
    # The node keeps its true kind. The edge claims it is a landing city.
    g["edges"].append({"type": "CHOKEPOINT_IN", "source": ds["id"], "target": net["id"]})
    return g


def g_undeclared_edge_type(g):
    """An edge type absent from EDGE_SCHEMA. The table IS the ontology, so an
    edge outside it is an undeclared commitment, not a warning."""
    g["edges"].append({"type": "DEPENDS_ON",
                       "source": g["nodes"][0]["id"],
                       "target": g["nodes"][1]["id"]})
    return g


def g_range_violation(g):
    """Domain holds, range does not. Catches the half of the declaration a
    source-only check would miss."""
    for e in g["edges"]:
        if e["type"] == "SOLE_PROVIDER":
            axis = next((n["id"] for n in g["nodes"] if n["kind"] == "Axis"), None)
            if axis is None:
                raise AssertionError("fixture is vacuous: no Axis node to point at")
            e["target"] = axis
            return g
    raise AssertionError("fixture is vacuous: no SOLE_PROVIDER edge exists")


def check_graph(results: list[tuple[str, bool]]) -> None:
    """KG-1. The fixtures build_graph.py's docstring has been naming since it
    was written, and which did not exist until now.

    `validate()` said "Fixtures live in scripts/test_gate.py; this is the
    assertion they exercise." A grep for "graph" in this file returned zero. A
    gate whose docstring names fixtures that do not exist is the same failure
    shape as a threshold living in prose (L-054), committed in the file whose
    entire argument is that typed edges make commitments explicit.

    One fixture the gate must accept, three it must refuse.
    """
    if not GRAPH_BUILDER.exists():
        results.append(("graph: builder present", False))
        return
    try:
        ok, fails = run_graph_validate()
    except Exception as exc:                      # noqa: BLE001
        results.append((f"graph: baseline build ({type(exc).__name__})", False))
        return
    results.append(("graph: baseline validates (accept fixture)", ok))
    if not ok:
        print(f"      baseline violations: {fails[:3]}")

    for name, mut, expect in [
        ("graph: provenance edge retyped as physical",
         g_retype_provenance_as_physical, "CHOKEPOINT_IN"),
        ("graph: undeclared edge type", g_undeclared_edge_type, "undeclared"),
        ("graph: range violation on SOLE_PROVIDER", g_range_violation, "range"),
        ("graph: physical edge resolves to a provenance kind",
         g_physical_edge_onto_provenance_kind, "provenance kind"),
    ]:
        try:
            ok, fails = run_graph_validate(mut)
        except AssertionError as exc:
            # A vacuous fixture is a failure of the fixture, not of the gate,
            # and it must be loud. A refuse case that cannot construct the
            # defect it names silently proves nothing (L-049).
            print(f"      VACUOUS FIXTURE: {exc}")
            results.append((f"caught: {name}", False))
            continue
        caught = (not ok) and any(expect in f for f in fails)
        results.append((f"caught: {name}", caught))


SECRETS_GATE = ROOT / "scripts" / "verify_no_plaintext_secrets.py"


def run_secrets_gate(root) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SECRETS_GATE), "--root", str(root)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)


def check_secrets(results: list[tuple[str, bool]]) -> None:
    """D-2. Two fixtures it must refuse, two it must accept.

    The accept cases are not padding. This gate's first working run produced two
    false positives out of three findings, `NON_SOURCE_KEYS` and
    `CREDENTIAL_FILES`, both collections whose names contain a secret word. A
    secrets gate that cries wolf is switched off by the third week (L-063), so
    the accept fixtures pin the discrimination rather than trusting it.

    The `os.getenv` case is the sharper one. The first repair excluded any value
    containing a collection separator, which silenced a real PG_PASSWORD line and
    would have silenced a getenv default carrying an actual secret. It is here so
    that repair cannot be reintroduced.
    """
    if not SECRETS_GATE.exists():
        results.append(("secrets: gate present", False))
        return
    import tempfile
    ign = ".env\n.env.local\ndatabase_string.txt\n"

    cases = [
        ("secrets: literal API_KEY refused",
         'API_KEY = "sk_live_9f3a2b7c4d1e8a6f"\n', ign, 1),
        ("secrets: .gitignore coverage gap refused", "", "unrelated\n", 1),
        ("secrets: env reference accepted",
         'PG_PASSWORD = os.getenv("PGPASSWORD", "postgres")\n', ign, 0),
        ("secrets: name-shaped collection accepted",
         'NON_SOURCE_KEYS = {"rule", "provenance_note"}\n'
         'CREDENTIAL_FILES = [".env", ".env.local"]\n', ign, 0),
    ]
    for name, content, ignore, want in cases:
        d = pathlib.Path(tempfile.mkdtemp())
        (d / "c.py").write_text(content, encoding="utf-8")
        (d / ".gitignore").write_text(ignore, encoding="utf-8")
        rc, out = run_secrets_gate(d)
        ok = (rc != 0) if want else (rc == 0)
        # A refusal must never print the value it refused (G-03).
        if want and "sk_live_9f3a2b7c4d1e8a6f" in out:
            ok = False
            print("      LEAK: the gate printed the value it was guarding")
        results.append((name, ok))



LEDGER_GATE = ROOT / "scripts" / "verify_ledger_singleton.py"


def check_ledger_singleton(results: list[tuple[str, bool]]) -> None:
    """V-2 for verify_ledger_singleton.py, wired rather than described.

    L-142: the gate shipped with five fixtures, a `--selftest` entry point, and a
    docstring stating that this file calls it. This file did not. Nothing in the
    repository referenced the gate at all, so the property it exists to assert,
    that a duplicate lesson id is a build failure (L-073), was still enforced by
    prose alone in the one place that had just been given code. That is L-054
    committed inside the change set written to close L-054, which is the most
    expensive place available for it.

    The fixtures live in the gate because they are its own accept-and-refuse pair.
    This function asserts that they RUN, and that the gate passes against the real
    ledger. Two different questions: the selftest proves the gate can still catch
    a duplicate, the live run proves the ledger currently holds none.
    """
    if not LEDGER_GATE.exists():
        results.append(("ledger singleton: gate present", False))
        return

    def run(args: list[str]) -> int:
        return subprocess.run([sys.executable, str(LEDGER_GATE), *args],
                              capture_output=True, text=True).returncode

    results.append(("ledger singleton: selftest, its own accept and refuse pair",
                    run(["--selftest"]) == 0))
    # Labelled for what it measures. The old label said "holds no duplicate id"
    # while the exit code also carried R2 and R3, so on 2026-08-24 a one-byte
    # mirror drift was reported as a duplicate-id miss (L-169).
    results.append(("ledger singleton: live ledger passes R1, R2, and R3 where a sibling is reachable",
                    run(["--quiet"]) == 0))


ECOSYSTEM_GATE = ROOT / "scripts" / "build_ecosystem_state.py"
SELFHEAL = ROOT / "scripts" / "selfheal.py"


def check_ecosystem_state(results: list[tuple[str, bool]]) -> None:
    """V-2 for the bootstrap gate, wired at rung 3 of gate_cannot_be_satisfied.

    Three occurrences of the same move: a staleness check compared something
    that legitimately differs between runs or machines (L-158, L-166, L-170).
    The gate's own fixtures accept volatile drift, including the checkout name,
    and refuse a moved canonical path, a dropped hard constraint, an absent or
    unreadable file. This step makes them a release blocker.
    """
    if not ECOSYSTEM_GATE.exists():
        results.append(("ecosystem state: gate present", False))
        return
    r = subprocess.run([sys.executable, str(ECOSYSTEM_GATE), "--selftest"],
                       capture_output=True, text=True)
    results.append(("ecosystem state: selftest, volatile drift accepted, contract drift refused",
                    r.returncode == 0))


def check_selfheal_runner(results: list[tuple[str, bool]]) -> None:
    """V-2 for the runner, wired at rung 2 of paired_what_is_not_pairable (L-171).

    The runner must survive a partial checkout with no kill switch module and
    still honour the stop control's channels, and must refuse a duplicated
    control name.
    """
    if not SELFHEAL.exists():
        results.append(("selfheal: runner present", False))
        return
    r = subprocess.run([sys.executable, str(SELFHEAL), "--selftest"],
                       capture_output=True, text=True)
    results.append(("selfheal: selftest, partial checkout tolerated, duplicate control refused",
                    r.returncode == 0))


RETRIEVAL_GATE = ROOT / "scripts" / "verify_retrieval_corpus.py"
RETRIEVAL_MANIFEST = ROOT / "scripts" / "retrieval_manifest.json"


def check_retrieval_corpus(results: list[tuple[str, bool]]) -> None:
    """SA-006 to SA-008 made executable. Scope decides, and both scopes are pinned.

    The gate's first version refused a restricted file outright, in every context.
    That was wrong: a copyright reservation governs transmission, not private
    reading, and refusing a locally held document forbade the operator from using
    material publishers had deliberately sent him. The fixtures below pin the
    correction so it cannot regress in either direction.

    The pair that matters is the same WEF file appearing twice: ADMITTED to
    private analysis and REFUSED from served retrieval. A gate that only refuses
    is broken in the safe direction, not correct, and a gate that only admits has
    stopped being a gate. Both failures are asserted here rather than trusted.
    """
    if not RETRIEVAL_GATE.exists():
        results.append(("retrieval corpus: gate present", False))
        return
    if not RETRIEVAL_MANIFEST.exists():
        results.append(("retrieval corpus: manifest present", False))
        return

    def run(files, scope, manifest=RETRIEVAL_MANIFEST) -> tuple[int, str]:
        p = subprocess.run(
            [sys.executable, str(RETRIEVAL_GATE), "--manifest", str(manifest),
             "--scope", scope, "--files", *files],
            capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    WEF = "WEF_Energy_Transition_Index_2026_260818_133013.pdf"
    OECD = "vulnerabilities in the semicondutor supply chain_OECD.pdf"
    VENDOR = "ibm-ai-governance-ebook.pdf"

    cases = [
        # The correction, both halves of it.
        ("retrieval: WEF verbatim refused from serving",
         [WEF], "served_verbatim", 1, "SA-006"),
        ("retrieval: WEF admitted to private analysis",
         [WEF], "private_analysis", 0, "ADMIT"),
        # The operator's point, pinned: citing a published figure and
        # publishing a statistic derived from it is accepted academic use.
        ("retrieval: WEF admitted to academic citation",
         [WEF], "academic_citation", 0, "ADMIT"),
        # The operator's pool declaration, SA-008. A newsletter-acquired vendor
        # document with no enumerated entry is his to read and not ours to serve.
        ("retrieval: pool vendor doc admitted to private analysis",
         [VENDOR], "private_analysis", 0, "SA-008 pool"),
        ("retrieval: pool vendor doc refused from served retrieval",
         [VENDOR], "served_verbatim", 1, "defaults to REFUSE"),
        # Open licence passes everywhere. Without this the gate could be a
        # blanket refuser and still look correct.
        ("retrieval: OECD CC BY 4.0 served verbatim",
         [OECD], "served_verbatim", 0, "ADMIT"),
        # Quarantine overrides the pool declaration in both scopes.
        ("retrieval: _RESTRICTED_ quarantine refused even privately",
         ["some_RESTRICTED_file.pdf"], "private_analysis", 1, "quarantine"),
    ]
    for name, files, scope, want_rc, expect in cases:
        rc, out = run(files, scope)
        ok = (rc != 0) if want_rc else (rc == 0)
        if expect not in out:
            ok = False
        results.append((name, ok))

    # Deleting the policy block must break the build, not silence the gate.
    d = pathlib.Path(tempfile.mkdtemp())
    stripped = json.loads(RETRIEVAL_MANIFEST.read_text(encoding="utf-8"))
    stripped.pop("corpus_policy", None)
    m = d / "retrieval_manifest.json"
    m.write_text(json.dumps(stripped), encoding="utf-8")
    rc, out = run([OECD], "served_verbatim", m)
    results.append(("retrieval: manifest without corpus_policy refused",
                    rc != 0 and "declares no corpus_policy" in out))

    # An undefined scope has no default and may not be assumed into one.
    stripped2 = json.loads(RETRIEVAL_MANIFEST.read_text(encoding="utf-8"))
    stripped2["corpus_policy"]["scopes"].pop("served_verbatim", None)
    m2 = d / "no_scope.json"
    m2.write_text(json.dumps(stripped2), encoding="utf-8")
    rc, out = run([OECD], "served_verbatim", m2)
    results.append(("retrieval: undefined scope refused",
                    rc != 0 and "declares no scope" in out))


WF_GATE = ROOT / "scripts" / "verify_workflow_contract.py"


def check_workflow_contract(results: list[tuple[str, bool]]) -> None:
    """Two fixtures for the gate that closes the local-green CI-red class.

    The refuse fixture is the 2026-08-19 failure itself: a workflow that runs
    `git push` under `contents: read`. The accept fixture carries a comment
    inside the permissions block, because the gate's own block reader treated a
    comment as end-of-structure and reported a workflow as lacking a permission
    it plainly granted. Three parser defects in one gate, all the same shape, so
    both halves are pinned rather than one.
    """
    if not WF_GATE.exists():
        results.append(("workflow: gate present", False))
        return
    import tempfile, os

    def run(wf_text: str) -> int:
        d = pathlib.Path(tempfile.mkdtemp())
        (d / ".github" / "workflows").mkdir(parents=True)
        (d / ".github" / "workflows" / "w.yml").write_text(wf_text, encoding="utf-8")
        (d / "scripts").mkdir()
        # The gate resolves ROOT from its own location, so it is copied in.
        (d / "scripts" / "verify_workflow_contract.py").write_text(
            WF_GATE.read_text(encoding="utf-8"), encoding="utf-8")
        (d / "scripts" / "selfheal.py").write_text(
            "CONTROLS = [\n    (\"x\", [\"scripts/verify_index.py\"]),\n]\n", encoding="utf-8")
        (d / "scripts" / "verify_index.py").write_text("", encoding="utf-8")
        r = subprocess.run([sys.executable, str(d / "scripts" / "verify_workflow_contract.py")],
                           capture_output=True, text=True)
        return r.returncode

    refuse = """name: w
permissions:
  contents: read
jobs:
  j:
    steps:
      - run: git push origin x
"""
    accept = """name: w
permissions:
  # a comment inside the block is not the end of the block
  contents: write
jobs:
  j:
    steps:
      - run: git push origin x
      - run: python scripts/verify_index.py
      - run: python scripts/selfheal.py
"""
    results.append(("workflow: git push under contents:read refused", run(refuse) != 0))
    results.append(("workflow: comment in permissions block accepted", run(accept) == 0))


def check_idempotent() -> bool | None:
    """Two builds from the same sources must agree, timestamp aside.

    Guards a defect this build already had once: it read its carried-forward
    values from the file it writes, so the second run recorded v8.1 numbers as
    the superseded ones and erased the provenance of the defect it fixed.
    Returns None when the canonical sources are unreachable, as in CI.
    """
    builder = ROOT / "scripts" / "build_index.py"
    if not builder.exists():
        return None          # operator-only tool, absent from the public repo
    outs = []
    for _ in range(2):
        p = Path(tempfile.mktemp(suffix=".json"))
        r = subprocess.run([sys.executable, str(builder), "--out", str(p)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            if "required input missing" in (r.stdout + r.stderr):
                return None
            print(f"  build failed: {r.stdout[-300:]}{r.stderr[-300:]}")
            return False
        outs.append(json.loads(p.read_text(encoding="utf-8")))
        p.unlink(missing_ok=True)
    for o in outs:
        o.get("lineage", {}).pop("generated_at_utc", None)
    return outs[0] == outs[1]


def main() -> int:
    print("mutation test: the gate must FAIL on each injected defect\n")
    rc, out = run_gate(BASE)
    baseline = rc == 0
    print(f"  {'ok ' if baseline else 'X  '} baseline (unmutated) passes    "
          f"exit={rc}")
    passed = int(baseline)
    if not baseline:
        print(out)

    for name, mut, expect in CASES:
        rc, out = run_gate(mut(copy.deepcopy(BASE)))
        caught = rc != 0 and expect in out
        passed += caught
        status = "ok " if caught else "X  "
        why = "" if caught else (
            f"  <-- expected {expect}, exit={rc}"
            f"{' (gate passed!)' if rc == 0 else ''}")
        print(f"  {status} caught: {name:<30} [{expect}]{why}")

    extra: list[tuple[str, bool]] = []
    check_chain(extra)
    check_pairing(extra)
    check_contract(extra)
    check_endpoints(extra)
    check_graph(extra)
    check_secrets(extra)
    check_workflow_contract(extra)
    check_retrieval_corpus(extra)
    check_ledger_singleton(extra)
    check_ecosystem_state(extra)
    check_selfheal_runner(extra)
    for name, ok in extra:
        print(f"  {'ok ' if ok else 'X  '} {name}")
    passed += sum(1 for _, ok in extra if ok)

    idem = check_idempotent()
    total = len(CASES) + 1 + len(extra)
    if idem is None:
        print("  ..  skipped: build idempotence "
              "(canonical sources unreachable from here)")
    else:
        total += 1
        passed += idem
        print(f"  {'ok ' if idem else 'X  '} build is idempotent "
              f"(two builds agree, timestamp aside)")

    print(f"\n{passed}/{total} gate behaviours verified")
    if passed != total:
        print("GATE IS NOT TRUSTWORTHY: it missed a defect it must catch.",
              file=sys.stderr)
        return 1
    print("Gate is trustworthy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
