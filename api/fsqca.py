"""fsQCA job runner, exposed as ASGI.

Three defects are closed here.

1. It imported Flask. Flask is not in requirements.txt and never has been, so
   this module raised ImportError the moment anything touched it -- including
   Vercel, which treats every file under api/ as a function. Declaring a second
   web framework to run one endpoint was never worth it; this is Starlette, which
   is already a hard dependency of the MCP runtime.

2. It exposed a Flask blueprint named `bp` and nothing else. Vercel's Python
   runtime dispatches to `app` or `handler`. There was no entry point, so
   /api/fsqca could not have answered even with Flask installed.

3. It reported "Rscript not found in PATH" as HTTP 500. Vercel's Python runtime
   has no R toolchain and never will, so on every deployment this is a permanent
   and knowable condition, not a server fault. It answers 501 and says what is
   missing.

D-103 applies to anything produced here: an fsQCA result computed by this
endpoint is a job output, not a published figure, and does not lift the
withdrawal of the v8.5 fsQCA figures.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

ROOT = Path(__file__).resolve().parent.parent
RSCRIPT_PATH = ROOT / "scripts" / "run_fsqca.R"

# Signing is optional and its absence is reported rather than hidden. A step that
# comes back with signer=None is an unsigned step; a step that comes back with a
# plausible-looking signature field and nothing behind it is worse than no field.
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
except ImportError:  # pragma: no cover - exercised only on a stripped install
    ed25519 = None  # type: ignore[assignment]

_PRIV_B64 = os.environ.get("FSQCA_ED25519_PRIV_B64") or ""
_priv_key = None
_key_status = "no FSQCA_ED25519_PRIV_B64 in the environment"

if ed25519 is None:
    _key_status = "cryptography is not installed on this deployment"
elif _PRIV_B64:
    import base64
    try:
        _priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(
            base64.b64decode(_PRIV_B64))
        _key_status = "loaded"
    except Exception as exc:  # noqa: BLE001 - a bad key is a bad key
        _key_status = f"FSQCA_ED25519_PRIV_B64 did not load: {type(exc).__name__}"


def sign_step(step: dict) -> dict:
    """Sign a provenance step, or state plainly that it is unsigned."""
    out = dict(step)
    out.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    if _priv_key is None:
        out["signer"] = None
        out["signature"] = None
        out["signature_status"] = f"UNSIGNED: {_key_status}"
        return out
    import base64
    payload = json.dumps(out, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    out["signer"] = "ed25519"
    out["signature"] = base64.b64encode(_priv_key.sign(payload)).decode("ascii")
    out["signature_status"] = "signed"
    return out


async def run_fsqca(request: Request) -> JSONResponse:
    """Run an fsQCA job synchronously via Rscript.

    Payload:
      {"cases":   [{"case": "A", "OUTCOME": 1, "C1": 1, "C2": 0}, ...],
       "config":  {"outcome": "OUTCOME", "conditions": ["C1","C2"],
                   "incl.cut": 0.5, "mode": "crisp"},
       "sources": [{"url": "https://...", "checksum": "..."}, ...]}
    """
    rscript = shutil.which("Rscript")
    if rscript is None:
        return JSONResponse({
            "status": "unavailable",
            "error": "No R toolchain on this deployment.",
            "detail": ("This endpoint shells out to Rscript with scripts/run_fsqca.R. "
                       "The Vercel Python runtime does not ship R, so the capability "
                       "is absent here rather than broken. Run it locally, or move the "
                       "job to a runner that has R."),
        }, status_code=501)

    if not RSCRIPT_PATH.is_file():
        return JSONResponse({
            "status": "unavailable",
            "error": f"{RSCRIPT_PATH.relative_to(ROOT)} is not present in this build.",
        }, status_code=501)

    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"error": "invalid json"}, status_code=400)

    if not isinstance(payload, dict) or "cases" not in payload or "config" not in payload:
        return JSONResponse({"error": "missing 'cases' or 'config'"}, status_code=400)

    job_id = str(uuid.uuid4())
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         encoding="utf-8") as fh:
            json.dump(payload, fh)
            tmp = fh.name

        proc = subprocess.run([rscript, str(RSCRIPT_PATH), tmp, job_id],
                              capture_output=True, text=True, check=False,
                              timeout=120)
    except subprocess.TimeoutExpired:
        return JSONResponse({"job_id": job_id, "status": "error",
                             "error": "Rscript exceeded 120s"}, status_code=504)
    finally:
        if tmp:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    if proc.returncode != 0:
        return JSONResponse({"job_id": job_id, "status": "error",
                             "stderr": proc.stderr[-4000:]}, status_code=500)

    try:
        result = json.loads(proc.stdout)
    except ValueError:
        return JSONResponse({"job_id": job_id, "status": "error",
                             "error": "invalid JSON from Rscript",
                             "stdout": proc.stdout[:4000]}, status_code=500)

    result.setdefault("chain", []).append(sign_step({
        "step": "run_fsqca",
        "tool": "Rscript/QCA",
        "job_id": job_id,
        "rscript": str(RSCRIPT_PATH.relative_to(ROOT)),
    }))
    result.setdefault("citation_concordance", [])
    if isinstance(payload.get("sources"), list):
        result["citation_concordance"].extend(payload["sources"])
    result["publication_status"] = (
        "Job output only. Under D-103 the v8.5 fsQCA figures remain withdrawn; "
        "nothing computed here is a published result.")

    return JSONResponse(result)


app = Starlette(routes=[Route("/api/fsqca", run_fsqca, methods=["POST"])])
