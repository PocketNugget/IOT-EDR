import os
import time
import json
import logging
import numpy as np
import paho.mqtt.client as mqtt
from sklearn.ensemble import IsolationForest
from influxdb_client import InfluxDBClient, Point, WritePrecision

logging.basicConfig(level=logging.INFO, format='%(asctime)s - Context_EDR - %(levelname)s - %(message)s')

BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("MQTT_PORT", 1883))
TELEMETRY_TOPIC = "home/telemetry/#"

INFLUX_URL = "http://influxdb:8086"
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "super_secret_token_123")
INFLUX_ORG = os.getenv("INFLUX_ORG", "soc_org")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "telemetry")

# ── Context-Aware Models — one per device profile ──
# contamination=0.005 → only truly extreme outliers flagged
# This prevents normal ON/OFF/CHARGING traffic variance from causing false positives
ml_models = {
    "bulb":     IsolationForest(contamination=0.005, random_state=42, n_estimators=150),
    "switch":   IsolationForest(contamination=0.005, random_state=42, n_estimators=150),
    "hub":      IsolationForest(contamination=0.005, random_state=42, n_estimators=150),
    "roomba":   IsolationForest(contamination=0.005, random_state=42, n_estimators=150),
    "sprinkler":IsolationForest(contamination=0.005, random_state=42, n_estimators=150),
}

anomaly_tracker: dict[str, int] = {}
clean_streak:    dict[str, int] = {}   # consecutive clean readings

# Must sustain 8 anomaly signals before auto-isolation.
# A real attack generates sustained abnormal traffic — not occasional spikes.
PERSISTENCE_THRESHOLD = 8
CLEAN_RESET_STREAK = 3   # consecutive clean ticks needed to reset strike counter


def pre_train_models():
    logging.info("🧠 Pre-training Context-Aware Models for all Smart Home profiles...")

    import random

    # Each profile covers ALL legitimate states the device can be in:
    # standby/OFF/IDLE (0 traffic), active/ON traffic, and OTA bursts.
    # This prevents the model from treating zero-traffic (OFF state) as anomalous.
    profile_samples = {
        "bulb": [
            # 50% OFF standby heartbeats
            *[[random.randint(0, 5), random.randint(0, 5), 80, 0]
              for _ in range(700)],
            # 45% ON — normal mdns/hub pings
            *[[max(0, np.random.normal(50, 15)), max(0, np.random.normal(20, 6)), 80, max(0, int(np.random.poisson(2)))]
              for _ in range(600)],
            # 5% OTA update (heavy but on 443)
            *[[max(0, np.random.normal(15000, 2000)), max(0, np.random.normal(500, 50)), 443, max(0, int(np.random.poisson(100)))]
              for _ in range(100)],
        ],
        "switch": [
            # 55% OFF heartbeat
            *[[random.randint(0, 5), random.randint(0, 5), 8080, 0]
              for _ in range(600)],
            # 40% ON — occasional bursts
            *[[max(0, np.random.normal(60, 20)), max(0, np.random.normal(80, 25)), 8080, max(0, int(np.random.poisson(8)))]
              for _ in range(500)],
            # 5% OTA
            *[[max(0, np.random.normal(12000, 1000)), max(0, np.random.normal(400, 40)), 443, max(0, int(np.random.poisson(80)))]
              for _ in range(100)],
        ],
        "hub": [
            # Hub is always on — only variance matters
            *[[max(0, np.random.normal(2000, 400)), max(0, np.random.normal(3500, 600)), 8443, max(0, int(np.random.poisson(45)))]
              for _ in range(1100)],
            # OTA
            *[[max(0, np.random.normal(30000, 5000)), max(0, np.random.normal(2000, 200)), 443, max(0, int(np.random.poisson(250)))]
              for _ in range(100)],
        ],
        "roomba": [
            # 65% CHARGING — docked, near-zero traffic
            *[[random.randint(0, 10), random.randint(0, 10), 443, 0]
              for _ in range(750)],
            # 35% CLEANING — LiDAR map upload
            *[[max(0, np.random.normal(8000, 1500)), max(0, np.random.normal(12000, 2500)), 443, max(0, int(np.random.poisson(80)))]
              for _ in range(350)],
        ],
        "sprinkler": [
            # 85% IDLE — near-zero weather API ping
            *[[random.randint(0, 20), random.randint(0, 10), 443, 0]
              for _ in range(950)],
            # 15% WATERING — HTTPS bursts
            *[[max(0, np.random.normal(3000, 500)), max(0, np.random.normal(800, 120)), 443, max(0, int(np.random.poisson(30)))]
              for _ in range(250)],
        ],
    }

    for profile, model in ml_models.items():
        X_train = profile_samples[profile]
        random.shuffle(X_train)
        model.fit(X_train)
        logging.info(f"✅ Profile '{profile}' — trained on {len(X_train)} samples covering all operational states.")


