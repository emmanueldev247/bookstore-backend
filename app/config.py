"""Define configuration classes for different environments."""
import os
from datetime import timedelta
from app.error_handlers import InvalidUsage
from typing import List


class Config:
    """
    Base configuration.

    Any setting here is common to all environments unless overridden below.
    """

    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ["true", "1"]
    TESTING: bool = os.getenv("TESTING", "False").lower() in ["true", "1"]
    ENV: str = os.getenv("ENV", "production")

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(hours=3)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=1)
    JWT_TOKEN_LOCATION: List[str] = ["headers", "query_string"]
    JWT_QUERY_STRING_NAME: str = "token"

    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    SOCKETIO_MESSAGE_QUEUE: str = os.getenv("RABBITMQ_URL")
    RABBITMQ_URL: str = SOCKETIO_MESSAGE_QUEUE

    API_TITLE: str = "Bookstore Backend API"
    API_VERSION: str = "1.0"
    OPENAPI_VERSION: str = "3.0.2"
    OPENAPI_URL_PREFIX: str = "/api"
    OPENAPI_SWAGGER_UI_PATH: str = "/docs"
    OPENAPI_SWAGGER_UI_URL: str = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    def __init__(self):
        """Raise if required environment variables are missing."""
        required_vars = {
            "SECRET_KEY": self.SECRET_KEY,
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
            "DATABASE_URL": self.SQLALCHEMY_DATABASE_URI,
        }

        missing = [k for k, v in required_vars.items() if not v]
        if missing:
            raise InvalidUsage(
                message="Missing required environment "
                f"variables: {', '.join(missing)}",
                status_code=500,
            )


class DevelopmentConfig(Config):
    """Configuration for local development."""

    DEBUG: bool = True
    ENV: str = "development"
    SQLALCHEMY_DATABASE_URI: str = (
        "postgresql://debug:debug@localhost:5432/bookstore_db"
    )


class TestingConfig(Config):
    """Configuration for testing."""

    DEBUG: bool = True
    ENV: str = "testing"
    SQLALCHEMY_DATABASE_URI: str = (
        "postgresql://test:test@localhost:5432/bookstore_test"
    )


class ProductionConfig(Config):
    """Configuration for production."""

    DEBUG: bool = False
    ENV: str = "production"


class InventoryConfig:
    """Configuration for Inventory service."""

    @staticmethod
    def init_app(app):
        """Set config from environment and validate."""
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
        app.config["RABBITMQ_URL"] = os.environ.get("RABBITMQ_URL")
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
        app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")

        # Validate all are present
        required_vars = {
            "DATABASE_URL": app.config["SQLALCHEMY_DATABASE_URI"],
            "RABBITMQ_URL": app.config["RABBITMQ_URL"],
            "SECRET_KEY": app.config["SECRET_KEY"],
            "JWT_SECRET_KEY": app.config["JWT_SECRET_KEY"],
        }
        missing = [k for k, v in required_vars.items() if not v]
        if missing:
            raise InvalidUsage(
                f"Missing required env variables: {', '.join(missing)}",
                status_code=500,
            )
