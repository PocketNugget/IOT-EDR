# 🏠🛡️ IOT-EDR — Smart Home Edge Detection & Response

> **Plataforma EDR contextualizada para el hogar inteligente.**  
> Detecta amenazas Zero-Day con Machine Learning, aísla dispositivos autónomamente y expone un panel SOC en tiempo real.

---

## 📚 Documentación Completa

La documentación técnica detallada del proyecto se encuentra en:

**[📄 `smart_home_edr/README.md`](smart_home_edr/README.md)**

Incluye:
- Diagrama Mermaid de arquitectura completa
- Documentación del Simulador IoT (11 dispositivos)
- Documentación del Motor ML (IsolationForest × 5 perfiles)
- Referencia completa de la REST API (FastAPI)
- Documentación del SOC Dashboard (React)
- Guía de Attack Scripts Red Team
- Esquema de InfluxDB
- Casos de uso y testing
- Consideraciones de seguridad

---

## 🚀 Inicio Rápido

```bash
git clone https://github.com/PocketNugget/IOT-EDR.git
cd IOT-EDR/smart_home_edr

docker-compose up -d --build
```

| Servicio | URL |
|---|---|
| **SOC Dashboard** | http://localhost:3002 |
| **Backend API** | http://localhost:8002/docs |
| **InfluxDB** | http://localhost:8086 |

---

## 🏗️ Stack

| Componente | Tecnología |
|---|---|
| Smart Home Simulator | Python + asyncio + paho-mqtt |
| EDR ML Engine | scikit-learn (IsolationForest) + InfluxDB |
| Backend API | FastAPI + WebSocket |
| SOC Dashboard | React + Vite + Tailwind CSS + Recharts |
| Message Bus | Eclipse Mosquitto (MQTT) |
| Time-Series DB | InfluxDB v2 |
| Orquestación | Docker Compose |

---

## 🎯 Target: Raspberry Pi 5 (`linux/arm64`)
