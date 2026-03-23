import time
import requests

API_URL = "http://localhost:8002/api/action"
DEVICE_ID = "switch_main_door" 

print(f"🚀 Iniciando simulación de Infección Mirai (Escaneo de Puertos HTTP/Telnet)")
print(f"🎯 Objetivo: Smart Switch (IoT de baja entropía - {DEVICE_ID})")

payload = {
    "device_id": DEVICE_ID,
    "action": "attack"
}

try:
    print(f"[*] Inyectando payload malicioso vía API C2...")
    response = requests.post(API_URL, json=payload, timeout=5)
    if response.status_code == 200:
        print("[+] 💀 Dispositivo Comprometido Exitosamente.")
        print("[!] Observa el Dashboard SOC para visualizar la reacción predictiva del IsolationForest.")
    else:
        print("[-] Falló la inyección por error en el endpoint.")
except Exception as e:
    print(f"[-] Error de red crítico: {e}")
