"""G-01: the served vintage must be recorded in the cross-repo lineage register.

Neither repository may serve a vintage the other does not record. The failure this
prevents is quiet: the public index advances, the private repository's lineage does
not, and six weeks later nobody can say which generation of the analysis produced a
figure someone cited.

This runs on a public CI runner, which cannot read the private repository. It therefore
checks the committed mirror, `data/vintage_lineage.json`, which is copied out of
`sovereign-infra/ops/vintage_lineage.json` when a vintage lands. That is a weaker check
than reading the private register directly and this file says so rather than implying
otherwise: it catches an unrecorded vintage, and it does not catch a mirror that was
updated without the register behind it. The second case is caught on the private side,
where both trees are reachable, by the same script run with --register.

Usage:  python scripts/verify_vintage_pairing.py [--register PATH] [--quiet]
Exit:   0 paired · 1 unrecorded or contradictory · 2 could not check
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _resolves(repo: Path, sha: str) -> bool | None:
    """Is `sha` a commit reachable from this repository's HEAD?

    None means the question could not be asked here, which is not the same as
    False and must never be reported as a failure. A public CI runner has no
    copy of the private repository, so only one column is ever checkable from
    either side.
    """
    if not (repo / ".git").exists():
        return None
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, "HEAD"],
            capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode in (0, 1):
        # 1 is a definite "not an ancestor"; anything else is git failing to
        # answer, most often because the object is absent from a shallow clone.
        cat = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True, text=True)
        if cat.returncode != 0:
            return False
        return r.returncode == 0
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(ROOT / "data" / "qesis_v8.json"))
    ap.add_argument("--register", default=str(ROOT / "data" / "vintage_lineage.json"),
                    help="the lineage register, or its committed mirror")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--resolve", action="store_true",
                    help="also require that this repository's own commit hashes "
                         "resolve to commits reachable from HEAD")
    args = ap.parse_args()
    say = (lambda *a: None) if args.quiet else print

    index_path, reg_path = Path(args.json), Path(args.register)
    if not reg_path.exists():
        print(f"PAIRING CHECK FAILED: no lineage register at {reg_path}. G-01 requires "
              f"that a served vintage be recorded; an absent register cannot record "
              f"anything.", file=sys.stderr)
        return 2

    served = json.loads(index_path.read_text(encoding="utf-8")).get("vintage")
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    entries = reg.get("entries") or []
    if not served:
        print("PAIRING CHECK FAILED: the index declares no vintage.", file=sys.stderr)
        return 2

    failures: list[str] = []
    row = next((e for e in entries if e.get("vintage") == served), None)
    if row is None:
        known = ", ".join(repr(e.get("vintage")) for e in entries) or "none"
        failures.append(f"G1.1 served vintage {served!r} has no row in the register. "
                        f"Registered: {known}")
    else:
        if not (row.get("summary") or "").strip():
            failures.append(f"G1.3 {served!r} has a row that says nothing about what "
                            f"changed")

    # A row must say something: either both repositories carry the change, or the
    # single-repo exemption is declared with a reason. Silence is not an exemption,
    # which is the whole point of G-01's third bullet.
    #
    # `pending` is tolerated on the vintage currently being introduced and nowhere
    # else. A change set cannot record its own commit hash before making it, and
    # that window is real. It is also exactly the excuse under which a placeholder
    # becomes permanent, so it expires the moment the next vintage is served.
    for e in entries:
        vin = e.get("vintage")
        pair = [e.get("qesis_mcp_commit"), e.get("sovereign_infra_commit")]
        reason = (e.get("single_repo_reason") or "").strip()
        pending = [p for p in pair if str(p).strip().lower() == "pending"]
        if pending and vin != served:
            failures.append(f"G1.2 {vin!r} is no longer the served vintage and still "
                            f"carries {len(pending)} pending commit reference. Fill it "
                            f"in or declare the exemption.")
        if not all(pair) and not reason:
            failures.append(f"G1.2 {vin!r} is recorded on one repository only "
                            f"({pair}) with no single_repo_reason. Declare the "
                            f"exemption or land the paired commit.")

    # A populated field is not a resolvable reference. Both squash and rebase
    # merges mint new commit hashes, so a hash copied from a feature branch
    # names a commit that stops existing the moment the pull request lands.
    # On 2026-08-01 three of the four recorded hashes went dangling in one
    # afternoon and every field-presence check still passed, which is why this
    # exists. Only this repository's own column is checkable here: the runner
    # has no copy of the other side, and "cannot ask" is reported as such
    # rather than counted as a pass or a failure.
    if args.resolve:
        unresolved = unknown = 0
        for e in entries:
            sha = e.get("qesis_mcp_commit")
            if not sha or str(sha).strip().lower() == "pending":
                continue
            verdict = _resolves(ROOT, str(sha))
            if verdict is False:
                unresolved += 1
                failures.append(
                    f"G1.5 {e.get('vintage')!r} cites qesis_mcp_commit {sha}, which "
                    f"is not reachable from HEAD. Record the hash after the merge: "
                    f"a pre-merge branch hash does not survive the merge.")
            elif verdict is None:
                unknown += 1
        say(f"resolve: {len(entries) - unresolved - unknown} of this repository's "
            f"hashes reachable, {unresolved} dangling, {unknown} not checkable here")

    # Duplicate rows would let two different change sets both claim to be the
    # record of one vintage, which is the ambiguity the register exists to end.
    seen: dict[str, int] = {}
    for e in entries:
        seen[e.get("vintage")] = seen.get(e.get("vintage"), 0) + 1
    dupes = [v for v, n in seen.items() if n > 1]
    if dupes:
        failures.append(f"G1.4 duplicate register rows for {dupes}")

    say(f"served vintage: {served}")
    say(f"register: {len(entries)} rows from {reg_path.name}")
    if row:
        say(f"  qesis-mcp {row.get('qesis_mcp_commit')} · "
            f"sovereign-infra {row.get('sovereign_infra_commit')}"
            + (f" · exemption: {row['single_repo_reason'][:60]}"
               if row.get("single_repo_reason") else ""))


    # ── R1.28. THE REGISTER TAIL MUST BE THE SERVED VINTAGE.
    # Added 2026-08-14 after the register announced v9.1 while the index served
    # v9.0 for several hours, through a full merge and promotion, with every
    # other gate green. This gate read the lineage file and never compared its
    # TAIL to the vintage the index declares, so a register could advertise a
    # vintage nobody serves. That is the CONC-1 family: one field resolved, another
    # still saying something else, and no control asserting the two agree.
    # A vintage is defined by its PAYLOAD. Scaffolding beside the index is not a
    # vintage, however much of it there is.
    tail = entries[-1] if entries else None
    if tail is None:
        failures.append("the lineage register carries no entries at all")
    elif tail.get("vintage") != served:
        failures.append(
            f"register tail is {tail.get('vintage')!r} but the index serves {served!r}. "
            f"A register that announces a vintage the index does not serve is a phantom "
            f"vintage. Either bump the index with scripts/bump_vintage.py, or withdraw "
            f"the entry. Do not promote with the two disagreeing.")
    else:
        say(f"  ok    register tail agrees with the served vintage: {served}")

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for f in failures:
            print(f"  x {f}", file=sys.stderr)
        print("\nPAIRING CHECK FAILED. Do not deploy a vintage the ecosystem does not "
              "record.", file=sys.stderr)
        return 1
    say("\nPAIRING CHECK PASSED: the served vintage is recorded.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:                                       # noqa: BLE001
        print(f"PAIRING CHECK FAILED: {type(exc).__name__}: {exc}.", file=sys.stderr)
        raise SystemExit(2)
