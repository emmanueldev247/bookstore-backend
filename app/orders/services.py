"""Service for publishing order events to RabbitMQ."""

import json
import pika
from flask import current_app
from app.orders.enums import OrderStatus


def _get_connection():
    """Establish a new pika.BlockingConnection."""
    rabbit_url = current_app.config.get("RABBITMQ_URL")
    if not rabbit_url:
        raise RuntimeError("RABBITMQ_URL is not configured.")

    params = pika.URLParameters(rabbit_url)
    return pika.BlockingConnection(params)


def _declare_exchange(channel):
    """Declare the 'order_events' exchange (durable, direct)."""
    channel.exchange_declare(
        exchange="order_events", exchange_type="direct", durable=True
    )


def publish_order_event(
    order_id: int, user_id: int, items: list, status: OrderStatus
):
    """Publish a JSON message to the 'order_events' exchange."""
    routing_key = f"order.{status.value}"

    connection = None
    try:
        connection = _get_connection()
        channel = connection.channel()

        # Ensure the exchange exists
        _declare_exchange(channel)

        payload = {
            "order_id": order_id,
            "user_id": user_id,
            "items": items,
            "status": status.value,
        }
        body = json.dumps(payload)

        channel.basic_publish(
            exchange="order_events",
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json", delivery_mode=2
            ),
        )
        current_app.logger.info(
            "Published RabbitMQ event to 'order_events' "
            "with routing_key='%s' for order_id=%s",
            routing_key,
            order_id,
        )
    except Exception as e:
        # Log any publishing errors for later troubleshooting
        current_app.logger.error(
            "Failed to publish order event (order_id=%s, status=%s): %s",
            order_id,
            status.value,
            str(e),
        )
    finally:
        if connection is not None and not connection.is_closed:
            connection.close()
