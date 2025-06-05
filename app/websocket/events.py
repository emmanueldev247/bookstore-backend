"""Events for WebSocket connections in the bookstore application."""

from flask import current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_socketio import emit, join_room, leave_room


class OrderNamespace:
    """Encapsulates WebSocket event handlers for the '/orders' namespace."""

    namespace = "/api/ws/orders"

    @classmethod
    def register(cls, socketio):
        """Register all event handlers on the given SocketIO instance."""
        # CONNECT
        @socketio.on("connect", namespace=cls.namespace)
        def on_connect():
            """Connect client to the WebSocket."""
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                room = f"user_{user_id}"
                join_room(room)
                current_app.logger.info(
                    "WebSocket connected: user_id=%s joined room %s",
                    user_id,
                    room,
                )

                emit("connected", {"msg": f"Joined room {room}"}, room=room)

            except Exception as e:
                current_app.logger.warning(
                    "WebSocket connection rejected: invalid JWT; error=%s",
                    str(e),
                )
                # Reject the connection by raising a ConnectionRefusedError
                raise ConnectionRefusedError("Authentication failed")

        # DISCONNECT
        @socketio.on("disconnect", namespace=cls.namespace)
        def on_disconnect():
            """Disconnect client."""
            current_app.logger.info("WebSocket disconnected")

        # SUBSCRIBE TO ORDER STATUS
        @socketio.on("order_status_subscribe", namespace=cls.namespace)
        def on_subscribe(data):
            """Subscribe to a specific order."""
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                order_id = data.get("order_id")
                if not order_id:
                    current_app.logger.warning(
                        "WebSocket subscribe failed: "
                        "missing order_id; user_id=%s",
                        user_id,
                    )
                    return

                room = f"order_{order_id}"
                join_room(room)
                current_app.logger.info(
                    "WebSocket: user_id=%s subscribed "
                    "to order_id=%s (room=%s)",
                    user_id,
                    order_id,
                    room,
                )
                emit(
                    "subscribed",
                    {"msg": f"Subscribed to order {order_id}"},
                    room=room,
                )
            except Exception as e:
                current_app.logger.error(
                    "WebSocket subscribe error: %s", str(e)
                )

        # UNSUBSCRIBE FROM ORDER STATUS
        @socketio.on("order_status_unsubscribe", namespace=cls.namespace)
        def on_unsubscribe(data):
            """Unsubscribe from a specific order."""
            try:
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                order_id = data.get("order_id")
                if not order_id:
                    current_app.logger.warning(
                        "WebSocket unsubscribe failed: "
                        "missing order_id; user_id=%s",
                        user_id,
                    )
                    return

                room = f"order_{order_id}"
                emit(
                    "unsubscribed",
                    {"msg": f"Unsubscribed from order {order_id}"},
                    room=room,
                )
                leave_room(room)
                current_app.logger.info(
                    "WebSocket: user_id=%s unsubscribed from "
                    "order_id=%s (room=%s)",
                    user_id,
                    order_id,
                    room,
                )
            except Exception as e:
                current_app.logger.error(
                    "WebSocket unsubscribe error: %s", str(e)
                )
