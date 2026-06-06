"""
exceptions.py
─────────────
Location : gym_app/exceptions.py
Purpose  : Central exception hierarchy for the entire application.

Design decision
───────────────
All custom exceptions inherit from a single AppError base so that
top-level handlers can catch everything with one clause, while
individual layers can still catch specific sub-types for fine-grained
recovery. Auth exceptions are kept in this file so every layer can
import them without circular dependencies.
"""


# ── Base ──────────────────────────────────────────────────────────────────────

class AppError(Exception):
    """Root exception for every custom error in this application."""


# ── Database layer ────────────────────────────────────────────────────────────

class DatabaseError(AppError):
    """Generic database failure."""


class RecordNotFoundError(DatabaseError):
    """A requested record does not exist."""


class DuplicateRecordError(DatabaseError):
    """A unique-constraint violation was detected."""


class TransactionError(DatabaseError):
    """A database transaction could not be committed."""


# ── Authentication layer ──────────────────────────────────────────────────────

class AuthError(AppError):
    """Root exception for all authentication failures."""


class InvalidCredentialsError(AuthError):
    """Username or password is incorrect."""


class AccountLockedError(AuthError):
    """Account has been locked after too many failed attempts."""


class SessionExpiredError(AuthError):
    """The current session has expired."""


class UnauthorizedError(AuthError):
    """The current user lacks permission for this action."""


class UserNotFoundError(AuthError):
    """No user matched the supplied identifier."""


# ── Validation layer ──────────────────────────────────────────────────────────

class ValidationError(AppError):
    """One or more input fields failed validation."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
