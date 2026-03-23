import time
import requests

API_URL = "http://localhost:8002/api/action"
DEVICE_ID = "bulb_living_room"

print(f"🚀 Iniciando simulación C2 (DDoS Flood Outbound)")
print(f"🎯 Objetivo: Smart Bulb (Foco Inteligente de bajo tráfico - {DEVICE_ID})")

payload = {
    "device_id": DEVICE_ID,
    "action": "attack"
}

try:
    print(f"[*] Transformando recurso lumínico en nodo zombie (Botnet)...")
    response = requests.post(API_URL, json=payload, timeout=5)
    if response.status_code == 200:
        print("[+] 💀 Foco ejecutando ráfagas DNS/NTP masivas que rompen su línea base de 3% a 10,000%.")
        print("[!] El motor de contexto EDR debería aislarlo a nivel switch en breve tiempo.")
    else:
        print("[-] Inyección desestimada.")
except Exception as e:
    print(f"[-] Error de conexión C2: {e}")
