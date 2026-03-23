# Edge EDR (Endpoint Detection & Response) for IoT

Plataforma de seguridad IoT en el borde diseñada para operar en Raspberry Pi 5 (`linux/arm64`). Utiliza Machine Learning (`IsolationForest` de Scikit-learn) para detectar ataques Zero-Day o anomalías en la telemetría, ejecutando aislamiento y contención de manera autónoma a través de MQTT.

## Arquitectura del Sistema

El sistema implementa 6 contenedores principales en Docker Compose:

1. **Mosquitto (MQTT Broker):** El bus de eventos principal. Expone puertos 1883 (TCP) y 9001 (WebSockets).
2. **InfluxDB v2:** Base de datos TSDB para telemetría a largo plazo.
3. **IoT Simulator (`simulator/`):** Simula variables de red (bytes in/out, packets, TCP flags) bajo modelos matemáticos de distribución Gaussiana y de Poisson.
4. **EDR Engine (`edr/`):** Escucha `telemetry/#`. Pre-entrena un modelo de `IsolationForest` al inicio. Escribe scores en InfluxDB y emite órdenes de cuarentena automáticas al broker MQTT si detecta rachas críticas de anomalías.
5. **REST & WebSocket API (`backend/`):** Aplicación FastAPI asíncrona que expone endpoints de control y transmite el estado general por WebSockets.
6. **SOC UI (`frontend/`):** Dashboard React + Tailwind CSS + Recharts que visualiza la red, los incidentes y permite interacción manual bajo un tema industrial / Ciberseguridad.

## Flujo de Detección y Contención (Autonomous Response)

1. El simulador emite telemetría a `telemetry/sensor_01`.
2. El EDR calcula el *Anomaly Score* (-1 = anomalía, 1 = normal) y lo publica en `edr/scores/sensor_01`.
3. Si el dispositivo mantiene 5 lecturas anómalas consecutivas (mitigación de falsos positivos), el *Response Handler* del EDR ordena el aislamiento lanzando el comando `quarantine` en el canal MQTT `control/sensor_01`.
4. El simulador, al recibir el comando de contención restrictivo vía MQTT, detiene los flujos simulados y entra en un estado inerte y seguro (QUARANTINED), emitiendo sólo un latido de vida cada 10 segundos.

## Endpoints de la API

- `POST /api/attack/{device_id}`: Fuerza al simulador a entrar en estado `UNDER_ATTACK` (Simulación Zero-Day), generando picos exponenciales de tráfico.
- `POST /api/restore/{device_id}`: Restaura al simulador al estado `NORMAL`.

- `GET /ws/telemetry`: Conexión de WebSocket para recibir datos de telemetría, score de anomalías y alertas críticas a una frecuencia de 1Hz.

## Instrucciones de Despliegue Local

### Requisitos Básicos
- Docker y Docker Compose
- Sistema operativo macOS, Linux o Raspberry Pi OS. 

1. Clona este repositorio.
2. Despliega la plataforma en tu entorno usando Docker Compose.

```bash
docker-compose up -d --build
```

### Accesos

- **SOC Dashboard (Frontend React):** [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend Swagger (Documentación):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **InfluxDB Admin UI:** [http://localhost:8086](http://localhost:8086) (Usuario: admin / Contraseña: adminpassword123)

## Autor y Rol

Desarrollado bajo el rol de Arquitecto de Ciberseguridad Enterprise & Ingeniero DevSecOps.
