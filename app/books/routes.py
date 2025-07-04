"""Define REST endpoints for book and review operations."""

from flask import current_app, request
from flask_jwt_extended import get_jwt_identity
from flask.views import MethodView
from marshmallow import ValidationError
from psycopg2 import errorcodes
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth.permissions import admin_required, protected
from app.books.ai_service import generate_summary
from app.books.schemas import (
    book_list_schema,
    inactive_book_list_schema,
    BookSummaryResponseWrapper,
    PaginatedBooksResponseWrapper,
    BookDataSchema,
    BookDetailsSchema,
    BookDataResponseWrapper,
    ReviewCreateSchema,
    ReviewsListResponseWrapper,
    ReviewResponseWrapper,
    CategoriesListResponseWrapper,
)
from app.error_handlers import InvalidUsage
from app.extensions import db
from app.models import Book, Category, Review
from app.utils.blueprints import books_blp


@books_blp.route("/categories")
class CategoryResource(MethodView):
    """Resource for managing book categories."""

    @books_blp.response(200, CategoriesListResponseWrapper)
    @protected
    def get(self):
        """List all book categories."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested list of categories", user_id
        )

        try:
            categories = Category.query.order_by(Category.name).all()
            current_app.logger.info("Retrieved %d categories", len(categories))
            return {
                "status": "success",
                "message": "Categories retrieved successfully.",
                "data": categories,
            }
        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Database error while listing categories: %s", str(db_err)
            )
            raise InvalidUsage(
                "Failed to retrieve categories due to a database error.",
                status_code=500,
            )
        except Exception as e:
            current_app.logger.error(
                "Unexpected error in list_categories: %s", str(e)
            )
            raise InvalidUsage(
                "An unexpected error occurred while retrieving categories.",
                status_code=500,
            )


@books_blp.route("/")
class BookStoreResource(MethodView):
    """Resource for managing book store operations."""

    @book_list_schema
    @books_blp.response(200, PaginatedBooksResponseWrapper)
    @protected
    def get(self):
        """Filter list of books."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested book list with filters %s",
            user_id,
            request.args.to_dict(),
        )

        try:
            query = Book.query.filter(Book.is_active.is_(True))

            # Filters
            title = request.args.get("title", type=str)
            author = request.args.get("author", type=str)
            category_id = request.args.get("category_id", type=int)
            min_price = request.args.get("min_price", type=float)
            max_price = request.args.get("max_price", type=float)

            if title:
                query = query.filter(Book.title.ilike(f"%{title}%"))
            if author:
                query = query.filter(Book.author.ilike(f"%{author}%"))
            if category_id:
                query = query.filter(Book.category_id == category_id)
            if min_price is not None:
                query = query.filter(Book.price >= min_price)
            if max_price is not None:
                query = query.filter(Book.price <= max_price)

            # Pagination
            page = request.args.get("page", default=1, type=int)
            per_page = request.args.get("per_page", default=10, type=int)

            paginated = query.order_by(Book.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )

            response_payload = {
                "status": "success",
                "message": "Books retrieved successfully.",
                "data": {
                    "items": paginated.items,
                    "page": paginated.page,
                    "pages": paginated.pages,
                    "total": paginated.total,
                    "per_page": paginated.per_page,
                },
            }

            current_app.logger.info(
                "Successfully retrieved %d books "
                "(page %d of %d) for user_id=%s",
                len(paginated.items),
                paginated.page,
                paginated.pages,
                user_id,
            )

            return response_payload

        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Database error while listing books for user_id=%s: %s",
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                "Failed to retrieve books due to a database error.",
                status_code=500,
            )

        except Exception as e:
            current_app.logger.error(
                "Unexpected error in list_books for user_id=%s: %s",
                user_id,
                str(e),
            )
            raise InvalidUsage(
                "An unexpected error occurred.", status_code=500
            )

    @books_blp.arguments(BookDataSchema, location="json")
    @books_blp.response(201, BookDataResponseWrapper)
    @protected
    @admin_required
    def post(self, validated_data):
        """Create a new book [Admin only]."""
        title = validated_data.get("title", "<untitled>")
        current_app.logger.info(
            "Admin (user_id=%s) is creating a book: title=%s",
            get_jwt_identity(),
            title,
        )

        current_app.logger.debug("Validated book data: %s", validated_data)
        book = Book(**validated_data)
        try:
            db.session.add(book)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            pgcode = getattr(
                getattr(e.orig, "pgcode", None), "__str__", lambda: None
            )()
            if (
                pgcode == errorcodes.UNIQUE_VIOLATION
                or "unique" in str(e.orig).lower()
            ):
                current_app.logger.warning(
                    "Unique constraint violation when "
                    "creating book title=%s: %s",
                    title,
                    str(e.orig),
                )
                raise InvalidUsage(
                    "A book with that identifier already exists.",
                    status_code=409,
                )

            if (
                pgcode == errorcodes.FOREIGN_KEY_VIOLATION
                or "foreign key" in str(e.orig).lower()
            ):
                current_app.logger.warning(
                    "Foreign key violation when creating book title=%s: %s",
                    title,
                    str(e.orig),
                )
                raise InvalidUsage(
                    "Invalid category_id or related resource.", status_code=400
                )

            current_app.logger.error(
                "Unexpected database error when creating book title=%s: %s",
                title,
                str(e),
            )
            raise InvalidUsage(
                "Database error while creating book.", status_code=500
            )
        except ValidationError as err:
            db.session.rollback()
            message = (
                "; ".join(err.messages)
                if hasattr(err, "messages")
                else str(err)
            )
            current_app.logger.warning(
                "Validation error when creating book title=%s: %s",
                title,
                message,
            )
            raise InvalidUsage(message, status_code=400)
        except Exception as e:
            # Catch any other unexpected exception
            db.session.rollback()
            current_app.logger.error(
                "Unhandled exception when creating book title=%s: %s",
                title,
                str(e),
            )
            raise InvalidUsage("Internal server error.", status_code=500)

        current_app.logger.info("Book created successfully: book=%s", book)

        return {
            "status": "success",
            "message": "Book created successfully.",
            "data": book,
        }


