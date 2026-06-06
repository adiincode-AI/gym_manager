"""
validators/auth_validator.py
────────────────────────────
Location : gym_app/auth/validators/auth_validator.py
Purpose  : All input validation rules for authentication forms.

Design decision
───────────────
Validation is intentionally separated from both the UI and the service:
  • UI calls the validator BEFORE submitting to the service, giving
    instant user feedback without a round-trip.
  • Service calls it again as a defensive second gate (belt-and-braces).
  • Rules live in one place → changes propagate everywhere automatically.

Each method raises ValidationError (not returns bool) so callers get
a structured error with a field name and human-readable message.
"""
from __future__ import annotations

from gym_app.exceptions import ValidationError


class AuthValidator:
    """
    Validates all authentication-related inputs.

    All methods are static; the class is a logical namespace, not a
    stateful object. This makes it trivially mockable in tests.
    """

    # ── constants ──────────────────────────────────────────────────────────────

    MIN_USERNAME_LEN: int = 3
    MAX_USERNAME_LEN: int = 50
    MIN_PASSWORD_LEN: int = 6
    MAX_PASSWORD_LEN: int = 128

    # ── public API ─────────────────────────────────────────────────────────────

    @staticmethod
    def validate_username(username: str) -> str:
        """
        Validate and normalise a username string.

        Rules
        -----
        • Must not be empty or whitespace-only.
        • Length between MIN_USERNAME_LEN and MAX_USERNAME_LEN.
        • Only letters, digits, underscores, and hyphens allowed.

        Returns
        -------
        str
            The stripped, lower-cased username.

        Raises
        ------
        ValidationError
            On any rule violation.
        """
        if not username or not username.strip():
            raise ValidationError("username", "Username is required.")

        username = username.strip().lower()

        if len(username) < AuthValidator.MIN_USERNAME_LEN:
            raise ValidationError(
                "username",
                f"Username must be at least "
                f"{AuthValidator.MIN_USERNAME_LEN} characters."
            )

        if len(username) > AuthValidator.MAX_USERNAME_LEN:
            raise ValidationError(
                "username",
                f"Username must not exceed "
                f"{AuthValidator.MAX_USERNAME_LEN} characters."
            )

        allowed = set(
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789"
            "_-"
        )
        if not all(ch in allowed for ch in username):
            raise ValidationError(
                "username",
                "Username may only contain letters, digits, "
                "underscores, and hyphens."
            )

        return username

    @staticmethod
    def validate_password(password: str) -> str:
        """
        Validate a plain-text password.

        Rules
        -----
        • Must not be empty.
        • Length between MIN_PASSWORD_LEN and MAX_PASSWORD_LEN.

        Returns
        -------
        str
            The password unchanged (no normalisation applied to preserve
            case and whitespace that the user may have intentionally set).

        Raises
        ------
        ValidationError
            On any rule violation.
        """
        if not password:
            raise ValidationError("password", "Password is required.")

        if len(password) < AuthValidator.MIN_PASSWORD_LEN:
            raise ValidationError(
                "password",
                f"Password must be at least "
                f"{AuthValidator.MIN_PASSWORD_LEN} characters."
            )

        if len(password) > AuthValidator.MAX_PASSWORD_LEN:
            raise ValidationError(
                "password",
                f"Password must not exceed "
                f"{AuthValidator.MAX_PASSWORD_LEN} characters."
            )

        return password

    @classmethod
    def validate_login_inputs(
        cls,
        username: str,
        password: str
    ) -> tuple[str, str]:
        """
        Validate both login fields in one call.

        Returns
        -------
        tuple[str, str]
            (normalised_username, raw_password)

        Raises
        ------
        ValidationError
            On the first failing field (username is checked first).
        """
        clean_username = cls.validate_username(username)
        clean_password = cls.validate_password(password)
        return clean_username, clean_password
