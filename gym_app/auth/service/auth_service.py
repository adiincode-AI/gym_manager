"""
service/auth_service.py
────────────────────────
Location : gym_app/auth/service/auth_service.py
Purpose  : Business logic for login, logout, and user management.

Design decision
───────────────
AuthService is the ONLY public API for authentication. It:
  1. Validates inputs (via AuthValidator) as a defensive second gate.
  2. Delegates DB work to UserRepository.
  3. Verifies bcrypt hashes here – not in the repository (the repo only
     stores/fetches hashes; the service owns the verification logic).
  4. Manages the session via SessionManager.
  5. Enforces brute-force protection via an in-process login attempt counter.

UI code NEVER imports repository or session_manager directly.
"""
from __future__ import annotations

import bcrypt
import logging
from datetime import datetime

from gym_app.auth.models import User, Role
from gym_app.auth.repository import UserRepository
from gym_app.auth.service.session_manager import SessionManager
from gym_app.auth.validators import AuthValidator
from gym_app.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    UserNotFoundError,
    DuplicateRecordError,
    ValidationError,
    UnauthorizedError,
)

logger = logging.getLogger(__name__)


# ── configuration ──────────────────────────────────────────────────────────────

MAX_LOGIN_ATTEMPTS: int = 5          # lock after this many consecutive failures
LOCKOUT_SECONDS:    int = 300        # 5-minute cooldown


class AuthService:
    """
    Orchestrates all authentication flows.

    Parameters
    ----------
    user_repo       : UserRepository  – data access for users table.
    session_manager : SessionManager  – manages active session state.

    Both are injected so they can be swapped with test doubles.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        session_manager: SessionManager,
    ) -> None:
        self._repo    = user_repo
        self._session = session_manager
        self._validator = AuthValidator()

        # brute-force tracking {username: {"count": int, "locked_at": datetime}}
        self._attempts: dict[str, dict] = {}

    # ── login / logout ─────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> User:
        """
        Authenticate a user and create a session.

        Steps
        -----
        1. Validate inputs.
        2. Check lockout.
        3. Fetch user from DB.
        4. Verify bcrypt hash.
        5. Reset attempt counter.
        6. Create session.
        7. Return User object (without password_hash exposure to UI).

        Parameters
        ----------
        username : str   – raw input from the login form.
        password : str   – raw input from the login form.

        Returns
        -------
        User

        Raises
        ------
        ValidationError          – blank / invalid input.
        AccountLockedError       – too many failed attempts.
        InvalidCredentialsError  – bad username or password.
        """
        # 1. Validate
        clean_username, clean_password = (
            self._validator.validate_login_inputs(username, password)
        )

        # 2. Lockout check
        self._check_lockout(clean_username)

        # 3. Fetch user
        user = self._repo.find_by_username(clean_username)
        if user is None:
            self._record_failure(clean_username)
            # Generic message: never tell the caller which field was wrong
            raise InvalidCredentialsError(
                "Invalid username or password."
            )

        # 4. Verify password
        if not _verify_password(clean_password, user.password_hash):
            self._record_failure(clean_username)
            raise InvalidCredentialsError(
                "Invalid username or password."
            )

        # 5. Reset attempt counter on success
        self._clear_attempts(clean_username)

        # 6. Create session
        self._session.create(user)

        logger.info(
            "User '%s' (role=%s) logged in at %s.",
            user.username,
            user.role.value,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        return user

    def logout(self) -> None:
        """
        Destroy the current session.

        Safe to call even when no session is active.
        """
        info = self._session.session_info()
        self._session.destroy()

        if info:
            logger.info("User '%s' logged out.", info["username"])

    # ── session helpers ────────────────────────────────────────────────────────

    def get_current_user(self) -> User:
        """Proxy to SessionManager.get_current_user()."""
        return self._session.get_current_user()

    def is_authenticated(self) -> bool:
        """Proxy to SessionManager.is_authenticated()."""
        return self._session.is_authenticated()

    def require_role(self, *roles: Role) -> User:
        """Proxy to SessionManager.require_role()."""
        return self._session.require_role(*roles)

    # ── user management (admin only) ──────────────────────────────────────────

    def create_user(
        self,
        requesting_user: User,
        username: str,
        plain_password: str,
        role: Role,
    ) -> User:
        """
        Create a new system user. Admin-only operation.

        Parameters
        ----------
        requesting_user : The user performing this action (must be admin).
        username        : Desired username.
        plain_password  : Password for the new account.
        role            : Role to assign.

        Returns
        -------
        User

        Raises
        ------
        UnauthorizedError      – requesting_user is not an admin.
        ValidationError        – invalid username or password.
        DuplicateRecordError   – username already exists.
        """
        if not requesting_user.is_admin():
            raise UnauthorizedError(
                "Only admins can create new user accounts."
            )

        clean_username = self._validator.validate_username(username)
        self._validator.validate_password(plain_password)

        return self._repo.create(clean_username, plain_password, role)

    def change_password(
        self,
        requesting_user: User,
        new_password: str,
        target_user_id: int | None = None,
    ) -> None:
        """
        Change a user's password.

        A user may change their own password; only an admin may change
        another user's password.

        Parameters
        ----------
        requesting_user : User performing the action.
        new_password    : New plain-text password.
        target_user_id  : ID of the user whose password is being changed.
                          Defaults to requesting_user.id (self-change).

        Raises
        ------
        UnauthorizedError  – non-admin trying to change another user's pwd.
        ValidationError    – new password fails validation.
        """
        target_id = target_user_id or requesting_user.id

        if target_id != requesting_user.id and not requesting_user.is_admin():
            raise UnauthorizedError(
                "Only admins can change another user's password."
            )

        self._validator.validate_password(new_password)
        self._repo.update_password(target_id, new_password)

    # ── brute-force protection (private) ──────────────────────────────────────

    def _check_lockout(self, username: str) -> None:
        """
        Raise AccountLockedError if the account is currently locked.

        The lock expires automatically after LOCKOUT_SECONDS.
        """
        record = self._attempts.get(username)
        if record is None:
            return

        if record["count"] < MAX_LOGIN_ATTEMPTS:
            return

        locked_at: datetime = record["locked_at"]
        elapsed = (datetime.now() - locked_at).total_seconds()

        if elapsed < LOCKOUT_SECONDS:
            remaining = int(LOCKOUT_SECONDS - elapsed)
            raise AccountLockedError(
                f"Account locked due to too many failed attempts. "
                f"Try again in {remaining} seconds."
            )

        # Lockout period has passed – reset
        self._clear_attempts(username)

    def _record_failure(self, username: str) -> None:
        """Increment the failed-attempt counter for a username."""
        if username not in self._attempts:
            self._attempts[username] = {"count": 0, "locked_at": None}

        self._attempts[username]["count"] += 1

        if self._attempts[username]["count"] >= MAX_LOGIN_ATTEMPTS:
            self._attempts[username]["locked_at"] = datetime.now()
            logger.warning(
                "Account '%s' locked after %d failed attempts.",
                username,
                MAX_LOGIN_ATTEMPTS,
            )

    def _clear_attempts(self, username: str) -> None:
        """Reset the failed-attempt counter for a username."""
        self._attempts.pop(username, None)


# ── private helpers ────────────────────────────────────────────────────────────

def _verify_password(plain: str, stored_hash: str) -> bool:
    """
    Compare a plain-text password against a stored bcrypt hash.

    Uses bcrypt.checkpw which is constant-time to prevent timing attacks.
    """
    try:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )
    except Exception:
        return False
