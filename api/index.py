from pydantic import BaseModel
from typing import Optional, Dict, Any

class TelemetryPayload(BaseModel):
    event: str
    localHash: Optional[str] = "n/a"
    data: Optional[Dict[str, Any]] = {}
    ts: Optional[str] = None

@app.post("/api/telemetry")
async def receive_telemetry(payload: TelemetryPayload):
    try:
        print(f"[TELEMETRY_EVENT] Type: {payload.event} | Hash: {payload.localHash} | Data: {payload.data}")
        return {"status": "logged", "received": True}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 400