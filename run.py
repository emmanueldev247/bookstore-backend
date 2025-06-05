"""This script is used to run the Flask application with SocketIO support."""

import os
from dotenv import load_dotenv

load_dotenv()

env = os.getenv("FLASK_ENV", "production")

if env == "production":
    import eventlet

    eventlet.monkey_patch()

from app import create_app, socketio  # noqa: E402


app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=True)
