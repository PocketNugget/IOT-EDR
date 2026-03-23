FROM python:3.10-slim

# Install essentials to avoid scientific dependency build failures in arm64
RUN apt-get update && apt-get install -y build-essential gcc

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "iot_device.py"]
