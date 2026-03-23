# Smart Home Context-Aware EDR 🏠🛡️

Plataforma de seguridad EDR en el borde diseñada para un Ecosistema Doméstico (Focos, Apagadores, Hubs Inteligentes). Esta arquitectura detecta anomalías Zero-Day considerando el contexto y uso legítimo de los dispositivos (e.g. descargas OTA) mediante Machine Learning (Scikit-Learn). 

Desarrollada para ejecutar en `linux/arm64` como la Raspberry Pi 5.

## 🏗️ Topología del Sistema

1. **Simulador Avanzado (Multi-Nodo):** Genera tráfico heterogéneo asíncrono basado en perfiles (Bulb, Switch, Hub), simulando heartbeats, ráfagas cortas, OTA updates y escaneos de red anómalos (Ataques C2).
2. **Mosquitto (MQTT):** Espina dorsal de comunicación sub-milisegundo uniendo las telemetrías crudas al ML.
3. **InfluxDB v2:** TSDB de alto rendimiento para guardar el timeline del ecosistema analizado.
4. **Context-Aware ML Engine:** Modelo jerárquico `IsolationForest` que correlaciona de manera sensitiva la rama del árbol según perfiles IoT. Aprende a discernir una actualización de firmware (Puerto 443 + Volumen Masivo) en un Smart Hub contra un DDoS Botnet corriendo en un Foco Inteligente.
5. **Backend FastAPI:** Endpoints API que mapean el inventario Smart y tuberías en tiempo real de WebSocket.
6. **React SOC Dashboard:** Grid matricial renderizando el plano físico de la vivienda y exponiendo terminales de logs contextuales y scores estadísticos.

## 🚀 Despliegue Inicial 

```bash
cd smart_home_edr
docker-compose up -d --build
```

### 🛰️ Puntos de Acceso Externos Mapeados
Debido a colisiones de red, el sistema orquesta sobre los siguientes puertos libres:
- **Frontend SOC Dashboard:** `http://localhost:3002`
- **Backend FastAPI / Swagger:** `http://localhost:8002/docs`
- **InfluxDB v2 UI:** `http://localhost:8086` (Usuario: `admin`, Clave: `adminpassword`)
- **Mosquitto MQTT:** Puerto nativo `1883`

### 🏴‍☠️ Auditoría de Ciberseguridad (Scripts C2)
Existen algoritmos *red-team* embebidos listos para disparar ráfagas anómalas e intentar evadir el análisis contextual del motor *IsolationForest*:

```bash
pip install requests

# 1. Infecta el Smart Switch (Anomalía: Escaneo HTTP)
python attack_scripts/01_mirai_botnet_scan.py

# 2. Orquesta Ransomware en el Hub
python attack_scripts/02_ransomware_lateral.py

# 3. Zombifica el Smart Bulb inyectando un DDoS Flood Outbound
python attack_scripts/03_ddos_flood.py
```
