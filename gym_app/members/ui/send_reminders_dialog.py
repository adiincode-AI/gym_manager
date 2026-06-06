"""
ui/send_reminders_dialog.py
Location : gym_app/members/ui/send_reminders_dialog.py
Purpose  : A dedicated dialog to view defaulters and send bulk API WhatsApp reminders.
"""
import tkinter as tk
from tkinter import messagebox
import threading

from gym_app.members.service.member_service import MemberService
from gym_app.notifications.whatsapp_service import WhatsAppService
from gym_app.ui.components import PrimaryButton, FONT_FAMILY, COLOR_BG, COLOR_TEXT, COLOR_MUTED

class SendRemindersDialog:
    def __init__(self, parent: tk.Widget, service: MemberService):
        self._parent = parent
        self._service = service
        self._defaulters = []
        
        self._build_dialog()

    def _build_dialog(self) -> None:
        self._dialog = tk.Toplevel(self._parent)
        self._dialog.title("Notification Center - Send Reminders")
        self._dialog.config(bg=COLOR_BG)
        self._dialog.transient(self._parent)
        self._dialog.grab_set()
        
        # Center the dialog
        width, height = 500, 600
        x = self._parent.winfo_x() + (self._parent.winfo_width() // 2) - (width // 2)
        y = self._parent.winfo_y() + (self._parent.winfo_height() // 2) - (height // 2)
        self._dialog.geometry(f"{width}x{height}+{x}+{y}")
        self._dialog.resizable(False, False)

        # ── Header ──
        header_frame = tk.Frame(self._dialog, bg=COLOR_BG, padx=20, pady=20)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="🔔 Bulk Reminders", font=(FONT_FAMILY, 18, "bold"), bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w")
        tk.Label(header_frame, text="Send automated WhatsApp reminders to expired members via API.", font=(FONT_FAMILY, 9), bg=COLOR_BG, fg=COLOR_MUTED).pack(anchor="w", pady=(5, 0))

        # ── List Container ──
        list_container = tk.Frame(self._dialog, bg="white", highlightbackground="#E5E7EB", highlightthickness=1)
        list_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Scrollable canvas for members
        canvas = tk.Canvas(list_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        self._scrollable_frame = tk.Frame(canvas, bg="white")

        self._scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._scrollable_frame, anchor="nw", width=440)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # ── Footer Actions ──
        footer = tk.Frame(self._dialog, bg=COLOR_BG, padx=20, pady=20)
        footer.pack(fill="x", side="bottom")

        tk.Button(
            footer, text="Cancel", command=self._dialog.destroy,
            font=(FONT_FAMILY, 10, "bold"), bg="#9CA3AF", fg="white",
            relief="flat", cursor="hand2", pady=10, width=12
        ).pack(side="left")

        self._send_btn = PrimaryButton(
            footer, text="Send All Reminders", 
            command=self._handle_send_reminders
        )
        self._send_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self._load_defaulters()

    def _load_defaulters(self) -> None:
        """Fetch expiring members from the database and populate the list."""
        for widget in self._scrollable_frame.winfo_children():
            widget.destroy()

        self._defaulters = self._service.get_expiring_members()

        if not self._defaulters:
            tk.Label(
                self._scrollable_frame, 
                text="Great job! No members are currently expired.", 
                font=(FONT_FAMILY, 11, "italic"), bg="white", fg=COLOR_MUTED
            ).pack(pady=40)
            self._send_btn.config(state="disabled", text="No Reminders to Send")
            return

        for idx, member in enumerate(self._defaulters, start=1):
            row = tk.Frame(self._scrollable_frame, bg="white")
            row.pack(fill="x", pady=6)
            
            # Use WhatsApp number if available, else fallback to primary phone
            target_phone = member.whatsapp if member.whatsapp else member.phone
            
            tk.Label(row, text=f"{idx}. {member.full_name}", font=(FONT_FAMILY, 10, "bold"), bg="white", fg=COLOR_TEXT).pack(side="left")
            tk.Label(row, text=f" ({target_phone})", font=(FONT_FAMILY, 9), bg="white", fg=COLOR_MUTED).pack(side="left")
            tk.Label(row, text=f"Exp: {member.expiry_date}", font=(FONT_FAMILY, 9, "bold"), bg="white", fg="#DC2626").pack(side="right", padx=(0, 10))
            
            div = tk.Frame(self._scrollable_frame, bg="#F3F4F6", height=1)
            div.pack(fill="x")

        self._send_btn.config(text=f"Send {len(self._defaulters)} Reminders")

    def _handle_send_reminders(self) -> None:
        """Triggers the background API thread."""
        if not self._defaulters:
            return
            
        confirm = messagebox.askyesno(
            "Confirm Setup", 
            f"Are you sure you want to send {len(self._defaulters)} WhatsApp reminders now?\n\nThis will happen instantly via the UltraMsg API."
        )
        
        if not confirm:
            return

        # Disable UI to prevent double clicks
        self._send_btn.config(state="disabled", text="Sending...")
        self._dialog.update_idletasks()

        # Run API calls in background thread to keep UI responsive
        threading.Thread(target=self._run_api_loop, daemon=True).start()

    def _run_api_loop(self) -> None:
        success_count = 0
        
        for member in self._defaulters:
            target_phone = member.whatsapp if member.whatsapp else member.phone
            
            # Fire the instant API request
            success = WhatsAppService.send_payment_reminder(target_phone, member.full_name)
            
            if success:
                success_count += 1
                
        # Schedule the UI update back on the main thread safely
        self._dialog.after(0, lambda: self._on_finish(success_count))

    def _on_finish(self, success_count: int) -> None:
        messagebox.showinfo(
            "Complete", 
            f"Successfully sent {success_count} out of {len(self._defaulters)} reminders!"
        )
        self._dialog.destroy()