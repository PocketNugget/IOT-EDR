FROM python:3.10-slim

# Install essentials and build deps for ARM64 SciPy & Sklearn building natively
RUN apt-get update && apt-get install -y build-essential gcc gfortran python3-dev \
    libopenblas-dev liblapack-dev

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start both scrips sequentially returning the background task correctly inside the container scope
CMD ["sh", "-c", "python -u response_handler.py & python -u detector.py"]
