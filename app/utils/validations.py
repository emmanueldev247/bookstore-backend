"""Utility functions for input validation such as strong password checks."""

import re

from typing import Any, Union
from marshmallow import ValidationError


def validate_strong_password(password: str) -> None:
    """
    Validate that a password is strong.

    A strong password must:
    - Be at least 8 characters long.
    - Contain at least one uppercase letter.
    - Contain at least one lowercase letter.
    - Include at least one digit.
    - Include at least one special character.

    Raises:
        ValueError: If password is empty.
        ValidationError: If password does not meet the required strength.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError(
            "Password must contain at least one uppercase letter."
        )
    if not re.search(r"[a-z]", password):
        raise ValidationError(
            "Password must contain at least one lowercase letter."
        )
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError(
            "Password must contain at least one special character."
        )


def validate_rating(n: Union[int, Any]) -> None:
    """
    Validate if a given number `n` is an integer between 1 and 5 (inclusive).

    Raises:
        ValidationError: If `n` is not an integer or not in the range 1 to 5.
    """
    if not isinstance(n, int):
        raise ValidationError("Rating must be an integer.")

    if not (1 <= n <= 5):
        raise ValidationError("Rating must be between 1 and 5.")
