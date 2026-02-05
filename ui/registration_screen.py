import tkinter as tk

from services.validation_service import validate_password, validate_user_id
from ui.base_screen import BaseScreen


class RegistrationScreen(BaseScreen):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.add_top_bar(back_command=lambda: self.app.show_screen("Login"))

        self.wrap = tk.Frame(self, padx=40, pady=20)
        self.wrap.grid(row=1, column=0, sticky="nsew")
        self.wrap.grid_columnconfigure(0, weight=1)

        self.title_lbl = tk.Label(self.wrap, font=("Segoe UI", 25, "bold"), anchor="w")
        self.title_lbl.grid(row=0, column=0, sticky="w", pady=(20, 20))

        self.user_lbl = tk.Label(self.wrap, font=("Segoe UI", 11))
        self.user_lbl.grid(row=1, column=0, sticky="w")
        self.user_entry = tk.Entry(self.wrap, font=("Segoe UI", 12), width=34)
        self.user_entry.grid(row=2, column=0, sticky="w", ipady=7, pady=(5, 2))
        self.user_err = tk.Label(self.wrap, font=("Segoe UI", 9))
        self.user_err.grid(row=3, column=0, sticky="w")

        self.password_lbl = tk.Label(self.wrap, font=("Segoe UI", 11))
        self.password_lbl.grid(row=4, column=0, sticky="w")
        self.password_entry = tk.Entry(self.wrap, font=("Segoe UI", 12), show="*", width=34)
        self.password_entry.grid(row=5, column=0, sticky="w", ipady=7, pady=(5, 2))
        self.password_hint = tk.Label(self.wrap, text="Min 8 chars, upper/lower/digit, no spaces.", font=("Segoe UI", 9))
        self.password_hint.grid(row=6, column=0, sticky="w")
        self.password_err = tk.Label(self.wrap, font=("Segoe UI", 9))
        self.password_err.grid(row=7, column=0, sticky="w")

        self.confirm_lbl = tk.Label(self.wrap, font=("Segoe UI", 11))
        self.confirm_lbl.grid(row=8, column=0, sticky="w")
        self.confirm_entry = tk.Entry(self.wrap, font=("Segoe UI", 12), show="*", width=34)
        self.confirm_entry.grid(row=9, column=0, sticky="w", ipady=7, pady=(5, 2))
        self.confirm_err = tk.Label(self.wrap, font=("Segoe UI", 9))
        self.confirm_err.grid(row=10, column=0, sticky="w")

        self.continue_btn = tk.Button(
            self.wrap,
            bd=0,
            width=24,
            pady=10,
            command=self._submit,
        )
        self.continue_btn.grid(row=11, column=0, sticky="w", pady=20)

        for widget in (self.user_entry, self.password_entry, self.confirm_entry):
            widget.bind("<KeyRelease>", lambda _e: self._on_change())
        self.confirm_entry.bind("<Return>", lambda _e: self._submit())

    def _on_change(self):
        uid = self.user_entry.get().strip()
        pwd = self.password_entry.get()
        cpwd = self.confirm_entry.get()

        uid_ok = False
        try:
            validate_user_id(uid)
            uid_ok = True
            self.user_err.configure(text="")
        except ValueError as exc:
            self.user_err.configure(text=str(exc))

        pwd_ok = False
        try:
            validate_password(pwd, uid)
            pwd_ok = True
            self.password_err.configure(text="")
        except ValueError as exc:
            self.password_err.configure(text=str(exc) if pwd else "Password is required.")

        confirm_ok = bool(cpwd and cpwd == pwd)
        self.confirm_err.configure(text="" if confirm_ok or not cpwd else "Confirm Password must match Password.")

        self.style_entry(self.user_entry, error=not uid_ok and bool(uid))
        self.style_entry(self.password_entry, error=not pwd_ok and bool(pwd))
        self.style_entry(self.confirm_entry, error=not confirm_ok and bool(cpwd))
        self.continue_btn.configure(state=("normal" if uid_ok and pwd_ok and confirm_ok else "disabled"))

    def _submit(self):
        self.app.save_registration_step1(self.user_entry.get(), self.password_entry.get(), self.confirm_entry.get())

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.wrap.configure(bg=th["bg"])
        self.title_lbl.configure(text=self.app.translate("user_registration"), bg=th["bg"], fg=th["text"])
        self.user_lbl.configure(text=self.app.translate("new_user_id"), bg=th["bg"], fg=th["text"])
        self.password_lbl.configure(text=self.app.translate("password"), bg=th["bg"], fg=th["text"])
        self.confirm_lbl.configure(text="Confirm Password", bg=th["bg"], fg=th["text"])

        for lbl in (self.user_err, self.password_err, self.confirm_err):
            lbl.configure(bg=th["bg"], fg="#D64545")
        self.password_hint.configure(bg=th["bg"], fg=th["muted"])

        self.style_entry(self.user_entry)
        self.style_entry(self.password_entry)
        self.style_entry(self.confirm_entry)
        self.continue_btn.configure(text=self.app.translate("continue"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])

        self.user_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.confirm_entry.delete(0, tk.END)
        self.continue_btn.configure(state="disabled")
        self.user_err.configure(text="")
        self.password_err.configure(text="")
        self.confirm_err.configure(text="")
