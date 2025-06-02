"""Create and configure the main Flask application."""

import os

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
    api.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    # Register error handlers
    register_error_handlers(app)

    # Register blueprints
    from app.health.routes import health_bp

    app.register_blueprint(health_bp, url_prefix="/api/health")

    return app
