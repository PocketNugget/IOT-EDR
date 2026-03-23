FROM python:3.10-slim

WORKDIR /app

# Upgrade pip and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator source code
COPY iot_device.py .

CMD ["python", "-u", "iot_device.py"]
