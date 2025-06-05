#!/bin/sh

set -e

echo "[worker] Waiting for RabbitMQ..."
while ! nc -z rabbitmq 5672; do
  sleep 1
done
echo "[worker] RabbitMQ is ready ✅"

echo "[worker] Starting inventory consumer..."
exec python -u -m app.inventory.consumer
