"""Inventory Service Consumer."""

import json
import logging
import pika
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from app.config import InventoryConfig
from app.extensions import db
from app.models import Book, Order

from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.config.from_object(InventoryConfig())

with app.app_context():
    db.init_app(app)

app.logger.setLevel(logging.INFO)


def handle_order_paid(ch, method, properties, body):
    """Process 'order.paid' events."""
    try:
        data = json.loads(body)
        order_id = data.get("order_id")
        items = data.get("items", [])
    except json.JSONDecodeError as e:
        app.logger.error("Inventory: Invalid JSONin 'order.paid': %s", str(e))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    except Exception as e:
        app.logger.error("Inventory: Error processing message: %s", str(e))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    app.logger.info(
        "Inventory: Received 'order.paid' for order_id=%s", order_id
    )

    with app.app_context():
        order = db.session.get(Order, order_id)
        if not order:
            app.logger.warning(
                "Inventory: Order not found (order_id=%s)", order_id
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if order.inventory_processed:
            app.logger.info(
                "Inventory: Already processed for order_id=%s; skipping",
                order_id,
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        try:
            app.logger.info(
                "Inventory: Processing order_id=%s with items: %s",
                order_id,
                items,
            )
            # 1) Pre-check: ensure all items have sufficient stock
            for it in items:
                book_id = it.get("book_id")
                qty = it.get("quantity", 0)

                book = db.session.get(Book, book_id)
                if not book or book.stock < qty:
                    app.logger.error(
                        "Inventory: Insufficient stock for "
                        "book_id=%s (needed=%s, available=%s) in order_id=%s",
                        book_id,
                        qty,
                        getattr(book, "stock", 0),
                        order_id,
                    )
                    return

            # 2) All checks passed—safe to decrement
            for it in items:
                book_id = it.get("book_id")
                qty = it.get("quantity", 0)

                book = db.session.get(Book, book_id)
                book.stock -= qty
                db.session.add(book)

            # Mark order as processed
            order.inventory_processed = True
            db.session.add(order)
            db.session.commit()

            app.logger.info(
                "Inventory: Stock updated and "
                "marked processed for order_id=%s",
                order_id,
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except SQLAlchemyError as db_err:
            db.session.rollback()
            app.logger.error(
                "Inventory: Database error while processing order_id=%s: %s",
                order_id,
                str(db_err),
            )
            return

        except Exception as ex:
            db.session.rollback()
            app.logger.error(
                "Inventory: Unexpected error processing order_id=%s: %s",
                order_id,
                str(ex),
            )
            return


def handle_order_cancelled(ch, method, properties, body):
    """Process 'order.cancelled' and 'order.refunded' events."""
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        app.logger.error(
            "Inventory: Invalid JSON in 'order.cancelled': %s", str(e)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    except Exception as e:
        app.logger.error("Inventory: Error processing message: %s", str(e))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    order_id = data.get("order_id")
    app.logger.info(
        "Inventory: Received 'order.cancelled' for order_id=%s", order_id
    )

    with app.app_context():
        order = db.session.get(Order, order_id)
        if not order:
            app.logger.warning(
                "Inventory: Order not found: order_id=%s", order_id
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Only restock if we previously processed inventory
        # and haven’t restocked yet
        if not order.inventory_processed:
            app.logger.info(
                "Inventory: order_id=%s was "
                "never processed; no restock needed",
                order_id,
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if order.inventory_restocked:
            app.logger.info(
                "Inventory: Already restocked for order_id=%s; skipping",
                order_id,
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # 1) Restock each item
        try:
            for it in data.get("items", []):
                book = db.session.get(Book, it["book_id"])
                if not book:
                    app.logger.warning(
                        "Inventory: Book not found for "
                        "restock: book_id=%s in order_id=%s",
                        it["book_id"],
                        order_id,
                    )
                    continue
                book.stock += it["quantity"]
                db.session.add(book)

            # 2) Mark restocked
            order.inventory_restocked = True
            db.session.add(order)
            db.session.commit()

            app.logger.info(
                "Inventory: Restocked and marked restocked for order_id=%s",
                order_id,
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except SQLAlchemyError as db_err:
            db.session.rollback()
            app.logger.error(
                "Inventory: DB error while restocking for order_id=%s: %s",
                order_id,
                str(db_err),
            )
            return

        except Exception as ex:
            db.session.rollback()
            app.logger.error(
                "Inventory: Unexpected error while "
                "restocking for order_id=%s: %s",
                order_id,
                str(ex),
            )
            return


def start_consumer():
    """Connect to RabbitMQ."""
    rabbit_url = app.config.get("RABBITMQ_URL")
    if not rabbit_url:
        raise RuntimeError("RABBITMQ_URL is not set in Config.")

    params = pika.URLParameters(rabbit_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(
        exchange="order_events", exchange_type="direct", durable=True
    )

    channel.queue_declare(queue="inventory_update_queue", durable=True)

    channel.queue_bind(
        queue="inventory_update_queue",
        exchange="order_events",
        routing_key="order.paid",
    )

    channel.queue_bind(
        queue="inventory_update_queue",
        exchange="order_events",
        routing_key="order.cancelled",
    )

    app.logger.info(
        "Inventory consumer started. Waiting for "
        "'order.paid', 'order.cancelled' and "
        "'order.refunded' events..."
    )

    channel.basic_qos(prefetch_count=1)

    def unified_callback(ch, method, properties, body):
        routing_key = method.routing_key
        if routing_key == "order.paid":
            handle_order_paid(ch, method, properties, body)
        elif routing_key in ("order.cancelled", "order.refunded"):
            handle_order_cancelled(ch, method, properties, body)
        else:
            app.logger.warning(
                "Inventory: Received unknown routing_key=%s", routing_key
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # Start consuming
    channel.basic_consume(
        queue="inventory_update_queue", on_message_callback=unified_callback
    )

    try:
        channel.start_consuming()
        app.logger.info("Inventory consumer is running...")
    except KeyboardInterrupt:
        app.logger.info("Inventory consumer interrupted; stopping.")
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    start_consumer()
