"""Marshmallow schemas for user authentication and serialisation."""

from marshmallow import Schema, fields

from app.utils.common_schema import StandardResponseSchema


class UserAuthSchema(Schema):
    """Marshmallow schema for validating user auth input."""

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


class UserResponseWrapper(StandardResponseSchema):
    """Schema for wrapping user response data."""

    data = fields.Nested(UserResponseSchema)


class TokenSchema(Schema):
    """Schema for serializing refresh tokens."""

    access_token = fields.Str(required=True)
    refresh_token = fields.Str(required=False)


class TokenResponseWrapper(StandardResponseSchema):
    """Schema for wrapping token response data."""

    data = fields.Nested(TokenSchema)
