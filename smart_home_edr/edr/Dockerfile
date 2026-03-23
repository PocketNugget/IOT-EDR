FROM python:3.10-slim

RUN apt-get update && apt-get install -y build-essential gcc gfortran python3-dev \
    libopenblas-dev liblapack-dev

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "context_detector.py"]
