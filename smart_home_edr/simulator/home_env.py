import os
import asyncio
import json
import random
import time
import numpy as np
import paho.mqtt.client as mqtt

BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("MQTT_PORT", 1883))


# ─────────────────────────────────────────────
#  BASE DEVICE
# ─────────────────────────────────────────────
class SmartDevice:
    def __init__(self, device_id, device_type, mqtt_client):
        self.device_id = device_id
        self.device_type = device_type
        self.client = mqtt_client
        self.status = "OFF"          # Physical power state
        self.attack_mode = False
        self.ota_mode = False

        # Subscribe to control commands
        self.client.subscribe(f"home/control/{self.device_id}")

    def handle_command(self, action):
        if action == "quarantine":
            self.status = "QUARANTINED"
            self.attack_mode = False
        elif action == "restore":
            self.status = "OFF"      # Goes back to normal off state
            self.attack_mode = False
            self.ota_mode = False
        elif action == "attack":
            if self.status != "QUARANTINED":
                self.attack_mode = True
                self.status = "ATTACKING"
        elif action == "ota":
            if self.status not in ("QUARANTINED", "ATTACKING"):
                self.ota_mode = True
                self.status = "UPDATING"

    def publish_telemetry(self, bytes_in, bytes_out, port, packet_rate):
        payload = {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "status": self.status,
            "timestamp": time.time(),
            "bytes_in": int(bytes_in),
            "bytes_out": int(bytes_out),
            "port": port,
            "packet_rate": int(packet_rate),
        }
        self.client.publish(
            f"home/telemetry/{self.device_type}/{self.device_id}",
            json.dumps(payload)
        )

    async def run(self):
        raise NotImplementedError


# ─────────────────────────────────────────────
#  SMART BULB  (salón, cocina, cuarto1, cuarto2, baño, patio)
# ─────────────────────────────────────────────
class SmartBulb(SmartDevice):
    def __init__(self, device_id, mqtt_client):
        super().__init__(device_id, "bulb", mqtt_client)
        # Random initial power state
        self.status = random.choice(["ON", "OFF"])

    async def run(self):
        while True:
            await asyncio.sleep(random.uniform(4, 8))

            if self.status == "QUARANTINED":
                self.publish_telemetry(0, 0, 0, 0)
                continue

            # ── State transition: randomly toggle power ──
            if self.status in ("ON", "OFF") and not self.attack_mode and not self.ota_mode:
                if random.random() < 0.07:          # ~7% chance per tick to toggle
                    self.status = "OFF" if self.status == "ON" else "ON"

            # ── Telemetry per state ──
            if self.status == "OFF":
                # Periodic heartbeat even when off (standby)
                self.publish_telemetry(
                    bytes_in=random.randint(0, 5),
                    bytes_out=random.randint(0, 5),
                    port=80,
                    packet_rate=0
                )

            elif self.status == "ON":
                # Light on: regular MDNS / hub pings
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(50, 10))),
                    bytes_out=max(0, int(np.random.normal(20, 5))),
                    port=80,
                    packet_rate=max(0, int(np.random.poisson(2)))
                )

            elif self.status == "UPDATING":
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(15000, 2000))),
                    bytes_out=max(0, int(np.random.normal(500, 50))),
                    port=443,
                    packet_rate=max(0, int(np.random.poisson(100)))
                )
                if random.random() < 0.15:
                    self.status = "ON"
                    self.ota_mode = False

            elif self.status == "ATTACKING":
                # DDoS / port scan
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(200, 30))),
                    bytes_out=max(0, int(np.random.normal(50000, 5000))),
                    port=random.randint(1, 65535),
                    packet_rate=max(0, int(np.random.poisson(500)))
                )


