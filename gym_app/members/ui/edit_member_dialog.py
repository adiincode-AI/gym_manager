import tkinter as tk
from datetime import date
from gym_app.members.models.member import Member
from gym_app.members.service.member_service import MemberService
from gym_app.ui.components import EntryField, PrimaryButton, COLOR_TEXT, COLOR_MUTED, FONT_FAMILY, PAD_MD, PAD_SM
from tkinter import messagebox

class EditMemberDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, member: Member, service: MemberService, on_success: callable) -> None:
        super().__init__(parent)
        self._member = member
        self._service = service
        self._on_success = on_success
        
        self.title(f"Edit Member Profile — {member.member_code}")
        self.geometry("450x650")
        self.config(bg="white")
        self.transient(parent)
        self.grab_set()
        
        self._build_layout()

    def _build_layout(self) -> None:
        # Create a scrollable canvas wrapper to prevent button cutoff
        canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        container = tk.Frame(canvas, bg="white", padx=20, pady=20)

        container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=container, anchor="nw", width=410)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # UI Elements
        tk.Label(container, text=f"Modify Details: {self._member.member_code}", font=(FONT_FAMILY, 14, "bold"), bg="white", fg=COLOR_TEXT).pack(anchor="w", pady=(0, PAD_MD))

        self._name_field = EntryField(container, label="FULL NAME", width=35)
        self._name_field.pack(fill="x", pady=(0, PAD_SM))
        self._name_field._entry.insert(0, self._member.full_name)

        self._phone_field = EntryField(container, label="PHONE NUMBER", width=35)
        self._phone_field.pack(fill="x", pady=(0, PAD_SM))
        self._phone_field._entry.insert(0, self._member.phone)

        self._whatsapp_field = EntryField(container, label="WHATSAPP NUMBER", width=35)
        self._whatsapp_field.pack(fill="x", pady=(0, PAD_SM))
        self._whatsapp_field._entry.insert(0, self._member.whatsapp)

        meta_row = tk.Frame(container, bg="white")
        meta_row.pack(fill="x", pady=(0, PAD_SM))
        meta_row.columnconfigure(0, weight=1)
        meta_row.columnconfigure(1, weight=1)

        age_col = tk.Frame(meta_row, bg="white")
        age_col.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        tk.Label(age_col, text="AGE", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_MUTED, bg="white").pack(anchor="w")
        self._age_field = EntryField(age_col, label="", width=10)
        self._age_field.pack(fill="x", expand=True, pady=(4, 0))
        if self._member.age: self._age_field._entry.insert(0, str(self._member.age))

        gender_col = tk.Frame(meta_row, bg="white")
        gender_col.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        tk.Label(gender_col, text="GENDER", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_MUTED, bg="white").pack(anchor="w")
        self._gender_var = tk.StringVar(value=self._member.gender or "Male")
        g_menu = tk.OptionMenu(gender_col, self._gender_var, "Male", "Female", "Other")
        g_menu.config(font=(FONT_FAMILY, 10), bg="white", relief="groove", bd=1, highlightthickness=0)
        g_menu.pack(fill="x", pady=(4, 0), ipady=3)

        self._address_field = EntryField(container, label="ADDRESS", width=35)
        self._address_field.pack(fill="x", pady=(0, PAD_SM))
        if self._member.address: self._address_field._entry.insert(0, self._member.address)

        tk.Label(container, text="MEMBERSHIP PLAN DURATION", font=(FONT_FAMILY, 8, "bold"), fg=COLOR_MUTED, bg="white").pack(anchor="w", pady=(PAD_SM, 0))
        self._plan_var = tk.StringVar(value=self._member.plan_name)
        p_menu = tk.OptionMenu(container, self._plan_var, "1 Month Plan", "3 Month Plan", "6 Month Plan", "12 Month Plan")
        p_menu.config(font=(FONT_FAMILY, 10), bg="white", relief="groove", bd=1, highlightthickness=0)
        p_menu.pack(fill="x", pady=(4, 15), ipady=3)

        btn_frame = tk.Frame(container, bg="white")
        btn_frame.pack(fill="x", pady=(PAD_MD, 20))

        PrimaryButton(btn_frame, text="Save Changes", command=self._handle_save).pack(side="right", padx=(PAD_SM, 0))
        tk.Button(btn_frame, text="Delete Member", command=self._handle_delete, font=(FONT_FAMILY, 10, "bold"), bg="#DC2626", fg="white", relief="flat", padx=12, pady=6, cursor="hand2").pack(side="left")

    def _handle_save(self) -> None:
        try:
            age_raw = self._age_field.get().strip()
            age = int(age_raw) if age_raw else None
            
            self._service.update_member_details(
                member_id=self._member.id, code=self._member.member_code,
                name=self._name_field.get(), phone=self._phone_field.get(),
                whatsapp=self._whatsapp_field.get(), gender=self._gender_var.get(),
                age=age, address=self._address_field.get(),
                plan_name=self._plan_var.get(), join_date=self._member.join_date
            )
            self._on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _handle_delete(self) -> None:
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you absolutely sure you want to delete {self._member.full_name}?", parent=self)
        if confirm:
            try:
                self._service.remove_member(self._member.id)
                self._on_success()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)