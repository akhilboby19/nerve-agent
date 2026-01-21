import time
import json
import psutil # You might need: sudo apt install python3-psutil
import socket
from datetime import datetime

class Agent:
    def __init__(self, interval=2):
        self.interval = interval
        self.prev_net=None

    def get_system_metrics(self):
        # 1. CPU Load
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 2. RAM Usage
        memory = psutil.virtual_memory()
        ram_usage = memory.percent
        
        # 3. Disk Usage (Root)
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # 4. Network Traffic (Bytes Sent/Recv)
        current_net = psutil.net_io_counters()

        if self.prev_net == None:
            self.prev_net = current_net
            
        bytes_sent = current_net.bytes_sent - self.prev_net.bytes_sent
        bytes_recv = current_net.bytes_recv - self.prev_net.bytes_recv

        self.prev_net = current_net


        # 5. Boot time
        boot_time_raw = psutil.boot_time()
        boot_time = datetime.fromtimestamp(boot_time_raw).isoformat()
        
        payload = {
            "boot_time": boot_time,
            "hostname": socket.gethostname(),
            "timestamp": datetime.now().isoformat(),
            "cpu": cpu_usage,
            "ram": ram_usage,
            "disk": disk_usage,
            "net_sent_mb": round(bytes_sent / (1024 * 1024), 2),
            "net_recv_mb": round(bytes_recv / (1024 * 1024), 2)
        }
        return payload

    def run_agent(self):

        print("--- NERVE AGENT STARTED ---")
        try:
            while True:
                data = self.get_system_metrics()
                print(json.dumps(data, indent=2)) 
                # Later, we will send this to a Go backend or React frontend
                time.sleep(self.interval) 
        except KeyboardInterrupt:
            print("\nStopping Agent...")


    def main(self):
        self.run_agent()


if __name__ == "__main__":
    agent = Agent(interval=2)
    agent.main()