# ─────────────────────────────────────────────
#  SMART SWITCH
# ─────────────────────────────────────────────
class SmartSwitch(SmartDevice):
    def __init__(self, device_id, mqtt_client):
        super().__init__(device_id, "switch", mqtt_client)
        self.status = "OFF"

    async def run(self):
        while True:
            await asyncio.sleep(random.uniform(3, 7))

            if self.status == "QUARANTINED":
                self.publish_telemetry(0, 0, 0, 0)
                continue

            if self.status in ("ON", "OFF") and not self.attack_mode and not self.ota_mode:
                if random.random() < 0.12:
                    if self.status == "OFF":
                        self.status = "ON"
                        # Burst on switch event
                        self.publish_telemetry(
                            bytes_in=max(0, int(np.random.normal(100, 20))),
                            bytes_out=max(0, int(np.random.normal(150, 30))),
                            port=8080,
                            packet_rate=max(0, int(np.random.poisson(15)))
                        )
                    else:
                        self.status = "OFF"

            if self.status == "OFF":
                self.publish_telemetry(
                    bytes_in=random.randint(0, 5),
                    bytes_out=random.randint(0, 5),
                    port=8080,
                    packet_rate=0
                )
            elif self.status == "ON":
                is_active = random.random() < 0.2
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(100 if is_active else 5, 10))),
                    bytes_out=max(0, int(np.random.normal(150 if is_active else 8, 15))),
                    port=8080,
                    packet_rate=max(0, int(np.random.poisson(15 if is_active else 1)))
                )
            elif self.status == "UPDATING":
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(12000, 1000))),
                    bytes_out=max(0, int(np.random.normal(400, 40))),
                    port=443,
                    packet_rate=max(0, int(np.random.poisson(80)))
                )
                if random.random() < 0.15:
                    self.status = "ON"
                    self.ota_mode = False
            elif self.status == "ATTACKING":
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(300, 50))),
                    bytes_out=max(0, int(np.random.normal(3000, 500))),
                    port=random.randint(1, 65535),
                    packet_rate=max(0, int(np.random.poisson(200)))
                )


# ─────────────────────────────────────────────
#  SMART HUB  (coordinador central)
# ─────────────────────────────────────────────
class SmartHub(SmartDevice):
    def __init__(self, device_id, mqtt_client):
        super().__init__(device_id, "hub", mqtt_client)
        self.status = "ON"   # Hub is always-on

    async def run(self):
        while True:
            await asyncio.sleep(random.uniform(2, 4))

            if self.status == "QUARANTINED":
                self.publish_telemetry(0, 0, 0, 0)
                continue

            if self.status == "ON":
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(2000, 300))),
                    bytes_out=max(0, int(np.random.normal(3500, 500))),
                    port=8443,
                    packet_rate=max(0, int(np.random.poisson(45)))
                )
            elif self.status == "UPDATING":
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(30000, 5000))),
                    bytes_out=max(0, int(np.random.normal(2000, 200))),
                    port=443,
                    packet_rate=max(0, int(np.random.poisson(250)))
                )
                if random.random() < 0.12:
                    self.status = "ON"
                    self.ota_mode = False
            elif self.status == "ATTACKING":
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(5000, 800))),
                    bytes_out=max(0, int(np.random.normal(80000, 10000))),
                    port=random.randint(1, 65535),
                    packet_rate=max(0, int(np.random.poisson(900)))
                )


# ─────────────────────────────────────────────
#  ROBOT VACUUM  (Roomba-style)
# ─────────────────────────────────────────────
class RobotVacuum(SmartDevice):
    """
    States:
      CHARGING - Docked, minimal network traffic.
      CLEANING - Actively mapping room: sends high-bandwidth LiDAR/sensor data.
      QUARANTINED / ATTACKING - modeled same as others.
    """
    def __init__(self, device_id, mqtt_client):
        super().__init__(device_id, "roomba", mqtt_client)
        self.status = "CHARGING"
        self._cleaning_ticks = 0

    async def run(self):
        while True:
            await asyncio.sleep(random.uniform(3, 6))

            if self.status == "QUARANTINED":
                self.publish_telemetry(0, 0, 0, 0)
                continue

            # State machine: CHARGING → CLEANING → CHARGING
            if self.status == "CHARGING" and not self.attack_mode:
                if random.random() < 0.04:     # ~4% per tick → starts a cleaning cycle
                    self.status = "CLEANING"
                    self._cleaning_ticks = 0
                # Heartbeat while docked
                self.publish_telemetry(
                    bytes_in=random.randint(0, 10),
                    bytes_out=random.randint(0, 10),
                    port=443,
                    packet_rate=0
                )

            elif self.status == "CLEANING":
                self._cleaning_ticks += 1
                # High-bandwidth LiDAR + map upload to hub
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(8000, 1000))),
                    bytes_out=max(0, int(np.random.normal(12000, 2000))),
                    port=443,
                    packet_rate=max(0, int(np.random.poisson(80)))
                )
                if self._cleaning_ticks > 20 or random.random() < 0.05:
                    self.status = "CHARGING"    # Done cleaning

            elif self.status == "ATTACKING":
                # Camera hijack: constant stream out
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(500, 50))),
                    bytes_out=max(0, int(np.random.normal(120000, 20000))),
                    port=random.randint(1, 65535),
                    packet_rate=max(0, int(np.random.poisson(1200)))
                )


