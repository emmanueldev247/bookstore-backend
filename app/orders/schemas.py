"""Schemas for the orders module."""

from marshmallow import Schema, fields, validate

from app.orders.enums import OrderStatus
from app.utils.common_schema import StandardResponseSchema


class CartItemCreateSchema(Schema):
    """Schema for creating a new cart item."""

    book_id = fields.Int(required=True)
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="Quantity must be at least 1"),
    )


class CartItemUpdateSchema(Schema):
    """Schema for updating an existing cart item."""

    book_id = fields.Int(required=True)
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, error="Quantity must be at least 1"),
    )


class CartItemReadSchema(Schema):
    """Schema for reading a cart item."""

    cart_item_id = fields.Int(attribute="id", dump_only=True)
    book_id = fields.Int(dump_only=True)
    title = fields.String(dump_only=True)
    author = fields.String(dump_only=True)
    price = fields.Float(dump_only=True)
    quantity = fields.Int(dump_only=True)
    subtotal = fields.Float(dump_only=True)
    added_at = fields.DateTime(dump_only=True)


class CartListDataSchema(Schema):
    """Schema for the data returned by the cart list endpoint."""

    items = fields.List(fields.Nested(CartItemReadSchema), required=True)
    total_amount = fields.Float(required=True)


class CartListResponseWrapper(StandardResponseSchema):
    """Schema for the response of the cart list endpoint."""

    data = fields.Nested(CartListDataSchema, required=True)


class SimpleMessageSchema(StandardResponseSchema):
    """Schema for a simple message response."""

    data = fields.Raw(allow_none=True)


class OrderItemReadSchema(Schema):
    """Serialize a single OrderItem."""

    id = fields.Int(dump_only=True)
    book_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    price_unit = fields.Float(required=True)
    author = fields.String(
        dump_only=True,
        attribute="book.author",
        description="The author of the book for this order item",
    )
    title = fields.String(
        dump_only=True,
        attribute="book.title",
        description="The title of the book for this order item",
    )


class OrderReadSchema(Schema):
    """Serialize a single Order, including its items."""

    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    status = fields.String(
        validate=validate.OneOf([e.value for e in OrderStatus]), dump_only=True
    )
    total_amount = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    items = fields.List(fields.Nested(OrderItemReadSchema), dump_only=True)


class OrderResponseWrapper(StandardResponseSchema):
    """Wrap a single Order under envelope."""

    data = fields.Nested(OrderReadSchema, required=True)


class OrdersListResponseWrapper(StandardResponseSchema):
    """Wrap a list of Orders under envelope."""

    data = fields.List(fields.Nested(OrderReadSchema), required=True)


class OrderStatusUpdateSchema(Schema):
    """
    Validate a payload containing a single 'status' field.

    ensuring it’s one of the OrderStatus enum values.
    """

    status = fields.String(
        required=True,
        validate=validate.OneOf(
            [e.value for e in OrderStatus],
            error="Status must be one of: "
            + ", ".join([e.value for e in OrderStatus]),
        ),
    )
