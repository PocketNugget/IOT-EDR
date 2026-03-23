import os
import json
import time
import threading
import numpy as np
import paho.mqtt.client as mqtt

MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
DEVICE_ID = "sensor_01"

TELEMETRY_TOPIC = f"telemetry/{DEVICE_ID}"
CONTROL_TOPIC = f"control/{DEVICE_ID}"

# Estados: NORMAL, UNDER_ATTACK, QUARANTINED
state_lock = threading.Lock()
current_state = "NORMAL"

def on_connect(client, userdata, flags, rc):
    print(f"[{DEVICE_ID}] Conectado a MQTT Broker con código {rc}")
    client.subscribe(CONTROL_TOPIC)
    print(f"[{DEVICE_ID}] Suscrito a topic: {CONTROL_TOPIC}")

def on_message(client, userdata, msg):
    global current_state
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        action = payload.get("action")
        
        with state_lock:
            if action == "quarantine":
                print(f"[{DEVICE_ID}] Comando recibido: QUARANTINE. Aislando dispositivo...")
                current_state = "QUARANTINED"
            elif action == "restore":
                print(f"[{DEVICE_ID}] Comando recibido: RESTORE. Restaurando operaciones...")
                current_state = "NORMAL"
            elif action == "attack":
                print(f"[{DEVICE_ID}] Comando recibido: ATTACK. Iniciando simulación Zero-Day...")
                current_state = "UNDER_ATTACK"
    except Exception as e:
        print(f"Error procesando mensaje de control: {str(e)}")

def generate_telemetry():
    """
    Genera métricas de red basadas en modelos matemáticos según el estado.
    """
    with state_lock:
        state = current_state

    if state == "QUARANTINED":
        # Dispositivo aislado: solo emite latidos para indicar que está vivo.
        return {
            "device_id": DEVICE_ID,
            "status": "QUARANTINED",
            "timestamp": time.time()
        }

    # Distribuciones base (Simulación Matemática)
    if state == "NORMAL":
        # Ruido de fondo: Gaussiana para bytes, Poisson para paquetes
        bytes_in = int(np.random.normal(500, 50))  # media 500, stddev 50
        bytes_out = int(np.random.normal(150, 20)) 
        packet_rate = np.random.poisson(10)        # media lambda 10 pkts/sec
        tcp_flags_syn = max(0, int(np.random.normal(1, 1)))
    elif state == "UNDER_ATTACK":
        # Simulando exfiltración/botnet: Ráfagas exponenciales masivas
        bytes_in = int(np.random.exponential(scale=5000))
        bytes_out = int(np.random.exponential(scale=20000)) # gran exfiltración
        packet_rate = np.random.poisson(500)       # ataque ddos / flood
        tcp_flags_syn = np.random.poisson(300)     # possible SYN flood

    # Aseguramos de no mandar negativos por si las distribuciones bajan del 0.
    return {
        "device_id": DEVICE_ID,
        "status": state,
        "bytes_in": max(0, bytes_in),
        "bytes_out": max(0, bytes_out),
        "packet_rate": max(0, packet_rate),
        "tcp_flags_syn": max(0, tcp_flags_syn),
        "timestamp": time.time()
    }

def main():
    client = mqtt.Client(client_id=DEVICE_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    connected = False
    while not connected:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            connected = True
        except Exception as e:
            print(f"Esperando MQTT broker... {str(e)}")
            time.sleep(2)

    client.loop_start()

    while True:
        payload = generate_telemetry()
        
        # Publicacion
        if payload.get("status") == "QUARANTINED":
            client.publish(TELEMETRY_TOPIC, json.dumps(payload))
            time.sleep(10) # En cuarentena solo reporta state cada 10s
        else:
            client.publish(TELEMETRY_TOPIC, json.dumps(payload))
            time.sleep(1) # En operación o ataque reporta cada 1s

if __name__ == "__main__":
    main()
