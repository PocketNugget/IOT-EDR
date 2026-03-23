import os
import time
import json
import logging
import numpy as np
import paho.mqtt.client as mqtt
from sklearn.ensemble import IsolationForest
from influxdb_client import InfluxDBClient, Point, WritePrecision

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - EDR Detector - %(levelname)s - %(message)s')

# MQTT Config
BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("MQTT_PORT", 1883))
TELEMETRY_TOPIC = "telemetry/#"

# InfluxDB Config
INFLUX_URL = "http://influxdb:8086"
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "super_secret_token_123")
INFLUX_ORG = os.getenv("INFLUX_ORG", "soc_org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "telemetry")

# ML Model Setup - isolation forest with contamination=0.05
ml_model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)

def pre_train_model():
    logging.info("Pre-training ML model with 2000 synthetic baseline samples...")
    X_train = []
    for _ in range(2000):
        # Emulate normal operation logic from simulator
        bytes_out = max(0, int(np.random.normal(loc=150.0, scale=30.0)))
        bytes_in = max(0, int(np.random.normal(loc=500.0, scale=100.0)))
        packet_rate = np.random.poisson(lam=10.0)
        tcp_flags_syn = 1 if np.random.random() < 0.05 else 0
        X_train.append([bytes_in, bytes_out, packet_rate, tcp_flags_syn])
    ml_model.fit(X_train)
    logging.info("✅ Pre-training complete!")

def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected to Mosquitto (code {rc}). Securing telemetry streams.")
    client.subscribe(TELEMETRY_TOPIC)

def on_message(client, userdata, msg):
    try:
        # Load JSON from MQTT
        payload = json.loads(msg.payload.decode())
        
        # Omit tracking metrics directly if the device is already quarantined securely
        if payload.get("status") == "QUARANTINED":
            return
            
        sensor_id = payload.get("sensor_id", "unknown")
        bytes_in = float(payload.get("bytes_in", 0))
        bytes_out = float(payload.get("bytes_out", 0))
        packet_rate = float(payload.get("packet_rate", 0))
        tcp_flags_syn = float(payload.get("tcp_flags_syn", 0))
        
        # Extraction logic
        features = [[bytes_in, bytes_out, packet_rate, tcp_flags_syn]]
        prediction = ml_model.predict(features)[0]  # -1 for anomaly
        raw_score = ml_model.decision_function(features)[0]
        
        # Normalized inverse metric (higher = anomaly risk)
        normalized_anomaly_score = float(-raw_score)
        is_anomaly = 1 if prediction == -1 else 0

        # Save event to TSDB (InfluxDB)
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as idb_client:
            write_api = idb_client.write_api()
            point = Point("network_telemetry") \
                .tag("sensor_id", sensor_id) \
                .field("bytes_in", bytes_in) \
                .field("bytes_out", bytes_out) \
                .field("packet_rate", packet_rate) \
                .field("tcp_flags_syn", tcp_flags_syn) \
                .field("anomaly_score", normalized_anomaly_score) \
                .field("is_anomaly", int(is_anomaly)) \
                .time(time.time_ns(), WritePrecision.NS)
            write_api.write(bucket=INFLUX_BUCKET, record=point)
        
        # Pipe evaluation out to internal Mosquitto topic for response_handler execution
        eval_payload = {
            "sensor_id": sensor_id,
            "anomaly_score": normalized_anomaly_score,
            "is_anomaly": is_anomaly,
            "timestamp": payload.get("timestamp")
        }
        client.publish("edr/evaluation", json.dumps(eval_payload))
        
    except Exception as e:
        logging.error(f"Error processing payload: {e}")

if __name__ == "__main__":
    pre_train_model()
    
    client = mqtt.Client(client_id="edr_detector_engine")
    client.on_connect = on_connect
    client.on_message = on_message
    
    while True:
        try:
            client.connect(BROKER, PORT, 60)
            break
        except Exception:
            logging.info("Waiting for Mosquitto Broker...")
            time.sleep(2)
            
    client.loop_forever()
