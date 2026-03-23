import os
import time
import json
import threading
import paho.mqtt.client as mqtt

# Configuración MQTT
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
SCORES_TOPIC = "edr/scores/+"

# Estado de dispositivos y anomalías
consecutive_anomalies = {}
quarantined_devices = set()
lock = threading.Lock()

def check_anomaly(device_id, is_anomaly, score, client):
    with lock:
        if device_id in quarantined_devices:
            return  # Ya fue aislado, ignorar

        if is_anomaly:
            count = consecutive_anomalies.get(device_id, 0) + 1
            consecutive_anomalies[device_id] = count
            
            print(f"[ResponseHandler] Alerta en {device_id}. Anomaly Score: {score:.3f}. Racha: {count}/5")
            
            if count >= 5: # Reducción de Falsos Positivos
                print(f"[ResponseHandler] => ¡Peligo Crítico! EDR accionando cuarentena autónoma en {device_id}")
                
                # Accion 1: Publicar alerta en bus de incidentes
                alert = {
                    "severity": "CRITICAL",
                    "device_id": device_id,
                    "reason": "Anomalía persistente detectada (Posible Zero-Day/Botnet)",
                    "action_taken": "QUARANTINE_ISSUED",
                    "timestamp": time.time()
                }
                client.publish("alerts/critical", json.dumps(alert))
                
                # Accion 2: Ordenar aislamiento via MQTT al IoT edge control hub
                control_cmd = {"action": "quarantine"}
                client.publish(f"control/{device_id}", json.dumps(control_cmd))
                
                quarantined_devices.add(device_id)
                consecutive_anomalies[device_id] = 0
        else:
            # Si hay un payload normal, resetear contador de racha
            if device_id in consecutive_anomalies and consecutive_anomalies[device_id] > 0:
                print(f"[ResponseHandler] {device_id} reportó tráfico normal. Reseteando racha de anomalías.")
            consecutive_anomalies[device_id] = 0

def on_connect(client, userdata, flags, rc):
    print(f"[ResponseHandler] Conectado a MQTT Broker con código {rc}")
    client.subscribe(SCORES_TOPIC)
    client.subscribe("control/+") # Para escuchar cuando alguien restaura manualmente
    
def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode("utf-8"))
        
        # Detectar comandos de restauración de red
        if topic.startswith("control/"):
            device_id = topic.split("/")[1]
            if payload.get("action") == "restore":
                with lock:
                    if device_id in quarantined_devices:
                        print(f"[ResponseHandler] Cuarentena levantada para {device_id}. EDR restaurando monitorización normal.")
                        quarantined_devices.remove(device_id)
                        consecutive_anomalies[device_id] = 0
            return
            
        # Analisis continuo
        if topic.startswith("edr/scores/"):
            is_anomaly = payload.get("is_anomaly")
            score = payload.get("score")
            device_id = payload.get("device_id")
            
            check_anomaly(device_id, is_anomaly, score, client)
            
    except Exception as e:
        print(f"[ResponseHandler] Error: {e}")

def main():
    client = mqtt.Client(client_id="edr_responder")
    client.on_connect = on_connect
    client.on_message = on_message

    connected = False
    while not connected:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            connected = True
        except Exception as e:
            print(f"[ResponseHandler] Esperando broker MQTT... {e}")
            time.sleep(2)

    client.loop_forever()

if __name__ == "__main__":
    main()
