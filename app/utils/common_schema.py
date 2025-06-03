"""Common schema for standard API responses."""

from marshmallow import Schema, fields


class StandardResponseSchema(Schema):
    """Schema for standard API responses with status, message, and data."""

    status = fields.String(required=True, example="success")
    message = fields.String(required=True)
    data = fields.Dict(required=True)
