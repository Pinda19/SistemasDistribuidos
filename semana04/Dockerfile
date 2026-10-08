FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping iproute2 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
CMD ["sleep", "infinity"]
