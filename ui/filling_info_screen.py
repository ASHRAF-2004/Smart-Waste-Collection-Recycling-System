import tkinter as tk
from tkinter import ttk

from ui.base_screen import BaseScreen


class FillingInfoScreen(BaseScreen):
    ZONES = ["Zone A", "Zone B", "Zone C", "Zone D"]

    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.add_top_bar()

        self.form = tk.Frame(self, padx=40, pady=20)
        self.form.grid(row=1, column=0)

        self.title_lbl = tk.Label(self.form, font=("Segoe UI", 24, "bold"))
        self.title_lbl.grid(row=0, column=0, columnspan=2, pady=(8, 20))

        self.entries = {}
        fields = [
            ("full_name", "passport_hint"),
            ("id_no", "id_hint"),
            ("telephone", "telephone_hint"),
            ("email", "email_hint"),
        ]

        for idx, (key, hint_key) in enumerate(fields, start=1):
            lbl = tk.Label(self.form, font=("Segoe UI", 11, "bold"), anchor="w")
            lbl.grid(row=idx * 2 - 1, column=0, sticky="w")
            hint = tk.Label(self.form, font=("Segoe UI", 9), anchor="w")
            hint.grid(row=idx * 2 - 1, column=1, sticky="w", padx=(16, 0))
            ent = tk.Entry(self.form, width=40, font=("Segoe UI", 11))
            ent.grid(row=idx * 2, column=0, columnspan=2, sticky="ew", ipady=6, pady=(5, 12))
            self.entries[key] = (lbl, hint, ent, hint_key)

        zone_row = len(fields) * 2 + 1
        self.zone_lbl = tk.Label(self.form, font=("Segoe UI", 11, "bold"))
        self.zone_lbl.grid(row=zone_row, column=0, sticky="w")
        self.zone_hint = tk.Label(self.form, font=("Segoe UI", 9))
        self.zone_hint.grid(row=zone_row, column=1, sticky="w", padx=(16, 0))

        self.zone_combo = ttk.Combobox(self.form, values=self.ZONES, state="readonly", width=38)
        self.zone_combo.grid(row=zone_row + 1, column=0, columnspan=2, sticky="ew", pady=(6, 14))
        self.zone_combo.current(0)

        self.create_btn = tk.Button(self.form, bd=0, width=26, pady=10, command=self._create_account)
        self.create_btn.grid(row=zone_row + 2, column=0, columnspan=2, pady=8)

    def _create_account(self):
        self.app.save_registration_step2(
            {
                "full_name": self.entries["full_name"][2].get(),
                "id_no": self.entries["id_no"][2].get(),
                "telephone": self.entries["telephone"][2].get(),
                "email": self.entries["email"][2].get(),
                "zone": self.zone_combo.get(),
            }
        )

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.form.configure(bg=th["bg"])
        self.title_lbl.configure(text=self.app.translate("create_account_title"), bg=th["bg"], fg=th["text"])

        for key, (lbl, hint, ent, hint_key) in self.entries.items():
            lbl.configure(text=self.app.translate(key), bg=th["bg"], fg=th["text"])
            hint.configure(text=self.app.translate(hint_key), bg=th["bg"], fg=th["muted"])
            self.style_entry(ent)

        self.zone_lbl.configure(text=self.app.translate("zone"), bg=th["bg"], fg=th["text"])
        self.zone_hint.configure(text=self.app.translate("zone_hint"), bg=th["bg"], fg=th["muted"])
        self.create_btn.configure(text=self.app.translate("create_account"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])
