"""Create and configure the main Flask application."""

import logging
import os
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler


load_dotenv()

env = os.getenv("FLASK_ENV", "production")
if env == "production":
    import eventlet

    eventlet.monkey_patch()

from flask import Flask, render_template  # noqa: E402
from app.error_handlers import register_error_handlers  # noqa: E402
from app.extensions import api, cors, db, jwt, migrate, socketio  # noqa: E402

print("Loaded env source:", os.getenv("SOURCE"))


def create_app() -> Flask:
    """Create and return a Flask application instance."""
    base_dir: str = os.path.abspath(os.path.dirname(__file__))
    template_folder: str = os.path.join(base_dir, "templates")
    static_folder: str = os.path.join(base_dir, "static")

    # Create the Flask app instance
    app: Flask = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
        static_url_path="/assets",
    )

    config_name = os.getenv("FLASK_ENV", "production").lower()
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
    from app.orders.routes import cart_blp
    from app.health.routes import health_bp
    from app.orders.routes import orders_blp

    # Register health check blueprint
    app.register_blueprint(health_bp, url_prefix="/api/health")

    # Register the API spec route
    app.add_url_rule("/api/spec", endpoint="spec", view_func=api.spec.to_dict)

    # Register API blueprints
    api.register_blueprint(auth_blp)
    api.register_blueprint(books_blp)
    api.register_blueprint(cart_blp)
    api.register_blueprint(orders_blp)

    # Register WebSocket event handlers
    from app.websocket.events import OrderNamespace

    OrderNamespace.register(socketio)

    @app.route("/")
    def index():
        return render_template("index.html")

    app.logger.info(f"Running in {config_name} mode.")
    app.logger.info(f"Loaded env source: {os.getenv('SOURCE')})")
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
