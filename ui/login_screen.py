import tkinter as tk

from ui.base_screen import BaseScreen


class LoginScreen(BaseScreen):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.add_top_bar()

        self.content = tk.Frame(self)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)

        self.app_name = tk.Label(self.content, font=("Segoe UI", 14, "bold"))
        self.app_name.grid(row=0, column=0, pady=(20, 6))

        self.title_lbl = tk.Label(self.content, font=("Segoe UI", 28, "bold"))
        self.title_lbl.grid(row=1, column=0, pady=(10, 4))

        self.subtitle_lbl = tk.Label(self.content, font=("Segoe UI", 13))
        self.subtitle_lbl.grid(row=2, column=0, pady=(0, 24))

        form = tk.Frame(self.content, padx=24, pady=20)
        form.grid(row=3, column=0)

        self.user_entry = tk.Entry(form, width=32, font=("Segoe UI", 12))
        self.user_entry.grid(row=0, column=0, pady=8, ipady=7)

        self.password_entry = tk.Entry(form, show="*", width=32, font=("Segoe UI", 12))
        self.password_entry.grid(row=1, column=0, pady=8, ipady=7)

        self.login_btn = tk.Button(form, command=lambda: self.app.submit_login(self.user_entry.get(), self.password_entry.get()), bd=0, width=28, pady=10)
        self.login_btn.grid(row=2, column=0, pady=(12, 8))

        self.request_btn = tk.Button(form, command=self.app.show_registration, bd=0, width=28, pady=10)
        self.request_btn.grid(row=3, column=0, pady=(4, 0))

        self.widgets.extend([self.content, self.app_name, self.title_lbl, self.subtitle_lbl, form])

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme

        self.content.configure(bg=th["bg"])
        self.app_name.configure(text=self.app.translate("app_name"), bg=th["bg"], fg=th["text"])
        self.title_lbl.configure(text=self.app.translate("welcome_back"), bg=th["bg"], fg=th["text"])
        self.subtitle_lbl.configure(text=self.app.translate("welcome_subtitle"), bg=th["bg"], fg=th["muted"])

        self.user_entry.delete(0, tk.END)
        self.user_entry.insert(0, self.app.translate("user_id"))
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, self.app.translate("password"))
        self.password_entry.configure(show="")

        def clear_user(_):
            if self.user_entry.get() == self.app.translate("user_id"):
                self.user_entry.delete(0, tk.END)

        def clear_pass(_):
            if self.password_entry.get() == self.app.translate("password"):
                self.password_entry.delete(0, tk.END)
                self.password_entry.configure(show="*")

        self.user_entry.bind("<FocusIn>", clear_user)
        self.password_entry.bind("<FocusIn>", clear_pass)

        self.style_entry(self.user_entry)
        self.style_entry(self.password_entry)

        self.login_btn.configure(text=self.app.translate("login"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])
        self.request_btn.configure(text=self.app.translate("resident_requester"), bg=th["secondary_bg"], fg=th["secondary_fg"], activebackground=th["secondary_bg"])
