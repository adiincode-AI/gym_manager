import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import urllib.parse
from datetime import date, timedelta
from gym_app.members.service.member_service import MemberService
from gym_app.ui.components import COLOR_BG, COLOR_TEXT, COLOR_MUTED, FONT_FAMILY, PAD_LG

class SendRemindersDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, service: MemberService):
        super().__init__(parent)
        self._service = service
        self._members_cache = {}
        
        self.title("🔔 Send Renewal Reminders")
        self.geometry("750x600")
        self.minsize(700, 500)
        self.config(bg=COLOR_BG)
        self.transient(parent)
        self.grab_set()
        
        self._build_style()
        self._build_layout()
        self._load_data()

    def _build_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview", background="white", foreground=COLOR_TEXT, 
            rowheight=35, fieldbackground="white", font=(FONT_FAMILY, 10), borderwidth=0
        )
        style.map("Treeview", background=[("selected", "#EFF6FF")], foreground=[("selected", "#1D4ED8")])
        style.configure(
            "Treeview.Heading", background=COLOR_BG, foreground=COLOR_MUTED, 
            font=(FONT_FAMILY, 9, "bold"), borderwidth=0, relief="flat"
        )

    def _build_layout(self) -> None:
        # 1. Top Header
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(side="top", fill="x", padx=PAD_LG, pady=PAD_LG)
        
        tk.Label(header, text="Needs Renewal Reminder", font=(FONT_FAMILY, 18, "bold"), bg=COLOR_BG, fg=COLOR_TEXT).pack(side="left")

        # 2. Bottom Action Bar (Packed SECOND so it glues to the bottom and never gets pushed off)
        action_bar = tk.Frame(self, bg=COLOR_BG)
        action_bar.pack(side="bottom", fill="x", padx=PAD_LG, pady=(0, PAD_LG))
        
        tk.Button(
            action_bar, text="Close Window", command=self.destroy,
            font=(FONT_FAMILY, 10, "bold"), bg="#9CA3AF", fg="white", relief="flat", padx=20, pady=10, cursor="hand2"
        ).pack(side="left")

        tk.Button(
            action_bar, text="🟢 Send WhatsApp Reminder", command=self._send_whatsapp,
            font=(FONT_FAMILY, 10, "bold"), bg="#16A34A", fg="white", relief="flat", padx=20, pady=10, cursor="hand2"
        ).pack(side="right")

        # 3. Middle Data Grid (Packed LAST so it fills whatever space is left between the header and footer)
        grid_frame = tk.Frame(self, bg="white", highlightbackground="#E5E7EB", highlightthickness=1)
        grid_frame.pack(side="top", fill="both", expand=True, padx=PAD_LG, pady=(0, PAD_LG))
        
        columns = ("name", "phone", "plan", "expiry", "status")
        self._tree = ttk.Treeview(grid_frame, columns=columns, show="headings", style="Treeview")
        
        self._tree.heading("name", text="FULL NAME", anchor="w")
        self._tree.column("name", width=180, anchor="w")
        self._tree.heading("phone", text="PHONE", anchor="w")
        self._tree.column("phone", width=120, anchor="w")
        self._tree.heading("plan", text="PLAN", anchor="w")
        self._tree.column("plan", width=100, anchor="w")
        self._tree.heading("expiry", text="EXPIRY DATE", anchor="w")
        self._tree.column("expiry", width=100, anchor="w")
        self._tree.heading("status", text="STATUS", anchor="w")
        self._tree.column("status", width=150, anchor="w")

        scrollbar = ttk.Scrollbar(grid_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        
        self._tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

        # Bottom Action Bar
        action_bar = tk.Frame(self, bg=COLOR_BG)
        action_bar.pack(fill="x", padx=PAD_LG, pady=(0, PAD_LG))
        
        tk.Button(
            action_bar, text="Close Window", command=self.destroy,
            font=(FONT_FAMILY, 10, "bold"), bg="#9CA3AF", fg="white", relief="flat", padx=20, pady=10, cursor="hand2"
        ).pack(side="left")

        tk.Button(
            action_bar, text="🟢 Send WhatsApp Reminder", command=self._send_whatsapp,
            font=(FONT_FAMILY, 10, "bold"), bg="#16A34A", fg="white", relief="flat", padx=20, pady=10, cursor="hand2"
        ).pack(side="right")

    def _load_data(self) -> None:
        today = date.today()
        # Only show members who are due for a reminder
        members = self._service.get_all_members()
        
        for item in self._tree.get_children():
            self._tree.delete(item)
        
        for m in members:
            # 1. Check if we sent them a message recently (the "Gatekeeper" check)
            if self._service.has_received_reminder_recently(m.id):
                continue # Skip this member if they were messaged in the last 7 days
                
            expiry = m.expiry_date if isinstance(m.expiry_date, date) else date.fromisoformat(m.expiry_date)
            days_diff = (expiry - today).days
            
            # 2. Filter: Expired in last 30 days OR expiring in next 7 days
            if -30 <= days_diff <= 7:
                status = "🟢 Eligible for Reminder"
                row_id = self._tree.insert("", "end", values=(m.full_name, m.phone, m.plan_name, expiry, status))
                self._members_cache[row_id] = m

    def _send_whatsapp(self) -> None:
        selected_item = self._tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please select a member from the list to message.", parent=self)
            return
            
        member = self._members_cache[selected_item]
        
        # 1. Format the phone number
        phone = str(member.phone).strip()
        if len(phone) == 10:
            phone = f"91{phone}"
            
        # 2. Draft the professional reminder message
        expiry_str = str(member.expiry_date)
        message = (
            f"Hello {member.full_name},\n\n"
            f"This is a gentle reminder from *The Iron Temple GYM* 🏋️‍♂️.\n"
            f"Your {member.plan_name} timeline points to *{expiry_str}*.\n\n"
            f"Please renew your plan at the front desk soon to continue crushing your fitness goals seamlessly! 💪\n\n"
            f"Thank you!"
        )
        
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
        
        # 3. Open WhatsApp
        webbrowser.open(whatsapp_url)
        
        # 4. MARK AS SENT IN DATABASE (The Gatekeeper)
        try:
            self._service.log_reminder_sent(member.id)
            
            # 5. Refresh the list so the member disappears automatically
            self._load_data()
            
            messagebox.showinfo("Success", f"Reminder logged for {member.full_name}.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to log reminder: {e}", parent=self)