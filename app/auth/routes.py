"""Routes for user registration, login, and token refresh."""

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.auth.models import User
from app.auth.schemas import (
    UserLoginSchema,
    UserRegistrationSchema,
    UserResponseSchema,
)
from app.error_handlers import InvalidUsage
from app.extensions import db

auth_bp = Blueprint("auth", __name__)
registration_schema = UserRegistrationSchema()
login_schema = UserLoginSchema()


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user and return user data with access tokens."""
    data = request.get_json() or {}
    try:
        validated = registration_schema.load(data)
    except ValidationError as err:
        raise InvalidUsage(message=err.messages, status_code=400)

    email = validated["email"].lower()
    password = validated["password"]

    # Log that someone is attempting to register
    current_app.logger.info("Attempting registration for email=%s", email)

    if User.query.filter_by(email=email).first():
        current_app.logger.warning(
            "Password validation failed for email=%s", email
        )
        raise InvalidUsage(message="Email already registered", status_code=409)

    new_user = User(email=email)
    try:
        new_user.set_password(password)
    except ValueError as err:
        current_app.logger.warning(
            "Password validation failed for email=%s: %s", email, str(err)
        )
        raise InvalidUsage(message=str(err), status_code=400)
    except Exception as e:
        current_app.logger.error(
            "Unexpected error setting password for email=%s: %s", email, str(e)
        )
        raise InvalidUsage(message="Registration failed", status_code=500)

    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if "unique constraint" in str(e.orig).lower():
            current_app.logger.info(
                "Registration unique constraint violation for email=%s", email
            )
            raise InvalidUsage(
                message="Email already registered", status_code=409
            )
        current_app.logger.error(
            "Database error on registration for email=%s: %s", email, str(e)
        )
        raise InvalidUsage(message="Registration failed", status_code=500)

    current_app.logger.info(
        "User registered successfully: email=%s, user_id=%d",
        email,
        new_user.id,
    )

    return (
        jsonify(
            {
                "message": "User registered successfully",
                "user": UserResponseSchema().dump(new_user),
            }
        ),
        201,
    )


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login a user and return access and refresh tokens."""
    data = request.get_json() or {}

    try:
        validated = login_schema.load(data)
    except ValidationError as err:
        current_app.logger.warning("Login validation failed: %s", err.messages)
        raise InvalidUsage(message=err.messages, status_code=400)

    email = validated["email"].lower()
    password = validated["password"]

    # Log that someone is attempting to login
    current_app.logger.info("Login attempt for email=%s", email)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        current_app.logger.warning("Invalid credentials for email=%s", email)
        raise InvalidUsage(message="Invalid credentials", status_code=401)

    if not user.is_active:
        current_app.logger.warning(
            "Inactive account login attempt for email=%s", email
        )
        raise InvalidUsage(message="Account is inactive", status_code=403)

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    current_app.logger.info(
        "Login successful for email=%s, user_id=%d", email, user.id
    )

    return (
        jsonify(
            {"access_token": access_token, "refresh_token": refresh_token}
        ),
        200,
    )


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh the access token using a valid refresh token."""
    current_user_id = get_jwt_identity()
    current_app.logger.info(
        "Refresh token used by user_id=%d", current_user_id
    )

    new_token = create_access_token(identity=current_user_id)
    return jsonify({"access_token": new_token}), 200
