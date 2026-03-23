import time
import json
import asyncio

class BaseDevice:
    def __init__(self, device_id, device_type):
        self.device_id = device_id
        self.device_type = device_type
        self.state = "ONLINE" # ONLINE, QUARANTINED, UPDATING, ATTACKING
        self.is_quarantined = False
        
    def set_quarantine(self, active):
        self.is_quarantined = active
        if active:
            self.state = "QUARANTINED"
            print(f"[{self.device_id}] 🛑 Isolated from physical network interface.")
        else:
            self.state = "ONLINE"
            print(f"[{self.device_id}] 🟢 Quarantine lifted. Restored to ecosystem.")
            
    def trigger_attack(self):
        if not self.is_quarantined:
            self.state = "ATTACKING"
            print(f"[{self.device_id}] 💀 Zero-Day / Malware Infection Triggered!")
            
    def trigger_ota(self):
        if not self.is_quarantined:
            self.state = "UPDATING"
            print(f"[{self.device_id}] 🔄 Legitimate OTA Firmware Update Started!")
            # Reset after 15 seconds simulating successful OTA completion
            asyncio.create_task(self._finish_ota())
            
    async def _finish_ota(self):
        await asyncio.sleep(15)
        if self.state == "UPDATING":
            self.state = "ONLINE"
            print(f"[{self.device_id}] ✅ Valid OTA Firmware Update Completed.")

    async def run(self, mqtt_client):
        while True:
            payload = self._generate_telemetry()
            
            if payload:
                topic = f"home/telemetry/{self.device_type}/{self.device_id}"
                mqtt_client.publish(topic, json.dumps(payload))
                
            await asyncio.sleep(1) # Base 1Hz clock tick per IoT node
            
    def _generate_telemetry(self):
        payload = {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "status": self.state,
            "timestamp": time.time(),
            "bytes_in": 0,
            "bytes_out": 0,
            "port": 0,
            "packet_rate": 0
        }
        
        if self.is_quarantined:
            # Emits only secure status heartbeat, zero internal network metrics
            return payload

        # To be overridden by subclasses
        return payload
