from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

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
    # If you add 'gpu_temp: float' here later, the print loop below handles it automatically.

@app.post("/metrics")
def receive_metrics(data: Metrics):
    
    # We convert the Model to a Dictionary for dynamic processing
    payload = data.dict()
    
    # Header
    print(f"\n--- PULSE: {payload['hostname']} [{payload['timestamp'].split('T')[1][:8]}] ---")
    
    # Dynamic Loop: Iterates over whatever fields exist in the Model
    # We filter out the 'meta' fields we already printed in the header
    meta_keys = {"hostname", "timestamp", "agent_id", "boot_time"}
    
    for key, value in payload.items():
        if key not in meta_keys:
            # Simple formatting to align keys nicely
            print(f"  {key:<12}: {value}")

    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)