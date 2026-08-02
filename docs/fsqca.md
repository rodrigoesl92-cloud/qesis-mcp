# docs/fsqca.md

fsQCA Engine (Phase 2)

Overview
--------
This module provides a synchronous fsQCA engine wrapped by a Python API endpoint. The engine uses R's QCA package via Rscript to ensure academically validated minimization and diagnostics. All results are emitted as JSON and include provenance fields required for EU AI Act traceability.

Requirements & Environment
--------------------------
- R (>=4.x) with the `QCA` package installed. Example (Debian/Ubuntu):
  - sudo apt-get install r-base
  - R -e "install.packages('QCA', repos='https://cloud.r-project.org')"
- Python dependencies for signing: see requirements-extra.txt (cryptography)
- Set the environment variable FSQCA_ED25519_PRIV_B64 to the base64-encoded 32-byte Ed25519 private key used to sign provenance entries.

API
---
POST /api/fsqca
Payload:
{
  "cases": [ {..}, .. ],
  "config": { "outcome": "OUTCOME", "conditions": [..], "incl.cut": 0.5, "mode": "crisp" },
  "sources": [ {"url": "...", "checksum":"..."}, ... ]
}

Response:
- On success: JSON including job_id, status: ok, solutions, truth_table, details, chain (signed step), citation_concordance.
- On error: JSON with status: error and message

Provenance & Signing
--------------------
The API attaches a `chain` entry for the run and signs it using Ed25519. The private key must be provisioned in FSQCA_ED25519_PRIV_B64. Third-party verifiers can verify signatures using the corresponding public key.

HOTL
----
This API is intentionally synchronous and does NOT auto-publish any DPPs or market artifacts. Upstream orchestration agents must route publishable artifacts to a staging area and call the explicit human-approval workflow before any final DPP publish.

