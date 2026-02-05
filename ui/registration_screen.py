import tkinter as tk

from ui.base_screen import BaseScreen


class RegistrationScreen(BaseScreen):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.add_top_bar()

        self.wrap = tk.Frame(self, padx=40, pady=20)
        self.wrap.grid(row=1, column=0, sticky="nsew")
        self.wrap.grid_columnconfigure(0, weight=1)

        self.title_lbl = tk.Label(self.wrap, font=("Segoe UI", 25, "bold"), anchor="w")
        self.title_lbl.grid(row=0, column=0, sticky="w", pady=(20, 20))

        self.user_lbl = tk.Label(self.wrap, font=("Segoe UI", 11))
        self.user_lbl.grid(row=1, column=0, sticky="w")
        self.user_entry = tk.Entry(self.wrap, font=("Segoe UI", 12), width=34)
        self.user_entry.grid(row=2, column=0, sticky="w", ipady=7, pady=(5, 10))

        self.password_lbl = tk.Label(self.wrap, font=("Segoe UI", 11))
        self.password_lbl.grid(row=3, column=0, sticky="w")
        self.password_entry = tk.Entry(self.wrap, font=("Segoe UI", 12), show="*", width=34)
        self.password_entry.grid(row=4, column=0, sticky="w", ipady=7, pady=(5, 10))

        self.continue_btn = tk.Button(
            self.wrap,
            bd=0,
            width=24,
            pady=10,
            command=lambda: self.app.save_registration_step1(self.user_entry.get(), self.password_entry.get()),
        )
        self.continue_btn.grid(row=5, column=0, sticky="w", pady=20)

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.wrap.configure(bg=th["bg"])
        self.title_lbl.configure(text=self.app.translate("user_registration"), bg=th["bg"], fg=th["text"])
        self.user_lbl.configure(text=self.app.translate("new_user_id"), bg=th["bg"], fg=th["text"])
        self.password_lbl.configure(text=self.app.translate("password"), bg=th["bg"], fg=th["text"])
        self.style_entry(self.user_entry)
        self.style_entry(self.password_entry)
        self.continue_btn.configure(text=self.app.translate("continue"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])