@books_blp.route("/<int:book_id>")
class BooksResource(MethodView):
    """Resource for managing individual book operations."""

    @books_blp.response(200, BookDataResponseWrapper)
    @protected
    def get(self, book_id):
        """Get a single book."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested book_id=%s", user_id, book_id
        )

        try:
            book = Book.query.get(book_id)

            if not book or not book.is_active:
                current_app.logger.warning(
                    "Book not found or inactive: book_id=%s", book_id
                )
                raise InvalidUsage("Book not found.", status_code=404)

            current_app.logger.info(
                "Book retrieved successfully: book_id=%s", book_id
            )
            return {
                "status": "success",
                "message": "Book retrieved successfully.",
                "data": book,
            }

        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Database error while fetching book_id=%s: %s",
                book_id,
                str(db_err),
            )
            raise InvalidUsage(
                "Failed to retrieve book due to a database error.",
                status_code=500,
            )
        except InvalidUsage:
            raise
        except Exception as e:
            current_app.logger.error(
                "Unexpected error in get_book for book_id=%s: %s",
                book_id,
                str(e),
            )
            raise InvalidUsage(
                "An unexpected error occurred.", status_code=500
            )

    @books_blp.arguments(BookDetailsSchema(partial=True), location="json")
    @books_blp.response(200, BookDataResponseWrapper)
    @admin_required
    @protected
    def patch(self, validated_data, book_id):
        """Update a book [Admin only]."""
        admin_id = get_jwt_identity()
        current_app.logger.info(
            "Admin (user_id=%s) requested update for book_id=%s with data: %s",
            admin_id,
            book_id,
            validated_data,
        )

        try:
            # 1) Fetch book manually, return JSON 404 if missing
            book = Book.query.get(book_id)
            if not book:
                current_app.logger.warning(
                    "Book not found when attempting update: book_id=%s",
                    book_id,
                )
                raise InvalidUsage("Book not found.", status_code=404)

            # 2) Record original description to detect change
            original_title = book.title
            original_author = book.author
            original_description = book.description

            # 3) Apply all provided fields
            for field, value in validated_data.items():
                setattr(book, field, value)

            # 4) If author, title, or description changed, clear summary cache
            if (
                "author" in validated_data
                and validated_data["author"] != original_author
            ):
                book.summary = None

                current_app.logger.info(
                    "Cleared summary cache for book_id=%s due "
                    "to author change.",
                    book_id,
                )

            if (
                "title" in validated_data
                and validated_data["title"] != original_title
            ):
                book.summary = None
                current_app.logger.info(
                    "Cleared summary cache for "
                    "book_id=%s due to title change.",
                    book_id,
                )

            if (
                "description" in validated_data
                and validated_data["description"] != original_description
            ):
                book.summary = None
                current_app.logger.info(
                    "Cleared summary cache for book_id=%s "
                    "due to description change.",
                    book_id,
                )

            # 5) Commit changes
            db.session.commit()

            current_app.logger.info(
                "Book updated successfully: book_id=%s by admin user_id=%s",
                book_id,
                admin_id,
            )

            # 6) Return wrapped response
            return {
                "status": "success",
                "message": "Book updated successfully.",
                "data": book,
            }

        except IntegrityError as ie:
            db.session.rollback()
            orig = getattr(ie, "orig", None)
            msg = str(orig) if orig else str(ie)

            # Example: if ISBN unique constraint violated
            if "unique" in msg.lower():
                current_app.logger.warning(
                    "Unique constraint violation "
                    "on update for book_id=%s: %s",
                    book_id,
                    msg,
                )
                raise InvalidUsage(
                    "Update failed: a book with that "
                    "unique field already exists.",
                    status_code=400,
                )

            # Other integrity issues
            current_app.logger.error(
                "Integrity error updating book_id=%s: %s", book_id, msg
            )
            raise InvalidUsage(
                "Update failed due to invalid data.",
                status_code=400,
            )

        except SQLAlchemyError as db_err:
            db.session.rollback()
            current_app.logger.error(
                "Database error updating book_id=%s "
                "by admin user_id=%s: %s",
                book_id,
                admin_id,
                str(db_err),
            )
            raise InvalidUsage(
                "Failed to update book due to a database error.",
                status_code=500,
            )

        except InvalidUsage:
            raise

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in update_book for "
                "book_id=%s by admin user_id=%s: %s",
                book_id,
                admin_id,
                str(e),
            )
            raise InvalidUsage(
                "An unexpected error occurred while updating the book.",
                status_code=500,
            )

    @books_blp.response(204)
    @admin_required
    @protected
    def delete(self, book_id):
        """Soft delete a book [Admin only]."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "Admin (user_id=%s) requested deactivation of book_id=%s",
            user_id,
            book_id,
        )

        try:
            # 1) Fetch the book
            book = Book.query.get(book_id)
            if not book:
                current_app.logger.warning(
                    "Book not found for deactivation: book_id=%s", book_id
                )
                raise InvalidUsage("Book not found.", status_code=404)

            # 2) Check if already inactive
            if not book.is_active:
                current_app.logger.warning(
                    "Attempt to deactivate already inactive book_id=%s",
                    book_id,
                )
                raise InvalidUsage(
                    "Book is already inactive.",
                    status_code=400,
                )

            # 3) Soft‐delete
            book.is_active = False
            db.session.commit()

            current_app.logger.info(
                "Book deactivated successfully: book_id=%s", book_id
            )
            return "", 204

        except InvalidUsage:
            # Reraise known 404/400 errors as JSON
            raise

        except SQLAlchemyError as db_err:
            db.session.rollback()
            current_app.logger.error(
                "Database error while deactivating book_id=%s "
                "by admin user_id=%s: %s",
                book_id,
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                "Failed to deactivate book due to a database error.",
                status_code=500,
            )

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in deactivate_book for book_id=%s "
                "by admin user_id=%s: %s",
                book_id,
                user_id,
                str(e),
            )
            raise InvalidUsage(
                "An unexpected error occurred while deactivating the book.",
                status_code=500,
            )


