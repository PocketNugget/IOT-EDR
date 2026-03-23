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
ml_models = {
    "bulb":     IsolationForest(contamination=0.02, random_state=42, n_estimators=100),
    "switch":   IsolationForest(contamination=0.02, random_state=42, n_estimators=100),
    "hub":      IsolationForest(contamination=0.02, random_state=42, n_estimators=100),
    "roomba":   IsolationForest(contamination=0.02, random_state=42, n_estimators=100),
    "sprinkler":IsolationForest(contamination=0.02, random_state=42, n_estimators=100),
}

anomaly_tracker: dict[str, int] = {}
PERSISTENCE_THRESHOLD = 3


def pre_train_models():
    logging.info("🧠 Pre-training Context-Aware Models for all Smart Home profiles...")

    training_data = {
        # [bytes_in, bytes_out, port, packet_rate]
        "bulb": {
            "normal": lambda: [
                max(0, np.random.normal(50, 10)),
                max(0, np.random.normal(20, 5)),
                80,
                np.random.poisson(2)
            ],
            "ota": lambda: [
                max(0, np.random.normal(15000, 2000)),
                max(0, np.random.normal(500, 50)),
                443,
                np.random.poisson(100)
            ],
        },
        "switch": {
            "normal": lambda: [
                max(0, np.random.normal(10, 2)),
                max(0, np.random.normal(15, 3)),
                8080,
                np.random.poisson(1)
            ],
            "ota": lambda: [
                max(0, np.random.normal(12000, 1000)),
                max(0, np.random.normal(400, 40)),
                443,
                np.random.poisson(80)
            ],
        },
        "hub": {
            "normal": lambda: [
                max(0, np.random.normal(2000, 300)),
                max(0, np.random.normal(3500, 500)),
                8443,
                np.random.poisson(45)
            ],
            "ota": lambda: [
                max(0, np.random.normal(30000, 5000)),
                max(0, np.random.normal(2000, 200)),
                443,
                np.random.poisson(250)
            ],
        },
        # Roomba: CHARGING (standby) + CLEANING (high BW)
        "roomba": {
            "normal": lambda: (
                [max(0, np.random.normal(8000, 1000)),
                 max(0, np.random.normal(12000, 2000)),
                 443,
                 np.random.poisson(80)]
                if np.random.random() < 0.35   # 35% cleaning, 65% charging
                else [random.randint(0, 10), random.randint(0, 10), 443, 0]
            ),
            "ota": lambda: [
                max(0, np.random.normal(20000, 3000)),
                max(0, np.random.normal(1000, 100)),
                443,
                np.random.poisson(150)
            ],
        },
        # Sprinkler: IDLE (near-zero) + WATERING (short bursts)
        "sprinkler": {
            "normal": lambda: (
                [max(0, np.random.normal(3000, 400)),
                 max(0, np.random.normal(800, 100)),
                 443,
                 np.random.poisson(30)]
                if np.random.random() < 0.15   # 15% watering, 85% idle
                else [random.randint(0, 20), random.randint(0, 10), 443, 0]
            ),
            "ota": lambda: [
                max(0, np.random.normal(5000, 500)),
                max(0, np.random.normal(300, 30)),
                443,
                np.random.poisson(40)
            ],
        },
    }

    import random  # local import to avoid polluting module namespace above
    for profile, model in ml_models.items():
        X_train = []
        data = training_data[profile]
        for _ in range(1000):
            X_train.append(data["normal"]())
        for _ in range(200):
            X_train.append(data["ota"]())
        model.fit(X_train)
        logging.info(f"✅ Profile '{profile}' — IsolationForest trained ({len(X_train)} samples).")


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

        # ── Persistence tracker ──
        if device_id not in anomaly_tracker:
            anomaly_tracker[device_id] = 0

        if is_anomaly:
            anomaly_tracker[device_id] += 1
            logging.warning(
                f"[{device_id}] Anomaly detected (profile={device_type}) "
                f"Strike {anomaly_tracker[device_id]}/{PERSISTENCE_THRESHOLD}"
            )
            if anomaly_tracker[device_id] >= PERSISTENCE_THRESHOLD:
                enforce_quarantine(client, device_id)
                anomaly_tracker[device_id] = 0
        else:
            anomaly_tracker[device_id] = max(0, anomaly_tracker[device_id] - 1)

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
