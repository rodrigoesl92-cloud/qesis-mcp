# qesis-mcp: fsQCA API wrapper (Phase 2)
# Usage: register the blueprint in your Flask/FastAPI app

import os
import json
import subprocess
import tempfile
import uuid
import base64
from datetime import datetime
from flask import Blueprint, request, jsonify

# cryptography for Ed25519 signing
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

bp = Blueprint("fsqca", __name__)

# Environment variable that holds base64-encoded Ed25519 private key (32 bytes)
FSQCA_PRIV_ENV = os.environ.get("FSQCA_ED25519_PRIV_B64", None)

# Load private key if available
_priv_key = None
if FSQCA_PRIV_ENV:
    try:
        raw = base64.b64decode(FSQCA_PRIV_ENV)
        _priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(raw)
    except Exception:
        _priv_key = None


def sign_step(step_dict):
    """Sign a step dict using Ed25519 if a private key is available.
    The function returns the original step dict augmented with signer and signature fields.
    """
    step = dict(step_dict)
    step.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
    if _priv_key is None:
        step["signer"] = None
        step["signature"] = None
        return step
    payload = json.dumps(step, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = _priv_key.sign(payload)
    step["signer"] = "ed25519:private-key"
    step["signature"] = base64.b64encode(sig).decode("ascii")
    return step


@bp.route("/api/fsqca", methods=["POST"])
def run_fsqca():
    """Run an fsQCA job synchronously via Rscript.

    Expected payload JSON shape:
    {
      "cases": [ {"case": "A", "OUTCOME": 1, "C1": 1, "C2": 0}, ... ],
      "config": { "outcome": "OUTCOME", "conditions": ["C1","C2"], "incl.cut": 0.5, "mode": "crisp" },
      "sources": [ {"url": "https://...", "checksum": "..."}, ... ]
    }

    Returns JSON with solutions, diagnostics and provenance fields attached.
    """
    payload = request.get_json(force=True)
    if payload is None:
        return jsonify({"error": "invalid json"}), 400

    # Basic validation
    if "cases" not in payload or "config" not in payload:
        return jsonify({"error": "missing 'cases' or 'config'"}), 400

    job_id = str(uuid.uuid4())
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        fname = f.name

    # Build Rscript command (scripts/run_fsqca.R expected at repo root)
    rscript_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "run_fsqca.R")
    rscript_path = os.path.normpath(rscript_path)
    cmd = ["Rscript", rscript_path, fname, job_id]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return jsonify({"error": "Rscript not found in PATH"}), 500

    if proc.returncode != 0:
        # Return stderr for diagnostics while protecting secrets
        return jsonify({
            "job_id": job_id,
            "status": "error",
            "stderr": proc.stderr
        }), 500

    try:
        result = json.loads(proc.stdout)
    except Exception:
        return jsonify({"job_id": job_id, "status": "error", "error": "invalid JSON from Rscript", "stdout": proc.stdout}), 500

    # Attach provenance fields
    step = {
        "step": "run_fsqca",
        "tool": "Rscript/QCA",
        "job_id": job_id,
        "rscript_path": rscript_path
    }
    signed = sign_step(step)

    if "chain" not in result:
        result["chain"] = []
    result["chain"].append(signed)

    # citation_concordance from payload.sources if present
    result.setdefault("citation_concordance", [])
    if isinstance(payload.get("sources"), list):
        result["citation_concordance"].extend(payload.get("sources"))

    return jsonify(result)
