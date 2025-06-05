#!/bin/sh

set -e

echo "[web] Waiting for Postgres..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "[web] Postgres is ready ✅"

echo "[web] Waiting for RabbitMQ..."
while ! nc -z rabbitmq 5672; do
  sleep 1
done
echo "[web] RabbitMQ is ready ✅"

echo "[web] Running migrations..."
flask db upgrade

python seed.py

if [ "$FLASK_ENV" = "development" ]; then
  echo "[web] Starting Flask dev server..."
  exec flask run --host=0.0.0.0 --port=5000
else
  echo "[web] Starting Gunicorn in production mode..."
  exec gunicorn -k eventlet -w 2 -b 0.0.0.0:5000 app:create_app()
fi
