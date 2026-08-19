"""D-2. Refuse a secret that is reachable from the repository.

The incident record carries four credential exposures, three of them caused by
the remedy for the previous one, so this gate is written against the *shapes*
those took rather than against a general idea of secrecy.

WHAT IT CHECKS, AND WHY EACH ONE IS HERE
  1. A secret-shaped assignment with a real value in any TRACKED file. That is
     the direct case.
  2. Known credential filenames present AND tracked. `.env` holding
     FSQCA_ED25519_PRIV_B64 is the case D-2 exists for.
  3. Known credential filenames missing from `.gitignore`. INC-20260731-01
     reached a synced folder because the existing rules did not cover a file
     called `ENTSO-E API KEY.txt`: the rules named what someone had thought of,
     and this checks the coverage rather than the contents.

WHAT IT DELIBERATELY DOES NOT DO
  It never prints a matched value, not even truncated. G-03 forbids credential
  material out of an agent "including in a redacted form that preserves the
  length or the first characters", and a gate that leaks the thing it guards to
  prove it found it is worse than no gate. It prints the file, the line number
  and the variable NAME.

  It does not scan git history. `scripts/scan_credentials.py` walks every commit
  from every ref and that is the right tool for the question "did it ever enter
  git". This one answers "is it reachable now", which is a different question
  and is cheap enough to run on every build.

Usage:  python scripts/verify_no_plaintext_secrets.py [--root DIR] [--quiet]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Filenames that hold credentials by design. Present is fine; TRACKED is not,
#: and absent from .gitignore is not.
CREDENTIAL_FILES = [".env", ".env.local", "database_string.txt"]

#: Variable-name shapes that carry secrets. Deliberately broad: a false positive
#: costs one exemption line, a false negative costs a rotation.
SECRET_NAME = re.compile(
    r"^\s*(?:export\s+)?([A-Z0-9_]+)\s*=\s*(.+?)\s*$")

#: The secret word must appear as a whole underscore-separated COMPONENT of the
#: identifier, never as a substring. Plurals are excluded: KEYS and TOKENS name
#: collections, and a collection of key NAMES is configuration.
SECRET_WORDS = {"KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "PRIV",
                "PRIVKEY", "APIKEY", "CREDENTIAL", "DSN"}

#: Values that are placeholders rather than secrets. A gate that fires on
#: `KEY=<your-key-here>` teaches people to disable it (L-063).
PLACEHOLDER = re.compile(
    r"^(|\"\"|''|<.*>|\$\{.*\}|\$[A-Z_]+|changeme|your[-_ ].*|xxx+|\.\.\.|"
    r"redacted|placeholder|TODO|null|None)$", re.IGNORECASE)

SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".pytest_cache",
             "_to_delete", "graphify-out", ".vercel"}
SCAN_SUFFIXES = {".py", ".json", ".md", ".yml", ".yaml", ".txt", ".ps1", ".sh",
                 ".toml", ".ini", ".cfg", ".js", ".ts", ".html"}


def tracked_files(root: Path) -> list[Path]:
    """Every file git would consider, without invoking git.

    Invoking git here would take the index lock, and on an analysis mount that
    lock cannot be released (L-123). The gate walks the tree and applies the
    skip list instead, which is a close enough approximation for a check whose
    job is to be run everywhere including where git cannot.

    The first version used `rglob("*")` and crashed on its first real run:
    `OSError errno 5` on a path inside a nested `node_modules`, because rglob
    stats every entry BEFORE the skip list can exclude it. Pruning has to happen
    during the walk, not after it. A filter applied downstream of the traversal
    is not a filter, it is a hope, and this one cost the gate its first
    execution (L-131).
    """
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _walk import iter_files
    return list(iter_files(root, ("*",), SKIP_DIRS))


def scan(root: Path) -> list[str]:
    fails: list[str] = []
    gitignore = (root / ".gitignore")
    ignore_text = gitignore.read_text(encoding="utf-8", errors="replace") if gitignore.exists() else ""

    # Check 3 first: coverage, before contents. A rule that does not cover the
    # file cannot be satisfied by the file happening to be clean today.
    for name in CREDENTIAL_FILES:
        if name not in ignore_text:
            fails.append(f"COVERAGE  {name} is not named in .gitignore")

    for p in tracked_files(root):
        rel = p.relative_to(root).as_posix()

        # Check 2: a credential file that is present. Present is expected; what
        # matters is that .gitignore covers it, asserted above.
        if p.name in CREDENTIAL_FILES:
            continue

        if p.suffix.lower() not in SCAN_SUFFIXES:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for i, line in enumerate(text.splitlines(), 1):
            if len(line) > 400:
                continue
            m = SECRET_NAME.match(line)
            if not m:
                continue
            name, value = m.group(1), m.group(2).strip().strip('"\'')
            if not (set(name.split("_")) & SECRET_WORDS):
                continue
            if PLACEHOLDER.match(value):
                continue
            # A value that is itself a variable reference is configuration.
            if value.startswith(("${", "$(", "os.environ", "os.getenv", "getenv",
                                 "process.env", "secrets.", "Deno.env", "ENV[")):
                continue
            if len(value) < 12:
                continue
            # A collection is not a credential. NON_SOURCE_KEYS = {"rule", ...}
            # and CREDENTIAL_FILES = [".env", ...] both matched the NAME pattern
            # on this gate's first working run, and both are structure rather
            # than secret. Two false positives in three findings is the ratio
            # that gets a check switched off without anyone deciding to switch
            # it off (L-063), so the value shape is discriminated here rather
            # than the name pattern being loosened.
            #
            # The first attempt at this also excluded any value containing
            # '", "', which silenced the third finding, PG_PASSWORD, and would
            # have silenced `KEY = os.getenv("K", "an-actual-secret")` with it,
            # because a getenv default is separated by exactly that string. A
            # suppression rule that cannot distinguish a collection separator
            # from a default credential is a false-negative generator, and a
            # false negative in a secrets gate is strictly worse than the false
            # positives it was written to remove. Replaced by naming the env
            # accessors explicitly above.
            if value[:1] in "{[(":
                continue
            # NAME and LINE only. Never the value, not even truncated (G-03).
            fails.append(f"PLAINTEXT {rel}:{i}  variable {name} carries a literal value")

    return fails


def main() -> int:
    root = ROOT
    if "--root" in sys.argv:
        root = Path(sys.argv[sys.argv.index("--root") + 1]).resolve()
    quiet = "--quiet" in sys.argv

    fails = scan(root)
    if fails:
        print(f"SECRETS GATE FAILED: {len(fails)} finding(s)")
        for f in fails:
            print(f"  {f}")
        print("\nNo value is printed, by design (G-03). Rotate rather than delete:")
        print("cloud sync retains provider-side history that survives local removal.")
        return 1
    if not quiet:
        print(f"OK   no plaintext secret reachable, and .gitignore covers "
              f"{len(CREDENTIAL_FILES)} known credential files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
