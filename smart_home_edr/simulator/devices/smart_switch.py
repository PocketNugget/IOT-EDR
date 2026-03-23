import random
import numpy as np
from .base_device import BaseDevice

class SmartSwitch(BaseDevice):
    def __init__(self, device_id):
        super().__init__(device_id, "switch")
        
    def _generate_telemetry(self):
        payload = super()._generate_telemetry()
        if self.is_quarantined: return payload
        
        if self.state == "ONLINE":
            # Short bursts: Usually near 0, sometimes spikes simulating a physical on/off trigger via app
            is_active = random.random() < 0.1
            payload["bytes_in"] = int(np.random.normal(100, 20)) if is_active else int(np.random.normal(10, 2))
            payload["bytes_out"] = int(np.random.normal(150, 30)) if is_active else int(np.random.normal(15, 3))
            payload["port"] = 8080
            payload["packet_rate"] = np.random.poisson(lam=15 if is_active else 1)
            
        elif self.state == "UPDATING":
            # Scheduled OTA update
            payload["bytes_in"] = int(np.random.normal(12000, 1000))
            payload["bytes_out"] = int(np.random.normal(400, 40))
            payload["port"] = 443
            payload["packet_rate"] = np.random.poisson(lam=80)
            
        elif self.state == "ATTACKING":
            # Bruteforce / HTTP scanning
            payload["bytes_in"] = int(np.random.exponential(1000))
            payload["bytes_out"] = int(np.random.exponential(35000)) + 10000
            payload["port"] = random.choice([23, 2323, 80]) # Telnet/HTTP legacy scanning ports
            payload["packet_rate"] = np.random.poisson(lam=600)
            
        payload["bytes_in"] = max(0, payload["bytes_in"])
        payload["bytes_out"] = max(0, payload["bytes_out"])
        return payload
