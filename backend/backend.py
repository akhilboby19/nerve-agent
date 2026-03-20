import logging
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import database # Assuming you created this from our previous step
from enum import Enum

# --- 1. CONFIGURATION (Do this once) ---
# This sets up a log format: [Time] [Level] Message
logging.basicConfig(
    level=logging.INFO, # Change to DEBUG to see everything
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("nerve_backend.log"), # Save to file
        logging.StreamHandler() # Also print to console
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
def startup():
    database.init_db()
    logger.info("Nerve Backend Initialized and DB connected.")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": str(exc)}
    )

class Metrics(BaseModel):
    agent_id: str
    hostname: str
    timestamp: str
    boot_time: str
    cpu: float
    ram: float
    disk: float
    net_sent_mb: float
    net_recv_mb: float

@app.post("/metrics")
def receive_metrics(data: Metrics):
    payload = data.dict()
    
    try:
        database.save_metric(payload)
        
        # --- 2. USAGE (Standard levels) ---
        # INFO: Routine events (Alive)
        logger.info(f"Pulse received from {payload['hostname']}")
        
        # DEBUG: Dev details (Hidden in production)
        logger.debug(f"Payload details: {payload}")
        
    except Exception as e:
        # ERROR: Something broke (Alerts)
        logger.error(f"Failed to save metric: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

    return {"status": "ok"}



# --- DASHBOARD ENDPOINT 1 — Agent list ---
# GET /agents
# Returns all known agents, their hostname, last seen time, and online/offline status.
 
@app.get("/agents")
def list_agents():
    agents = database.get_all_agents()
    return agents
 
 
# --- DASHBOARD ENDPOINT 2 — Latest snapshot ---
# GET /metrics/{agent_id}/latest
# Returns the single most recent metric row for a given agent.
# Used for the current-value stat cards on the dashboard (not graphs).
 
@app.get("/metrics/{agent_id}/latest")
def latest_metric(agent_id: str):
    row = database.get_latest_metric(agent_id)
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    return row


# --- DASHBOARD ENDPOINT 3 — Time series graph data ---
# GET /metrics/{agent_id}?range=1h&resolution=1m
#
# range options:      1h | 6h | 12h
# resolution options: 1m | 5m | 15m
#
# Returns averaged metric buckets for the requested time window.
# The frontend feeds this directly into charts.

class RangeOption(str, Enum):
    h1  = "1h"
    h6  = "6h"
    h12 = "12h"

class ResolutionOption(str, Enum):
    m1  = "1m"
    m5  = "5m"
    m15 = "15m"

@app.get("/metrics/{agent_id}")
def get_metrics(
    agent_id:   str,
    range:      RangeOption = Query(default=RangeOption.h1),
    resolution: ResolutionOption = Query(default=ResolutionOption.m1)
):
    rows = database.get_metrics(agent_id, range=range.value, resolution=resolution.value)
    if not rows:
        raise HTTPException(status_code=404, detail="No data found")
    return rows


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)