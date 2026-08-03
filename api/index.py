from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

# Instantiate FastAPI app so the serverless/ASGI environment picks it up
app = FastAPI()
logger = logging.getLogger("uvicorn.error")

class TelemetryPayload(BaseModel):
    event: str
    localHash: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    ts: Optional[str] = None

@app.post("/api/telemetry")
async def receive_telemetry(payload: TelemetryPayload):
    try:
        # Structured logging for easier ingestion
        logger.info(
            "[TELEMETRY_EVENT] event=%s localHash=%s data=%s ts=%s",
            payload.event,
            payload.localHash,
            payload.data,
            payload.ts,
        )
        # TODO: enqueue/persist to analytics store asynchronously
        return JSONResponse(content={"status": "logged", "received": True}, status_code=200)
    except Exception:
        logger.exception("Failed to process telemetry payload")
        raise HTTPException(status_code=500, detail="telemetry processing failed")
