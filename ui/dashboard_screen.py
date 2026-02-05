import tkinter as tk
from tkinter import ttk

from ui.base_screen import BaseScreen


class DashboardScreen(BaseScreen):
    def __init__(self, master, app, user_id: str, **kwargs):
        super().__init__(master, app, **kwargs)
        self.user_id = user_id
        self.user = self.app.db.get_user(user_id)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.add_top_bar(back_command=self.app.go_back)

        wrap = tk.Frame(self)
        wrap.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.wrap = wrap

        self.title_lbl = tk.Label(wrap, font=("Segoe UI", 26, "bold"))
        self.title_lbl.grid(row=0, column=0, sticky="w", pady=(5, 10))
        self.sub_lbl = tk.Label(wrap, font=("Segoe UI", 12))
        self.sub_lbl.grid(row=1, column=0, sticky="w", pady=6)

        self.unread_lbl = tk.Label(wrap, font=("Segoe UI", 10, "bold"))
        self.unread_lbl.grid(row=2, column=0, sticky="w", pady=4)
        self.mark_read_btn = tk.Button(wrap, bd=0, command=self._mark_read)
        self.mark_read_btn.grid(row=2, column=1, sticky="w", padx=8)

        self.leader_title = tk.Label(wrap, font=("Segoe UI", 16, "bold"))
        self.leader_title.grid(row=3, column=0, sticky="w", pady=(12, 6))
        self.leader_tree = ttk.Treeview(wrap, columns=("zone", "name", "points"), show="headings", height=8)
        for c, text in (("zone", "Zone"), ("name", "Name"), ("points", "Points")):
            self.leader_tree.heading(c, text=text)
        self.leader_tree.grid(row=4, column=0, columnspan=2, sticky="ew")

        self.logout_btn = tk.Button(wrap, bd=0, width=20, pady=10, command=lambda: self.app.show_screen("Login"))
        self.logout_btn.grid(row=5, column=0, pady=16, sticky="w")

        self._refresh_data()

    def _refresh_data(self):
        self.unread = self.app.db.unread_count(self.user_id)
        rows = self.app.db.get_zone_leaderboard()
        for i in self.leader_tree.get_children():
            self.leader_tree.delete(i)
        for r in rows[:20]:
            self.leader_tree.insert("", "end", values=(r["zone"], r["full_name"], r["total_points"]))

    def _mark_read(self):
        self.app.db.mark_notifications_read(self.user_id)
        self._refresh_data()
        self.refresh_ui()

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.wrap.configure(bg=th["bg"])
        self.title_lbl.configure(text=f"{self.app.translate('dashboard')} ({self.user_id})", bg=th["bg"], fg=th["text"])
        role = self.user["role"] if self.user else "Unknown"
        self.sub_lbl.configure(text=f"Role: {role}", bg=th["bg"], fg=th["muted"])
        self.unread_lbl.configure(text=f"{self.app.translate('unread')}: {self.unread}", bg=th["bg"], fg=th["text"])
        self.mark_read_btn.configure(text=self.app.translate("mark_read"), bg=th["secondary_bg"], fg=th["secondary_fg"], activebackground=th["secondary_bg"])
        self.leader_title.configure(text=self.app.translate("leaderboard"), bg=th["bg"], fg=th["text"])
        self.logout_btn.configure(text=self.app.translate("logout"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])
