#!/usr/bin/env python3
"""Read the landing manifest for the lander, so the shell never parses JSON.

WHY (L-176, L-177). Revision 5 of LAND_EVERYTHING_FINAL.ps1 carried its branch
name, both commit titles and the pull request body as literals written for one
landing, the 2026-08-24 one. Every later click would have landed new work under
the old words. It also parsed JSON in Windows PowerShell 5.1, where
ConvertFrom-Json emits an array as ONE pipeline item, and that single quirk
turned a run that had pushed both repositories into a summary that said NOTHING
DONE. The rule after that run: the shell parses nothing. Values come from this
reader, and GitHub state comes from gh_ops.py.

The manifest is a small JSON file beside the lander, written by the session
that prepared the change set:

    {
      "written_utc": "2026-08-26T02:40:00Z",
      "branch": "fix/land-20260826-guard-and-lander",
      "body": "one paragraph, shared by both commits and both pull requests",
      "repos": {
        "qesis-mcp":       {"title": "fix(...): ..."},
        "sovereign-infra": {"title": "fix(...): ..."}
      }
    }

Usage:
    python scripts/landing_manifest.py --file PATH --check
    python scripts/landing_manifest.py --file PATH --key branch
    python scripts/landing_manifest.py --file PATH --key body
    python scripts/landing_manifest.py --file PATH --title sovereign-infra
    python scripts/landing_manifest.py --selftest

Exit 0 and the value on stdout, or exit 1 and the reason on stderr. A missing
or malformed manifest is a refusal, never a default: a lander that invents its
own commit message is the defect this file replaces.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPOS = ("qesis-mcp", "sovereign-infra")
BRANCH_RE = re.compile(r"^(fix|feat|chore|docs)/[A-Za-z0-9][A-Za-z0-9._-]{3,80}$")
#: Writing doctrine, W-1 and ops/WRITING_STYLE.md. A commit message is prose.
EM_DASH = "\u2014"
BANNED = ("delve", "unlock", "robust", "seamless", "crucial", "foster", "empower",
          "elevate", "tapestry", "game-changer")


def problems(m: object) -> list[str]:
    """Every reason this manifest may not drive a landing. Empty means valid."""
    out: list[str] = []
    if not isinstance(m, dict):
        return ["the manifest is not a JSON object"]
    br = m.get("branch")
    if not isinstance(br, str) or not BRANCH_RE.match(br):
        out.append("branch must match (fix|feat|chore|docs)/<slug>, 4 to 81 characters; "
                   f"got {br!r}")
    elif br.strip().lower() == "main":
        out.append("branch may not be main (G-06: no direct push to main)")
    body = m.get("body")
    if not isinstance(body, str) or len(body.strip()) < 40:
        out.append("body must be a paragraph of at least 40 characters")
    repos = m.get("repos")
    if not isinstance(repos, dict):
        out.append("repos must be an object keyed by repository name")
    else:
        for r in REPOS:
            t = (repos.get(r) or {}).get("title") if isinstance(repos.get(r), dict) else None
            if not isinstance(t, str) or len(t.strip()) < 12:
                out.append(f"repos.{r}.title must be a commit title of at least 12 characters")
            elif len(t) > 200:
                out.append(f"repos.{r}.title is longer than 200 characters")
    texts = [x for x in [body] + [((repos or {}).get(r) or {}).get("title")
                                  for r in REPOS] if isinstance(x, str)] \
        if isinstance(repos, dict) else ([body] if isinstance(body, str) else [])
    for x in texts:
        if EM_DASH in x:
            out.append("an em dash in a title or body; W-1 forbids it in prose")
        low = x.lower()
        hits = [w for w in BANNED if re.search(r"\b" + re.escape(w) + r"\b", low)]
        if hits:
            out.append("banned words in a title or body (ops/WRITING_STYLE.md): " + ", ".join(hits))
    return out


def load(path: Path) -> tuple[dict | None, list[str]]:
    if not path.exists():
        return None, [f"no manifest at {path}. The session that prepared the change set "
                      "writes it; the lander does not invent one."]
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"manifest is not valid JSON: {exc}"]
    return m, problems(m)


def selftest() -> int:
    good = {"written_utc": "2026-08-26T00:00:00Z", "branch": "fix/land-20260826-x",
            "body": "A paragraph long enough to be a body for two commits and two pull requests.",
            "repos": {"qesis-mcp": {"title": "fix(lander): read the manifest"},
                      "sovereign-infra": {"title": "fix(lander): read the manifest"}}}
    bad_branch = dict(good, branch="main")
    bad_title = json.loads(json.dumps(good))
    bad_title["repos"]["sovereign-infra"] = {"title": "x"}
    bad_prose = dict(good, body=good["body"] + " " + EM_DASH + " and a robust ending.")
    cases = [
        ("accepts a complete manifest", problems(good) == []),
        ("refuses branch main", any("main" in p for p in problems(bad_branch))),
        ("refuses a missing repository title", any("title" in p for p in problems(bad_title))),
        ("refuses an em dash and a banned word in prose", len(problems(bad_prose)) == 2),
        ("refuses a non-object", problems([1, 2]) != []),
    ]
    for name, ok in cases:
        print(f"  {'PASS' if ok else 'FAIL'}  manifest: {name}")
    n = sum(ok for _, ok in cases)
    print(f"landing manifest selftest: {n}/{len(cases)} fixtures " + ("hold" if n == len(cases) else "FAILED"))
    return 0 if n == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--key", choices=["branch", "body", "written_utc"])
    ap.add_argument("--title", metavar="REPO")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file:
        print("landing_manifest: --file is required", file=sys.stderr)
        return 1
    m, errs = load(Path(a.file))
    if errs:
        for e in errs:
            print(f"landing_manifest: {e}", file=sys.stderr)
        return 1
    if a.check:
        print(f"LANDING MANIFEST OK: branch {m['branch']}, written {m.get('written_utc', '?')}")
        return 0
    if a.key:
        print(m[a.key])
        return 0
    if a.title:
        if a.title not in m["repos"]:
            print(f"landing_manifest: no title for {a.title}", file=sys.stderr)
            return 1
        print(m["repos"][a.title]["title"])
        return 0
    print("landing_manifest: nothing asked; use --check, --key or --title", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
