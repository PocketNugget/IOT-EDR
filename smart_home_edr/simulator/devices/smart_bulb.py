import random
import numpy as np
from .base_device import BaseDevice

class SmartBulb(BaseDevice):
    def __init__(self, device_id):
        super().__init__(device_id, "bulb")
        
    def _generate_telemetry(self):
        payload = super()._generate_telemetry()
        if self.is_quarantined: return payload
        
        if self.state == "ONLINE":
            # Low traffic: State heartbeats and occasional commands
            payload["bytes_in"] = int(np.random.normal(loc=50, scale=10))
            payload["bytes_out"] = int(np.random.normal(loc=20, scale=5))
            payload["port"] = 80 # internal generic IoT port
            payload["packet_rate"] = np.random.poisson(lam=2)
            
        elif self.state == "UPDATING":
            # High traffic, port 443 (HTTPS secure firmware download footprint)
            payload["bytes_in"] = int(np.random.normal(loc=15000, scale=2000))
            payload["bytes_out"] = int(np.random.normal(loc=500, scale=50))
            payload["port"] = 443
            payload["packet_rate"] = np.random.poisson(lam=100)
            
        elif self.state == "ATTACKING":
            # Massive outgoing scanning/DDoS to random ports (Mirai / Scanner)
            payload["bytes_in"] = int(np.random.normal(loc=100, scale=20))
            payload["bytes_out"] = int(np.random.exponential(scale=20000)) + 5000
            payload["port"] = random.randint(1024, 65535) # Anomalous signature
            payload["packet_rate"] = np.random.poisson(lam=400)
            
        payload["bytes_in"] = max(0, payload["bytes_in"])
        payload["bytes_out"] = max(0, payload["bytes_out"])
        return payload
