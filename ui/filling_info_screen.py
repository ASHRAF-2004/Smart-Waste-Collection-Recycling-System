import tkinter as tk
from tkinter import ttk

from ui.base_screen import BaseScreen
from ui.common_widgets import ScrollableFrame


class FillingInfoScreen(BaseScreen):
    def __init__(self, master, app, form_data=None, **kwargs):
        super().__init__(master, app, **kwargs)
        self.form_data = form_data or {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.add_top_bar(back_command=self._go_back)

        self.scrollable = ScrollableFrame(self)
        self.scrollable.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        body = self.scrollable.inner

        self.entries = {}
        fields = [
            ("full_name", "Full Name"),
            ("id_no", "Identification Card No. / Passport No."),
            ("telephone", "Telephone No."),
            ("email", "Email"),
            ("zone", "Residential Zone"),
            ("address", "Address"),
        ]
        self.zone_combo = None
        for idx, (key, label) in enumerate(fields):
            ttk.Label(body, text=label).grid(row=idx * 2, column=0, sticky="w", pady=(6, 2))
            if key == "zone":
                self.zone_combo = ttk.Combobox(body, values=[z["name"] for z in self.app.db.list_zones()], state="readonly", width=30)
                self.zone_combo.grid(row=idx * 2 + 1, column=0, sticky="w")
                self.entries[key] = self.zone_combo
            else:
                entry = ttk.Entry(body, width=40)
                entry.grid(row=idx * 2 + 1, column=0, sticky="w")
                self.entries[key] = entry
            if self.form_data.get(key):
                self.entries[key].insert(0, self.form_data[key])

        ttk.Button(body, text="Save Profile", command=self._submit).grid(row=20, column=0, sticky="w", pady=12)

    def _go_back(self):
        self.app.show_screen("Registration")

    def _submit(self):
        data = {k: w.get().strip() for k, w in self.entries.items()}
        self.app.save_registration_step2(data)

    def refresh_ui(self):
        super().refresh_ui()
