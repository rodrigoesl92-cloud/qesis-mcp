
## BACK_LOG & Compliance Incident Ledger Update (2026-08-02)
* **INC-20260731-01/A2**: Cloud-sync provider-side credential retention mitigated; secret keys strictly purged from sync paths and enforced via .gitignore.
* **D-103 (fsQCA)**: fsQCA pipeline re-staged under v8.5; reproducibility verified against clean environment inputs.
* **ISO/IEC 42001 A.4.5 (Resource Management)**: Ollama service purged from local docker-compose.yml to respect the 5.8 GB RAM hardware ceiling and eliminate Out-Of-Memory (OOM) risks.
* **EU AI Act Article 12 (Audit Trails)**: Cryptographic hash chain logging and qesis_get_integrity endpoint fully integrated and test-gated.
* **EN 18286 (QMS)**: Build artifacts, metadata lineage, and citation concordances locked under verifiable state controls.
