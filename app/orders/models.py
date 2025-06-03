"""Models for managing orders and shopping cart items."""

from sqlalchemy import (
    Column,
    Integer,
    Float,
    DateTime,
    func,
    Enum as SQLEnum,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.extensions import db
from app.orders.enums import OrderStatus


class Order(db.Model):
    """
    Represent a customer order in the database.

    An order is associated with a user and contains multiple order items.
    It tracks the order status and total amount.
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(
        SQLEnum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.PENDING,
    )
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=db.func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0", name="check_order_total_amount_non_negative"
        ),
    )

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        """Return a string representation of the Order object."""
        return (
            f"<Order id={self.id} status={self.status.value} "
            f"total={self.total_amount}>"
        )


class OrderItem(db.Model):
    """Represent a single item within an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_unit = Column(Float, nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "quantity >= 0", name="check_order_item_quantity_non_negative"
        ),
        CheckConstraint(
            "price_unit >= 0", name="check_order_item_price_non_negative"
        ),
    )

    # Relationships
    order = relationship("Order", back_populates="items")
    book = relationship("Book")

    def __repr__(self) -> str:
        """Return a string representation of the OrderItem object."""
        return (
            f"<OrderItem Order:{self.order_id} Book:{self.book_id} "
            f"Qty:{self.quantity} Price:{self.price_unit}>"
        )


class CartItem(db.Model):
    """Represent an item within a user's shopping cart."""

    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uix_user_book_cart"),
        CheckConstraint(
            "quantity >= 0", name="check_cart_item_quantity_non_negative"
        ),
    )

    # Relationships
    user = relationship("User", back_populates="cart_items")
    book = relationship("Book")

    def __repr__(self) -> str:
        """Return a string representation of the CartItem object."""
        return (
            f"<CartItem User:{self.user_id} "
            f"Book:{self.book_id} Qty:{self.quantity}>"
        )
