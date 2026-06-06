import tkinter as tk
from tkinter import messagebox
from gym_app.members.models.member import Member
from gym_app.members.service.member_service import MemberService
from gym_app.ui.components import COLOR_TEXT, COLOR_MUTED, FONT_FAMILY, PrimaryButton

class RenewMemberDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, member: Member, service: MemberService, on_success: callable) -> None:
        super().__init__(parent)
        self._member = member
        self._service = service
        self._on_success = on_success
        
        self.title(f"Renew Plan — {member.member_code}")
        self.geometry("350x260")
        self.config(bg="white")
        self.transient(parent)
        self.grab_set()
        
        self._build_layout()

    def _build_layout(self) -> None:
        container = tk.Frame(self, bg="white", padx=20, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(
            container, text=f"Renewing {self._member.full_name}", 
            font=(FONT_FAMILY, 14, "bold"), bg="white", fg=COLOR_TEXT
        ).pack(anchor="w", pady=(0, 5))
        
        tk.Label(
            container, text=f"Current Expiry: {self._member.expiry_date}", 
            font=(FONT_FAMILY, 10), bg="white", fg=COLOR_MUTED
        ).pack(anchor="w", pady=(0, 20))

        tk.Label(
            container, text="SELECT NEW PLAN DURATION", 
            font=(FONT_FAMILY, 8, "bold"), bg="white", fg=COLOR_MUTED
        ).pack(anchor="w")

        self._plan_var = tk.StringVar(value="1 Month Plan")
        plan_menu = tk.OptionMenu(
            container, self._plan_var, 
            "1 Month Plan", "3 Month Plan", "6 Month Plan", "12 Month Plan"
        )
        plan_menu.config(
            font=(FONT_FAMILY, 10), bg="white", relief="groove", bd=1, highlightthickness=0  
        )
        plan_menu.pack(anchor="w", fill="x", pady=(4, 25), ipady=3)

        PrimaryButton(container, text="Confirm Renewal", command=self._process_renewal).pack(fill="x", ipady=4)

    def _process_renewal(self) -> None:
        try:
            self._service.renew_member_plan(self._member, self._plan_var.get())
            messagebox.showinfo("Success", f"Membership for {self._member.full_name} renewed successfully!", parent=self)
            self._on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Renewal Error", str(e), parent=self)