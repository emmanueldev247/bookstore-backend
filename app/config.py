"""Define configuration classes for different environments."""
import os
from datetime import timedelta


class Config:
    """
    Base configuration.

    Any setting here is common to all environments unless overridden below.
    """

    # Core flags (default to False/production if not explicitly set)
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ["true", "1"]
    TESTING: bool = os.getenv("TESTING", "False").lower() in ["true", "1"]
    # We keep ENV here so that you can inspect it in your code if needed.
    ENV: str = os.getenv("ENV", "production")

    # Flask/Extension settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_jwt_secret_key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # 1 hour access token
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)  # 1 day refresh token

    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/" "bookstore_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "default_openai_api_key")
    SOCKETIO_MESSAGE_QUEUE: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/",
    )

    # OpenAPI settings (for flask-smorest or similar)
    API_TITLE: str = "Bookstore Backend API"
    API_VERSION: str = "1.0"
    OPENAPI_VERSION: str = "3.0.2"
    OPENAPI_URL_PREFIX: str = "/api"
    OPENAPI_SWAGGER_UI_PATH: str = "/docs"
    OPENAPI_SWAGGER_UI_URL: str = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )


class DevelopmentConfig(Config):
    """
    Configuration for local development.

    Debug & reloader ON; use a local dev database, etc.
    """

    DEBUG: bool = True
    ENV: str = "development"
    SQLALCHEMY_DATABASE_URI: str = (
        "postgresql://debug:debug@localhost:5432/" "bookstore_db"
    )


class TestingConfig(Config):
    """Configuration for testing."""

    DEBUG: bool = True
    ENV: str = "testing"
    SQLALCHEMY_DATABASE_URI: str = (
        "postgresql://test:test@localhost:5432/" "bookstore_db"
    )


class ProductionConfig(Config):
    """
    Configuration for production.

    Debug & auto-reload OFF; use real production database URL, etc.
    """

    DEBUG: bool = False
    ENV: str = "production"
