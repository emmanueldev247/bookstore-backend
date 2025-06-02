"""Marshmallow schemas for user authentication and serialisation."""

from typing import Any, Union

from marshmallow import Schema, ValidationError, fields, validates

from app.auth.utils import validate_strong_password


class UserRegistrationSchema(Schema):
    """Marshmallow schema for validating user registration input."""

    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate_strong_password)


class UserLoginSchema(Schema):
    """Marshmallow schema for validating user login input."""

    email = fields.Email(required=True)
    password = fields.String(required=True)


class UserResponseSchema(Schema):
    """Schema for serializing User model data into API responses."""

    id = fields.Int(dump_only=True)
    email = fields.Email()
    is_active = fields.Bool()
    is_admin = fields.Bool()
    is_superadmin = fields.Bool()
    created_at = fields.DateTime()


class UserUpdateSchema(Schema):
    """Marshmallow schema for validating user update input."""

    email = fields.Email(required=False)
    is_active = fields.Boolean(required=False)
    is_admin = fields.Boolean(required=False)
    is_superadmin = fields.Boolean(required=False)

    @validates("is_superadmin")
    def validate_is_superadmin(self, value: Union[bool, Any]) -> None:
        """Validate the 'is_superadmin' field."""
        if not isinstance(value, bool):
            raise ValidationError("Invalid value for is_superadmin.")

        # guard against updating self to superadmin
        if value and not self.context.get("is_superadmin", False):
            raise ValidationError(
                "Cannot elevate to superadmin without proper permissions."
            )


class UserListSchema(Schema):
    """Marshmallow schema for paginated lists of users."""

    items = fields.List(fields.Nested(UserResponseSchema))
    total = fields.Int()
    page = fields.Int()
    pages = fields.Int()
