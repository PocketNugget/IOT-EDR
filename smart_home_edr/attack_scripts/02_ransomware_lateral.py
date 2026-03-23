import time
import requests

API_URL = "http://localhost:8002/api/action"
DEVICE_ID = "hub_central"

print(f"🚀 Iniciando simulación de Movimiento Lateral y Ransomware")
print(f"🎯 Objetivo: Smart Hub (Coordinador de la red del Ecosistema Doméstico - {DEVICE_ID})")

payload = {
    "device_id": DEVICE_ID,
    "action": "attack"
}

try:
    print(f"[*] Infiltrando el orquestador principal del hogar...")
    response = requests.post(API_URL, json=payload, timeout=5)
    if response.status_code == 200:
        print("[+] 💀 Hub comprometido y propagando anomalías volumétricas a la ruta de red.")
        print("[!] Monitorea como el Threshold Model identifica la diferencia entre un OTA real vs Escaneo Ransomware.")
    else:
        print("[-] Falló la inyección por el plano de control.")
except Exception as e:
    print(f"[-] Error fatal C2 de inyección: {e}")
