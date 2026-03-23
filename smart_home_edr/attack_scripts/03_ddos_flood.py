import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

BROKER = "localhost"
PORT = 1883
DEVICE_ID = "bulb_living_room"

print(f"🚀 Iniciando simulación C2 (DDoS Flood Outbound)")
print(f"🎯 Objetivo: Smart Bulb (Foco Inteligente de bajo tráfico - {DEVICE_ID})")

payload = {"action": "attack"}

try:
    print(f"[*] Transformando recurso lumínico en nodo zombie (Botnet) atacando la IP LAN...")
    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="attacker_ddos_3")
    client.connect(BROKER, PORT, 60)
    client.publish(f"home/control/{DEVICE_ID}", json.dumps(payload))
    client.disconnect()

    print("[+] 💀 Foco ejecutando ráfagas DNS/NTP masivas que rompen su línea base de 3% a 10,000%.")
    print("[!] El motor de contexto EDR debería aislarlo a nivel switch en breve tiempo.")
except Exception as e:
    print(f"[-] Error de conexión C2 (MQTT Bus Offline): {e}")
