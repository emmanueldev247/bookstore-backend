"""Define REST endpoints for managing orders in the bookstore application."""

from flask import current_app, request
from flask_jwt_extended import get_jwt_identity
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth.permissions import admin_required, protected
from app.error_handlers import InvalidUsage
from app.extensions import db
from app.models import Order, OrderItem, Book, CartItem
from app.orders.enums import OrderStatus
from app.orders.schemas import (
    CartListResponseWrapper,
    SimpleMessageSchema,
    CartItemCreateSchema,
    CartItemUpdateSchema,
    OrderResponseWrapper,
    OrdersListResponseWrapper,
    OrderStatusUpdateSchema,
)
from app.utils.blueprints import orders_blp, cart_blp


@cart_blp.route("/")
class CartResource(MethodView):
    """Resource for managing the user's shopping cart."""

    @cart_blp.response(200, CartListResponseWrapper)
    @protected
    def get(self):
        """List all cart items for the current user."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested cart contents", user_id
        )

        try:
            # Query all CartItem rows for this user, joining Book for details
            cart_items = (
                db.session.query(CartItem)
                .filter_by(user_id=user_id)
                .join(Book)
                .all()
            )

            items_list = []
            total_amount = 0.0
            for item in cart_items:
                subtotal = item.quantity * item.book.price
                total_amount += subtotal
                items_list.append(
                    {
                        "cart_item_id": item.id,
                        "book_id": item.book.id,
                        "title": item.book.title,
                        "author": item.book.author,
                        "price": item.book.price,
                        "quantity": item.quantity,
                        "subtotal": float(round(subtotal, 2)),
                        "added_at": item.added_at,
                    }
                )

            current_app.logger.info(
                "Found %d items in cart for user_id=%s; total_amount=%.2f",
                len(items_list),
                user_id,
                total_amount,
            )

            return {
                "status": "success",
                "message": "Cart retrieved successfully.",
                "data": {
                    "items": items_list,
                    "total_amount": round(total_amount, 2),
                },
            }

        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Database error retrieving cart for user_id=%s: %s",
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to retrieve cart due to a database error.",
                status_code=500,
            )

        except Exception as e:
            current_app.logger.error(
                "Unexpected error in get_cart for user_id=%s: %s",
                user_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while retrieving the cart.",
                status_code=500,
            )

    @cart_blp.arguments(CartItemCreateSchema, location="json")
    @cart_blp.response(201, SimpleMessageSchema)
    @protected
    def post(self, validated_data):
        """Add a book to the user's cart."""
        user_id = get_jwt_identity()
        book_id = validated_data["book_id"]
        quantity = validated_data["quantity"]

        current_app.logger.info(
            "User (user_id=%s) adding book_id=%s (qty=%s) to cart",
            user_id,
            book_id,
            quantity,
        )

        try:
            # 1) Verify the book exists and is active
            book = Book.query.get(book_id)
            if not book or not book.is_active:
                current_app.logger.warning(
                    "Book not found or inactive "
                    "when adding to cart: book_id=%s",
                    book_id,
                )
                raise InvalidUsage(
                    message="Book not found.",
                    status_code=404,
                )

            # 2) Check if a CartItem already exists for this user & book
            existing = CartItem.query.filter_by(
                user_id=user_id, book_id=book_id
            ).first()
            if existing:
                # Increase quantity
                existing.quantity += quantity
                current_app.logger.info(
                    "Incremented quantity for existing cart_item_id=%s to %s",
                    existing.id,
                    existing.quantity,
                )
            else:
                # Create a new CartItem
                new_item = CartItem(
                    user_id=user_id, book_id=book_id, quantity=quantity
                )
                db.session.add(new_item)
                current_app.logger.info(
                    "Created new cart_item for "
                    "user_id=%s, book_id=%s, qty=%s",
                    user_id,
                    book_id,
                    quantity,
                )

            db.session.commit()
            return {
                "status": "success",
                "message": "Item added to cart.",
                "data": None,
            }, 201

        except IntegrityError as ie:
            db.session.rollback()
            msg = str(getattr(ie, "orig", ie))
            if "uix_user_book_cart" in msg.lower() or "unique" in msg.lower():
                current_app.logger.warning(
                    "Duplicate cart item prevented for user_id=%s, book_id=%s",
                    user_id,
                    book_id,
                )
                raise InvalidUsage(
                    message="Item already in cart; quantity "
                    "was incremented automatically.",
                    status_code=400,
                )
            current_app.logger.error(
                "Integrity error adding to cart for user_id=%s: %s",
                user_id,
                msg,
            )
            raise InvalidUsage(
                message="Failed to add item to cart due to invalid data.",
                status_code=400,
            )

        except SQLAlchemyError as db_err:
            db.session.rollback()
            current_app.logger.error(
                "Database error adding to cart for user_id=%s: %s",
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to add item to cart due to a database error.",
                status_code=500,
            )

        except InvalidUsage:
            raise

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in add_to_cart for user_id=%s: %s",
                user_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred while adding to cart.",
                status_code=500,
            )

    @cart_blp.arguments(CartItemUpdateSchema, location="json")
    @cart_blp.response(200, SimpleMessageSchema)
    @protected
    def patch(self, validated_data):
        """Update quantity of a specific book in the cart."""
        user_id = get_jwt_identity()
        book_id = validated_data["book_id"]
        quantity = validated_data["quantity"]

        current_app.logger.info(
            "User (user_id=%s) updating cart item book_id=%s to qty=%s",
            user_id,
            book_id,
            quantity,
        )

        try:
            # 1) Find the CartItem for this user & book
            cart_item = CartItem.query.filter_by(
                user_id=user_id, book_id=book_id
            ).first()
            if not cart_item:
                current_app.logger.warning(
                    "Cart item not found for user_id=%s, book_id=%s",
                    user_id,
                    book_id,
                )
                raise InvalidUsage(
                    message="Cart item not found.", status_code=404
                )

            # 2) Update the quantity
            cart_item.quantity = quantity
            db.session.commit()

            current_app.logger.info(
                "Cart item updated: cart_item_id=%s to qty=%s",
                cart_item.id,
                quantity,
            )
            return {
                "status": "success",
                "message": "Cart item updated successfully.",
                "data": None,
            }

        except IntegrityError as ie:
            db.session.rollback()
            msg = str(getattr(ie, "orig", ie))
            current_app.logger.error(
                "Integrity error updating cart for user_id=%s: %s",
                user_id,
                msg,
            )
            raise InvalidUsage(
                message="Failed to update cart item due to invalid data.",
                status_code=400,
            )

        except SQLAlchemyError as db_err:
            db.session.rollback()
            current_app.logger.error(
                "Database error updating cart for user_id=%s: %s",
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to update cart item due to a database error.",
                status_code=500,
            )

        except InvalidUsage:
            raise

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in update_cart_item for user_id=%s: %s",
                user_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while updating cart item.",
                status_code=500,
            )

    @cart_blp.response(200, SimpleMessageSchema)
    @protected
    def delete(self):
        """Remove a book from the user's cart."""
        user_id = get_jwt_identity()
        cart_item_id = request.args.get("cart_item_id", type=int)

        current_app.logger.info(
            "User (user_id=%s) attempting to delete cart_item_id=%s",
            user_id,
            cart_item_id,
        )

        # 1) Validate cart_item_id presence
        if cart_item_id is None:
            current_app.logger.warning(
                "Missing cart_item_id in delete request for user_id=%s",
                user_id,
            )
            raise InvalidUsage(
                message="cart_item_id query parameter is required.",
                status_code=400,
            )

        try:
            # 2) Fetch the CartItem
            cart_item = CartItem.query.filter_by(
                id=cart_item_id, user_id=user_id
            ).first()
            if not cart_item:
                current_app.logger.warning(
                    "Cart item not found for deletion: "
                    "cart_item_id=%s, user_id=%s",
                    cart_item_id,
                    user_id,
                )
                raise InvalidUsage(
                    message="Cart item not found.", status_code=404
                )

            # 3) Delete and commit
            db.session.delete(cart_item)
            db.session.commit()

            current_app.logger.info(
                "Cart item deleted successfully: cart_item_id=%s", cart_item_id
            )
            return {
                "status": "success",
                "message": "Cart item removed successfully.",
                "data": None,
            }

        except SQLAlchemyError as db_err:
            db.session.rollback()
            current_app.logger.error(
                "Database error deleting cart_item_id=%s for user_id=%s: %s",
                cart_item_id,
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to remove cart item due to a database error.",
                status_code=500,
            )

        except InvalidUsage:
            raise

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in delete_cart_item for user_id=%s: %s",
                user_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while removing the cart item.",
                status_code=500,
            )


