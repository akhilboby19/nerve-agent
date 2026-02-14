import logging
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import database # Assuming you created this from our previous step

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)