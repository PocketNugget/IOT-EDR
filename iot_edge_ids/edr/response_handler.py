import os
import time
import json
import logging
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - ResponseHandler - %(message)s')

BROKER = os.getenv("MQTT_BROKER", "mosquitto")
PORT = int(os.getenv("MQTT_PORT", 1883))
EVAL_TOPIC = "edr/evaluation"

# Mechanism dictionary to track the persistance algorithm and decrease False Positives (FPs)
anomaly_tracker = {}
PERSISTENCE_THRESHOLD = 5

def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected to Mosquitto (code {rc}). Awaiting analytics from Detector ML.")
    client.subscribe(EVAL_TOPIC)

def enforce_quarantine(client, sensor_id):
    logging.warning(f"🚨 ACTIVE RESPONSE TRIGGERED! Quarantining {sensor_id}.")
    
    # Send highly critical alert packet
    alert_payload = {
        "level": "CRITICAL",
        "sensor_id": sensor_id,
        "reason": "Persistent Network Anomaly Detected (Zero-Day Exfiltration sequence observed)",
        "timestamp": time.time()
    }
    client.publish("alerts/critical", json.dumps(alert_payload))
    
    # Execute Auto-quarantine mitigation
    control_payload = {"action": "quarantine"}
    client.publish(f"control/{sensor_id}", json.dumps(control_payload))

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        sensor_id = payload.get("sensor_id")
        is_anomaly = payload.get("is_anomaly")
        
        if not sensor_id: return
        
        if sensor_id not in anomaly_tracker:
            anomaly_tracker[sensor_id] = 0
            
        if is_anomaly == 1:
            anomaly_tracker[sensor_id] += 1
            logging.warning(f"Anomalous telemetry from {sensor_id}! Strike {anomaly_tracker[sensor_id]}/{PERSISTENCE_THRESHOLD}")
            
            # If the evaluated threat persists beyond the threshold logic
            if anomaly_tracker[sensor_id] >= PERSISTENCE_THRESHOLD:
                enforce_quarantine(client, sensor_id)
                anomaly_tracker[sensor_id] = 0 # reset tracking mechanism after quarantine mitigation
        else:
            if anomaly_tracker[sensor_id] > 0:
                logging.info(f"Traffic normalized for {sensor_id}. Clearing anomaly tracking pipeline.")
                anomaly_tracker[sensor_id] = 0
                
    except Exception as e:
        logging.error(f"Error handling event tracking evaluation: {e}")

if __name__ == "__main__":
    client = mqtt.Client(client_id="edr_response_handler")
    client.on_connect = on_connect
    client.on_message = on_message
    
    while True:
        try:
            client.connect(BROKER, PORT, 60)
            break
        except Exception:
            logging.info("Waiting for broker connection map...")
            time.sleep(3)
            
    client.loop_forever()
