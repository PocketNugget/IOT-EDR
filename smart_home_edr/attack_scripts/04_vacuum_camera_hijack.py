import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

BROKER = "localhost"
PORT = 1883
DEVICE_ID = "roomba_main"

print("🚀 Vacuum Camera Hijack — Exfiltración de Video en Vivo")
print(f"🎯 Objetivo: Robot Aspiradora ({DEVICE_ID})")
print("[*] Inyectando payload de exfiltración masiva al canal de control MQTT...")

payload = {"action": "attack"}

try:
    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="attacker_camera_hijack_4")
    client.connect(BROKER, PORT, 60)
    client.publish(f"home/control/{DEVICE_ID}", json.dumps(payload))
    client.disconnect()
    print("[+] 💀 Cámara de la Roomba comprometida. El dispositivo enviará streams masivos de video.")
    print("[!] Observa cómo el IsolationForest detecta el delta vs baseline 'CLEANING' y la aísla.")
except Exception as e:
    print(f"[-] Error de inyección (¿Mosquitto offline?): {e}")
