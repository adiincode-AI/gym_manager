"""
ui/member_form_frame.py
Location : gym_app/members/ui/member_form_frame.py
Purpose  : The layout for registering a new member, now with silent API WhatsApp automation.
"""
import tkinter as tk
from datetime import date
import threading

from gym_app.members.service.member_service import MemberService
from gym_app.notifications.whatsapp_service import WhatsAppService
from gym_app.ui.components import (
    Card, EntryField, PrimaryButton,
    COLOR_BG, COLOR_CARD, COLOR_TEXT, COLOR_MUTED, FONT_FAMILY,
    PAD_LG, PAD_MD, PAD_SM
)
from gym_app.exceptions import AppError


class MemberFormFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, member_service: MemberService, on_cancel: callable) -> None:
        super().__init__(parent, bg=COLOR_BG)
        self._service = member_service
        self._on_cancel = on_cancel
        self._build_layout()

    def _build_layout(self) -> None:
        # ── Header ──
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=PAD_LG, pady=PAD_LG)

        tk.Label(
            header, text="Register New Member",
            font=(FONT_FAMILY, 24, "bold"), bg=COLOR_BG, fg=COLOR_TEXT
        ).pack(side="left")

        # ── Main Card Container ──
        card = Card(self)
        card.pack(padx=PAD_LG, pady=PAD_MD, fill="both", expand=True)

        # ── Action Buttons (Packed Bottom FIRST) ──
        btn_row = tk.Frame(card, bg=COLOR_CARD)
        btn_row.pack(side="bottom", fill="x", pady=(20, 0))

        PrimaryButton(
            btn_row,
            text="Save Member",
            command=self._handle_save
        ).pack(side="right", padx=(15, 0))

        tk.Button(
            btn_row,
            text="Cancel",
            command=self._on_cancel,
            font=(FONT_FAMILY, 10, "bold"),
            bg="#9CA3AF",
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        ).pack(side="right")

        # ── Status Message Banner ──
        self._status_lbl = tk.Label(card, text="", font=(FONT_FAMILY, 10), bg=COLOR_CARD)
        self._status_lbl.pack(side="bottom", pady=PAD_SM)

        # ── SCROLLABLE AREA SETUP ──
        scroll_container = tk.Frame(card, bg=COLOR_CARD)
        scroll_container.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, bg=COLOR_CARD, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        form_grid = tk.Frame(canvas, bg=COLOR_CARD)
        canvas_frame = canvas.create_window((0, 0), window=form_grid, anchor="nw")

        def _configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def _configure_canvas_width(event):
            canvas.itemconfig(canvas_frame, width=event.width)

        form_grid.bind("<Configure>", _configure_scroll_region)
        canvas.bind("<Configure>", _configure_canvas_width)

        # ── SAFE MOUSEWHEEL BINDING ──
        def _on_mousewheel(event):
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_mouse(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        def _unbind_mouse(event):
            canvas.unbind_all("<MouseWheel>")

        scroll_container.bind("<Enter>", _bind_mouse)
        scroll_container.bind("<Leave>", _unbind_mouse)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))


        # ── FORM FIELDS ──
        self._name_field = EntryField(form_grid, label="FULL NAME", width=40)
        self._name_field.pack(fill="x", pady=(0, PAD_SM))

        phone_row = tk.Frame(form_grid, bg=COLOR_CARD)
        phone_row.pack(fill="x", pady=(0, PAD_SM))

        self._phone_field = EntryField(phone_row, label="PHONE NUMBER", width=18)
        self._phone_field.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self._whatsapp_field = EntryField(phone_row, label="WHATSAPP NUMBER", width=18)
        self._whatsapp_field.pack(side="right", expand=True, fill="x")

        meta_row = tk.Frame(form_grid, bg=COLOR_CARD)
        meta_row.pack(fill="x", pady=(0, PAD_SM))
        meta_row.columnconfigure(0, weight=1)
        meta_row.columnconfigure(1, weight=1)

        age_col = tk.Frame(meta_row, bg=COLOR_CARD)
        age_col.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        tk.Label(
            age_col, text="AGE", font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_MUTED, bg=COLOR_CARD
        ).pack(anchor="w")

        self._age_field = EntryField(age_col, label="", width=10)
        self._age_field.pack(fill="x", expand=True, pady=(4, 0))

        gender_col = tk.Frame(meta_row, bg=COLOR_CARD)
        gender_col.grid(row=0, column=1, sticky="ew")

        tk.Label(
            gender_col, text="GENDER", font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_MUTED, bg=COLOR_CARD
        ).pack(anchor="w")

        self._gender_var = tk.StringVar(value="Male")
        gender_menu = tk.OptionMenu(
            gender_col, self._gender_var, "Male", "Female", "Other"
        )
        gender_menu.config(
            font=(FONT_FAMILY, 10), bg="white", relief="flat", bd=0,
            activebackground="#F8FAFC", highlightthickness=1, 
            highlightbackground="#D1C7B5" 
        )
        gender_menu.pack(anchor="w", fill="x", pady=(4, 0), ipady=5)

        self._address_field = EntryField(form_grid, label="ADDRESS", width=40)
        self._address_field.pack(fill="x", pady=(0, PAD_SM))

        sub_row = tk.Frame(form_grid, bg=COLOR_CARD)
        sub_row.pack(fill="x", pady=(0, PAD_MD))

        tk.Label(
            sub_row, text="MEMBERSHIP PLAN DURATION", font=(FONT_FAMILY, 9, "bold"),
            fg=COLOR_MUTED, bg=COLOR_CARD
        ).pack(anchor="w")

        self._plan_var = tk.StringVar(value="1 Month Plan")
        plan_menu = tk.OptionMenu(
            sub_row, self._plan_var,
            "1 Month Plan", "3 Month Plan", "6 Month Plan", "12 Month Plan"
        )
        plan_menu.config(
            font=(FONT_FAMILY, 10), bg="white", relief="flat", bd=0,
            activebackground="#F8FAFC", highlightthickness=1,
            highlightbackground="#D1C7B5" 
        )
        plan_menu.pack(anchor="w", fill="x", pady=(4, 0), ipady=5)


    def _handle_save(self) -> None:
        self._status_lbl.config(text="")

        name = self._name_field.get().strip()
        phone = self._phone_field.get().strip()
        whatsapp = self._whatsapp_field.get().strip()
        gender = self._gender_var.get()
        address = self._address_field.get().strip()
        plan_name = self._plan_var.get()

        try:
            age_raw = self._age_field.get().strip()
            age = int(age_raw) if age_raw else None
        except ValueError:
            self._status_lbl.config(text="Age must be a valid number.", fg="#DC2626")
            return

        if not name or not phone:
            self._status_lbl.config(text="Full Name and Phone Number are required.", fg="#DC2626")
            return

        try:
            member = self._service.register_new_member(
                full_name=name, phone=phone, whatsapp=whatsapp,
                gender=gender, age=age, address=address,
                plan_name=plan_name, join_date=date.today()
            )

            self._status_lbl.config(
                text=f"Registered successfully! Code: {member.member_code}", fg="#B8C4A9")
            
            # ── SILENT API WHATSAPP AUTOMATION ──
            target_number = whatsapp if whatsapp else phone
            
            # Run the API call in a tiny background thread so even if the internet 
            # is slightly slow, the app UI doesn't stutter for a split second.
            threading.Thread(
                target=WhatsAppService.send_welcome_message, 
                args=(target_number, name), 
                daemon=True
            ).start()
            
            # Close the form after 1.5 seconds
            self.after(1500, self._on_cancel)

        except AppError as exc:
            self._status_lbl.config(text=str(exc), fg="#DC2626")