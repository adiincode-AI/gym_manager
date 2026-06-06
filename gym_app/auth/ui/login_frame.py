"""
auth/ui/login_frame.py
───────────────────────
Location : gym_app/auth/ui/login_frame.py
Purpose  : Login screen – the entry-point UI for the application.

Design decision
───────────────
LoginFrame is a tk.Frame subclass, NOT a tk.Toplevel or tk.Tk. This
means the caller (main app or test harness) decides where to place it
(full-window, embedded, etc.), keeping the frame reusable and testable.

Communication with the rest of the app uses a single on_login_success
callback injected at construction time. This avoids circular imports
between UI and the main application controller.

UI is deliberately split into private _build_* methods so each visual
section can be understood and changed in isolation.
"""
from __future__ import annotations
from PIL import Image, ImageTk
import os

import tkinter as tk
from typing import Callable

from gym_app.auth.models import User
from gym_app.auth.service import AuthService
from gym_app.auth.validators import AuthValidator
from gym_app.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    ValidationError,
    AppError,
)
from gym_app.ui.components import (
    Card,
    Label,
    EntryField,
    PrimaryButton,
    MessageBanner,
    COLOR_BG,
    COLOR_CARD,
    COLOR_PRIMARY,
    COLOR_MUTED,
    COLOR_TEXT,
    FONT_FAMILY,
    PAD_MD,
    PAD_LG,
    PAD_SM,
)


