"""One tree walker, imported by every gate that scans the repository.

WHY THIS IS A MODULE AND NOT A SNIPPET
    Three scripts had the same defect written three times:
    `verify_no_plaintext_secrets.py`, `verify_domains.py` and
    `verify_endpoints.py` each called `Path.rglob(...)` and then filtered the
    RESULTS against a skip list. `rglob` stats every entry before any downstream
    filter can exclude it, so an unreadable subtree is touched and the walk dies
    with `OSError errno 5` on a path the skip list was written to avoid.

    The secrets gate hit it on its first real run and was repaired in place
    (L-131). The other two were not, because nobody looked, and they carried the
    identical defect for as long as they have existed.

    L-048 is the rule: a gate is a module that callers import, never a block
    they copy. Copied checks drift, and the drift is invisible until the surface
    they guard is already wrong. Repairing this in three files would have been
    the same defect committed a fourth time, in the change set that fixed it.

WHAT IT GUARANTEES
    Pruning happens DURING traversal, in place, so an excluded directory is
    never descended into rather than being descended into and forgiven. An
    unreadable path is skipped rather than fatal, and the caller can ask how
    many were skipped rather than discovering silence.
"""
from __future__ import annotations

import fnmatch
import os
from pathlib import Path

#: Directories no repository gate should ever descend into. Shared, so adding
#: one here adds it everywhere rather than in whichever file someone remembered.
DEFAULT_SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".vercel", "_to_delete", "graphify-out", ".eve", "dist", "build",
}


def iter_files(root: Path, patterns=("*",), skip_dirs=None, skip_files=None):
    """Yield files under `root` matching any glob in `patterns`.

    Directories in `skip_dirs` are pruned during the walk, never filtered after
    it. Paths that cannot be stat'ed are skipped, because a broken snapshot
    symlink is not a finding and must not be fatal to a gate that has nothing to
    do with it.
    """
    skip_dirs = DEFAULT_SKIP_DIRS if skip_dirs is None else set(skip_dirs)
    skip_files = set(skip_files or ())
    pats = tuple(patterns)
    skipped = 0

    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
        # In place. os.walk honours mutation of dirnames and will not descend
        # into what is removed here.
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            if fn in skip_files:
                continue
            if not any(fnmatch.fnmatch(fn, p) for p in pats):
                continue
            p = Path(dirpath) / fn
            try:
                if p.is_file():
                    yield p
            except OSError:
                skipped += 1
                continue
    iter_files.last_skipped = skipped


iter_files.last_skipped = 0
