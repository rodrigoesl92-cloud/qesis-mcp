#!/usr/bin/env python3
"""The lander's own contract: the shell parses nothing and restores only what changed.

WHY THIS GATE EXISTS. Second occurrence of the family shell_built_the_query
(L-167, L-176), so the ladder demands a gate with fixtures (V-2, SH-10).

    L-167  PowerShell expanded a jq expression before gh saw it; forty pull
           request closures were attempted on branches named after the words
           of the error message.
    L-176  Windows PowerShell 5.1 ConvertFrom-Json emits a JSON array as ONE
           pipeline item. `Select-Object -ExpandProperty number` saw the array,
           not its elements, the pull request number stayed empty, merge and CI
           feedback were skipped in both repositories, and a run that had pushed
           everything reported NOTHING DONE.

    Same epistemic move both times: the shell interpreted structured data that
    only a parser should interpret. The rule is not better quoting and not a
    newer PowerShell. It is that the lander's shell never parses JSON and never
    hands gh a query: every value comes from a Python reader (gh_ops.py,
    landing_manifest.py) that prints one plain string.

    L-177 rides on the same gate because it is checked on the same file: the
    lander restored the WHOLE disk snapshot over origin/main (`git checkout
    $save -- .`), so any commit a runner had landed on main since the last click
    would have been silently reverted by the next one, the moment the self-heal
    loop is allowed to land (L-174). The restore is now the delta the session
    made, `git diff --name-only <before> <snapshot>`, and nothing else.

CHECKS, over the lander text with comments blanked
    LC-1  no ConvertFrom-Json, no ConvertTo-Json
    LC-2  no `--jq` and no `-q` flag on a gh call; no `--json` on a gh call
          (JSON is consumed by gh_ops.py, never by the shell)
    LC-3  ASCII only: PowerShell 5.1 reads a BOM-less file as ANSI, and any
          non-ASCII byte becomes mojibake in commit titles and log lines
    LC-4  the branch and the messages come from landing_manifest.py; no
          literal `fix/land-` branch is assigned in the script
    LC-5  the restore is selective: `--diff-filter` present and the whole-tree
          form `checkout',$save,'--','.'` absent

Usage:
    python scripts/verify_lander_contract.py [--file PATH]   # default: sovereign-infra/LAND_EVERYTHING_FINAL.ps1
    python scripts/verify_lander_contract.py --selftest
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = [
    Path(r"C:\Users\Lenovo\OneDrive\sovereign-infra\LAND_EVERYTHING_FINAL.ps1"),
    ROOT.parent / "sovereign-infra" / "LAND_EVERYTHING_FINAL.ps1",
    ROOT / "LAND_EVERYTHING_FINAL.ps1",
]


def code_lines(text: str) -> list[str]:
    """The lander's lines with comments blanked, line numbers preserved.

    A comment that names the forbidden cmdlet while explaining why it is
    forbidden is not a violation, and a gate that refuses its own rationale
    teaches people to delete rationale. Block comments `<# ... #>` and lines
    whose first character is `#` are blanked; a trailing `# ...` after code is
    left alone, because `#` also appears inside strings.
    """
    blanked = re.sub(r"<#.*?#>", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return ["" if l.lstrip().startswith("#") else l for l in blanked.splitlines()]


def findings(text: str) -> list[str]:
    """Every violation in a lander text. Pure."""
    out: list[str] = []
    lines = code_lines(text)

    def where(pat: str) -> list[int]:
        return [i for i, l in enumerate(lines, 1) if re.search(pat, l)]

    for n in where(r"Convert(From|To)-Json"):
        out.append(f"LC-1 line {n}: the shell parses JSON. Read the value through "
                   "scripts/gh_ops.py or scripts/landing_manifest.py instead (L-176).")
    for n in where(r"--jq\b|'gh'[^\n]*(?:'-q'|\s-q\s)"):
        out.append(f"LC-2 line {n}: a jq query handed to gh from the shell (L-167).")
    for n in where(r"'gh'.*'--json'|\bgh\s[^\n]*--json\b"):
        out.append(f"LC-2 line {n}: gh is asked for --json in the shell; only gh_ops.py "
                   "consumes JSON (L-176).")
    bad = [(i, c) for i, l in enumerate(text.splitlines(), 1) for c in l if ord(c) > 127]
    if bad:
        n, c = bad[0]
        out.append(f"LC-3 line {n}: non-ASCII character U+{ord(c):04X}; PowerShell 5.1 reads "
                   f"a BOM-less file as ANSI ({len(bad)} such character(s)).")
    if "landing_manifest.py" not in text:
        out.append("LC-4 the lander does not read scripts/landing_manifest.py; its branch and "
                   "messages would be literals written for one landing (L-177 context).")
    for n in where(r"^\s*\$Branch\s*=\s*'(fix|feat|chore|docs)/"):
        out.append(f"LC-4 line {n}: a literal branch name is assigned; it belongs in the manifest.")
    if "--diff-filter" not in text:
        out.append("LC-5 no selective restore (`git diff --name-only --diff-filter`): the lander "
                   "would write the whole disk snapshot over origin/main and revert every "
                   "runner-side commit since the last click (L-177).")
    for n in where(r"checkout'\s*,\s*\$save\s*,\s*'--'\s*,\s*'\.'"):
        out.append(f"LC-5 line {n}: whole-tree restore `git checkout $save -- .` (L-177).")
    return out


REFUSE = """$Branch = 'fix/land-20260824-consolidated'
$prs = (Run 'gh' @('pr','list','--head',$Branch,'--json','number')).Out | ConvertFrom-Json
$ex = $prs | Select-Object -ExpandProperty number
Run 'git' @('checkout',$save,'--','.') | Out-Null
"""
ACCEPT = """$Branch = (Run 'python' @("$Qesis\\scripts\\landing_manifest.py",'--file',$Manifest,'--key','branch')).Out.Trim()
$pn = Run 'python' @("$Qesis\\scripts\\gh_ops.py",'pr-number','--repo',"$Owner/$($r.Name)",'--head',$Branch)
$changed = @((Run 'git' @('diff','--name-only','--no-renames','--diff-filter=ACMT',$base,$save)).Out -split "`n")
foreach ($f in $changed) { Run 'git' @('checkout',$save,'--',$f) | Out-Null }
"""


def selftest() -> int:
    r = findings(REFUSE)
    a = findings(ACCEPT)
    cases = [
        ("refuses ConvertFrom-Json (LC-1)", any(x.startswith("LC-1") for x in r)),
        ("refuses gh --json in the shell (LC-2)", any(x.startswith("LC-2") for x in r)),
        ("refuses a literal branch and no manifest (LC-4)", sum(x.startswith("LC-4") for x in r) == 2),
        ("refuses the whole-tree restore (LC-5)", sum(x.startswith("LC-5") for x in r) == 2),
        ("refuses a non-ASCII byte (LC-3)",
         any(x.startswith("LC-3") for x in findings("Say \"caf\u00e9\"\n" + ACCEPT))),
        ("accepts the manifest-driven, selective, parser-free form", a == []),
        ("accepts a comment that names ConvertFrom-Json while forbidding it",
         findings("<# revision 6: no ConvertFrom-Json #>\n# ConvertFrom-Json is banned here\n" + ACCEPT) == []),
    ]
    for name, ok in cases:
        print(f"  {'PASS' if ok else 'FAIL'}  lander: {name}")
    n = sum(ok for _, ok in cases)
    print(f"lander contract selftest: {n}/{len(cases)} fixtures " + ("hold" if n == len(cases) else "FAILED"))
    if n != len(cases):
        for x in r + a:
            print("   ", x)
    return 0 if n == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    # Fixtures first, always. A gate whose fixtures fail has no standing (V-2).
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        st = selftest()
    if st != 0:
        print(buf.getvalue(), end="")
        print("LANDER CONTRACT FAILED: the gate's own fixtures do not hold")
        return 1
    path = Path(a.file) if a.file else next((p for p in CANDIDATES if p.exists()), None)
    if path is None or not path.exists():
        print("LANDER CONTRACT: no lander found at " + "; ".join(str(p) for p in CANDIDATES))
        return 1
    text = path.read_bytes().decode("utf-8", errors="replace")
    f = findings(text)
    if f:
        print(f"LANDER CONTRACT FAILED: {len(f)} finding(s) in {path}")
        for x in f:
            print("  " + x)
        return 1
    print(f"OK   lander contract holds for {path.name}: no shell parsing, manifest-driven, "
          "selective restore, ASCII")
    return 0


if __name__ == "__main__":
    sys.exit(main())