# ─────────────────────────────────────────────
#  SPRINKLER SYSTEM
# ─────────────────────────────────────────────
class SprinklerSystem(SmartDevice):
    """
    States:
      IDLE    - Sends ping once a minute for weather API polling.
      WATERING - Short burst of HTTPS requests (weather + zone control).
    """
    def __init__(self, device_id, mqtt_client):
        super().__init__(device_id, "sprinkler", mqtt_client)
        self.status = "IDLE"
        self._watering_ticks = 0

    async def run(self):
        while True:
            await asyncio.sleep(random.uniform(5, 10))

            if self.status == "QUARANTINED":
                self.publish_telemetry(0, 0, 0, 0)
                continue

            if self.status == "IDLE" and not self.attack_mode:
                if random.random() < 0.03:
                    self.status = "WATERING"
                    self._watering_ticks = 0
                # Cold ping: weather API heartbeat
                self.publish_telemetry(
                    bytes_in=random.randint(0, 20),
                    bytes_out=random.randint(0, 10),
                    port=443,
                    packet_rate=0
                )

            elif self.status == "WATERING":
                self._watering_ticks += 1
                # HTTPS bursts to weather + irrigation controller
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(3000, 400))),
                    bytes_out=max(0, int(np.random.normal(800, 100))),
                    port=443,
                    packet_rate=max(0, int(np.random.poisson(30)))
                )
                if self._watering_ticks > 10 or random.random() < 0.08:
                    self.status = "IDLE"

            elif self.status == "ATTACKING":
                self.publish_telemetry(
                    bytes_in=max(0, int(np.random.normal(400, 80))),
                    bytes_out=max(0, int(np.random.normal(40000, 5000))),
                    port=random.randint(1, 65535),
                    packet_rate=max(0, int(np.random.poisson(400)))
                )


# ─────────────────────────────────────────────
#  MQTT MESSAGE ROUTER
# ─────────────────────────────────────────────
device_registry: dict[str, SmartDevice] = {}

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        action = payload.get("action")
        # Extract device_id from topic: home/control/<device_id>
        device_id = msg.topic.split("/")[-1]
        if device_id in device_registry:
            device_registry[device_id].handle_command(action)
    except Exception as e:
        print(f"Control parse error: {e}")

def on_connect(client, userdata, flags, rc):
    print(f"Simulator connected to Eclipse Mosquitto (code {rc})")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
async def main():
    client = mqtt.Client(client_id="smart_home_simulator")
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(BROKER, PORT, 60)
            break
        except Exception:
            print("Waiting for Mosquitto broker...")
            await asyncio.sleep(2)

    client.loop_start()
    await asyncio.sleep(1)

    # ── Define the full smart home ecosystem ──
    devices: list[SmartDevice] = [
        # Bulbs — multi-zone
        SmartBulb("bulb_living_room",  client),
        SmartBulb("bulb_kitchen",      client),
        SmartBulb("bulb_bedroom1",     client),
        SmartBulb("bulb_bedroom2",     client),
        SmartBulb("bulb_bathroom",     client),
        SmartBulb("bulb_porch",        client),
        # Switches
        SmartSwitch("switch_main_door",  client),
        SmartSwitch("switch_garage",     client),
        # Hub
        SmartHub("hub_central", client),
        # Robot Vacuum
        RobotVacuum("roomba_main", client),
        # Sprinkler
        SprinklerSystem("sprinkler_garden", client),
    ]

    # Build global registry for control routing
    for d in devices:
        device_registry[d.device_id] = d

    print(f"🚀 Smart Home Multi-Node Simulator Started! ({len(devices)} devices online)")

    # Run all devices concurrently
    await asyncio.gather(*[d.run() for d in devices])


if __name__ == "__main__":
    asyncio.run(main())
