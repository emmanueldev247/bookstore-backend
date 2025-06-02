"""
Initialize and manage Flask extensions for the application.

This module provides instances of SQLAlchemy, JWTManager,
Flask-Smorest, etc.
"""
from typing import Any, Dict, Optional, Tuple

from flask import Flask, Response, jsonify
from werkzeug.exceptions import HTTPException


class InvalidUsage(Exception):
    """
    Raise to signal invalid API usage scenarios.

    Allows custom messages, status codes, and additional payload data.
    """

    status_code: int = 400

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize an InvalidUsage exception.

        Args:
            message (str): A descriptive error message.
            status_code (Optional[int]): The HTTP status code to return.
                Defaults to 400.
            payload (Optional[Dict[str, Any]]): Additional data to include
                in the error response.
        """
        super().__init__(message)
        if status_code:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception details to a dictionary for JSON response.

        Returns:
            Dict[str, Any]: A dictionary containing error details,
            including the message and any specified payload.
        """
        rv: Dict[str, Any] = dict(self.payload or {})
        rv["message"] = str(self)
        return rv


def register_error_handlers(app: Flask) -> None:
    """
    Register custom error handlers for the Flask application.

    This configures handlers for:
    - InvalidUsage: Custom API-specific errors.
    - HTTPException: Built-in HTTP errors (404, 405, etc.).
    - Exception: Catch-all for any other unhandled exceptions.

    Args:
        app (Flask): The Flask application instance to register handlers with.
    """

    @app.errorhandler(InvalidUsage)
    def handle_invalid_usage(error: InvalidUsage) -> Response:
        """
        Handle InvalidUsage exceptions and return JSON response.

        Args:
            error (InvalidUsage): The custom exception that was raised.

        Returns:
            Response: A Flask JSON response containing the error message
            and any payload, with the appropriate HTTP status code.
        """
        response: Response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException) -> Tuple[Response, int]:
        """
        Handle HTTPException errors (e.g., 404, 405).

        Returns a JSON response with the error description and status code.

        Args:
            e (HTTPException): The caught HTTPException instance.

        Returns:
            Tuple[Response, int]: A Flask JSON response with the error
            description and the HTTP status code.
        """
        return jsonify({"message": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_general_exception(e: Exception) -> Tuple[Response, int]:
        """
        Handle uncaught exceptions not handled by other handlers.

        Logs the exception and returns a generic "Internal Server Error" JSON
        response with a 500 status code.

        Args:
            e (Exception): The unhandled exception instance.

        Returns:
            Tuple[Response, int]: A Flask JSON response with a generic
            error message and a 500 status code.
        """
        app.logger.exception(e)
        return jsonify({"message": "Internal Server Error"}), 500
