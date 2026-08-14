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
