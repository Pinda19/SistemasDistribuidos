FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# el código se monta como volumen desde la carpeta del equipo (ver compose)
