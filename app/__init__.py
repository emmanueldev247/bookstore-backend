"""Create and configure the main Flask application."""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask

from app.error_handlers import register_error_handlers
from app.extensions import api, cors, db, jwt, migrate, socketio


def create_app() -> Flask:
    """Create and return a Flask application instance."""
    app: Flask = Flask(__name__)

    config_name = os.getenv("FLASK_ENV", "production").lower()
    print(f"Configuring app for {config_name} environment")
    if config_name == "development":
        app.config.from_object("app.config.DevelopmentConfig")
    elif config_name == "testing":
        app.config.from_object("app.config.TestingConfig")
    else:
        app.config.from_object("app.config.ProductionConfig")

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, message_queue=app.config["SOCKETIO_MESSAGE_QUEUE"])
    migrate.init_app(app, db)
    cors.init_app(app)
    api.init_app(app)
    api.spec.components.security_scheme(
        "BearerAuth",
        {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
    )

    # Register error handlers
    register_error_handlers(app)

    # Set up logging
    configure_logging(app)

    # Import models to register with SQLAlchemy metadata
    from app import models  # noqa: F401, E402
    from app.auth.routes import auth_blp
    from app.books.routes import books_blp
    from app.health.routes import health_bp

    # Register blueprints

    app.register_blueprint(health_bp, url_prefix="/api/health")
    # app.register_blueprint(auth_blp, url_prefix="/api/auth")

    api.register_blueprint(auth_blp)
    api.register_blueprint(books_blp)

    return app


def configure_logging(app):
    """Configure a rotating file logger and also stream to console."""
    # If there's already a handler, skip (so we don't double-add on re-import)
    if app.logger.handlers:
        return

    # Log format: timestamp, log level, file:line, message
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s:%(lineno)d: %(message)s"
    )

    # -------------------------
    # 1) StreamHandler (console)
    # -------------------------
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)

    # -------------------------
    # 2) RotatingFileHandler (file)
    # -------------------------
    log_dir = app.config.get("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "bookstore.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB per file
        backupCount=5,  # keep up to 5 old log files
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    # Set the overall logging level
    app.logger.setLevel(logging.INFO)
    app.logger.info("Logging is configured.")