@cart_blp.route("/clear", methods=["DELETE"])
class CartClearResource(MethodView):
    """Resource for clearing the entire cart."""

    @cart_blp.response(200, SimpleMessageSchema)
    @protected
    def delete(self):
        """Clear all items from the current user's cart."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested to clear the cart", user_id
        )

        try:
            deleted = (
                db.session.query(CartItem)
                .filter_by(user_id=user_id)
                .delete(synchronize_session=False)
            )
            db.session.commit()
            current_app.logger.info(
                "Cleared %d items from cart for user_id=%s", deleted, user_id
            )
            return {
                "status": "success",
                "message": "Cart cleared successfully.",
                "data": None,
            }
        except SQLAlchemyError as db_err:
            db.session.rollback()
            current_app.logger.error(
                "Database error clearing cart for user_id=%s: %s",
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to clear cart due to a database error.",
                status_code=500,
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in clear_cart for user_id=%s: %s",
                user_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while clearing the cart.",
                status_code=500,
            )


@orders_blp.route("/")
class OrdersResource(MethodView):
    """Place a new order or list all orders for the current user."""

    @orders_blp.response(201, OrderResponseWrapper)
    @protected
    def post(self):
        """Place an order using the current user's cart."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) is attempting to place an order", user_id
        )

        try:
            # 1) Fetch all CartItems for this user, joined with Book
            cart_items = (
                db.session.query(CartItem)
                .filter_by(user_id=user_id)
                .join(Book)
                .all()
            )

            if not cart_items:
                current_app.logger.warning(
                    "Cart is empty for user_id=%s; cannot place order",
                    user_id,
                )
                raise InvalidUsage(
                    message="Cannot place order. Your cart is empty.",
                    status_code=400,
                )

            # 2) Validate each cart item and compute totals
            total_amount = 0.0
            order_items_data = []
            for ci in cart_items:
                book = ci.book
                if not book or not book.is_active:
                    current_app.logger.warning(
                        "Book not found or inactive in cart "
                        "for user_id=%s: book_id=%s",
                        user_id,
                        ci.book_id,
                    )
                    raise InvalidUsage(
                        message=f"Book (id={ci.book_id}) not "
                        "found or inactive.",
                        status_code=404,
                    )

                if book.stock < ci.quantity:
                    current_app.logger.warning(
                        "Insufficient stock for book_id=%s: "
                        "requested %s, available %s",
                        book.id,
                        ci.quantity,
                        book.stock,
                    )
                    raise InvalidUsage(
                        message=(
                            f"Insufficient stock for '{book.title}'. "
                            f"Requested {ci.quantity}, available {book.stock}."
                        ),
                        status_code=400,
                    )

                price_unit = book.price
                subtotal = price_unit * ci.quantity
                total_amount += subtotal

                order_items_data.append(
                    {
                        "book_id": book.id,
                        "quantity": ci.quantity,
                        "price_unit": price_unit,
                    }
                )

            # 3) Create the Order
            new_order = Order(
                user_id=user_id,
                total_amount=round(total_amount, 2),  # ensure rounding
            )
            db.session.add(new_order)
            db.session.flush()  # get new_order.id

            # 4) Create each OrderItem and reduce Book.stock
            for item_data in order_items_data:
                oi = OrderItem(
                    order_id=new_order.id,
                    book_id=item_data["book_id"],
                    quantity=item_data["quantity"],
                    price_unit=item_data["price_unit"],
                )
                db.session.add(oi)

                # Reduce stock in the Book table
                Book.query.filter_by(id=item_data["book_id"]).update(
                    {"stock": Book.stock - item_data["quantity"]}
                )

            # 5) Clear the user's cart
            deleted_count = (
                db.session.query(CartItem)
                .filter_by(user_id=user_id)
                .delete(synchronize_session=False)
            )

            db.session.commit()
            current_app.logger.info(
                "Order placed successfully: order_id=%s for "
                "user_id=%s; cleared %d cart items",
                new_order.id,
                user_id,
                deleted_count,
            )

            # 6) Reload the order with its items for serialization
            order = Order.query.options(
                db.joinedload(Order.items).joinedload(OrderItem.book)
            ).get(new_order.id)

            return {
                "status": "success",
                "message": "Order placed successfully.",
                "data": order,
            }, 201

        except IntegrityError as ie:
            db.session.rollback()
            msg = str(getattr(ie, "orig", ie))
            current_app.logger.error(
                "Integrity error placing order for user_id=%s: %s",
                user_id,
                msg,
            )
            raise InvalidUsage(
                message="Failed to place order due to invalid data.",
                status_code=400,
            )

        except SQLAlchemyError as db_err:
            db.session.rollback()
            current_app.logger.error(
                "Database error placing order for user_id=%s: %s",
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to place order due to a database error.",
                status_code=500,
            )

        except InvalidUsage:
            raise  # Re-raise known 400/404

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in place_order for user_id=%s: %s",
                user_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred while placing order.",
                status_code=500,
            )

    @orders_blp.response(200, OrdersListResponseWrapper)
    @protected
    def get(self):
        """List all orders placed by the current user."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested their orders", user_id
        )

        try:
            orders = (
                Order.query.filter_by(user_id=user_id)
                .options(db.joinedload(Order.items).joinedload(OrderItem.book))
                .order_by(Order.created_at.desc())
                .all()
            )

            current_app.logger.info(
                "Found %d orders for user_id=%s", len(orders), user_id
            )
            return {
                "status": "success",
                "message": "Orders retrieved successfully.",
                "data": orders,
            }

        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Database error listing orders for user_id=%s: %s",
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to retrieve orders due to a database error.",
                status_code=500,
            )

        except Exception as e:
            current_app.logger.error(
                "Unexpected error in list_orders for user_id=%s: %s",
                user_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while retrieving orders.",
                status_code=500,
            )


@orders_blp.route("/<int:order_id>")
class OrderDetailResource(MethodView):
    """Endpoint to fetch details of a specific order."""

    @orders_blp.response(200, OrderResponseWrapper)
    @protected
    def get(self, order_id):
        """Get detail of a single order (if it belongs to current user)."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested order details for order_id=%s",
            user_id,
            order_id,
        )

        try:
            order = (
                Order.query.filter_by(id=order_id, user_id=user_id)
                .options(db.joinedload(Order.items).joinedload(OrderItem.book))
                .first()
            )

            if not order:
                current_app.logger.warning(
                    "Order not found for user_id=%s: order_id=%s",
                    user_id,
                    order_id,
                )
                raise InvalidUsage(message="Order not found.", status_code=404)

            current_app.logger.info(
                "Order retrieved successfully: order_id=%s for user_id=%s",
                order_id,
                user_id,
            )
            return {
                "status": "success",
                "message": "Order retrieved successfully.",
                "data": order,
            }

        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Database error fetching order_id=%s for user_id=%s: %s",
                order_id,
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to retrieve order due to a database error.",
                status_code=500,
            )

        except InvalidUsage:
            raise  # Propagate 404

        except Exception as e:
            current_app.logger.error(
                "Unexpected error in get_order_detail for "
                "user_id=%s order_id=%s: %s",
                user_id,
                order_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while retrieving the order.",
                status_code=500,
            )


