# CI last failure

**Repository:** `rodrigoesl92-cloud/sovereign-infra`  
**Branch:** `fix/land-20260824-consolidated`  
**Workflow:** QESIS+ integrity gate  
**Run:** 32763266581, concluded **failure**  
**Captured:** 2026-08-24T18:35:52+00:00

This file is written by `scripts/ci_feedback.py` and committed, so the next session reads the real reason from the repository instead of inferring it from a local run in a different environment. D-115: query the resource, never a proxy for it.

**Root-caused 2026-08-24 evening:** L-170. `ECOSYSTEM_STATE.json` carried `repository`, the checkout name, and `--check` compared it. Fixed in `build_ecosystem_state.py` (the field is volatile; `--selftest` proves both halves). This file is overwritten by the next `ci_feedback.py --sha` run on the pushed commit.

## Failing log

```
qesis-integrity	The ecosystem bootstrap is not stale	﻿2026-08-24T18:35:24.6119782Z ##[group]Run python scripts/build_ecosystem_state.py --check
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6121336Z ^[[36;1mpython scripts/build_ecosystem_state.py --check^[[0m
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6161057Z shell: /usr/bin/bash -e {0}
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6161975Z env:
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6163221Z   pythonLocation: /opt/hostedtoolcache/Python/3.12.14/x64
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6164736Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.14/x64/lib/pkgconfig
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6166227Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.14/x64
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6167583Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.14/x64
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6168942Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.14/x64
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6170312Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.12.14/x64/lib
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.6171504Z ##[endgroup]
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.7564720Z   STALE  ECOSYSTEM_STATE.json disagrees with a fresh measurement
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.7567408Z ECOSYSTEM STATE CHECK FAILED
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.7569497Z   Regenerate with: python scripts/build_ecosystem_state.py
qesis-integrity	The ecosystem bootstrap is not stale	2026-08-24T18:35:24.7646538Z ##[error]Process completed with exit code 1.
```
