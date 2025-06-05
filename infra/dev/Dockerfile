FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure scripts are executable
RUN chmod +x /app/infra/scripts/entrypoint.web.sh \
    && chmod +x /app/infra/scripts/entrypoint.worker.sh
EXPOSE 5000

# Entrypoints will be handled by docker-compose
