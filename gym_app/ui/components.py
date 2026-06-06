"""
ui/components.py
Location : gym_app/ui/components.py
Purpose  : Reusable, styled Tkinter widgets with Premium Modern Organic theme.
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable

# ── design tokens (Premium Organic Palette) ──────────────────────────────────

FONT_FAMILY   = "Segoe UI"
COLOR_BG      = "#F4E9D7"  # Cream Background
COLOR_CARD    = "#FFFFFF"  # White Card
COLOR_PRIMARY = "#D97D55"  # Terracotta (Primary Actions)
COLOR_ACCENT  = "#6FA4AF"  # Muted Blue-Gray (Highlights)
COLOR_SUCCESS = "#B8C4A9"  # Sage Green (Success)
COLOR_DANGER  = "#DC2626"  # Error
COLOR_TEXT    = "#333333"  # Soft Charcoal
COLOR_MUTED   = "#666666"  # Secondary text
COLOR_BORDER  = "#D1C7B5"  # Subtle structure

# General padding variables
PAD_SM  = 12
PAD_MD  = 20
PAD_LG  = 48 


# ── label ──────────────────────────────────────────────────────────────────────

class Label(tk.Label):
    """Premium label with clear hierarchy."""
    def __init__(self, parent: tk.Widget, text: str = "", bold: bool = False, 
                 size: int = 10, color: str = COLOR_TEXT, **kwargs) -> None:
        weight = "bold" if bold else "normal"
        super().__init__(parent, text=text, font=(FONT_FAMILY, size, weight),
                         fg=color, bg=kwargs.pop("bg", COLOR_CARD), **kwargs)


# ── entry ──────────────────────────────────────────────────────────────────────

class EntryField(tk.Frame):
    """Spacious, interactive text entry."""
    def __init__(self, parent: tk.Widget, label: str, show: str = "", 
                 width: int = 30, **kwargs) -> None:
        super().__init__(parent, bg=COLOR_CARD, **kwargs)

        tk.Label(self, text=label, font=(FONT_FAMILY, 9, "bold"), fg=COLOR_MUTED,
                 bg=COLOR_CARD, anchor="w").pack(fill="x", pady=(0, 4))

        self._var = tk.StringVar()
        self._entry = tk.Entry(self, textvariable=self._var, show=show, width=width,
                               font=(FONT_FAMILY, 11), fg=COLOR_TEXT, bg="#FFFFFF",
                               relief="flat", bd=0, highlightthickness=1,
                               highlightbackground=COLOR_BORDER,
                               highlightcolor=COLOR_ACCENT)
        self._entry.pack(fill="x", ipady=8)

        self._error_label = tk.Label(self, text="", font=(FONT_FAMILY, 8),
                                     fg=COLOR_DANGER, bg=COLOR_CARD, anchor="w")
        self._error_label.pack(fill="x")

    def get(self) -> str: return self._var.get()
    def clear(self) -> None: self._var.set("")
    def set_error(self, message: str) -> None:
        self._error_label.config(text=message)
        self._entry.config(highlightbackground=COLOR_DANGER)
    def clear_error(self) -> None:
        self._error_label.config(text="")
        self._entry.config(highlightbackground=COLOR_BORDER)
    def bind_return(self, callback: Callable) -> None:
        self._entry.bind("<Return>", lambda _: callback())


# ── button ─────────────────────────────────────────────────────────────────────

class PrimaryButton(tk.Button):
    """Elegant action button with hover interaction."""
    def __init__(self, parent: tk.Widget, text: str, command: Callable, **kwargs) -> None:
        super().__init__(parent, text=text, command=command, font=(FONT_FAMILY, 11, "bold"),
                         fg="#FFFFFF", bg=COLOR_PRIMARY, activeforeground="#FFFFFF",
                         activebackground="#B56A48", relief="flat", bd=0,
                         cursor="hand2", padx=20, pady=12, **kwargs)
        self.bind("<Enter>", lambda _: self.config(bg="#B56A48"))
        self.bind("<Leave>", lambda _: self.config(bg=COLOR_PRIMARY))


# ── message banner ─────────────────────────────────────────────────────────────

class MessageBanner(tk.Label):
    """Subtle status feedback."""
    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, text="", font=(FONT_FAMILY, 9), bg=COLOR_CARD,
                         pady=10, padx=PAD_MD, anchor="center", **kwargs)

    def show_error(self, message: str) -> None:
        self.config(text=f"⚠  {message}", fg=COLOR_DANGER, bg="#FEE2E2")

    def show_success(self, message: str) -> None:
        self.config(text=f"✓  {message}", fg="#4A5D4E", bg="#E8EEDF")

    def clear(self) -> None:
        self.config(text="", bg=COLOR_CARD)


# ── card frame ─────────────────────────────────────────────────────────────────

class Card(tk.Frame):
    """Premium container with smart padding (wide horizontal, tighter vertical)."""
    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(
            parent, 
            bg=COLOR_CARD, 
            highlightthickness=1,
            highlightbackground=COLOR_BORDER, 
            padx=40,  # Premium wide horizontal breathing room
            pady=16,  # Tighter vertical padding to keep elements on screen
            **kwargs
        )