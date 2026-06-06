"""
repository/user_repository.py
──────────────────────────────
Location : gym_app/auth/repository/user_repository.py
Purpose  : All database operations for the users table.

Design decision
───────────────
The Repository pattern isolates every raw SQL query behind a typed
Python interface. Benefits:
  • The service layer NEVER writes SQL — it calls repository methods.
  • Swapping SQLite for PostgreSQL later means changing only this file.
  • Every query uses parameterised placeholders (?) – no string
    interpolation anywhere, eliminating SQL-injection risk.
  • The repository returns domain objects (User), not raw dicts,
    so callers are never coupled to DB column names.
"""
from __future__ import annotations

import bcrypt

from gym_app.database import DatabaseManager
from gym_app.exceptions import (
    DatabaseError,
    DuplicateRecordError,
    UserNotFoundError,
)
from gym_app.auth.models import User, Role


class UserRepository:
    """
    Data-access object for the ``users`` table.

    Parameters
    ----------
    db : DatabaseManager
        Injected database manager (enables testing with a mock/in-memory DB).
    """

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ── reads ──────────────────────────────────────────────────────────────────

    def find_by_username(self, username: str) -> User | None:
        """
        Fetch a user by exact username match.

        Parameters
        ----------
        username : str
            The (already-normalised) username to look up.

        Returns
        -------
        User | None
            A User domain object, or None if no match is found.
        """
        query = """
            SELECT id, username, password_hash, role, created_at, updated_at
            FROM   users
            WHERE  username = ?
        """
        row = self._db.fetch_one(query, (username,))
        return User.from_db_row(row) if row else None

    def find_by_id(self, user_id: int) -> User | None:
        """
        Fetch a user by primary key.

        Returns
        -------
        User | None
        """
        query = """
            SELECT id, username, password_hash, role, created_at, updated_at
            FROM   users
            WHERE  id = ?
        """
        row = self._db.fetch_one(query, (user_id,))
        return User.from_db_row(row) if row else None

    def get_by_id(self, user_id: int) -> User:
        """
        Same as find_by_id but raises if not found.

        Raises
        ------
        UserNotFoundError
        """
        user = self.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(
                f"No user with id={user_id}."
            )
        return user

    def username_exists(self, username: str) -> bool:
        """Return True if the username is already taken."""
        query = "SELECT 1 FROM users WHERE username = ?"
        return self._db.exists(query, (username,))

    # ── writes ─────────────────────────────────────────────────────────────────

    def create(
        self,
        username: str,
        plain_password: str,
        role: Role,
    ) -> User:
        """
        Insert a new user with a bcrypt-hashed password.

        Parameters
        ----------
        username       : Normalised, unique username.
        plain_password : Raw password – hashed here before storage.
        role           : Role enum value.

        Returns
        -------
        User
            The newly created user fetched back from the DB.

        Raises
        ------
        DuplicateRecordError
            If the username is already taken.
        DatabaseError
            On any other DB failure.
        """
        if self.username_exists(username):
            raise DuplicateRecordError(
                f"Username '{username}' is already taken."
            )

        hashed = _hash_password(plain_password)

        query = """
            INSERT INTO users (username, password_hash, role)
            VALUES            (?,        ?,             ?)
        """
        new_id = self._db.execute(query, (username, hashed, role.value))

        user = self.find_by_id(new_id)
        if user is None:
            raise DatabaseError(
                "User was inserted but could not be retrieved."
            )
        return user

    def update_password(
        self,
        user_id: int,
        new_plain_password: str,
    ) -> None:
        """
        Replace the stored password hash for a user.

        Parameters
        ----------
        user_id            : Target user's primary key.
        new_plain_password : New raw password – hashed before storage.
        """
        hashed = _hash_password(new_plain_password)
        query = """
            UPDATE users
            SET    password_hash = ?,
                   updated_at    = CURRENT_TIMESTAMP
            WHERE  id = ?
        """
        self._db.execute(query, (hashed, user_id))


# ── private helpers ────────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    """
    Hash a plain-text password with bcrypt (work factor = 12).

    Work factor 12 is the current industry recommendation: fast enough
    to be unnoticeable at login (<200 ms on modern hardware), but slow
    enough to make brute-force attacks expensive.
    """
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")
