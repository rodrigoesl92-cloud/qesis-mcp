from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_telemetry_endpoint():
    r = client.post("/api/telemetry", json={"event":"ut","localHash":"sha:ut","data":{"a":"b"}})
    assert r.status_code == 200
    assert r.json()["status"] == "logged"