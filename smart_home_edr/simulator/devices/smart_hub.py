import random
import numpy as np
from .base_device import BaseDevice

class SmartHub(BaseDevice):
    def __init__(self, device_id):
        super().__init__(device_id, "hub")
        
    def _generate_telemetry(self):
        payload = super()._generate_telemetry()
        if self.is_quarantined: return payload
        
        if self.state == "ONLINE":
            # Constant heavy traffic coordinating other edge nodes over TLS/ZigBee bridging
            payload["bytes_in"] = int(np.random.normal(2000, 300))
            payload["bytes_out"] = int(np.random.normal(3500, 500))
            payload["port"] = 8443 # Default secure cluster port
            payload["packet_rate"] = np.random.poisson(lam=45)
            
        elif self.state == "UPDATING":
            # Heavy operating system OTA download footprint
            payload["bytes_in"] = int(np.random.normal(30000, 5000))
            payload["bytes_out"] = int(np.random.normal(2000, 200))
            payload["port"] = 443
            payload["packet_rate"] = np.random.poisson(lam=250)
            
        elif self.state == "ATTACKING":
            # Lateral movement within the deep network + Ransomware beaconing
            payload["bytes_in"] = int(np.random.normal(5000, 1000))
            payload["bytes_out"] = int(np.random.exponential(60000)) + 20000
            payload["port"] = random.randint(1024, 65535)
            payload["packet_rate"] = np.random.poisson(lam=800)
            
        payload["bytes_in"] = max(0, payload["bytes_in"])
        payload["bytes_out"] = max(0, payload["bytes_out"])
        return payload
