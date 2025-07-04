"""Routes for user registration, login, and token refresh."""

from flask import current_app
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from psycopg2 import errorcodes

from app.auth.permissions import protected
from app.auth.schemas import (
    UserAuthSchema,
    UserResponseWrapper,
    AccessTokenWrapper,
    RefreshTokenWrapper,
)
from app.error_handlers import InvalidUsage
from app.extensions import db
from app.models import User
from app.utils.blueprints import auth_blp
from app.utils.validations import validate_strong_password


@auth_blp.route("/register")
class RegisterResource(MethodView):
    """Register a new user and return user data with tokens."""

    @auth_blp.arguments(UserAuthSchema, location="json")
    @auth_blp.response(201, UserResponseWrapper)
    def post(self, validated_data):
        """Register a new user and return user data."""
        email = validated_data["email"].lower()
        password = validated_data["password"]

        try:
            validate_strong_password(password)
        except ValidationError as err:
            message = (
                "; ".join(err.messages)
                if hasattr(err, "messages")
                else str(err)
            )
            current_app.logger.warning(
                "Password strength validation failed for email=%s: %s",
                email,
                message,
            )
            raise InvalidUsage(message=message, status_code=400)

        if User.query.filter_by(email=email).first():
            current_app.logger.warning(
                "Registration attempt with existing email=%s",
                email,
            )
            raise InvalidUsage(
                message="Email already registered", status_code=409
            )

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
                "Unexpected error setting password for email=%s: %s",
                email,
                str(e),
            )
            raise InvalidUsage(message="Registration failed", status_code=500)

        try:
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            pgcode = getattr(
                getattr(e.orig, "pgcode", None), "__str__", lambda: None
            )()
            if pgcode == errorcodes.UNIQUE_VIOLATION:
                current_app.logger.warning(
                    "Registration unique constraint violated for email=%s",
                    email,
                )
                raise InvalidUsage(
                    message="Email already registered", status_code=409
                )

            if "unique" in str(e.orig).lower():
                current_app.logger.info(
                    "Registration unique constraint violation for email=%s",
                    email,
                )
                raise InvalidUsage(
                    message="Email already registered", status_code=409
                )

            current_app.logger.error(
                "Database error creating user for email=%s: %s", email, str(e)
            )
            raise InvalidUsage(message="Registration failed", status_code=500)

        current_app.logger.info(
            "User registered successfully: email=%s, user_id=%d",
            email,
            new_user.id,
        )

        return {
            "status": "success",
            "message": "User registered successfully.",
            "data": new_user,
        }


@auth_blp.route("/login")
class LoginResource(MethodView):
    """Login a user and return access & refresh tokens."""

    @auth_blp.arguments(UserAuthSchema, location="json")
    @auth_blp.response(200, AccessTokenWrapper, description="Return tokens")
    def post(self, validated_data):
        """Login a user and return access and refresh tokens."""
        email = validated_data["email"].lower()
        password = validated_data["password"]

        # Log that someone is attempting to login
        current_app.logger.info("Login attempt for email=%s", email)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            current_app.logger.warning(
                "Invalid credentials for email=%s", email
            )
            raise InvalidUsage(message="Invalid credentials", status_code=401)

        if not user.is_active:
            current_app.logger.warning(
                "Inactive account login attempt for email=%s",
                email,
            )
            raise InvalidUsage(message="Account is inactive", status_code=403)

        try:
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)
        except Exception as e:
            current_app.logger.error(
                "Token creation failed for email=%s: %s", email, str(e)
            )
            raise InvalidUsage(message="Login failed", status_code=500)

        current_app.logger.info(
            "Login successful for email=%s, user_id=%d", email, user.id
        )

        return {
            "status": "success",
            "message": "Login successful.",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
        }


@auth_blp.route("/refresh")
class RefreshResource(MethodView):
    """Refresh the access token using a valid refresh token."""

    @auth_blp.response(200, RefreshTokenWrapper)
    @auth_blp.doc(security=[{"BearerAuth": []}])
    @jwt_required(refresh=True)
    def post(self):
        """Refresh the access token using a valid refresh token."""
        current_user_id = get_jwt_identity()
        current_app.logger.info(
            "Refresh token used by user_id=%d", current_user_id
        )

        try:
            new_access = create_access_token(identity=current_user_id)
        except Exception as e:
            current_app.logger.error(
                "Error generating new access token for user_id=%d: %s",
                current_user_id,
                str(e),
            )
            raise InvalidUsage(message="Token refresh failed", status_code=500)

        return {
            "status": "success",
            "message": "Access token refreshed successfully.",
            "data": {"access_token": new_access},
        }


@auth_blp.route("/me")
class CurrentUserResource(MethodView):
    """Return the currently authenticated user's profile data."""

    @auth_blp.response(200, UserResponseWrapper)
    @protected
    def get(self):
        """Return the currently authenticated user's profile data."""
        current_user_id = get_jwt_identity()
        current_app.logger.info(
            "Fetching profile for user_id=%s", current_user_id
        )

        try:
            user = User.query.get(current_user_id)
        except SQLAlchemyError as e:
            current_app.logger.error(
                "DB error fetching profile for user_id=%s: %s",
                current_user_id,
                str(e),
            )
            raise InvalidUsage(
                message="Could not retrieve user profile", status_code=500
            )

        if not user:
            current_app.logger.warning(
                "User not found for user_id=%s", current_user_id
            )
            raise InvalidUsage(message="User not found", status_code=404)

        current_app.logger.info(
            "Fetched profile for user_id=%s", current_user_id
        )
        return {
            "status": "success",
            "message": "User profile fetched successfully.",
            "data": user,
        }
