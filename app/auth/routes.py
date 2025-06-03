"""Routes for user registration, login, and token refresh."""

from flask import current_app
from flask_smorest import Blueprint
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import ValidationError
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError

from app.auth.models import User
from app.auth.schemas import (
    TokenResponseWrapper,
    UserAuthSchema,
    UserResponseWrapper,
)
from app.error_handlers import InvalidUsage
from app.extensions import db
from app.utils.validate_password import validate_strong_password


auth_blp = Blueprint(
    "auth",
    "auth",
    url_prefix="/api/auth",
    description="User registration, login, and token refresh",
)


@auth_blp.route("/register", methods=["POST"])
@auth_blp.arguments(UserAuthSchema, location="json")
@auth_blp.response(201, UserResponseWrapper)
def register(validated_data):
    """Register a new user and return user data with access tokens."""
    email = validated_data["email"].lower()
    password = validated_data["password"]

    if not email or "@" not in email:
        raise InvalidUsage(
            message="Please provide a valid email address.", status_code=400
        )

    try:
        validate_strong_password(password)
    except ValidationError as err:
        raise InvalidUsage(message=err, status_code=400)

    current_app.logger.info("Attempting registration for email=%s", email)

    if User.query.filter_by(email=email).first():
        current_app.logger.warning(
            "Attempt to register already-existing email=%s",
            email,
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
        if isinstance(e.orig, UniqueViolation):
            current_app.logger.info(
                "Registration unique constraint violation for email=%s", email
            )
            raise InvalidUsage(
                message="Email already registered", status_code=409
            )

        if "unique" in str(e.orig).lower():
            current_app.logger.info(
                "Registration unique constraint violation for email=%s", email
            )
            raise InvalidUsage(
                message="Email already registered", status_code=409
            )

        raise InvalidUsage(message="Registration failed", status_code=500)

    current_app.logger.info(
        "User registered successfully: email=%s, user_id=%d",
        email,
        new_user.id,
    )

    return {
        "status": "success",
        "message": "user registered successfully.",
        "data": new_user,
    }


@auth_blp.route("/login", methods=["POST"])
@auth_blp.arguments(UserAuthSchema, location="json")
@auth_blp.response(
    200, TokenResponseWrapper, description="Return access & refresh tokens"
)
def login(validated_data):
    """Login a user and return access and refresh tokens."""
    email = validated_data["email"].lower()
    password = validated_data["password"]

    # Log that someone is attempting to login
    current_app.logger.info("Login attempt for email=%s", email)

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        current_app.logger.warning("Invalid credentials for email=%s", email)
        raise InvalidUsage(message="Invalid credentials", status_code=401)

    if not user.is_active:
        current_app.logger.warning(
            "Inactive account login attempt for email=%s",
            email,
        )
        raise InvalidUsage(message="Account is inactive", status_code=403)

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    current_app.logger.info(
        "Login successful for email=%s, user_id=%d", email, user.id
    )

    return {
        "status": "success",
        "message": "login successful.",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
        },
    }


@auth_blp.route("/refresh", methods=["POST"])
@auth_blp.response(200, TokenResponseWrapper)
@auth_blp.doc(security=[{"BearerAuth": []}])
@jwt_required(refresh=True)
def refresh():
    """Refresh the access token using a valid refresh token."""
    current_user_id = get_jwt_identity()
    current_app.logger.info(
        "Refresh token used by user_id=%d", current_user_id
    )
    new_token = create_access_token(identity=current_user_id)
    return {
        "status": "success",
        "message": "User profile fetched successfully.",
        "data": {"access_token": new_token},
    }


@auth_blp.route("/me", methods=["GET"])
@auth_blp.response(200, UserResponseWrapper)
@auth_blp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def get_current_user():
    """Return the currently authenticated user's profile data."""
    current_user_id = get_jwt_identity()

    user = User.query.get(current_user_id)
    if not user:
        current_app.logger.warning(
            "User not found for user_id=%s", current_user_id
        )
        raise InvalidUsage(message="User not found", status_code=404)

    current_app.logger.info("Fetched profile for user_id=%s", current_user_id)
    return {
        "status": "success",
        "message": "User profile fetched successfully.",
        "data": user,
    }
