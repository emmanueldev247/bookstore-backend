"""Define health‐check endpoints."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/", strict_slashes=False, methods=["GET"])
def health_check():
    """Return a JSON response indicating service health."""
    return jsonify({"status": "ok"}), 200