class LoginFrame(tk.Frame):
    """
    Login screen frame.

    Parameters
    ----------
    parent           : tk.Widget – parent container.
    auth_service     : AuthService – handles credential verification.
    on_login_success : Callable[[User], None] – called after successful login.
    """

    def __init__(
        self,
        parent: tk.Widget,
        auth_service: AuthService,
        on_login_success: Callable[[User], None],
    ) -> None:
        super().__init__(parent, bg=COLOR_BG)

        self._auth         = auth_service
        self._on_success   = on_login_success
        self._validator    = AuthValidator()

        self._build_layout()

    # ── layout builders ────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """Build the full-screen centred login layout."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        centre = tk.Frame(self, bg=COLOR_BG)
        centre.grid(row=0, column=0)

        self._build_logo(centre)
        self._build_card(centre)
        self._build_footer(centre)

    def _build_logo(self, parent: tk.Widget) -> None:
        """Logo area with custom image support."""
        
        # Path to your logo (assuming it's in an 'assets' folder)
        logo_path = os.path.join("assets", "iron_temple_icon.png")
        
        if os.path.exists(logo_path):
            # FIX 1: Resource Leak Prevention
            # Using a 'with' block ensures the file pointer is closed immediately 
            # after the image is resized and loaded into memory, preventing OS locks.
            with Image.open(logo_path) as img:
                resized_img = img.resize((100, 100), Image.Resampling.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(resized_img) 
            
            tk.Label(parent, image=self._logo_img, bg=COLOR_BG).pack(pady=(0, PAD_SM))
        else:
            # Fallback to emoji if file isn't found
            tk.Label(parent, text="🏋️", font=(FONT_FAMILY, 40), bg=COLOR_BG).pack(pady=(0, PAD_SM))

        tk.Label(
            parent,
            text="The Iron Temple GYM",
            font=(FONT_FAMILY, 18, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_BG,
        ).pack()

        tk.Label(
            parent,
            text="Management System",
            font=(FONT_FAMILY, 10),
            fg=COLOR_MUTED,
            bg=COLOR_BG,
        ).pack(pady=(0, PAD_LG))

    def _build_card(self, parent: tk.Widget) -> None:
        """Login form card."""
        card = Card(parent)
        card.pack(ipadx=PAD_MD, ipady=PAD_SM)

        # ── heading ────────────────────────────────────────────────────────────
        tk.Label(
            card,
            text="Sign In",
            font=(FONT_FAMILY, 16, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD,
        ).pack(anchor="w", pady=(0, PAD_SM))

        tk.Label(
            card,
            text="Enter your credentials to continue.",
            font=(FONT_FAMILY, 9),
            fg=COLOR_MUTED,
            bg=COLOR_CARD,
        ).pack(anchor="w", pady=(0, PAD_MD))

        # ── banner (errors / success) ──────────────────────────────────────────
        self._banner = MessageBanner(card)
        self._banner.pack(fill="x", pady=(0, PAD_SM))

        # ── username field ─────────────────────────────────────────────────────
        self._username_field = EntryField(card, label="USERNAME", width=32)
        self._username_field.pack(fill="x", pady=(0, PAD_SM))
        self._username_field.bind_return(self._handle_login)

        # ── password field ─────────────────────────────────────────────────────
        self._password_field = EntryField(
            card, label="PASSWORD", show="•", width=32
        )
        self._password_field.pack(fill="x", pady=(0, PAD_MD))
        self._password_field.bind_return(self._handle_login)

        # ── show/hide password toggle ──────────────────────────────────────────
        self._show_password = tk.BooleanVar(value=False)
        tk.Checkbutton(
            card,
            text="Show password",
            variable=self._show_password,
            command=self._toggle_password_visibility,
            font=(FONT_FAMILY, 9),
            fg=COLOR_MUTED,
            bg=COLOR_CARD,
            activebackground=COLOR_CARD,
            cursor="hand2",
            relief="flat",
            bd=0,
        ).pack(anchor="w", pady=(0, PAD_MD))

        # ── login button ───────────────────────────────────────────────────────
        self._login_btn = PrimaryButton(
            card,
            text="Sign In",
            command=self._handle_login,
        )
        self._login_btn.pack(fill="x", pady=(0, PAD_SM))

        # Keep reference for re-enabling after lock feedback
        self._card = card

    def _build_footer(self, parent: tk.Widget) -> None:
        """Version / copyright footer below the card."""
        tk.Label(
            parent,
            text="© 2026 The Iron Temple GYM  •  v1.0.0",
            font=(FONT_FAMILY, 8),
            fg=COLOR_MUTED,
            bg=COLOR_BG,
        ).pack(pady=(PAD_LG, 0))

    # ── event handlers ─────────────────────────────────────────────────────────

    def _handle_login(self) -> None:
        """Called when Sign In button is pressed or Enter key is hit."""
        self._clear_errors()

        username = self._username_field.get()
        password = self._password_field.get()

        # ── client-side validation first (fast feedback, no DB round-trip) ────
        try:
            self._validator.validate_login_inputs(username, password)
        except ValidationError as exc:
            self._show_field_error(exc.field, exc.message)
            return

        # ── disable button to prevent double-submission ────────────────────────
        self._set_loading(True)
        
        # FIX 2: UI Responsiveness
        # Force Tkinter to process pending draw events. Without this, the UI
        # freezes before the button text updates to "Signing in..." because 
        # bcrypt hashing blocks the thread.
        self.update_idletasks()

        # ── delegate to auth service ───────────────────────────────────────────
        try:
            user = self._auth.login(username, password)
            self._on_login_success(user)

        except ValidationError as exc:
            self._show_field_error(exc.field, exc.message)

        except AccountLockedError as exc:
            self._banner.show_error(str(exc))

        except InvalidCredentialsError as exc:
            self._banner.show_error(str(exc))
            
        except AppError as exc:
            self._banner.show_error(f"Unexpected error: {exc}")

        finally:
            self._set_loading(False)

    def _on_login_success(self, user: User) -> None:
        """Show brief success feedback then invoke the app callback."""
        self._banner.show_success(
            f"Welcome, {user.username}! "
            f"({user.role.value.capitalize()})"
        )
        # Small delay so the user sees the success banner before transition
        self.after(600, lambda: self._on_success(user))

    def _toggle_password_visibility(self) -> None:
        """Toggle password masking on/off."""
        # EntryField exposes its inner entry via the _entry attribute.
        show_char = "" if self._show_password.get() else "•"
        self._password_field._entry.config(show=show_char)

    # ── state helpers ──────────────────────────────────────────────────────────

    def _set_loading(self, loading: bool) -> None:
        """Disable/enable the login button during the auth call."""
        state = "disabled" if loading else "normal"
        text  = "Signing in…" if loading else "Sign In"
        self._login_btn.config(state=state, text=text)

    def _clear_errors(self) -> None:
        """Remove all inline errors and the banner."""
        self._banner.clear()
        self._username_field.clear_error()
        self._password_field.clear_error()

    def _show_field_error(self, field: str, message: str) -> None:
        """Route a ValidationError to the correct field's error label."""
        if field == "username":
            self._username_field.set_error(message)
            # FIX 3: Tkinter Widget Focusing
            # Target the inner tk.Entry directly so the text cursor appears.
            self._username_field._entry.focus_set()
        elif field == "password":
            self._password_field.set_error(message)
            self._password_field._entry.focus_set()
        else:
            self._banner.show_error(message)

    def focus_username(self) -> None:
        """Move focus to the username field (call after pack/grid/place)."""
        # FIX 3: Tkinter Widget Focusing
        self._username_field._entry.focus_set()