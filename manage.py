"""This script is used to run the Flask application with SocketIO support."""

from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    # Use socketio.run() instead of app.run()
    socketio.run(app, host="0.0.0.0", port=5000)
