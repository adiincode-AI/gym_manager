"""
ui/dashboard_frame.py
Location : gym_app/dashboard/ui/dashboard_frame.py
Purpose  : The main admin dashboard with real-time search.
"""
import tkinter as tk
from typing import Callable

from gym_app.dashboard.service.dashboard_service import DashboardService
from gym_app.members.service.member_service import MemberService
from gym_app.members.models.member import Member
from gym_app.ui.components import Card, PrimaryButton, COLOR_BG, COLOR_CARD, COLOR_TEXT, COLOR_MUTED, FONT_FAMILY, PAD_LG, PAD_MD, PAD_SM
from gym_app.members.ui.renew_member_dialog import RenewMemberDialog
from gym_app.members.ui.send_reminders_dialog import SendRemindersDialog

class AdminDashboardFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, service: DashboardService, member_service: MemberService, on_logout: Callable, on_add_member: Callable, on_view_members: Callable):
        super().__init__(parent, bg=COLOR_BG)
        self._service = service
        self._member_service = member_service
        self._on_logout = on_logout
        self._on_add_member = on_add_member
        self._on_view_members = on_view_members
        
        self._search_timer = None
        
        self._build_layout()
        self._load_data()

    def _build_layout(self) -> None:
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=PAD_LG, pady=PAD_LG)
        
        tk.Label(header, text="The Iron Temple GYM", font=(FONT_FAMILY, 24, "bold"), bg=COLOR_BG, fg=COLOR_TEXT).pack(side="left")
        tk.Button(header, text="Log Out", command=self._on_logout, font=(FONT_FAMILY, 10), bg="#ff4d4d", fg="white", relief="flat", padx=10).pack(side="right")

        self._stats_frame = tk.Frame(self, bg=COLOR_BG)
        self._stats_frame.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))

        self._lbl_members = self._create_stat_card(self._stats_frame, "Active Members", "0")
        self._lbl_expiring = self._create_stat_card(self._stats_frame, "Expiring Soon", "0")

        tk.Label(self, text="Quick Actions", font=(FONT_FAMILY, 16, "bold"), bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w", padx=PAD_LG, pady=(PAD_LG, PAD_SM))
        
        nav_grid = tk.Frame(self, bg=COLOR_BG)
        nav_grid.pack(fill="x", padx=PAD_LG)
        
        self._create_nav_card(nav_grid, "➕ Add New Member", self._nav_add_member)
        self._create_nav_card(nav_grid, "👥 Member Database", self._nav_member_db)
        self._create_nav_card(nav_grid, "🔔 Send Reminders", self._nav_reminders)

        main_content = tk.Frame(self, bg=COLOR_BG)
        main_content.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_LG)

        main_content.columnconfigure(0, weight=1) 
        main_content.columnconfigure(1, weight=2) 
        main_content.rowconfigure(0, weight=1) 

        # ── LEFT COLUMN: SEARCH AREA ──
        search_col = tk.Frame(main_content, bg=COLOR_BG)
        search_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(search_col, text="🔍 Quick Lookup", font=(FONT_FAMILY, 14, "bold"), bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor="w", pady=(0, 5))

        self._results_frame = tk.Frame(search_col, bg="white", highlightbackground="#E5E7EB", highlightthickness=1)
        
        search_card = Card(search_col)
        search_card.pack(fill="x")

        self._search_var = tk.StringVar()
        
        self._search_entry = tk.Entry(search_card, textvariable=self._search_var, font=(FONT_FAMILY, 11), bg="white", fg=COLOR_MUTED, relief="flat", bd=0)
        self._search_entry.insert(0, "Search Name or Code...")
        
        self._search_entry.bind("<FocusIn>", lambda e: (self._search_entry.delete(0, "end"), self._search_entry.config(fg=COLOR_TEXT)) if "Search Name" in self._search_entry.get() else None)
        self._search_entry.bind("<FocusOut>", lambda e: (self._search_entry.insert(0, "Search Name or Code..."), self._search_entry.config(fg=COLOR_MUTED)) if not self._search_var.get().strip() else None)
        self._search_entry.pack(fill="x", padx=10, pady=8)
       
        self._search_var.trace_add("write", self._on_search_change)

        # ── RIGHT COLUMN: ALERTS FEED ONLY ──
        feeds_col = tk.Frame(main_content, bg=COLOR_BG)
        feeds_col.grid(row=0, column=1, sticky="nsew")

        alerts_wrapper = tk.Frame(feeds_col, bg=COLOR_BG)
        alerts_wrapper.pack(fill="both", expand=True)

        tk.Label(alerts_wrapper, text="⚠️ Alerts: Expiring Soon", font=(FONT_FAMILY, 12, "bold"), bg=COLOR_BG, fg="#DC2626").pack(anchor="w", pady=(0, 5))
        self._alerts_card = Card(alerts_wrapper)
        self._alerts_card.pack(fill="both", expand=True)
        self._alerts_container = tk.Frame(self._alerts_card, bg="white")
        self._alerts_container.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_stat_card(self, parent: tk.Widget, title: str, default_val: str) -> tk.Label:
        card = Card(parent)
        card.pack(side="left", expand=True, fill="x", padx=5)
        tk.Label(card, text=title, font=(FONT_FAMILY, 10), bg="white", fg=COLOR_MUTED).pack(pady=(10, 0))
        val_label = tk.Label(card, text=default_val, font=(FONT_FAMILY, 20, "bold"), bg="white", fg=COLOR_TEXT)
        val_label.pack(pady=(0, 10))
        return val_label

    def _create_nav_card(self, parent: tk.Widget, title: str, command: Callable) -> None:
        btn = PrimaryButton(parent, text=title, command=command)
        btn.pack(side="left", expand=True, fill="both", padx=5, ipady=15)

    def _load_data(self) -> None:
        stats = self._service.get_summary()
        self._lbl_members.config(text=f"{stats.active_members} / {stats.total_members}")
        self._lbl_expiring.config(text=str(stats.expiring_soon), fg="#DC2626" if stats.expiring_soon > 0 else COLOR_TEXT)

        for c in self._alerts_container.winfo_children(): c.destroy()

        expiring = self._member_service.get_expiring_members()
        if not expiring:
            tk.Label(self._alerts_container, text="No members expiring this week.", font=(FONT_FAMILY, 10, "italic"), bg="white", fg=COLOR_MUTED).pack(anchor="w")
        else:
            for m in expiring:
                row = tk.Frame(self._alerts_container, bg="white")
                row.pack(fill="x", pady=4)
                tk.Label(row, text=f"• {m.full_name}", font=(FONT_FAMILY, 10, "bold"), bg="white", fg=COLOR_TEXT).pack(side="left")
                tk.Label(row, text=f" ({m.phone})", font=(FONT_FAMILY, 10), bg="white", fg=COLOR_MUTED).pack(side="left")
                tk.Label(row, text=f"Exp: {m.expiry_date}", font=(FONT_FAMILY, 9, "bold"), bg="white", fg="#DC2626").pack(side="right")

    def _on_search_change(self, *args) -> None:
        if self._search_timer is not None:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(300, self._execute_search)

    def _execute_search(self) -> None:
        query = self._search_var.get().strip()
        if not query or "Search Name" in query or len(query) < 2:
            self._results_frame.pack_forget()
            return

        for child in self._results_frame.winfo_children(): child.destroy()
        
        results = self._member_service.search_active_members(query)
        
        if not results:
            lbl = tk.Label(self._results_frame, text="No matching members found.", font=(FONT_FAMILY, 10, "italic"), bg="white", fg=COLOR_MUTED)
            lbl.pack(fill="x", padx=10, pady=5, anchor="w")
        else:
            for item in results:
                row = tk.Frame(self._results_frame, bg="white", cursor="hand2")
                row.pack(fill="x", padx=5, pady=2)
                
                info_str = f"🆔 {item.member_code}  |  👤 {item.full_name}  |  📞 {item.phone}"
                lbl = tk.Label(row, text=info_str, font=(FONT_FAMILY, 10), bg="white", fg=COLOR_TEXT)
                lbl.pack(side="left", padx=5, pady=4)
                
                row.bind("<Button-1>", lambda e, m=item: self._show_member_popup(m))
                lbl.bind("<Button-1>", lambda e, m=item: self._show_member_popup(m))
                
                row.bind("<Enter>", lambda e, r=row: r.config(bg="#F3F4F6"))
                row.bind("<Leave>", lambda e, r=row: r.config(bg="white"))
                lbl.bind("<Enter>", lambda e, r=row: r.config(bg="#F3F4F6"))
                lbl.bind("<Leave>", lambda e, r=row: r.config(bg="white"))

        self._results_frame.pack(fill="x", padx=2, pady=2)

    def _show_member_popup(self, member: Member) -> None:
        self._search_var.set("")
        self._results_frame.pack_forget()
        
        if hasattr(self, "_active_popup") and self._active_popup.winfo_exists():
            self._active_popup.destroy()

        popup = tk.Toplevel(self)
        self._active_popup = popup
        
        popup.title(f"Member Profile — {member.member_code}")
        popup.config(bg="#F8FAFC")
        popup.transient(self.winfo_toplevel())
        popup.grab_set()
        
        popup.protocol("WM_DELETE_WINDOW", popup.destroy)
        
        main_box = tk.Frame(popup, bg="white", highlightbackground="#E2E8F0", highlightthickness=1, padx=24, pady=24)
        main_box.pack(fill="both", expand=True, padx=20, pady=20)
        
        badge_frame = tk.Frame(main_box, bg="#EFF6FF", padx=12, pady=6)
        badge_frame.pack(anchor="w", pady=(0, 15))
        tk.Label(badge_frame, text=member.member_code, font=(FONT_FAMILY, 11, "bold"), bg="#EFF6FF", fg="#1D4ED8").pack()
        
        tk.Label(main_box, text=member.full_name, font=(FONT_FAMILY, 18, "bold"), bg="white", fg=COLOR_TEXT).pack(anchor="w")
        
        status_text = "🟢 Active Profile" if member.is_active else "🔴 Expired Profile"
        status_color = "#16A34A" if member.is_active else "#DC2626"
        tk.Label(main_box, text=status_text, font=(FONT_FAMILY, 10, "bold"), bg="white", fg=status_color).pack(anchor="w", pady=(0, 20))
        
        def add_info_line(label_text: str, value_text: str):
            line = tk.Frame(main_box, bg="white")
            line.pack(fill="x", pady=6)
            tk.Label(line, text=label_text, font=(FONT_FAMILY, 9, "bold"), bg="white", fg=COLOR_MUTED, width=18, anchor="w").pack(side="left")
            tk.Label(line, text=value_text, font=(FONT_FAMILY, 10), bg="white", fg=COLOR_TEXT, anchor="w", justify="left").pack(side="left", expand=True, fill="x")
        
        add_info_line("Primary Phone:", member.phone)
        add_info_line("WhatsApp Link:", member.whatsapp)
        add_info_line("Gender / Age:", f"{member.gender or '-'}   /   {f'{member.age} Yrs' if member.age else '-'}")
        add_info_line("Home Address:", member.address or "No home address recorded.")
        
        div = tk.Frame(main_box, bg="#E2E8F0", height=1)
        div.pack(fill="x", pady=15)
        
        add_info_line("Plan Enrolled:", member.plan_name)
        add_info_line("Join Date:", str(member.join_date))
        add_info_line("Expiry Target:", str(member.expiry_date))
        
        action_row = tk.Frame(main_box, bg="white")
        action_row.pack(fill="x", pady=(20, 0))

        tk.Button(
            action_row, text="Close", command=popup.destroy,
            font=(FONT_FAMILY, 10, "bold"), bg="#9CA3AF", fg="white",
            relief="flat", cursor="hand2", pady=8, width=12
        ).pack(side="left", expand=True, padx=(0, 5))

        tk.Button(
            action_row, text="⏳ Renew Plan", 
            command=lambda: self._open_renewal_dialog(member, popup),
            font=(FONT_FAMILY, 10, "bold"), bg="#16A34A", fg="white",
            relief="flat", cursor="hand2", pady=8, width=12
        ).pack(side="right", expand=True, padx=(5, 0))

        popup.update_idletasks()
        safe_width = popup.winfo_reqwidth() + 30
        safe_height = popup.winfo_reqheight() + 50 
        
        popup.geometry(f"{safe_width}x{safe_height}")
        popup.minsize(safe_width, safe_height)

    def _open_renewal_dialog(self, member: Member, parent_popup: tk.Toplevel) -> None:
        def on_success():
            parent_popup.destroy()
            self._load_data()

        RenewMemberDialog(
            parent=self.winfo_toplevel(),
            member=member,
            service=self._member_service,
            on_success=on_success
        )

    # Navigation Handlers
    def _nav_add_member(self): self._on_add_member()
    def _nav_member_db(self): self._on_view_members()
    def _nav_reminders(self):
        SendRemindersDialog(
            parent=self.winfo_toplevel(),
            service=self._member_service
        )