@books_blp.route("/<int:book_id>/reviews")
class ReviewResource(MethodView):
    """Resource for managing book reviews."""

    @books_blp.response(200, ReviewsListResponseWrapper)
    @protected
    def get(self, book_id):
        """List reviews for a book."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested reviews for book_id=%s",
            user_id,
            book_id,
        )

        try:
            # 1) Fetch the book
            book = Book.query.get(book_id)
            if not book:
                current_app.logger.warning(
                    "Book not found when listing reviews: book_id=%s", book_id
                )
                raise InvalidUsage("Book not found.", status_code=404)

            # 2) Return all reviews for that book
            reviews = book.reviews or []
            current_app.logger.info(
                "Retrieved %d reviews for book_id=%s", len(reviews), book_id
            )

            return {
                "status": "success",
                "message": "Reviews retrieved successfully.",
                "data": reviews,
            }

        except InvalidUsage:
            # Re‐raise 404
            raise

        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Database error while listing reviews for book_id=%s: %s",
                book_id,
                str(db_err),
            )
            raise InvalidUsage(
                "Failed to retrieve reviews due to a database error.",
                status_code=500,
            )

        except Exception as e:
            current_app.logger.error(
                "Unexpected error in list_reviews for book_id=%s: %s",
                book_id,
                str(e),
            )
            raise InvalidUsage(
                "An unexpected error occurred while retrieving reviews.",
                status_code=500,
            )

    @books_blp.arguments(ReviewCreateSchema)
    @books_blp.response(201, ReviewResponseWrapper)
    @protected
    def post(self, validated_data, book_id):
        """Add a new review to a book."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) attempting to add "
            "review for book_id=%s. Payload: %s",
            user_id,
            book_id,
            validated_data,
        )

        try:
            # 1) Fetch the book. Return 404 JSON if not found or inactive.
            book = Book.query.get(book_id)
            if not book or not book.is_active:
                current_app.logger.warning(
                    "Book not found or inactive when "
                    "adding review: book_id=%s",
                    book_id,
                )
                raise InvalidUsage("Book not found.", status_code=404)

            # 2) Create the Review instance
            review = Review(user_id=user_id, book_id=book.id, **validated_data)

            # 3) Persist to the database
            db.session.add(review)
            db.session.commit()

            current_app.logger.info(
                "Review created successfully: review_id=%s "
                "by user_id=%s for book_id=%s",
                review.id,
                user_id,
                book_id,
            )

            return {
                "status": "success",
                "message": "Review added successfully.",
                "data": {"review": review},
            }, 201

        except IntegrityError as e:
            db.session.rollback()
            orig = getattr(e, "orig", None)
            msg = str(orig) if orig else str(e)

            if "unique" in msg.lower():
                current_app.logger.warning(
                    """Duplicate review attempt: user_id=%s \
                        already reviewed book_id=%s""",
                    user_id,
                    book_id,
                )
                raise InvalidUsage(
                    "You have already submitted a review for this book.",
                    status_code=400,
                )

            current_app.logger.error(
                "Database integrity error when adding "
                "review for book_id=%s by user_id=%s: %s",
                book_id,
                user_id,
                msg,
            )
            raise InvalidUsage(
                "Failed to add review due to invalid data.",
                status_code=400,
            )

        except SQLAlchemyError as db_err:
            # General database error (e.g. connection issue)
            db.session.rollback()
            current_app.logger.error(
                """Database error when adding review \
                    for book_id=%s by user_id=%s: %s""",
                book_id,
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                "Failed to add review due to a database error.",
                status_code=500,
            )

        except InvalidUsage:
            # Re‐raise any 404 or 400 we explicitly raised above
            raise

        except Exception as e:
            # Anything else unexpected
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error in add_review for "
                "book_id=%s by user_id=%s: %s",
                book_id,
                user_id,
                str(e),
            )
            raise InvalidUsage(
                "An unexpected error occurred while adding review.",
                status_code=500,
            )


