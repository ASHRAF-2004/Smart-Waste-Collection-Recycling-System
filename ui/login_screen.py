import tkinter as tk

from services.validation_service import validate_user_id
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

        self.user_prompt_lbl = tk.Label(form, font=("Segoe UI", 11, "bold"), anchor="w")
        self.user_prompt_lbl.grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.user_entry = tk.Entry(form, width=32, font=("Segoe UI", 12))
        self.user_entry.grid(row=1, column=0, pady=(0, 2), ipady=7)
        self.user_err = tk.Label(form, font=("Segoe UI", 9), anchor="w")
        self.user_err.grid(row=2, column=0, sticky="w", pady=(0, 6))

        self.password_prompt_lbl = tk.Label(form, font=("Segoe UI", 11, "bold"), anchor="w")
        self.password_prompt_lbl.grid(row=3, column=0, sticky="w", pady=(4, 4))
        self.password_entry = tk.Entry(form, show="*", width=32, font=("Segoe UI", 12))
        self.password_entry.grid(row=4, column=0, pady=(0, 2), ipady=7)
        self.pass_err = tk.Label(form, font=("Segoe UI", 9), anchor="w")
        self.pass_err.grid(row=5, column=0, sticky="w")

        self.login_btn = tk.Button(form, command=self._submit, bd=0, width=28, pady=10)
        self.login_btn.grid(row=6, column=0, pady=(12, 8))

        self.request_btn = tk.Button(form, command=lambda: self.app.show_screen("Registration"), bd=0, width=28, pady=10)
        self.request_btn.grid(row=7, column=0, pady=(4, 0))

        self.user_entry.bind("<KeyRelease>", lambda _e: self._on_change())
        self.password_entry.bind("<KeyRelease>", lambda _e: self._on_change())
        self.password_entry.bind("<Return>", lambda _e: self._submit())

        self.widgets.extend([self.content, self.app_name, self.title_lbl, self.subtitle_lbl, form])

    def _on_change(self):
        entered_user_id = self.user_entry.get().strip()
        entered_password = self.password_entry.get()
        user_id_is_valid = False
        try:
            validate_user_id(entered_user_id)
            user_id_is_valid = True
            self.user_err.configure(text="")
        except ValueError as exc:
            self.user_err.configure(text=self.app.translate(str(exc)) if str(exc).startswith("error_") else str(exc))

        if not entered_password:
            self.pass_err.configure(text=self.app.translate("error_password_required"))
            password_is_valid = False
        else:
            self.pass_err.configure(text="")
            password_is_valid = True

        self.style_entry(self.user_entry, error=not user_id_is_valid and bool(entered_user_id))
        self.style_entry(self.password_entry, error=not password_is_valid)
        self.login_btn.configure(state=("normal" if user_id_is_valid and password_is_valid else "disabled"))

    def _submit(self):
        self.app.submit_login(self.user_entry.get(), self.password_entry.get())

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme

        self.content.configure(bg=th["bg"])
        self.app_name.configure(text=self.app.translate("app_name"), bg=th["bg"], fg=th["text"])
        self.title_lbl.configure(text=self.app.translate("welcome_back"), bg=th["bg"], fg=th["text"])
        self.subtitle_lbl.configure(text=self.app.translate("welcome_subtitle"), bg=th["bg"], fg=th["muted"])

        self.user_prompt_lbl.configure(text=self.app.translate("enter_user_id"), bg=th["bg"], fg=th["text"])
        self.password_prompt_lbl.configure(text=self.app.translate("enter_password"), bg=th["bg"], fg=th["text"])

        self.user_err.configure(bg=th["bg"], fg="#D64545")
        self.pass_err.configure(bg=th["bg"], fg="#D64545")

        self.style_entry(self.user_entry)
        self.style_entry(self.password_entry)

        self.login_btn.configure(text=self.app.translate("login"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])
        self.request_btn.configure(text=self.app.translate("resident_requester"), bg=th["secondary_bg"], fg=th["secondary_fg"], activebackground=th["secondary_bg"])

        self.user_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.login_btn.configure(state="disabled")
        self.user_err.configure(text="")
        self.pass_err.configure(text="")
