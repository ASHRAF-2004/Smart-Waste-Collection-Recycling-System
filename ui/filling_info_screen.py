import tkinter as tk
from tkinter import ttk

from services.validation_service import collect_filling_info_errors
from ui.base_screen import BaseScreen


class FillingInfoScreen(BaseScreen):

    def __init__(self, master, app, **kwargs):
        super().__init__(master, app, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.add_top_bar(back_command=self.app.go_back)

        # Scrollable container so the form remains usable on smaller screens.
        self.container = tk.Frame(self)
        self.container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(4, 12))
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.container, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.v_scroll = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll = ttk.Scrollbar(self.container, orient="horizontal", command=self.canvas.xview)
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        self.form = tk.Frame(self.canvas, padx=40, pady=20)
        self.form_window = self.canvas.create_window((0, 0), window=self.form, anchor="nw")

        self.form.bind("<Configure>", self._sync_scroll_region)
        self.canvas.bind("<Configure>", self._resize_scroll_content)

        self.title_lbl = tk.Label(self.form, font=("Segoe UI", 24, "bold"))
        self.title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(8, 20))

        self.entries = {}
        self.error_labels = {}
        fields = [
            ("full_name", "passport_hint", "enter_full_name"),
            ("id_no", "id_hint", "enter_id_no"),
            ("telephone", "telephone_hint", "enter_telephone"),
            ("email", "email_hint", "enter_email"),
            ("address", "email_hint", "enter_address"),
        ]

        for idx, (field_key, hint_key, label_key) in enumerate(fields, start=1):
            label_widget = tk.Label(self.form, font=("Segoe UI", 11, "bold"), anchor="w")
            label_widget.grid(row=idx * 3 - 2, column=0, sticky="w")
            hint_widget = tk.Label(self.form, font=("Segoe UI", 9), anchor="w")
            hint_widget.grid(row=idx * 3 - 2, column=1, sticky="w", padx=(16, 0))
            entry_widget = tk.Entry(self.form, width=42, font=("Segoe UI", 11))
            entry_widget.grid(row=idx * 3 - 1, column=0, columnspan=2, sticky="ew", ipady=6, pady=(5, 2))
            error_widget = tk.Label(self.form, font=("Segoe UI", 9), anchor="w")
            error_widget.grid(row=idx * 3, column=0, columnspan=2, sticky="w", pady=(0, 8))
            entry_widget.bind("<KeyRelease>", lambda _e: self._on_change())
            self.entries[field_key] = (label_widget, hint_widget, entry_widget, hint_key, label_key)
            self.error_labels[field_key] = error_widget

        base_row = len(fields) * 3 + 1
        self.zone_lbl = tk.Label(self.form, font=("Segoe UI", 11, "bold"))
        self.zone_lbl.grid(row=base_row, column=0, sticky="w")
        self.zone_hint = tk.Label(self.form, font=("Segoe UI", 9))
        self.zone_hint.grid(row=base_row, column=1, sticky="w", padx=(16, 0))

        zones = ["", *[z["name"] for z in self.app.db.list_zones()]]
        self.zone_combo = ttk.Combobox(self.form, values=zones, state="readonly", width=40)
        self.zone_combo.grid(row=base_row + 1, column=0, columnspan=2, sticky="ew", pady=(6, 2))
        self.zone_combo.current(0)
        self.zone_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_change())

        self.zone_err = tk.Label(self.form, font=("Segoe UI", 9), anchor="w")
        self.zone_err.grid(row=base_row + 2, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.continue_btn = tk.Button(self.form, bd=0, width=26, pady=10, command=self._continue_registration)
        self.continue_btn.grid(row=base_row + 6, column=0, columnspan=2, pady=10)

        self._configure_tab_order()

    def _configure_tab_order(self):
        tab_order = [
            self.entries["full_name"][2],
            self.entries["id_no"][2],
            self.entries["telephone"][2],
            self.entries["email"][2],
            self.entries["address"][2],
            self.zone_combo,
            self.continue_btn,
        ]
        for idx, widget in enumerate(tab_order[:-1]):
            next_widget = tab_order[idx + 1]
            widget.bind("<Tab>", lambda _e, target=next_widget: (target.focus_set(), "break")[1])

    def _sync_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_scroll_content(self, event):
        self.canvas.itemconfigure(self.form_window, width=max(event.width, 780))

    def _payload(self):
        return {
            "full_name": self.entries["full_name"][2].get(),
            "id_no": self.entries["id_no"][2].get(),
            "telephone": self.entries["telephone"][2].get(),
            "email": self.entries["email"][2].get(),
            "address": self.entries["address"][2].get(),
            "zone": self.zone_combo.get(),
        }

    def _on_change(self):
        validation_errors = collect_filling_info_errors(self._payload())
        for key, (_, _, entry_widget, _, _) in self.entries.items():
            if key == "address":
                self.error_labels[key].configure(text="")
                self.style_entry(entry_widget, error=False)
                continue
            self.error_labels[key].configure(text=validation_errors.get(key, ""))
            self.style_entry(entry_widget, error=key in validation_errors)

        self.zone_err.configure(text=validation_errors.get("zone", ""))
        self.continue_btn.configure(state=("normal" if not validation_errors else "disabled"))

    def _continue_registration(self):
        self.app.save_registration_step2(self._payload())

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.container.configure(bg=th["bg"])
        self.canvas.configure(bg=th["bg"])
        self.form.configure(bg=th["bg"])
        self.title_lbl.configure(text=self.app.translate("create_account_title"), bg=th["bg"], fg=th["text"])

        for key, (label_widget, hint_widget, entry_widget, hint_key, label_key) in self.entries.items():
            label_widget.configure(text=self.app.translate(label_key), bg=th["bg"], fg=th["text"])
            hint_widget.configure(text=self.app.translate(hint_key), bg=th["bg"], fg=th["muted"])
            self.error_labels[key].configure(bg=th["bg"], fg="#D64545")
            self.style_entry(entry_widget)

        self.zone_lbl.configure(text=self.app.translate("enter_zone"), bg=th["bg"], fg=th["text"])
        self.zone_hint.configure(text=self.app.translate("zone_hint"), bg=th["bg"], fg=th["muted"])
        self.zone_err.configure(bg=th["bg"], fg="#D64545")
        self.continue_btn.configure(text=self.app.translate("continue"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])

        for _, (_, _, entry_widget, _, _) in self.entries.items():
            entry_widget.delete(0, tk.END)
        self.zone_combo.current(0)
        self.continue_btn.configure(state="disabled")
