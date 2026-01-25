from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Metrics(BaseModel):
    agent_id: str
    hostname: str
    timestamp: str
    cpu: float
    ram: float
    disk: float
    net_sent_mb: float
    net_recv_mb: float

@app.post("/metrics")
def receive_metrics(data: Metrics):
    print("Received metrics:")
    print(data.dict())
    return {"status": "ok"}
