FROM python:3.12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends iproute2 iputils-ping iperf3 \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY servidor.py cliente.py ./
