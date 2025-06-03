"""Utility module for defining Flask blueprints."""
from flask_smorest import Blueprint

auth_blp = Blueprint(
    "auth",
    "auth",
    url_prefix="/api/auth",
    description="User registration, login, and token refresh",
)

books_blp = Blueprint(
    "books",
    "books",
    url_prefix="/api/books",
    description="Books and reviews operations",
)

cart_blp = Blueprint(
    "cart",
    "orders",
    url_prefix="/api/cart",
    description="Cart management operations",
)

orders_blp = Blueprint(
    "orders",
    "orders",
    url_prefix="/api/orders",
    description="Order management operations",
)
