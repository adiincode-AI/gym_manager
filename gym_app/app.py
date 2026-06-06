"""
app.py
───────
Location : gym_app/app.py
Purpose  : Application root – builds the dependency graph and launches the UI.

Design decision
───────────────
All dependency construction lives here (poor-man's DI container). This means:
  • No module constructs its own dependencies (no hidden singletons).
  • Swapping any layer (e.g. for testing) requires changing only this file.
  • The main entry-point (main.py) just calls App().run() – one line.

The App class also owns the Tk root window so it controls the event loop
and window lifecycle.
"""
from __future__ import annotations

import logging
import sys
import tkinter as tk
from pathlib import Path

from gym_app.database import DatabaseManager
from gym_app.auth.repository import UserRepository
from gym_app.auth.service import AuthService, SessionManager
from gym_app.auth.models import User, Role
from gym_app.auth.ui import LoginFrame
from gym_app.ui.components import COLOR_BG, FONT_FAMILY
from gym_app.exceptions import AppError
from gym_app.members.ui.member_list_frame import MemberListFrame

# ── New Dashboard Imports ──────────────────────────────────────────────────────
from gym_app.dashboard.repository.dashboard_repository import DashboardRepository
from gym_app.dashboard.service.dashboard_service import DashboardService
from gym_app.dashboard.ui.dashboard_frame import AdminDashboardFrame

# ── New Member Imports ──────────────────────────────────────────────────────
from gym_app.members.repository.member_repository import MemberRepository
from gym_app.members.service.member_service import MemberService
from gym_app.members.ui.member_form_frame import MemberFormFrame

# ── logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("gym_app.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


class App:
    """
    Application root.

    Constructs the full dependency graph, initialises the database,
    seeds a default admin if needed, and launches the Tkinter event loop.
    """

    WINDOW_TITLE = "The Iron Temple GYM"
    WINDOW_WIDTH = 1024
    WINDOW_HEIGHT = 700
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    DB_PATH = "database/gym.db"

    def __init__(self) -> None:
        self._root = self._build_root()
        # Destructured assignments are expanded to accommodate MemberService
        self._db, self._auth, self._dashboard_service, self._member_service = self._build_services()
        self._current_frame: tk.Frame | None = None

    # ── bootstrap ──────────────────────────────────────────────────────────────

    def _build_root(self) -> tk.Tk:
        """Create and configure the root Tk window."""
        root = tk.Tk()
        root.title(self.WINDOW_TITLE)
        root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        root.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        root.configure(bg=COLOR_BG)

        # Centre on screen
        root.update_idletasks()
        x = (root.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y = (root.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        root.geometry(f"+{x}+{y}")

        root.protocol("WM_DELETE_WINDOW", self._on_close)
        return root

    def _build_services(self) -> tuple[DatabaseManager, AuthService, DashboardService, MemberService]:
        """Instantiate and wire all service-layer dependencies."""
        Path("database").mkdir(exist_ok=True)

        # 1. Base Core Architecture Initialization
        db = DatabaseManager(db_path=self.DB_PATH)

        # FORCE INITIALIZATION FIRST: This runs conn.executescript(SCHEMA)
        db.initialize_database()

        # 2. Build Repositories AFTER database tables are confirmed to exist
        repo = UserRepository(db)
        session = SessionManager()
        auth = AuthService(user_repo=repo, session_manager=session)

        # Seed the default administrator profile safely
        self._seed_default_admin(repo)

        # Dashboard Dependency Module Wiring
        dashboard_repo = DashboardRepository(db)
        dashboard_service = DashboardService(dashboard_repo)

        # Member Dependency Module Wiring
        member_repo = MemberRepository(db)
        member_service = MemberService(member_repo)

        return db, auth, dashboard_service, member_service

    @staticmethod
    def _seed_default_admin(repo: UserRepository) -> None:
        """
        Create a default admin account if no users exist yet.

        This is a one-time bootstrap step. The first thing an admin should
        do after first launch is change this password.
        """
        if not repo.username_exists("admin"):
            repo.create(
                username="admin",
                plain_password="admin123",
                role=Role.ADMIN,
            )
            logger.warning(
                "Default admin account created (username=admin, "
                "password=admin123). Change this password immediately."
            )

    # ── navigation ─────────────────────────────────────────────────────────────

    def _show_login(self) -> None:
        """Display the login frame."""
        self._swap_frame(
            LoginFrame(
                parent=self._root,
                auth_service=self._auth,
                on_login_success=self.on_login_success,
            )
        )
        # Move keyboard focus to username field after render
        self._root.after(
            100,
            lambda: (
                # type: ignore[union-attr]
                self._current_frame.focus_username()
                if hasattr(self._current_frame, "focus_username")
                else None
            ),
        )

    def on_login_success(self, user: User) -> None:
        """Called by LoginFrame after a successful login."""
        logger.info(
            "Login successful – user='%s' role='%s'.",
            user.username,
            user.role.value,
        )
        self._show_dashboard()

    def _show_dashboard(self) -> None:
        """Displays the active main Admin Dashboard view."""
        self._swap_frame(
            AdminDashboardFrame(
                parent=self._root,
                service=self._dashboard_service,
                member_service=self._member_service,
                on_logout=self._logout,
                on_add_member=self.show_member_form,
                on_view_members=self.show_member_database
            )
        )

    def show_member_form(self) -> None:
        """Routes layout display safely to the New Member registration screen."""
        self._swap_frame(
            MemberFormFrame(
                parent=self._root,
                member_service=self._member_service,
                on_cancel=self._show_dashboard
            )
        )

    def show_member_database(self) -> None:
        """Route to the Member Database list view."""
        self._swap_frame(
            MemberListFrame(
                parent=self._root,
                member_service=self._member_service,
                on_back=self._show_dashboard
            )
        )

    def _logout(self) -> None:
        """Log out the current user and return to login screen."""
        self._auth.logout()
        self._show_login()

    def _swap_frame(self, new_frame: tk.Frame) -> None:
        """Replace the current full-window frame with a new one safely."""
        if self._current_frame is not None:
            self._current_frame.destroy()

        new_frame.pack(fill="both", expand=True)
        self._current_frame = new_frame

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        """Clean shutdown on window close."""
        self._auth.logout()
        self._root.destroy()

    def run(self) -> None:
        """Start the application."""
        self._show_login()
        logger.info("Gym Manager started.")
        self._root.mainloop()
