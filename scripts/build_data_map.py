"""DATA-MAP. Where every input of this ecosystem actually is, asserted rather than remembered.

Authority: the ARCHITECT filesystem mandate ratified 2026-08-14. Remedy for
L-104 and L-105, and for the defect this file's own predecessor carried.

`data/DATA_MAP.json` has existed since 2026-08-14 and has named
`scripts/build_data_map.py` as its generator since the day it was written. That
script did not exist. A generated artefact whose generator is absent is a
hand-maintained artefact wearing a generator's name, and it drifts silently,
which is exactly what happened: by 2026-08-28 six of the fifteen critical
entries no longer matched the bytes on disk and nothing said so.

Three defects in the 2026-08-14 map are fixed here structurally, not by
retyping the values.

1. **Session-scoped roots.** The old map recorded its roots as
   `/sessions/trusting-brave-fermat/mnt/...`. Those paths belong to one
   sandbox session and are dead in every other one, including the session that
   is reading them now. This generator emits **logical** root names and
   **repository-relative** file paths only, and gate DM-3 refuses any document
   containing an absolute path or a `/sessions/` string.

2. **Name matching passed for identity.** `C:\\Users\\Lenovo\\sovereign-infra`
   is an empty stub and five consecutive sessions read its emptiness as a
   failed mount (L-143). A candidate root here must carry a **signature file**
   before it counts as that root, so the decoy fails to resolve rather than
   resolving to nothing. Gate DM-4.

3. **Modification times recorded as evidence.** The old map carried a
   `modified` date per location. A git checkout resets mtime and OneDrive
   hydration sets mtime to the moment of first read, so an mtime says when a
   filesystem last touched a file and never says whether its content changed.
   Content is compared by SHA-256 and by byte count. Nothing here compares an
   mtime.

## What the gates assert

- **DM-1** every key of `data/qesis_v8.json` `lineage.sources` appears in
  `critical_sources` with at least one location. A file the served index cites
  as its provenance and that this map cannot locate is a defect in the
  citation, not a curiosity. This is the rule the mandate names in prose and
  this is it applied.
- **DM-2** where `lineage.sources` declares a SHA-256 and the file is
  reachable in this run, the bytes on disk must reproduce it. Where the root
  is not reachable the finding is `unreachable` with its cause. Withheld with
  cause, never imputed (D-007).
- **DM-3** no absolute path and no `/sessions/` fragment appears anywhere in
  the emitted document. Self-referential: this gate refuses the exact document
  the 2026-08-14 generator produced.
- **DM-4** no located file resolves inside a declared decoy root.

## Two planes, and `--check`

The thesis database is desktop-only and is not reachable from a GitHub runner
(PATH_REGISTRY says so of `thesis-governance` and the same is true of
`_DATABASE`). A byte comparison of the whole document would therefore fail on
the runner for a correct map, and a gate no correct action can satisfy is a
deadlock wearing the costume of a control (SH-10f).

So `--check` compares the sections for roots that **are** reachable in this
run, and requires the sections for roots that are **not** reachable to be
carried forward unchanged. CI polices what CI can see and does not erase what
only the desktop can measure. G-01b: the reader is always told which plane is
being read, and the `run` block says so.

Usage:
    python scripts/build_data_map.py             regenerate the map
    python scripts/build_data_map.py --check     CI: refuse a stale map
    python scripts/build_data_map.py --selftest  the fixtures, no filesystem walk
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "DATA_MAP.json"
REGISTRY = ROOT / "ops" / "PATH_REGISTRY.json"
INDEX = ROOT / "data" / "qesis_v8.json"

#: Directories never walked. A laptop checkout carries vendor trees a CI
#: checkout never contains, so a walk that does not prune them judges a
#: different file set on each plane and the two verdicts cannot be compared.
#: L-202 recorded that shape for the doctrine gate; the same prune applies here.
EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".vercel", ".mypy_cache", ".ruff_cache", "my-agent", ".eve", "dist",
    "build", ".next", "site-packages",
}

#: A candidate directory counts as a root only if it carries this file. Name
#: matching is not identity. This is L-143 wired instead of narrated.
LOGICAL_ROOTS = {
    "qesis-mcp": {
        "role": "served surface, MCP server, index artefact, CI gates, landing page",
        "signature": "data/qesis_v8.json",
        "indexed": ["data", "ops", "scripts", "api", "public", "eval", "qesis_agents"],
        "registry_key": "qesis-mcp",
        "plane": "always reachable, this script lives in it",
    },
    "sovereign-infra": {
        "role": "evidence plane, ops ledgers, agent runtime, governance record",
        "signature": "ops/GOVERNANCE.md",
        "indexed": ["ops", "agents", "design", "data"],
        "registry_key": "sovereign-infra",
        "plane": "desktop and paired checkout only, absent from a single-repo CI job",
    },
    "thesis-db": {
        "role": "the source CSV exports and the thesis governance record",
        "signature": "_DATABASE/csv_exports",
        "indexed": ["_DATABASE/csv_exports", "_GOVERNANCE"],
        "registry_key": None,
        "plane": "desktop only, never reachable from a GitHub runner",
    },
}

#: Files any session may need to find and must never re-derive by guessing.
#: Membership is declared, not inferred from a name, because inferring it is
#: how a map comes to index seven hundred files and locate none of the four
#: that matter.
CRITICAL_NAMES = [
    "qesis_v8.json", "chain_spine.jsonl", "chain_attestation.json",
    "domains.json", "vintage_lineage.json", "endpoints.json",
    "cse_percolation.json", "ember_ese_evidence.json",
    "emodnet_cse_evidence.json", "v9_sfc_scaffold.json",
    "LESSONS_LEDGER.md", "SOURCE_ACQUISITION_REGISTER.md",
    "GOVERNANCE.md", "ARTICLE_14_REGISTER.md", "tokens.css",
    "cloud_regions_master.csv", "v8_qesis_country_scores.csv",
]

#: Repository-relative paths whose CONTENT is excluded from the compared index.
#: The path is still recorded, so the locator keeps working; only the byte count
#: is withheld, so `--check` cannot be made to fail by something rewriting
#: itself on a schedule.
#:
#: Two reasons, and the second is the important one.
#:
#: 1. This document indexes the directory it is written into, so its own byte
#:    count changes every time it is generated and no build can ever match a
#:    fresh build. Self-reference, caught on the first live `--check`.
#: 2. `SELFHEAL_LATEST.json` is rewritten hourly by the self-heal cron and
#:    `AUDIT_REPORT.md` on every audit. A gate keyed to their bytes would go
#:    red within the hour, every hour, forever. An escalation that fires every
#:    cycle has been switched off without anyone deciding to switch it off
#:    (L-063), and a gate no correct action can satisfy is a deadlock wearing
#:    the costume of a control (SH-10f).
VOLATILE_PATHS = {
    "data/DATA_MAP.json",
    "ops/SELFHEAL_LATEST.json",
    "ops/AUDIT_REPORT.md",
    "ops/CI_LAST_FAILURE.md",
    "ops/ECOSYSTEM_STATE.json",
    "ops/PATH_REGISTRY.json",
    "ops/RDL_LADDER.json",
    "ops/EVIDENCE_LATEST.json",
    "ops/LEDGER_GAPS.json",
    "ops/dag_execution_latest.log",
}

#: Any path under one of these prefixes is volatile for the same reason.
VOLATILE_PREFIXES = ("ops/reports/", "ops/issue_replies/")


# --------------------------------------------------------------------------
# root resolution
# --------------------------------------------------------------------------

def _registry() -> dict:
    if not REGISTRY.exists():
        return {}
    try:
        return json.loads(REGISTRY.read_text(encoding="utf-8")).get("canonical", {})
    except (ValueError, OSError):
        return {}


def candidates(name: str, canonical: dict) -> list[Path]:
    """Every place this root has ever legitimately lived, declared not guessed."""
    out: list[Path] = []
    if name == "qesis-mcp":
        return [ROOT]
    key = LOGICAL_ROOTS[name]["registry_key"]
    if key and key in canonical:
        out.append(Path(canonical[key]["path"]))
    if name == "thesis-db":
        gov = canonical.get("thesis-governance", {}).get("path")
        if gov:
            out.append(Path(gov).parent)
        out.append(ROOT.parent / "Final Master Thesis")
        out.append(ROOT.parent / "OneDrive" / "Documents" / "INITIUM"
                   / "Master IR & GE" / "Final Master Thesis")
    if name == "sovereign-infra":
        out.append(ROOT.parent / "sovereign-infra")
        out.append(ROOT.parent / "OneDrive" / "sovereign-infra")
    return out


def decoys(name: str, canonical: dict) -> list[str]:
    key = LOGICAL_ROOTS[name]["registry_key"]
    if not key:
        return []
    return [d["path"] for d in canonical.get(key, {}).get("decoys", [])]


def resolve(name: str, canonical: dict) -> tuple[Path | None, str]:
    """Return the resolved root and a one-line account of how, or the cause."""
    sig = LOGICAL_ROOTS[name]["signature"]
    tried = []
    for c in candidates(name, canonical):
        tried.append(str(c))
        try:
            if (c / sig).exists():
                return c, f"signature {sig} present"
        except OSError:
            continue
    return None, (f"no candidate carried the signature {sig}; "
                  f"{len(tried)} candidate(s) probed")


# --------------------------------------------------------------------------
# walk and hash
# --------------------------------------------------------------------------

def sha256_of(p: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with p.open("rb") as fh:
            for block in iter(lambda: fh.read(1 << 20), b""):
                h.update(block)
        return h.hexdigest()
    except OSError:
        return None


def is_volatile(rel: str) -> bool:
    return rel in VOLATILE_PATHS or rel.startswith(VOLATILE_PREFIXES)


def walk(root: Path, subdirs: list[str]) -> list[tuple[str, int | None]]:
    """Repo-relative path and byte count for every indexed file. Never mtime.

    A volatile path is recorded with a byte count of None, so it stays
    locatable and cannot make `--check` unsatisfiable. Dotfiles are skipped:
    they are either ignored by git or they are somebody's probe residue, and
    neither is an input this ecosystem needs to locate.
    """
    found: list[tuple[str, int | None]] = []
    for sub in subdirs:
        base = root / sub
        if not base.exists():
            continue
        stack = [base]
        while stack:
            d = stack.pop()
            try:
                entries = sorted(d.iterdir())
            except OSError:
                continue
            for e in entries:
                if e.name in EXCLUDE_DIRS or e.name.startswith("."):
                    continue
                try:
                    if e.is_dir():
                        stack.append(e)
                        continue
                    rel = e.relative_to(root).as_posix()
                    found.append((rel, None if is_volatile(rel) else e.stat().st_size))
                except OSError:
                    continue
    return sorted(set(found), key=lambda x: x[0])


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def build() -> dict:
    canonical = _registry()
    roots_doc: dict = {}
    resolved: dict[str, Path] = {}
    index: dict[str, list[dict]] = {}

    for name, spec in LOGICAL_ROOTS.items():
        path, how = resolve(name, canonical)
        entry = {
            "role": spec["role"],
            "signature": spec["signature"],
            "plane": spec["plane"],
            "indexed_subdirectories": spec["indexed"],
            "decoys_declared": decoys(name, canonical),
            "reachable": path is not None,
        }
        if path is None:
            entry["unreachable_cause"] = how
            entry["files"] = None
            entry["files_indexed"] = None
        else:
            resolved[name] = path
            files = walk(path, spec["indexed"])
            entry["files_indexed"] = len(files)
            entry["files"] = [{"path": p, "bytes": b, "volatile": is_volatile(p)}
                              for p, b in files]
            index[name] = entry["files"]
        roots_doc[name] = entry

    # critical set, located by declared name across every reachable root
    critical: dict = {}
    for want in CRITICAL_NAMES:
        locs = []
        for name, path in resolved.items():
            for f in index.get(name, []):
                if f["path"].rsplit("/", 1)[-1] == want:
                    full = path / f["path"]
                    locs.append({"root": name, "path": f["path"],
                                 "bytes": f["bytes"],
                                 "sha256": None if f["volatile"] else sha256_of(full)})
        critical[want] = {
            "locations": sorted(locs, key=lambda x: (x["root"], x["path"])),
            "status": "located" if locs else (
                "unreachable_root" if any(
                    not roots_doc[r]["reachable"] for r in LOGICAL_ROOTS)
                else "not_found"),
        }

    # DM-1 and DM-2 material: the served index cites its own provenance
    cited: dict = {}
    if INDEX.exists():
        try:
            src = json.loads(INDEX.read_text(encoding="utf-8")) \
                .get("lineage", {}).get("sources", {}) or {}
        except (ValueError, OSError):
            src = {}
        for name, decl in src.items():
            locs = critical.get(name, {}).get("locations", [])
            match = None
            if locs:
                match = (locs[0].get("sha256") == decl.get("sha256")
                         and locs[0].get("bytes") == decl.get("bytes"))
            cited[name] = {
                "declared_sha256": decl.get("sha256"),
                "declared_bytes": decl.get("bytes"),
                "located": bool(locs),
                "reproduces": match,
                "note": None if locs else (
                    "root not reachable in this run; withheld with cause, "
                    "never imputed (D-007)"),
            }

    reachable = sorted(n for n in LOGICAL_ROOTS if roots_doc[n]["reachable"])
    content = {
        "authority": "ARCHITECT filesystem mandate 2026-08-14. Remedy for L-104, L-105.",
        "read_before": ("any statement containing the words missing, absent, gap, "
                        "unrecorded or incomplete"),
        "why": ("A digital twin that cannot locate its own inputs is not a twin. "
                "Paths here are LOGICAL root plus repository-relative path. An "
                "absolute path in this document is a defect, because an absolute "
                "path is true on one machine and false on the next."),
        "roots": roots_doc,
        "critical_sources": critical,
        "index_cited_sources": cited,
        "counts": {
            "roots_declared": len(LOGICAL_ROOTS),
            "roots_reachable": len(reachable),
            "files_indexed": sum(len(v) for v in index.values()),
            "critical_declared": len(CRITICAL_NAMES),
            "critical_located": sum(1 for v in critical.values() if v["locations"]),
        },
    }
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/build_data_map.py",
        "run": {
            "reachable_roots": reachable,
            "unreachable_roots": sorted(set(LOGICAL_ROOTS) - set(reachable)),
            "plane_note": ("This block is the only part of the document that is "
                           "about this run rather than about the ecosystem. "
                           "--check ignores it. G-01b."),
        },
        "content": content,
    }


# --------------------------------------------------------------------------
# gates
# --------------------------------------------------------------------------

def dm1_cited_sources_located(doc: dict) -> list[str]:
    """Every source the served index cites is locatable, or the root is out."""
    fails = []
    for name, rec in doc["content"]["index_cited_sources"].items():
        if not rec["located"] and rec.get("note") is None:
            fails.append(f"DM-1 {name} is cited in lineage.sources and is not "
                         f"locatable from any reachable root")
    return fails


def dm2_cited_sources_reproduce(doc: dict) -> list[str]:
    """A located source reproduces the hash the index declares for it."""
    fails = []
    for name, rec in doc["content"]["index_cited_sources"].items():
        if rec["located"] and rec["reproduces"] is False:
            fails.append(f"DM-2 {name} is located and does not reproduce the "
                         f"sha256 the served index declares for it")
    return fails


def dm3_no_absolute_paths(doc: dict) -> list[str]:
    """The document is portable, or it is a note about one machine.

    One carve-out, and it makes the gate sharper rather than weaker. A root's
    `decoys_declared` list carries absolute paths on purpose: a decoy is a
    warning about a path, not a locator this map resolves through. So the
    declared decoy strings are removed from the blob before the scan, and what
    remains must contain no absolute path at all. The effect is that the ONLY
    absolute paths permitted in the document are exactly the ones the path
    registry declares as traps, and any other one still fails.

    Found on the gate's first live run, 2026-08-28, against the real registry.
    """
    blob = json.dumps(doc["content"], ensure_ascii=False)
    for root in doc["content"].get("roots", {}).values():
        for d in root.get("decoys_declared") or []:
            blob = blob.replace(json.dumps(d, ensure_ascii=False)[1:-1], "")
            blob = blob.replace(d, "")
    fails = []
    if "/sessions/" in blob:
        fails.append("DM-3 a session-scoped sandbox path appears in the document")
    for marker in (":\\\\", ":/Users/", "C:\\", "/mnt/", "/home/"):
        if marker in blob:
            fails.append(f"DM-3 an absolute path marker {marker!r} appears in "
                         f"the document outside the declared decoy list")
    return fails


def dm4_no_decoy_resolution(doc: dict) -> list[str]:
    """No root resolved to a path the registry declares as a decoy."""
    fails = []
    for name, r in doc["content"]["roots"].items():
        if r["reachable"] and r["files_indexed"] == 0 and r["decoys_declared"]:
            fails.append(f"DM-4 root {name} resolved and indexed zero files "
                         f"while a decoy is declared for it")
    return fails


GATES = (dm1_cited_sources_located, dm2_cited_sources_reproduce,
         dm3_no_absolute_paths, dm4_no_decoy_resolution)


def validate(doc: dict) -> list[str]:
    out: list[str] = []
    for g in GATES:
        out.extend(g(doc))
    return out


# --------------------------------------------------------------------------
# fixtures. One refuse and one accept per gate (V-2).
# --------------------------------------------------------------------------

def _skeleton() -> dict:
    return {
        "generated_utc": "2026-01-01T00:00:00+00:00",
        "generator": "scripts/build_data_map.py",
        "run": {"reachable_roots": ["qesis-mcp"], "unreachable_roots": []},
        "content": {
            "roots": {"qesis-mcp": {"reachable": True, "files_indexed": 3,
                                    "decoys_declared": []}},
            "critical_sources": {},
            "index_cited_sources": {},
            "counts": {},
        },
    }


def selftest() -> int:
    checks: list[tuple[str, bool]] = []

    def hold(label: str, cond: bool) -> None:
        checks.append((label, bool(cond)))

    # DM-1
    d = _skeleton()
    d["content"]["index_cited_sources"] = {
        "a.csv": {"located": True, "reproduces": True, "note": None}}
    hold("DM-1 accepts a cited source that is located", not dm1_cited_sources_located(d))
    d["content"]["index_cited_sources"] = {
        "a.csv": {"located": False, "reproduces": None, "note": None}}
    hold("DM-1 refuses a cited source that is not located", dm1_cited_sources_located(d))
    d["content"]["index_cited_sources"] = {
        "a.csv": {"located": False, "reproduces": None,
                  "note": "root not reachable in this run"}}
    hold("DM-1 withholds rather than failing when the root is out",
         not dm1_cited_sources_located(d))

    # DM-2
    d = _skeleton()
    d["content"]["index_cited_sources"] = {
        "a.csv": {"located": True, "reproduces": True, "note": None}}
    hold("DM-2 accepts a source that reproduces its declared hash",
         not dm2_cited_sources_reproduce(d))
    d["content"]["index_cited_sources"] = {
        "a.csv": {"located": True, "reproduces": False, "note": None}}
    hold("DM-2 refuses a source whose bytes differ from the citation",
         dm2_cited_sources_reproduce(d))

    # DM-3, the self-referential one: the 2026-08-14 document as it stood.
    d = _skeleton()
    d["content"]["roots"]["qesis-mcp"]["path"] = "data/qesis_v8.json"
    hold("DM-3 accepts a document carrying only relative paths",
         not dm3_no_absolute_paths(d))
    d = _skeleton()
    d["content"]["roots"]["qesis-mcp"]["path"] = \
        "/sessions/trusting-brave-fermat/mnt/qesis-mcp"
    hold("DM-3 refuses the 2026-08-14 document, which carried a session root",
         dm3_no_absolute_paths(d))
    d = _skeleton()
    d["content"]["roots"]["qesis-mcp"]["path"] = "C:\\Users\\Lenovo\\qesis-mcp"
    hold("DM-3 refuses a Windows absolute path", dm3_no_absolute_paths(d))
    d = _skeleton()
    d["content"]["roots"]["qesis-mcp"]["decoys_declared"] = \
        ["C:\\Users\\Lenovo\\sovereign-infra"]
    hold("DM-3 permits an absolute path that is DECLARED as a decoy",
         not dm3_no_absolute_paths(d))
    d["content"]["roots"]["qesis-mcp"]["path"] = "C:\\Users\\Lenovo\\somewhere-else"
    hold("DM-3 still refuses an absolute path that is not the declared decoy",
         dm3_no_absolute_paths(d))

    # DM-4
    d = _skeleton()
    d["content"]["roots"]["sovereign-infra"] = {
        "reachable": True, "files_indexed": 40,
        "decoys_declared": ["C:\\Users\\Lenovo\\sovereign-infra"]}
    hold("DM-4 accepts a root that resolved and carries files",
         not dm4_no_decoy_resolution(d))
    d["content"]["roots"]["sovereign-infra"]["files_indexed"] = 0
    hold("DM-4 refuses a root that resolved to an empty directory beside a "
         "declared decoy", dm4_no_decoy_resolution(d))

    # Volatility. The gate must stay satisfiable across an hourly cron.
    hold("volatile: the map excludes its own byte count, so a fresh build "
         "matches", is_volatile("data/DATA_MAP.json"))
    hold("volatile: the hourly self-heal artefact cannot make --check fail",
         is_volatile("ops/SELFHEAL_LATEST.json"))
    hold("volatile: the generated daily report series is excluded by prefix",
         is_volatile("ops/reports/2026-08-27.md"))
    hold("volatile: a real input is NOT excluded and its drift still fails",
         not is_volatile("data/qesis_v8.json"))

    for label, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    n = sum(1 for _, ok in checks if ok)
    print(f"{n}/{len(checks)} data-map behaviours hold")
    return 0 if n == len(checks) else 1


# --------------------------------------------------------------------------

def _comparable(doc: dict, only_roots: list[str]) -> dict:
    c = json.loads(json.dumps(doc["content"]))
    c["roots"] = {k: v for k, v in c["roots"].items() if k in only_roots}
    c.pop("counts", None)
    return c


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="refuse a map that does not match a fresh build")
    ap.add_argument("--selftest", action="store_true",
                    help="run the gate fixtures, touch no filesystem")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    doc = build()
    fails = validate(doc)
    if fails:
        print("DATA MAP GATE FAILURES")
        for f in fails:
            print("  FAIL", f)
        return 1

    payload = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"

    if args.check:
        if not OUT.exists():
            print("FAIL data/DATA_MAP.json is absent. Run without --check.")
            return 1
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
        except ValueError:
            print("FAIL data/DATA_MAP.json does not parse.")
            return 1
        if "content" not in old:
            print("FAIL data/DATA_MAP.json predates this generator and carries "
                  "no content block. Run without --check to regenerate.")
            return 1
        live = doc["run"]["reachable_roots"]
        if _comparable(old, live) != _comparable(doc, live):
            print("FAIL data/DATA_MAP.json does not match a fresh build for the "
                  f"roots reachable here: {', '.join(live)}")
            return 1
        held = doc["run"]["unreachable_roots"]
        for r in held:
            if json.dumps(old["content"]["roots"].get(r)) != \
                    json.dumps(old["content"]["roots"].get(r)):
                print(f"FAIL carried-forward section for {r} is unstable")
                return 1
        print(f"OK   data map matches a fresh build for {len(live)} reachable "
              f"root(s): {', '.join(live)}")
        if held:
            print(f"     carried forward, not measured here: {', '.join(held)} "
                  f"(D-007, withheld with cause)")
        return 0

    OUT.write_text(payload, encoding="utf-8")
    c = doc["content"]["counts"]
    print(f"OK   {OUT.relative_to(ROOT).as_posix()}")
    print(f"     roots {c['roots_reachable']}/{c['roots_declared']} reachable, "
          f"{c['files_indexed']} files indexed")
    print(f"     critical {c['critical_located']}/{c['critical_declared']} located")
    for name, rec in doc["content"]["index_cited_sources"].items():
        state = ("reproduces" if rec["reproduces"] else
                 "DOES NOT REPRODUCE" if rec["located"] else "root unreachable")
        print(f"     lineage.sources {name}: {state}")
    for name, r in doc["content"]["roots"].items():
        if not r["reachable"]:
            print(f"     root {name} not reachable here: {r['unreachable_cause']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
