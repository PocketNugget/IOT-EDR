import os
import json
import time
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import paho.mqtt.client as mqtt

app = FastAPI(title="Smart Home EDR Core")

# Fully open CORS to allow remote browser React connections on local Pi 5 IP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("MQTT_PORT", 1883))

# Global Ecosystem RAM Architecture
inventory = {} # Stores latest contextual hardware state of each node
activity_logs = []

mqtt_client = mqtt.Client(client_id="fastapi_smarthome_backend")

def add_log(device_id, message, level="info"):
    global activity_logs
    # Throttle exactly identical repetitive logs to avoid spam
    if len(activity_logs) > 0:
        last_log = activity_logs[-1]
        if last_log["device_id"] == device_id and last_log["message"] == message:
            return
            
    log_entry = {
        "id": int(time.time() * 1000) + len(activity_logs),
        "timestamp": time.time(),
        "device_id": device_id,
        "message": message,
        "level": level # info, success, warning, error
    }
    activity_logs.append(log_entry)
    if len(activity_logs) > 500:
        activity_logs.pop(0)

def on_connect(client, userdata, flags, rc):
    print(f"Backend connected to Smart Home Broker (code {rc})")
    client.subscribe("home/telemetry/#")
    client.subscribe("edr/evaluation")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        if topic.startswith("home/telemetry/"):
            device_id = payload.get("device_id")
            
            # Handle hardware inventory registration dynamically
            if device_id not in inventory:
                inventory[device_id] = {
                    "device_type": payload.get("device_type", "unknown"),
                    "status": "ONLINE",
                    "metrics": payload,
                    "anomaly_score": 0.0,
                    "is_anomaly": 0
                }
                add_log(device_id, f"Node Registered dynamically in Mesh: Profile '{payload.get('device_type')}'", "info")
            
            # Track state changes for SOC Incident tracking
            old_status = inventory[device_id]["status"]
            new_status = payload.get("status", "ONLINE")
            
            if old_status != new_status:
                if new_status == "UPDATING":
                    add_log(device_id, "Initiated secure OTA Firmware Update sequence.", "info")
                elif new_status == "ATTACKING":
                    add_log(device_id, "Zero-Day/Lateral botnet footprint simulated!", "warning")
                elif new_status == "QUARANTINED":
                    add_log(device_id, "⚠️ ACTIVE ISOLATION PROTOCOL EFFECTIVE. Host restricted from LAN router.", "success")
                elif new_status == "ONLINE":
                    add_log(device_id, "Device metrics synchronized. Operation restored.", "success")
                    
            # Memory mapping
            inventory[device_id]["status"] = new_status
            inventory[device_id]["metrics"] = payload
            
        elif topic == "edr/evaluation":
            # EDR Scoring injection into main data structure
            device_id = payload.get("device_id")
            if device_id in inventory:
                inventory[device_id]["anomaly_score"] = payload.get("anomaly_score")
                inventory[device_id]["is_anomaly"] = payload.get("is_anomaly")
                
                if payload.get("is_anomaly") == 1:
                    score = payload.get("anomaly_score", 0)
                    add_log(device_id, f"Heuristic Threat Footprint Detected against profile. Score: {score:.3f}", "error")
                    
    except Exception as e:
        print(f"MQTT Backend Parse Error: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    """Starts the event bus binding"""
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
    device_id: str
    action: str

@app.get("/api/inventory")
async def get_inventory():
    return inventory
    
@app.get("/api/logs")
async def get_logs():
    return activity_logs

@app.post("/api/action")
async def trigger_action(req: ActionRequest):
    """
    Valid SOC defensive actions: quarantine (manual isolation), restore
    NOTE: 'attack' is intentionally excluded — use external attack_scripts/ instead.
    """
    valid_actions = ["quarantine", "restore"]
    if req.action not in valid_actions:
        return {"status": "error", "message": "Security Exception: Invalid or malicious command vector blocked."}
        
    control_payload = {"action": req.action}
    mqtt_client.publish(f"home/control/{req.device_id}", json.dumps(control_payload))
    return {"status": "success", "message": f"[SOC] Action '{req.action}' dispatched to {req.device_id}"}



@app.websocket("/ws/soc_feed")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Package complete holistic network matrix
            package = {
                "inventory": inventory,
                "logs": activity_logs[-40:] # Stream tail context directly to UI securely
            }
            await websocket.send_json(package)
            await asyncio.sleep(1) 
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Exception pipeline: {e}")
