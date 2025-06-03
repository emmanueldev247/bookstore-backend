"""SQLAlchemy models for user authentication and management."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils.validate_password import validate_strong_password
from app.orders.models import CartItem


class User(db.Model):
    """User model for the bookstore application."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_superadmin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    reviews = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    cart_items = relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        """Set the user's password after validating it."""
        validate_strong_password(password)
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the password matches the stored hashed password."""
        return check_password_hash(self.password_hash, password)

    def add_to_cart(self, book_id: int, quantity: int = 1):
        """Add a book to the user’s cart or increment quantity if it exists."""
        existing_item = CartItem.query.filter_by(
            user_id=self.id, book_id=book_id
        ).first()
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = CartItem(
                user_id=self.id, book_id=book_id, quantity=quantity
            )
            db.session.add(new_item)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    def __repr__(self):
        """Return a string representation of the User object."""
        return f"<User {self.email!r}>"
