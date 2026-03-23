FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias base necesarias para compilacion de paquetes cientificos en ARM64
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY detector.py .
COPY response_handler.py .
COPY run.py .

CMD ["python", "-u", "run.py"]
