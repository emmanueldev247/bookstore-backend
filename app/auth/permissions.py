"""Define custom permissions for Flask routes."""

from functools import wraps
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask import current_app
from app.models import User
from app.error_handlers import InvalidUsage
from app.utils.blueprints import auth_blp


def admin_required(fn):
    """Ensure the user has admin privileges."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            current_app.logger.warning(
                f"Unauthorized admin access attempt by user_id={user_id}"
            )
            raise InvalidUsage("Admin privileges required", status_code=403)
        return fn(*args, **kwargs)

    return wrapper


def superadmin_required(fn):
    """Ensure the user has superadmin privileges."""

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_superadmin:
            current_app.logger.warning(
                f"Unauthorized superadmin access attempt by user_id={user_id}"
            )
            raise InvalidUsage(
                "Superadmin privileges required", status_code=403
            )
        return fn(*args, **kwargs)

    return wrapper


def protected(fn):
    """Apply both JWT protection and doc security to a view."""

    @wraps(fn)
    @auth_blp.doc(security=[{"BearerAuth": []}])
    @jwt_required()
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper
