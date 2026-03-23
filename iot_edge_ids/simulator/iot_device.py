import time
import json
import random
import numpy as np
import paho.mqtt.client as mqtt

# Configuration
BROKER = "mosquitto"
PORT = 1883
TELEMETRY_TOPIC = "telemetry/sensor_01"
CONTROL_TOPIC = "control/sensor_01"

state = "NORMAL"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to Mosquitto MQTT Broker with result code {rc}")
    client.subscribe(CONTROL_TOPIC)

def on_message(client, userdata, msg):
    global state
    try:
        payload = json.loads(msg.payload.decode())
        action = payload.get("action")
        if action == "quarantine":
            print("Received QUARANTINE command! Isolating apparatus.")
            state = "QUARANTINED"
        elif action == "restore":
            print("Received RESTORE command! Resuming normal operation.")
            state = "NORMAL"
        elif action == "attack":
            print("Triggering ZERO-DAY attack simulation!")
            state = "UNDER_ATTACK"
    except Exception as e:
        print(f"Error parsing control message: {e}")

client = mqtt.Client(client_id="iot_sensor_01")
client.on_connect = on_connect
client.on_message = on_message

while True:
    try:
        client.connect(BROKER, PORT, 60)
        break
    except Exception as e:
        print(f"Waiting for broker... {e}")
        time.sleep(2)

client.loop_start()

if __name__ == "__main__":
    print("Starting IoT Simulator...")
    # Seed for reproducibility if needed, but random is okay since it's dynamic
    while True:
        if state == "QUARANTINED":
            # Entra en estado QUARANTINED, detiene el envío de métricas de red
            # y solo emite un ping de estado cada 10 segundos.
            payload = {
                "sensor_id": "sensor_01",
                "status": "QUARANTINED",
                "timestamp": time.time()
            }
            client.publish(TELEMETRY_TOPIC, json.dumps(payload))
            time.sleep(10)
            continue
        
        # Math logic for emulation
        if state == "NORMAL":
            # Lógica Matemática Estricta: ruido de fondo
            # bytes_out sigue una distribución Gaussiana
            bytes_out = int(np.random.normal(loc=150.0, scale=30.0))
            bytes_in = int(np.random.normal(loc=500.0, scale=100.0))
            # packet_rate sigue distribución de Poisson
            packet_rate = np.random.poisson(lam=10.0)
            tcp_flags_syn = 1 if random.random() < 0.05 else 0
        elif state == "UNDER_ATTACK":
            # Ráfagas exponenciales masivas (DDoS botnet o exfiltración)
            bytes_out = int(np.random.exponential(scale=50000.0)) + 10000
            bytes_in = int(np.random.exponential(scale=1000.0))
            packet_rate = np.random.poisson(lam=500.0)
            tcp_flags_syn = 1 if random.random() < 0.8 else 0
        else:
            bytes_out, bytes_in, packet_rate, tcp_flags_syn = 0, 0, 0, 0
        
        # Ensure bounds
        bytes_out = max(0, bytes_out)
        bytes_in = max(0, bytes_in)
        
        payload = {
            "sensor_id": "sensor_01",
            "bytes_in": bytes_in,
            "bytes_out": bytes_out,
            "packet_rate": packet_rate,
            "tcp_flags_syn": tcp_flags_syn,
            "status": state,
            "timestamp": time.time()
        }
        
        client.publish(TELEMETRY_TOPIC, json.dumps(payload))
        time.sleep(1)
