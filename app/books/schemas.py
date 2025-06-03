"""Define Marshmallow schemas for books, categories, and reviews."""

from marshmallow import Schema, fields
from app.utils.common_schema import StandardResponseSchema

from app.utils.validations import validate_rating
from app.utils.blueprints import books_blp


class CategorySchema(Schema):
    """Marshmallow schema for serializing and validating Category data."""

    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)


class BookDataSchema(Schema):
    """Marshmallow schema for validating a Book."""

    id = fields.Int(dump_only=True)
    title = fields.String(required=True)
    author = fields.String(required=True)
    isbn = fields.String(required=True)
    price = fields.Float(required=True)
    stock = fields.Integer(required=True)
    description = fields.String()
    publication_date = fields.Date()
    category_id = fields.Integer(load_only=True, required=True)
    is_active = fields.Bool(dump_only=True)
    average_rating = fields.Float(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    category = fields.Nested(CategorySchema, dump_only=True)
    summary = fields.String(dump_only=True, allow_none=True)


class BookDataResponseWrapper(StandardResponseSchema):
    """Response wrapper for book data."""

    data = fields.Nested(BookDataSchema)


class PaginatedBooksSchema(Schema):
    """Schema for paginated book responses."""

    items = fields.List(fields.Nested(BookDataSchema), required=True)
    page = fields.Int(required=True)
    pages = fields.Int(required=True)
    total = fields.Int(required=True)
    per_page = fields.Int(required=True)


class PaginatedBooksResponseWrapper(StandardResponseSchema):
    """Response wrapper for paginated book lists."""

    data = fields.Nested(PaginatedBooksSchema, required=True)


class BookSummarySchema(Schema):
    """Marshmallow schema for a book summary (AI-generated summaries)."""

    book_id = fields.Int(required=True)
    summary = fields.String(required=True)


class BookSummaryResponseWrapper(StandardResponseSchema):
    """Response wrapper for book summaries."""

    data = fields.Nested(BookSummarySchema, required=True)


class ReviewCreateSchema(Schema):
    """Marshmallow schema for validating input when creating a new Review."""

    rating = fields.Int(required=True, validate=validate_rating)
    comment = fields.String()


class ReviewReadSchema(Schema):
    """Marshmallow schema for serializing Review data into API responses."""

    id = fields.Int(dump_only=True)
    reviewer = fields.Email(
        attribute="user.email",
        dump_only=True,
    )
    book_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    rating = fields.Int(dump_only=True)
    comment = fields.Str(dump_only=True)


class ReviewDataSchema(Schema):
    """Wrap a single review under 'review' key."""

    review = fields.Nested(ReviewReadSchema, required=True)


class ReviewResponseWrapper(StandardResponseSchema):
    """Wraps a single review in the standard envelope."""

    data = fields.Nested(ReviewDataSchema, required=True)


class ReviewsListResponseWrapper(StandardResponseSchema):
    """Wrap a list of reviews in the standard envelope."""

    data = fields.List(fields.Nested(ReviewReadSchema), required=True)


class CategoriesListResponseWrapper(StandardResponseSchema):
    """Wrap a list of categories in the standard envelope."""

    data = fields.List(fields.Nested(CategorySchema), required=True)


book_list_schema = books_blp.doc(
    parameters=[
        {
            "name": "title",
            "in": "query",
            "description": "Filter by book title",
        },
        {"name": "author", "in": "query", "description": "Filter by author"},
        {
            "name": "category_id",
            "in": "query",
            "description": "Filter by category",
        },
        {"name": "min_price", "in": "query", "description": "Minimum price"},
        {"name": "max_price", "in": "query", "description": "Maximum price"},
        {"name": "page", "in": "query", "description": "Page number"},
        {"name": "per_page", "in": "query", "description": "Items per page"},
    ]
)

inactive_book_list_schema = books_blp.doc(
    parameters=[
        {"name": "page", "in": "query", "description": "Page number"},
        {"name": "per_page", "in": "query", "description": "Items per page"},
    ]
)
