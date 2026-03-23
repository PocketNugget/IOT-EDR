import json
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
DEVICE_ID = "switch_main_door" 

print(f"🚀 Iniciando simulación de Infección Mirai (Escaneo de Puertos HTTP/Telnet)")
print(f"🎯 Objetivo: Smart Switch (IoT de baja entropía - {DEVICE_ID})")

payload = {"action": "attack"}

try:
    print(f"[*] Inyectando payload malicioso directamente al bus MQTT físico (Comprometiendo nodo)...")
    client = mqtt.Client(client_id="attacker_mirai_1")
    client.connect(BROKER, PORT, 60)
    client.publish(f"home/control/{DEVICE_ID}", json.dumps(payload))
    client.disconnect()
    
    print("[+] 💀 Dispositivo Comprometido Exitosamente.")
    print("[!] Observa el Dashboard SOC para visualizar la reacción defensiva del IsolationForest.")
except Exception as e:
    print(f"[-] Error de red (MQTT Bus Inaccesible): {e}")
