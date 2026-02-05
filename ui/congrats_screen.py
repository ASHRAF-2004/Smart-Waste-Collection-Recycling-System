import tkinter as tk

from ui.base_screen import BaseScreen


class CongratsScreen(BaseScreen):
    def __init__(self, master, app, user_id: str, **kwargs):
        super().__init__(master, app, **kwargs)
        self.user_id = user_id
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.add_top_bar()

        self.wrap = tk.Frame(self)
        self.wrap.grid(row=1, column=0)

        self.title_lbl = tk.Label(self.wrap, font=("Segoe UI", 28, "bold"))
        self.title_lbl.grid(row=0, column=0, pady=(20, 8))
        self.rose_lbl = tk.Label(self.wrap, text="🌹", font=("Segoe UI Emoji", 40))
        self.rose_lbl.grid(row=1, column=0, pady=8)
        self.welcome_lbl = tk.Label(self.wrap, font=("Segoe UI", 17, "bold"))
        self.welcome_lbl.grid(row=2, column=0, pady=(8, 3))
        self.msg_lbl = tk.Label(self.wrap, font=("Segoe UI", 12))
        self.msg_lbl.grid(row=3, column=0, pady=(3, 20))
        self.login_now_btn = tk.Button(self.wrap, bd=0, width=22, pady=10, command=self.app.show_login)
        self.login_now_btn.grid(row=4, column=0)

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.wrap.configure(bg=th["bg"])
        self.title_lbl.configure(text=self.app.translate("account_created"), bg=th["bg"], fg=th["text"])
        self.rose_lbl.configure(bg=th["bg"], fg=th["text"])
        self.welcome_lbl.configure(text=f"{self.app.translate('welcome_user')}\n({self.user_id})", bg=th["bg"], fg=th["text"])
        self.msg_lbl.configure(text=self.app.translate("success_msg"), bg=th["bg"], fg=th["muted"])
        self.login_now_btn.configure(text=self.app.translate("login_now"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])
