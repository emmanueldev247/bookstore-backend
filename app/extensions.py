"""
Initialize and provide instances of various Flask extensions.

These extensions are configured and bound to the Flask application
within the create_app factory function.
"""
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

# Extensions for the Flask application typed and initialized here
db: SQLAlchemy = SQLAlchemy()
jwt: JWTManager = JWTManager()
socketio: SocketIO = SocketIO(
    cors_allowed_origins="*",  # Allow CORS for WebSocket
)
api: Api = Api()
cors: CORS = CORS()
migrate: Migrate = Migrate()
