
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema para MySQL
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

EXPOSE 3000

# Usar Gunicorn con 4 workers para producción
CMD ["sh", "-c", "python wait-for-mysql.py && gunicorn --bind 0.0.0.0:3000 --workers 4 --worker-class gevent --worker-connections 1000 --timeout 120 --max-requests 2000 --max-requests-jitter 200 --keep-alive 30 --backlog 2048 src.main:app"]