def on_connect(client, userdata, flags, rc):
    logging.info(f"EDR Engine connected to Mosquitto (code {rc}). Listening telemetry/#")
    client.subscribe(TELEMETRY_TOPIC)


def enforce_quarantine(client, device_id):
    logging.warning(f"🚨 AUTO-ISOLATION: quarantining {device_id}")
    client.publish(f"home/control/{device_id}", json.dumps({"action": "quarantine"}))


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        if payload.get("status") == "QUARANTINED":
            return

        device_id   = payload.get("device_id")
        device_type = payload.get("device_type")

        if device_type not in ml_models:
            return

        bytes_in    = float(payload.get("bytes_in", 0))
        bytes_out   = float(payload.get("bytes_out", 0))
        port        = float(payload.get("port", 0))
        packet_rate = float(payload.get("packet_rate", 0))

        model       = ml_models[device_type]
        features    = [[bytes_in, bytes_out, port, packet_rate]]
        prediction  = model.predict(features)[0]
        raw_score   = model.decision_function(features)[0]

        normalized_score = float(-raw_score)
        is_anomaly = 1 if prediction == -1 else 0

        # ── Persistence tracker with clean-streak reset ──
        if device_id not in anomaly_tracker:
            anomaly_tracker[device_id] = 0
            clean_streak[device_id] = 0

        if is_anomaly:
            anomaly_tracker[device_id] += 1
            clean_streak[device_id] = 0    # reset clean streak on any anomaly
            logging.warning(
                f"[{device_id}] Anomaly detected (profile={device_type}) "
                f"Strike {anomaly_tracker[device_id]}/{PERSISTENCE_THRESHOLD} | Score={normalized_score:.3f}"
            )
            if anomaly_tracker[device_id] >= PERSISTENCE_THRESHOLD:
                enforce_quarantine(client, device_id)
                anomaly_tracker[device_id] = 0
                clean_streak[device_id] = 0
        else:
            clean_streak[device_id] += 1
            # Only forgive strikes after CLEAN_RESET_STREAK consecutive normal readings
            if clean_streak[device_id] >= CLEAN_RESET_STREAK:
                anomaly_tracker[device_id] = max(0, anomaly_tracker[device_id] - 1)
                clean_streak[device_id] = 0

        # ── Write to InfluxDB ──
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as idb:
            write_api = idb.write_api()
            point = (
                Point("home_telemetry")
                .tag("device_id", device_id)
                .tag("device_type", device_type)
                .field("bytes_in", bytes_in)
                .field("bytes_out", bytes_out)
                .field("port", port)
                .field("packet_rate", packet_rate)
                .field("anomaly_score", normalized_score)
                .field("is_anomaly", int(is_anomaly))
                .time(time.time_ns(), WritePrecision.NS)
            )
            write_api.write(bucket=INFLUX_BUCKET, record=point)

        # ── Forward evaluation to Backend ──
        eval_payload = {
            "device_id": device_id,
            "anomaly_score": normalized_score,
            "is_anomaly": is_anomaly,
        }
        client.publish("edr/evaluation", json.dumps(eval_payload))

    except Exception as e:
        logging.error(f"EDR payload error: {e}")


if __name__ == "__main__":
    pre_train_models()

    client = mqtt.Client(client_id="edr_context_detector")
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(BROKER, PORT, 60)
            break
        except Exception:
            logging.info("Waiting for Mosquitto broker...")
            time.sleep(2)

    client.loop_forever()
