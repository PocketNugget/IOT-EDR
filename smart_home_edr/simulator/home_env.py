import os
import json
import asyncio
import paho.mqtt.client as mqtt

from devices.smart_bulb import SmartBulb
from devices.smart_switch import SmartSwitch
from devices.smart_hub import SmartHub

BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("MQTT_PORT", 1883))

devices = [
    SmartBulb("bulb_living_room"),
    SmartBulb("bulb_kitchen"),
    SmartSwitch("switch_main_door"),
    SmartSwitch("switch_kitchen"),
    SmartHub("hub_central")
]

device_map = {d.device_id: d for d in devices}

def on_connect(client, userdata, flags, rc):
    print(f"Simulator connected to Eclipse Mosquitto (code {rc})")
    client.subscribe("home/control/#")
    
def on_message(client, userdata, msg):
    try:
        topic_parts = msg.topic.split("/")
        # format: home/control/<device_id>
        if len(topic_parts) == 3 and topic_parts[1] == "control":
            target_id = topic_parts[2]
            payload = json.loads(msg.payload.decode())
            action = payload.get("action")
            
            if target_id in device_map:
                device = device_map[target_id]
                if action == "quarantine":
                    device.set_quarantine(True)
                elif action == "restore":
                    device.set_quarantine(False)
                elif action == "attack":
                    device.trigger_attack()
                elif action == "ota":
                    device.trigger_ota()
    except Exception as e:
        print(f"Error handling edge control command: {e}")

async def run_simulator():
    client = mqtt.Client(client_id="smart_home_simulator")
    client.on_connect = on_connect
    client.on_message = on_message
    
    while True:
        try:
            client.connect(BROKER, PORT, 60)
            break
        except Exception:
            print("Simulator waiting for broker mesh...")
            await asyncio.sleep(2)
            
    client.loop_start()
    print("🚀 Smart Home Multi-Node Simulator Started!")
    
    # Run all node environments concurrently
    tasks = [d.run(client) for d in devices]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(run_simulator())