@books_blp.route("/<int:book_id>/summary")
class BookSummaryResource(MethodView):
    """Generate or return a Cohere‐generated summary for a book."""

    @books_blp.response(200, BookSummaryResponseWrapper)
    @protected
    def get(self, book_id):
        """Get or generate a book summary."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "User (user_id=%s) requested summary for book_id=%s",
            user_id,
            book_id,
        )

        try:
            # 1) Fetch book; 404 if missing or inactive
            book = Book.query.get(book_id)
            if not book or not book.is_active:
                current_app.logger.warning(
                    "Book not found or inactive for summary: book_id=%s",
                    book_id,
                )
                raise InvalidUsage("Book not found.", status_code=404)

            # 2) If cached summary exists, return it
            if book.summary:
                current_app.logger.info(
                    "Returning cached summary for book_id=%s", book_id
                )
                return {
                    "status": "success",
                    "message": "Summary returned from cache.",
                    "data": {"book_id": book.id, "summary": book.summary},
                }

            # 3) Generate new summary via Cohere, cache it, and return
            current_app.logger.info(
                "Generating summary for book_id=%s via Cohere", book_id
            )
            summary_text = generate_summary(book)
            book.summary = summary_text
            db.session.commit()

            current_app.logger.info(
                "Successfully generated summary for book_id=%s", book_id
            )
            return {
                "status": "success",
                "message": "Book summary generated successfully.",
                "data": {"book_id": book.id, "summary": summary_text},
            }

        except InvalidUsage:
            raise

        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Database error while fetching "
                "book for summary: book_id=%s: %s",
                book_id,
                str(db_err),
            )
            raise InvalidUsage(
                message="Failed to retrieve book due to a database error.",
                status_code=500,
            )

        except Exception as e:
            current_app.logger.error(
                "Unexpected error in get_book_summary for book_id=%s: %s",
                book_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while generating summary.",
                status_code=500,
            )


@books_blp.route("/inactive")
class InactiveBooksResource(MethodView):
    """List all deactivated books (admin only, paginated)."""

    @inactive_book_list_schema
    @books_blp.response(200, PaginatedBooksResponseWrapper)
    @admin_required
    @protected
    def get(self):
        """List all deactivated books [Admin only]."""
        user_id = get_jwt_identity()
        current_app.logger.info(
            "Admin (user_id=%s) requested list of inactive books", user_id
        )

        try:
            query = Book.query.filter(Book.is_active.is_(False))

            # Pagination params
            page = request.args.get("page", default=1, type=int)
            per_page = request.args.get("per_page", default=10, type=int)

            paginated = query.order_by(Book.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )

            inactive_books = paginated.items
            current_app.logger.info(
                "Found %d inactive books for admin user_id=%s",
                len(inactive_books),
                user_id,
            )

            response_payload = {
                "status": "success",
                "message": "Inactive books retrieved successfully.",
                "data": {
                    "items": inactive_books,
                    "page": paginated.page,
                    "pages": paginated.pages,
                    "total": paginated.total,
                    "per_page": paginated.per_page,
                },
            }

            current_app.logger.info(
                "Successfully retrieved %d inactive books "
                "(page %d of %d) for user_id=%s",
                len(inactive_books),
                paginated.page,
                paginated.pages,
                user_id,
            )
            return response_payload

        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Database error while listing inactive "
                "books for admin user_id=%s: %s",
                user_id,
                str(db_err),
            )
            raise InvalidUsage(
                message=(
                    "Failed to retrieve inactive books"
                    " due to a database error."
                ),
                status_code=500,
            )

        except Exception as e:
            current_app.logger.error(
                "Unexpected error in list_inactive_books "
                "for admin user_id=%s: %s",
                user_id,
                str(e),
            )
            raise InvalidUsage(
                message="An unexpected error occurred "
                "while retrieving inactive books.",
                status_code=500,
            )
