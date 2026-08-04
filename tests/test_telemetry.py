from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_telemetry_endpoint():
    resp = client.post("/api/telemetry", json={"event":"unit_test","localHash":"sha:ut","data":{"foo":"bar"}})
    assert resp.status_code == 200
    assert resp.json().get("status") == "logged"

