"""
models/user.py
──────────────
Location : gym_app/auth/models/user.py
Purpose  : Pure domain model that represents an authenticated user.

Design decision
───────────────
This is a plain dataclass with NO database or framework imports.
Keeping the model free of infrastructure concerns means:
  • It can be unit-tested without a database.
  • It can be serialised / de-serialised in any format.
  • The service layer owns the mapping from raw DB dicts → User objects,
    which is the single place that ever touches DB column names.

The password_hash is stored on the model so the service can verify
passwords, but it is NEVER exposed to the UI layer (see AuthService).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Role(str, Enum):
    """Enumerated roles that exactly mirror the DB CHECK constraint."""

    ADMIN = "admin"
    RECEPTIONIST = "receptionist"

    # ── helpers ───────────────────────────────────────────────────────────────

    @classmethod
    def from_string(cls, value: str) -> "Role":
        """
        Convert a raw string (e.g. from the DB) to a Role enum.

        Raises
        ------
        ValueError
            If the string does not match any known role.
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid = ", ".join(r.value for r in cls)
            raise ValueError(
                f"Unknown role '{value}'. Valid roles: {valid}"
            )

    def is_admin(self) -> bool:
        """Return True when this role has admin-level privileges."""
        return self == Role.ADMIN


@dataclass(frozen=True)
class User:
    """
    Immutable representation of a gym system user.

    Attributes
    ----------
    id            : Primary key from the users table.
    username      : Unique login identifier.
    password_hash : bcrypt hash – never exposed outside the service layer.
    role          : Role enum driving all permission checks.
    created_at    : Row creation timestamp (informational).
    updated_at    : Last update timestamp (informational).
    """

    id: int
    username: str
    password_hash: str
    role: Role
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # ── permission helpers ────────────────────────────────────────────────────

    def has_role(self, *roles: Role) -> bool:
        """Return True if this user's role is one of the supplied roles."""
        return self.role in roles

    def is_admin(self) -> bool:
        """Shortcut – True when the user is an admin."""
        return self.role.is_admin()

    # ── safe representation ───────────────────────────────────────────────────

    def __repr__(self) -> str:
        """Never include password_hash in repr output."""
        return (
            f"User(id={self.id}, username={self.username!r}, "
            f"role={self.role.value!r})"
        )

    # ── factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_db_row(cls, row: dict) -> "User":
        """
        Build a User from a raw database dictionary.

        Parameters
        ----------
        row : dict
            A row dict as returned by DatabaseManager.fetch_one().

        Returns
        -------
        User
        """
        return cls(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            role=Role.from_string(row["role"]),
            created_at=_parse_dt(row.get("created_at")),
            updated_at=_parse_dt(row.get("updated_at")),
        )


# ── private helpers ────────────────────────────────────────────────────────────

def _parse_dt(value: str | datetime | None) -> datetime:
    """Safely coerce a DB timestamp string to a datetime object."""
    if value is None:
        return datetime.now()
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return datetime.now()
