"""This module is for defining custom permissions for Flask routes."""

from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import current_app
from app.auth.models import User
from app.error_handlers import InvalidUsage


def admin_required(fn):
    """Ensure the user has admin privileges."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user and not user.is_admin:
            current_app.logger.warning(
                f"Unauthorized admin access attempt by user_id={user_id}"
            )
            raise InvalidUsage("Admin privileges required", status_code=403)
        return fn(*args, **kwargs)

    return wrapper


def superadmin_required(fn):
    """Ensure the user has superadmin privileges."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user and not user.is_superadmin:
            current_app.logger.warning(
                f"Unauthorized superadmin access attempt by user_id={user_id}"
            )
            raise InvalidUsage(
                "Superadmin privileges required", status_code=403
            )
        return fn(*args, **kwargs)

    return wrapper
