import os
import time
import json
import threading
import numpy as np
from sklearn.ensemble import IsolationForest
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuración MQTT
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
TELEMETRY_TOPIC = "telemetry/#"

# Configuración InfluxDB
INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://localhost:8086")
INFLUXDB_TOKEN = os.environ.get("INFLUXDB_TOKEN", "supersecrettoken123")
INFLUXDB_ORG = os.environ.get("INFLUXDB_ORG", "soc_org")
INFLUXDB_BUCKET = os.environ.get("INFLUXDB_BUCKET", "telemetry")

# Variables ML
MODEL = IsolationForest(contamination=0.05, random_state=42)
MODEL_READY = False

def pre_train_model():
    """
    Pre-entrena el modelo con 2000 muestras de telemetría sintética (estado NORMAL).
    Esto establece una línea base de comportamiento seguro en la memoria RAM,
    evitando que el sistema necesite días de entrenamiento.
    """
    global MODEL_READY, MODEL
    print("[Detector] Generando 2000 muestras sintéticas para pre-entrenamiento (Línea Base)...")
    
    # Simula estado "NORMAL" (mismas distribuciones que el simulador o parecidas)
    bytes_in = np.random.normal(500, 50, 2000)
    bytes_out = np.random.normal(150, 20, 2000)
    packet_rate = np.random.poisson(10, 2000)
    tcp_flags_syn = max(0, int(np.random.normal(1, 1))) * np.ones(2000) # Simplificación
    
    # Preparar matriz de características
    X_train = np.column_stack((bytes_in, bytes_out, packet_rate, tcp_flags_syn))
    
    print("[Detector] Entrenando IsolationForest...")
    MODEL.fit(X_train)
    MODEL_READY = True
    print("[Detector] Modelo pre-entrenado y listo.")

def process_telemetry(payload, mqtt_client, write_api):
    try:
        device_id = payload.get("device_id")
        status = payload.get("status")

        # Extraemos features
        b_in = payload.get("bytes_in", 0)
        b_out = payload.get("bytes_out", 0)
        p_rate = payload.get("packet_rate", 0)
        t_syn = payload.get("tcp_flags_syn", 0)

        # Si el dispositivo ya está aislado, el simulador solo manda pings sin métricas.
        # No hace falta pasarlo por el modelo.
        if status == "QUARANTINED":
            return

        # Análisis con ML ML ML
        X_test = np.array([[b_in, b_out, p_rate, t_syn]])
        prediction = MODEL.predict(X_test)[0]          # 1: Normal, -1: Anomalía
        score = MODEL.decision_function(X_test)[0]     # Score continuo
        
        is_anomaly = True if prediction == -1 else False

        # Guardar telemetría cruda y el score de ML en InfluxDB
        point = Point("network_traffic") \
            .tag("device_id", device_id) \
            .tag("status", status) \
            .field("bytes_in", float(b_in)) \
            .field("bytes_out", float(b_out)) \
            .field("packet_rate", float(p_rate)) \
            .field("tcp_flags_syn", float(t_syn)) \
            .field("anomaly_score", float(score)) \
            .field("is_anomaly", int(is_anomaly))
            
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        
        # Publicar el score para el Response Handler via MQTT
        # Esto desacopla la detección de la respuesta
        score_payload = {
            "device_id": device_id,
            "is_anomaly": is_anomaly,
            "score": score,
            "timestamp": payload.get("timestamp", time.time())
        }
        
        mqtt_client.publish(f"edr/scores/{device_id}", json.dumps(score_payload))

    except Exception as e:
        print(f"[Detector] Error procesando telemetría: {e}")

def main():
    pre_train_model()

    # Setup InfluxDB
    influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    # Setup MQTT
    mqtt_client = mqtt.Client(client_id="edr_detector")
    
    def on_connect(client, userdata, flags, rc):
        print(f"[Detector] Conectado a MQTT con código {rc}")
        client.subscribe(TELEMETRY_TOPIC)
        
    def on_message(client, userdata, msg):
        if not MODEL_READY:
            return
        payload = json.loads(msg.payload.decode("utf-8"))
        process_telemetry(payload, client, write_api)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    connected = False
    while not connected:
        try:
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            connected = True
        except Exception as e:
            print(f"[Detector] Esperando broker MQTT... {e}")
            time.sleep(2)

    mqtt_client.loop_forever()

if __name__ == "__main__":
    main()
