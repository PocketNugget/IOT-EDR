import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

BROKER = "localhost"
PORT = 1883
DEVICE_ID = "hub_central"

print(f"🚀 Iniciando simulación de Movimiento Lateral y Ransomware")
print(f"🎯 Objetivo: Smart Hub (Coordinador de la red del Ecosistema Doméstico - {DEVICE_ID})")

payload = {"action": "attack"}

try:
    print(f"[*] Infiltrando el orquestador principal del hogar vía protocolo físico...")
    client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id="attacker_ransom_2")
    client.connect(BROKER, PORT, 60)
    client.publish(f"home/control/{DEVICE_ID}", json.dumps(payload))
    client.disconnect()
    
    print("[+] 💀 Hub comprometido y propagando anomalías volumétricas a la ruta de red.")
    print("[!] Monitorea como el Threshold Model identifica la diferencia entre un OTA real vs Escaneo Ransomware.")
except Exception as e:
    print(f"[-] Error fatal de inyección en bus MQTT: {e}")
