import tkinter as tk
from tkinter import ttk

from ui.base_screen import BaseScreen


class RegistrationScreen(BaseScreen):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.add_top_bar(back_command=self.app.go_back)

        frm = ttk.Frame(self)
        frm.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
        ttk.Label(frm, text="Resident Registration", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(frm, text="User ID").grid(row=1, column=0, sticky="w")
        self.user_entry = ttk.Entry(frm, width=30)
        self.user_entry.grid(row=2, column=0, sticky="w", pady=(0, 8))

        ttk.Label(frm, text="Password").grid(row=3, column=0, sticky="w")
        self.password_entry = ttk.Entry(frm, show="*", width=30)
        self.password_entry.grid(row=4, column=0, sticky="w", pady=(0, 8))

        ttk.Label(frm, text="Confirm Password").grid(row=5, column=0, sticky="w")
        self.confirm_entry = ttk.Entry(frm, show="*", width=30)
        self.confirm_entry.grid(row=6, column=0, sticky="w", pady=(0, 8))

        ttk.Button(frm, text="Continue", command=self._submit).grid(row=7, column=0, sticky="w")

    def _submit(self):
        self.app.save_registration_step1(self.user_entry.get(), self.password_entry.get(), self.confirm_entry.get())

    def refresh_ui(self):
        super().refresh_ui()
