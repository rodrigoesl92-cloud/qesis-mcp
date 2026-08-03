# tests/test_fsqca_integration.py
import os
import json
import shutil
import subprocess
import tempfile
import pytest

R_AVAILABLE = shutil.which("Rscript") is not None

@pytest.mark.skipif(not R_AVAILABLE, reason="Rscript not installed on PATH")
def test_run_fsqca_rscript_basic():
    # prepare a minimal sample dataset with 4 cases and 2 conditions
    payload = {
        "cases": [
            {"case": "a", "OUT": 1, "C1": 1, "C2": 1},
            {"case": "b", "OUT": 1, "C1": 1, "C2": 0},
            {"case": "c", "OUT": 0, "C1": 0, "C2": 1},
            {"case": "d", "OUT": 0, "C1": 0, "C2": 0}
        ],
        "config": {"outcome": "OUT", "conditions": ["C1", "C2"], "incl.cut": 0.5, "mode": "crisp"},
        "sources": [{"url": "test://generated", "checksum": "none"}]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        fname = f.name

    job_id = "test-job-1"
    rscript = shutil.which("Rscript")
    rpath = os.path.join(os.path.dirname(__file__), "..", "scripts", "run_fsqca.R")
    rpath = os.path.normpath(rpath)
    cmd = [rscript, rpath, fname, job_id]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"Rscript failed: {proc.stderr}\n{proc.stdout}"
    out = json.loads(proc.stdout)
    assert out.get("job_id") == job_id
    assert out.get("status") == "ok"
    assert "solutions" in out

