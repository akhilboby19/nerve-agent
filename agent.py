import time
import json
import psutil # You might need: sudo apt install python3-psutil
import socket
from datetime import datetime

def get_system_metrics():
    # 1. CPU Load
    cpu_usage = psutil.cpu_percent(interval=1)
    
    # 2. RAM Usage
    memory = psutil.virtual_memory()
    ram_usage = memory.percent
    
    # 3. Disk Usage (Root)
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    
    # 4. Network Traffic (Bytes Sent/Recv)
    net = psutil.net_io_counters()

    boot_time_raw = psutil.boot_time()
    boot_time = datetime.fromtimestamp(boot_time_raw).isoformat()
    
    payload = {
        "boot_time": boot_time,
        "hostname": socket.gethostname(),
        "timestamp": datetime.now().isoformat(),
        "cpu": cpu_usage,
        "ram": ram_usage,
        "disk": disk_usage,
        "net_sent_mb": round(net.bytes_sent / (1024 * 1024), 2),
        "net_recv_mb": round(net.bytes_recv / (1024 * 1024), 2)
    }
    return payload

print("--- NERVE AGENT STARTED ---")
try:
    while True:
        data = get_system_metrics()
        print(json.dumps(data, indent=2)) 
        # Later, we will send this to a Go backend or React frontend
        time.sleep(2) 
except KeyboardInterrupt:
    print("\nStopping Agent...")