@orders_blp.route("/<int:order_id>/cancel", methods=["POST"])
class OrderCancelResource(MethodView):
    """Endpoint for users to cancel their own pending orders."""

    @orders_blp.response(200, SimpleMessageSchema)
    @protected
    def post(self, order_id):
        """Cancel an order if it is still pending."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested cancellation of order_id=%s",
            user_id,
            order_id,
        )

        try:
            # 1) Fetch the order and verify ownership
            order = Order.query.filter_by(id=order_id, user_id=user_id).first()
            if not order:
                current_app.logger.warning(
                    "Order not found or not owned by user_id=%s: order_id=%s",
                    user_id,
                    order_id,
                )
                raise InvalidUsage(message="Order not found.", status_code=404)

            # 2) Only PENDING orders can be cancelled by the user
            if order.status != OrderStatus.PENDING:
                current_app.logger.warning(
                    "Attempt to cancel non‐pending order_id=%s with status=%s",
                    order_id,
                    order.status.value,
                )
                raise InvalidUsage(
                    message=f"Cannot cancel an order with "
                    f"status '{order.status.value}'.",
                    status_code=400,
                )

            # 3) Perform cancellation
            order.status = OrderStatus.CANCELLED
            db.session.commit()
            current_app.logger.info(
                "Order cancelled successfully: order_id=%s by user_id=%s",
                order_id,
                user_id,
            )

            return {
                "status": "success",
                "message": "Order cancelled successfully.",
                "data": None,
            }

        except SQLAlchemyError as db_err:
            db.session.rollback()
            current_app.logger.error(
                "Database error cancelling order_id=%s for user_id=%s: %s",
                order_id,
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to cancel order due to a database error.",
                status_code=500,
            )

        except InvalidUsage:
            raise

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in cancel_order for "
                "order_id=%s by user_id=%s: %s",
                order_id,
                user_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while cancelling the order.",
                status_code=500,
            )


@orders_blp.route("/<int:order_id>/status", methods=["PATCH"])
class OrderStatusUpdateResource(MethodView):
    """Update an order’s status [Admin-only]."""

    @orders_blp.arguments(OrderStatusUpdateSchema, location="json")
    @orders_blp.response(200, OrderResponseWrapper)
    @admin_required
    @protected
    def patch(self, validated_data, order_id):
        """Update the status of an order. Admin privileges required."""
        new_status_value = validated_data["status"]

        # Logging the attempt
        current_app.logger.info(
            "Admin requested status update for order_id=%s to '%s'",
            order_id,
            new_status_value,
        )

        try:
            # 1) Fetch the order
            order = Order.query.get(order_id)
            if not order:
                current_app.logger.warning(
                    "Order not found for status " "update: order_id=%s",
                    order_id,
                )
                raise InvalidUsage(
                    "Order not found.",
                    status_code=404,
                )

            # 2) If equal, return 400
            if order.status.value == new_status_value:
                current_app.logger.warning(
                    "Attempt to set order_id=%s to its current status '%s'",
                    order_id,
                    new_status_value,
                )
                raise InvalidUsage(
                    message=f"Order already has status '{new_status_value}'.",
                    status_code=400,
                )

            # 3) Update and commit
            order.status = OrderStatus(new_status_value)
            db.session.commit()

            current_app.logger.info(
                "Order status updated successfully: order_id=%s to '%s'",
                order_id,
                new_status_value,
            )

            # 4) Return updated order
            return {
                "status": "success",
                "message": "Order status updated successfully.",
                "data": order,
            }

        except InvalidUsage:
            # Re‐raise known 404 or 400
            raise

        except SQLAlchemyError as db_err:
            db.session.rollback()
            current_app.logger.error(
                "Database error updating status for order_id=%s: %s",
                order_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to update order status "
                "due to a database error.",
                status_code=500,
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in update_order_status "
                "for order_id=%s: %s",
                order_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while updating order status.",
                status_code=500,
            )
