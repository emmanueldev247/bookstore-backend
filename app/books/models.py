"""Define SQLAlchemy models for categories, books, and reviews."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    CheckConstraint,
    Date,
    Boolean,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship, validates
from typing import Optional

from app.extensions import db


class Category(db.Model):
    """Represents a book category in the database."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    # Relationships
    books = relationship("Book", back_populates="category")

    def __repr__(self) -> str:
        """Return a string representation of the Category object."""
        return f"<Category {self.name}>"


class Book(db.Model):
    """Represents a book in the database."""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    description = Column(Text)
    isbn = Column(String(20), unique=True, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    publication_date = Column(Date)
    category_id = Column(Integer, ForeignKey("categories.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_active = Column(Boolean, default=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price_non_negative"),
        CheckConstraint("stock >= 0", name="check_stock_non_negative"),
    )

    # Relationships
    category = relationship("Category", back_populates="books")
    reviews = relationship(
        "Review", back_populates="book", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return a string representation of the Book object."""
        return f"<Book {self.title!r} by {self.author!r}>"

    @property
    def average_rating(self) -> Optional[float]:
        """
        Calculate and return average rating across all reviews for this book.

        Returns:
            float: Average rating rounded to 2 decimal places, or None
                    if there are no reviews.
        """
        if not self.reviews:
            return None
        total: float = sum(review.rating for review in self.reviews)
        return round(total / len(self.reviews), 2)


class Review(db.Model):
    """Represents a user's review for a book."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "rating >= 1 AND rating <= 5", name="check_rating_range"
        ),
        db.UniqueConstraint("user_id", "book_id", name="uq_review_user_book"),
    )

    # Relationships
    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")

    @validates("rating")
    def validate_rating(self, key: str, rating: int) -> int:
        """Validate the 'rating' field."""
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return rating

    def __repr__(self) -> str:
        """Return a string representation of the Review object."""
        return (
            f"<Review {self.rating} stars by User {self.user_id} "
            f"on Book {self.book_id}>"
        )
