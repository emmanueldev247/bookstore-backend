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
