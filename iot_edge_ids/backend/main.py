import os
import time
import json
import asyncio
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import paho.mqtt.client as mqtt

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))

app = FastAPI(title="Edge EDR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global para enviar al frontend
# device_id -> { "telemetry": {...}, "score": {...} }
state = {}
alerts = []
state_lock = threading.Lock()

mqtt_client = mqtt.Client(client_id="fastapi_backend")

def on_connect(client, userdata, flags, rc):
    print(f"[Backend] Conectado a MQTT con código {rc}")
    client.subscribe("telemetry/#")
    client.subscribe("edr/scores/#")
    client.subscribe("alerts/critical")

def on_message(client, userdata, msg):
    global state, alerts
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode("utf-8"))
        
        with state_lock:
            if topic.startswith("telemetry/"):
                device_id = payload.get("device_id")
                if device_id not in state:
                    state[device_id] = {"telemetry": {}, "score": {}}
                state[device_id]["telemetry"] = payload
                
            elif topic.startswith("edr/scores/"):
                device_id = payload.get("device_id")
                if device_id not in state:
                    state[device_id] = {"telemetry": {}, "score": {}}
                state[device_id]["score"] = payload
                
            elif topic.startswith("alerts/critical"):
                alerts.append(payload)
                if len(alerts) > 50:
                    alerts.pop(0)

    except Exception as e:
        print(f"[Backend] Error processing msg: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

@app.on_event("startup")
def startup_event():
    # Iniciar cliente MQTT en background
    def run_mqtt():
        connected = False
        while not connected:
            try:
                mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
                connected = True
            except:
                time.sleep(2)
        mqtt_client.loop_forever()
        
    threading.Thread(target=run_mqtt, daemon=True).start()

@app.post("/api/attack/{device_id}")
async def trigger_attack(device_id: str):
    mqtt_client.publish(f"control/{device_id}", json.dumps({"action": "attack"}))
    return {"status": f"Attack initiated on {device_id}"}

@app.post("/api/restore/{device_id}")
async def trigger_restore(device_id: str):
    mqtt_client.publish(f"control/{device_id}", json.dumps({"action": "restore"}))
    return {"status": f"Restore initiated on {device_id}"}

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Envia una foto del estado actual a 1Hz para visualización fluida
            with state_lock:
                data = {
                    "devices": state,
                    "alerts": alerts
                }
            await websocket.send_json(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("[Backend] Cliente WS desconectado")
