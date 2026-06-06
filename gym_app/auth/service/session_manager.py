"""
service/session_manager.py
───────────────────────────
Location : gym_app/auth/service/session_manager.py
Purpose  : Manages the lifecycle of the currently logged-in user session.

Design decision
───────────────
A dedicated SessionManager keeps session state separate from both the
AuthService (which handles credential verification) and the UI (which
just reads session state).  This single-responsibility split means:

  • AuthService.login()  → creates a session via SessionManager.
  • AuthService.logout() → destroys the session via SessionManager.
  • UI widgets           → call SessionManager.get_current_user() /
                           require_role() to gate access.

Session is kept in-memory (one process = one logged-in user), which is
appropriate for a desktop application.  Replacing with a token-based
or multi-user session store later requires only changing this file.

Idle timeout: sessions auto-expire after IDLE_TIMEOUT_MINUTES of
inactivity so an unattended workstation cannot be abused.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from dataclasses import dataclass, field

from gym_app.auth.models import User, Role
from gym_app.exceptions import (
    SessionExpiredError,
    UnauthorizedError,
)


# ── configuration ──────────────────────────────────────────────────────────────

IDLE_TIMEOUT_MINUTES: int = 30


# ── session data ───────────────────────────────────────────────────────────────

@dataclass
class _Session:
    """Internal session record – not exposed outside this module."""

    user: User
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def touch(self) -> None:
        """Refresh the last-activity timestamp."""
        self.last_activity = datetime.now()

    def is_expired(self, timeout_minutes: int) -> bool:
        """Return True if the session has been idle too long."""
        idle = datetime.now() - self.last_activity
        return idle > timedelta(minutes=timeout_minutes)


# ── manager ────────────────────────────────────────────────────────────────────

class SessionManager:
    """
    Manages a single in-process user session.

    This is intentionally NOT a singleton – the caller (usually
    AuthService) holds the one instance and passes it to whoever needs
    it, keeping dependency injection clean.
    """

    def __init__(
        self,
        idle_timeout_minutes: int = IDLE_TIMEOUT_MINUTES,
    ) -> None:
        self._session: _Session | None = None
        self._timeout = idle_timeout_minutes

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def create(self, user: User) -> None:
        """
        Start a new session for the given user.

        Any previous session is discarded (only one user at a time).
        """
        self._session = _Session(user=user)

    def destroy(self) -> None:
        """Terminate the current session (logout)."""
        self._session = None

    # ── access ─────────────────────────────────────────────────────────────────

    def is_authenticated(self) -> bool:
        """
        Return True if a valid, non-expired session exists.

        Does NOT raise – safe to call as a predicate anywhere.
        """
        if self._session is None:
            return False
        if self._session.is_expired(self._timeout):
            self.destroy()
            return False
        return True

    def get_current_user(self) -> User:
        """
        Return the currently logged-in User.

        Raises
        ------
        SessionExpiredError
            If there is no session or it has timed out.
        """
        if self._session is None:
            raise SessionExpiredError("No active session. Please log in.")

        if self._session.is_expired(self._timeout):
            self.destroy()
            raise SessionExpiredError(
                "Your session has expired due to inactivity. "
                "Please log in again."
            )

        self._session.touch()
        return self._session.user

    def require_role(self, *roles: Role) -> User:
        """
        Ensure the current user has one of the required roles.

        Parameters
        ----------
        *roles : Role
            One or more acceptable roles.

        Returns
        -------
        User
            The current user if they have a matching role.

        Raises
        ------
        SessionExpiredError
            If no valid session exists.
        UnauthorizedError
            If the user's role is not in the allowed set.
        """
        user = self.get_current_user()

        if not user.has_role(*roles):
            allowed = ", ".join(r.value for r in roles)
            raise UnauthorizedError(
                f"Access denied. Required role(s): {allowed}. "
                f"Your role: {user.role.value}."
            )

        return user

    # ── info ───────────────────────────────────────────────────────────────────

    def session_info(self) -> dict | None:
        """
        Return a dict of session metadata, or None if no session exists.

        Safe to call without raising – used for status-bar display.
        """
        if self._session is None:
            return None

        return {
            "username": self._session.user.username,
            "role": self._session.user.role.value,
            "created_at": self._session.created_at.strftime("%Y-%m-%d %H:%M"),
            "last_activity": self._session.last_activity.strftime("%H:%M:%S"),
            "expires_at": (
                self._session.last_activity
                + timedelta(minutes=self._timeout)
            ).strftime("%H:%M:%S"),
        }
