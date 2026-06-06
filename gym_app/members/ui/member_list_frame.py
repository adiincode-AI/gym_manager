import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from gym_app.members.service.member_service import MemberService
from gym_app.members.ui.edit_member_dialog import EditMemberDialog
from gym_app.ui.components import (
    Card, COLOR_BG, COLOR_CARD, COLOR_TEXT, COLOR_MUTED, FONT_FAMILY, 
    PAD_LG, PAD_MD, PAD_SM
)

class MemberListFrame(tk.Frame):
    def __init__(self, parent: tk.Widget, member_service: MemberService, on_back: callable) -> None:
        super().__init__(parent, bg=COLOR_BG)
        self._service = member_service
        self._on_back = on_back
        self._members_cache = {}  
        
        self._build_style()
        self._build_layout()
        self._apply_filters()  # Replaces the old direct _load_data call

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
        # ── Header ──
        header = tk.Frame(self, bg=COLOR_BG)
        header.pack(fill="x", padx=PAD_LG, pady=(PAD_LG, PAD_SM))
        
        tk.Label(
            header, text="Member Database", 
            font=(FONT_FAMILY, 20, "bold"), bg=COLOR_BG, fg=COLOR_TEXT
        ).pack(side="left")

        tk.Button(
            header, text="← Back to Dashboard", command=self._on_back, 
            font=(FONT_FAMILY, 10, "bold"), bg="#9CA3AF", fg="white", 
            relief="flat", padx=15, pady=5, cursor="hand2"
        ).pack(side="right", padx=(10, 0))

        tk.Button(
            header, text="✏️ Edit Selected Member", command=self._open_edit_modal, 
            font=(FONT_FAMILY, 10, "bold"), bg="#1E40AF", fg="white", 
            relief="flat", padx=15, pady=5, cursor="hand2"
        ).pack(side="right")

        # ── NEW: Unified Search & Filter Bar ──
        search_section = tk.Frame(self, bg=COLOR_BG)
        search_section.pack(fill="x", padx=PAD_LG, pady=(0, PAD_MD))
        
        search_card = Card(search_section)
        search_card.pack(fill="x")
        
        inner_bar = tk.Frame(search_card, bg="white")
        inner_bar.pack(fill="x", padx=12, pady=8)

        # 1. Text Search Input
        self._search_var = tk.StringVar()
        self._search_entry = tk.Entry(
            inner_bar, textvariable=self._search_var, 
            font=(FONT_FAMILY, 11), bg="white", fg=COLOR_MUTED, relief="flat", bd=0
        )
        self._search_entry.insert(0, "🔍 Search by Name, Member Code, or Phone Number...")
        
        self._search_entry.bind("<FocusIn>", lambda e: (self._search_entry.delete(0, "end"), self._search_entry.config(fg=COLOR_TEXT)) if "🔍" in self._search_entry.get() else None)
        self._search_entry.bind("<FocusOut>", lambda e: (self._search_entry.insert(0, "🔍 Search by Name, Member Code, or Phone Number..."), self._search_entry.config(fg=COLOR_MUTED)) if not self._search_var.get().strip() else None)
        self._search_entry.pack(side="left", fill="x", expand=True)

        # 2. Status Filter Dropdown
        self._filter_var = tk.StringVar(value="All Members")
        filter_menu = tk.OptionMenu(
            inner_bar, self._filter_var, 
            "All Members", "Active Only", "Expired Only",
            command=self._apply_filters  # Triggers filter whenever dropdown changes
        )
        filter_menu.config(
            font=(FONT_FAMILY, 9, "bold"), bg="#F3F4F6", fg=COLOR_TEXT, 
            relief="flat", bd=0, highlightthickness=0, indicatoron=0, padx=10
        )
        filter_menu.pack(side="right", padx=(10, 0))

        # ── Data Grid Card ──
        card = Card(self)
        card.pack(padx=PAD_LG, pady=(0, PAD_LG), fill="both", expand=True)

        columns = ("code", "name", "phone", "plan", "joined", "expiry", "status")
        self._tree = ttk.Treeview(card, columns=columns, show="headings", style="Treeview")
        
        headers = {
            "code": ("ID CODE", 90), "name": ("FULL NAME", 180), 
            "phone": ("PHONE", 110), "plan": ("PLAN TAKEN", 120), 
            "joined": ("JOIN DATE", 100), "expiry": ("EXPIRY DATE", 100),
            "status": ("STATUS", 90) # Added visual status column!
        }
        
        for col, (title, width) in headers.items():
            self._tree.heading(col, text=title, anchor="w")
            self._tree.column(col, width=width, anchor="w")

        scrollbar = ttk.Scrollbar(card, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        
        self._tree.pack(side="left", fill="both", expand=True, padx=(PAD_MD, 0), pady=PAD_MD)
        scrollbar.pack(side="right", fill="y", padx=(0, PAD_MD), pady=PAD_MD)

        self._tree.bind("<Double-1>", lambda e: self._open_edit_modal())

        # Attach real-time search hook last
        self._search_var.trace_add("write", self._apply_filters)

    def _apply_filters(self, *args) -> None:
        """Master logic hub combining the text search and dropdown status filter."""
        search_query = self._search_var.get().strip()
        status_filter = self._filter_var.get()
        
        # 1. Fetch base list based on text search
        if not search_query or "🔍" in search_query or len(search_query) < 2:
            base_list = self._service.get_all_members()
        else:
            base_list = self._service.search_active_members(search_query)

        # 2. Filter the resulting base list by active/expired status
        today = date.today()
        final_list = []
        
        for m in base_list:
            is_active = m.expiry_date >= today
            
            if status_filter == "Active Only" and not is_active:
                continue
            if status_filter == "Expired Only" and is_active:
                continue
                
            final_list.append(m)

        # 3. Load the filtered data into the UI
        self._load_data(members_list=final_list)

    def _load_data(self, members_list: list) -> None:
        """Injects a specific list of members into the treeview."""
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._members_cache.clear()
            
        today = date.today()
        
        try:
            for m in members_list:
                status_text = "🟢 Active" if m.expiry_date >= today else "🔴 Expired"
                
                row_id = self._tree.insert("", "end", values=(
                    m.member_code, m.full_name, m.phone, 
                    m.plan_name, m.join_date, m.expiry_date, status_text
                ))
                self._members_cache[row_id] = m
        except Exception as e:
            messagebox.showerror("Error", f"Error loading database view: {e}")

    def _open_edit_modal(self) -> None:
        selected_item = self._tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please click on a member row to edit.")
            return

        member_obj = self._members_cache.get(selected_item)
        if member_obj:
            EditMemberDialog(
                parent=self.winfo_toplevel(),
                member=member_obj,
                service=self._service,
                on_success=lambda: self._apply_filters() # Re-apply current filters upon save
            )