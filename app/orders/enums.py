"""Order status enumeration for the bookstore application."""

from enum import Enum


class OrderStatus(Enum):
    """Enumeration for different order statuses."""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
