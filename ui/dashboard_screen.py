import tkinter as tk

from ui.base_screen import BaseScreen


class DashboardScreen(BaseScreen):
    def __init__(self, master, app, user_id: str, **kwargs):
        super().__init__(master, app, **kwargs)
        self.user_id = user_id
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.add_top_bar(back_command=lambda: self.app.show_screen("Login"))

        wrap = tk.Frame(self)
        wrap.grid(row=1, column=0)
        self.wrap = wrap

        self.title_lbl = tk.Label(wrap, font=("Segoe UI", 26, "bold"))
        self.title_lbl.grid(row=0, column=0, pady=(20, 10))
        self.sub_lbl = tk.Label(wrap, font=("Segoe UI", 12))
        self.sub_lbl.grid(row=1, column=0, pady=8)
        self.logout_btn = tk.Button(wrap, bd=0, width=20, pady=10, command=lambda: self.app.show_screen("Login"))
        self.logout_btn.grid(row=2, column=0, pady=16)

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.wrap.configure(bg=th["bg"])
        self.title_lbl.configure(text=f"{self.app.translate('dashboard')} ({self.user_id})", bg=th["bg"], fg=th["text"])
        self.sub_lbl.configure(text=self.app.translate("dashboard_sub"), bg=th["bg"], fg=th["muted"])
        self.logout_btn.configure(text=self.app.translate("logout"), bg=th["secondary_bg"], fg=th["secondary_fg"], activebackground=th["secondary_bg"])
