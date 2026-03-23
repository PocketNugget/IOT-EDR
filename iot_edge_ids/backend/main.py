import os
import json
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import paho.mqtt.client as mqtt

app = FastAPI(title="IoT Edge EDR API", description="Control Plane & Telemetry WebSocket for SoC Dashboard")

# Enable CORS fully to allow the standalone React Vite UI visualization
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("MQTT_PORT", 1883))

# In-memory transient caching of real-time MQTT payload for Fast-WebSocket distribution 
# (Bypassing direct InfluxDB polling for ultra-low latency dashboard UX)
latest_telemetry = {}

mqtt_client = mqtt.Client(client_id="fastapi_backend")

def on_connect(client, userdata, flags, rc):
    print(f"Backend connected to Broker (Code: {rc}). Syncing state streams.")
    client.subscribe("telemetry/#")
    client.subscribe("edr/evaluation")

def on_message(client, userdata, msg):
    global latest_telemetry
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        if topic.startswith("telemetry/"):
            sensor_id = payload.get("sensor_id")
            if sensor_id not in latest_telemetry:
                latest_telemetry[sensor_id] = {}
            latest_telemetry[sensor_id].update(payload)
            
        elif topic == "edr/evaluation":
            sensor_id = payload.get("sensor_id")
            if sensor_id in latest_telemetry:
                # Merge anomaly scoring back into main telemetry metrics map
                latest_telemetry[sensor_id]["anomaly_score"] = payload.get("anomaly_score")
                latest_telemetry[sensor_id]["is_anomaly"] = payload.get("is_anomaly")
    except Exception as e:
        print(f"MQTT Parsing Error in Backend Bus: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    """Connects to the event bus in the startup phase."""
    while True:
        try:
            mqtt_client.connect(BROKER, PORT, 60)
            break
        except Exception:
            time.sleep(2)
    mqtt_client.loop_start()

@app.on_event("startup")
async def startup_event():
    start_mqtt()

class ActionRequest(BaseModel):
    sensor_id: str

@app.post("/api/attack")
async def trigger_attack(req: ActionRequest):
    """Inyecta trafico ofensivo zero-day en el sensor especificado (Under Attack Mode)"""
    control_payload = {"action": "attack"}
    mqtt_client.publish(f"control/{req.sensor_id}", json.dumps(control_payload))
    return {"status": "success", "message": f"Zero-Day Simulation Escalated on {req.sensor_id}"}

@app.post("/api/restore")
async def restore_device(req: ActionRequest):
    """Levanta mitigaciones de cuarentena preventivas en el dispositivo IoT."""
    control_payload = {"action": "restore"}
    mqtt_client.publish(f"control/{req.sensor_id}", json.dumps(control_payload))
    return {"status": "success", "message": f"Quarantine Override Verified for {req.sensor_id}"}

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    """Multiplexa el backend en vivo (telemetría + anomalies combinados) al dashboard."""
    await websocket.accept()
    try:
        while True:
            # Transmit the most synchronized state map at ~1Hz frame-rate mapping requirement
            if latest_telemetry:
                await websocket.send_json(latest_telemetry)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Frontend WebSocket Connection Closed")
    except Exception as e:
        print(f"WebSocket Pipeline Error: {e}")
