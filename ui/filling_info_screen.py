import tkinter as tk
from tkinter import ttk

from services.validation_service import collect_filling_info_errors
from ui.base_screen import BaseScreen


class FillingInfoScreen(BaseScreen):
    ZONES = ["", "Zone A", "Zone B", "Zone C", "Zone D"]

    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.add_top_bar(back_command=self.app.go_back)

        self.form = tk.Frame(self, padx=40, pady=20)
        self.form.grid(row=1, column=0)

        self.title_lbl = tk.Label(self.form, font=("Segoe UI", 24, "bold"))
        self.title_lbl.grid(row=0, column=0, columnspan=2, pady=(8, 20))

        self.entries = {}
        self.error_labels = {}
        fields = [
            ("full_name", "passport_hint"),
            ("id_no", "id_hint"),
            ("telephone", "telephone_hint"),
            ("email", "email_hint"),
            ("address", "email_hint"),
        ]

        for idx, (key, hint_key) in enumerate(fields, start=1):
            lbl = tk.Label(self.form, font=("Segoe UI", 11, "bold"), anchor="w")
            lbl.grid(row=idx * 3 - 2, column=0, sticky="w")
            hint = tk.Label(self.form, font=("Segoe UI", 9), anchor="w")
            hint.grid(row=idx * 3 - 2, column=1, sticky="w", padx=(16, 0))
            ent = tk.Entry(self.form, width=40, font=("Segoe UI", 11))
            ent.grid(row=idx * 3 - 1, column=0, columnspan=2, sticky="ew", ipady=6, pady=(5, 2))
            err = tk.Label(self.form, font=("Segoe UI", 9), anchor="w")
            err.grid(row=idx * 3, column=0, columnspan=2, sticky="w", pady=(0, 8))
            ent.bind("<KeyRelease>", lambda _e: self._on_change())
            self.entries[key] = (lbl, hint, ent, hint_key)
            self.error_labels[key] = err

        base_row = len(fields) * 3 + 1
        self.zone_lbl = tk.Label(self.form, font=("Segoe UI", 11, "bold"))
        self.zone_lbl.grid(row=base_row, column=0, sticky="w")
        self.zone_hint = tk.Label(self.form, font=("Segoe UI", 9))
        self.zone_hint.grid(row=base_row, column=1, sticky="w", padx=(16, 0))

        self.zone_combo = ttk.Combobox(self.form, values=self.ZONES, state="readonly", width=38)
        self.zone_combo.grid(row=base_row + 1, column=0, columnspan=2, sticky="ew", pady=(6, 2))
        self.zone_combo.current(0)
        self.zone_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_change())

        self.zone_err = tk.Label(self.form, font=("Segoe UI", 9), anchor="w")
        self.zone_err.grid(row=base_row + 2, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.role_lbl = tk.Label(self.form, font=("Segoe UI", 11, "bold"))
        self.role_lbl.grid(row=base_row + 3, column=0, sticky="w")
        self.role_combo = ttk.Combobox(self.form, values=["Resident", "WasteCollector"], state="readonly", width=38)
        self.role_combo.grid(row=base_row + 4, column=0, columnspan=2, sticky="ew", pady=(6, 2))
        self.role_combo.current(0)
        self.role_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_change())
        self.role_err = tk.Label(self.form, font=("Segoe UI", 9), anchor="w")
        self.role_err.grid(row=base_row + 5, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.create_btn = tk.Button(self.form, bd=0, width=26, pady=10, command=self._create_account)
        self.create_btn.grid(row=base_row + 6, column=0, columnspan=2, pady=8)

    def _payload(self):
        return {
            "full_name": self.entries["full_name"][2].get(),
            "id_no": self.entries["id_no"][2].get(),
            "telephone": self.entries["telephone"][2].get(),
            "email": self.entries["email"][2].get(),
            "address": self.entries["address"][2].get(),
            "zone": self.zone_combo.get(),
            "role": self.role_combo.get(),
        }

    def _on_change(self):
        errors = collect_filling_info_errors(self._payload())
        for key, (_, _, ent, _) in self.entries.items():
            if key == "address":
                self.error_labels[key].configure(text="")
                self.style_entry(ent, error=False)
                continue
            self.error_labels[key].configure(text=errors.get(key, ""))
            self.style_entry(ent, error=key in errors)

        self.zone_err.configure(text=errors.get("zone", ""))
        self.role_err.configure(text=errors.get("role", ""))
        self.create_btn.configure(state=("normal" if not errors else "disabled"))

    def _create_account(self):
        self.app.save_registration_step2(self._payload())

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.form.configure(bg=th["bg"])
        self.title_lbl.configure(text=self.app.translate("create_account_title"), bg=th["bg"], fg=th["text"])

        for key, (lbl, hint, ent, hint_key) in self.entries.items():
            lbl_key = "address" if key == "address" else key
            lbl.configure(text=self.app.translate(lbl_key), bg=th["bg"], fg=th["text"])
            hint.configure(text=self.app.translate(hint_key), bg=th["bg"], fg=th["muted"])
            self.error_labels[key].configure(bg=th["bg"], fg="#D64545")
            self.style_entry(ent)

        self.zone_lbl.configure(text=self.app.translate("zone"), bg=th["bg"], fg=th["text"])
        self.zone_hint.configure(text=self.app.translate("zone_hint"), bg=th["bg"], fg=th["muted"])
        self.role_lbl.configure(text=self.app.translate("role"), bg=th["bg"], fg=th["text"])
        self.zone_err.configure(bg=th["bg"], fg="#D64545")
        self.role_err.configure(bg=th["bg"], fg="#D64545")
        self.create_btn.configure(text=self.app.translate("create_account"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])

        for _, (_, _, ent, _) in self.entries.items():
            ent.delete(0, tk.END)
        self.zone_combo.current(0)
        self.role_combo.current(0)
        self.create_btn.configure(state="disabled")
