import tkinter as tk
from tkinter import ttk, messagebox

from ui.common_widgets import handle_action, guarded_button_call


class LoginWindow(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master, padding=12)
        self.app = app
        self.grid(sticky="nsew")

        ttk.Label(self, text="Smart Waste System", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Label(self, text="User ID").grid(row=1, column=0, sticky="w")
        self.user_id_entry = ttk.Entry(self)
        self.user_id_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(self, text="Password").grid(row=2, column=0, sticky="w")
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.grid(row=2, column=1, sticky="ew", pady=2)

        login_btn = ttk.Button(self, text="Login")
        login_btn.grid(row=3, column=0, columnspan=2, pady=8, sticky="ew")
        login_btn.configure(command=guarded_button_call(login_btn, self.on_login))

        ttk.Separator(self).grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(self, text="Resident Registration", font=("Arial", 11, "bold")).grid(row=5, column=0, columnspan=2)

        ttk.Label(self, text="Name").grid(row=6, column=0, sticky="w")
        self.reg_name = ttk.Entry(self)
        self.reg_name.grid(row=6, column=1, sticky="ew", pady=2)

        ttk.Label(self, text="Password").grid(row=7, column=0, sticky="w")
        self.reg_pwd = ttk.Entry(self, show="*")
        self.reg_pwd.grid(row=7, column=1, sticky="ew", pady=2)

        ttk.Label(self, text="Zone (optional)").grid(row=8, column=0, sticky="w")
        self.zone_combo = ttk.Combobox(self, state="readonly")
        self.zone_combo.grid(row=8, column=1, sticky="ew", pady=2)

        reg_btn = ttk.Button(self, text="Register Resident")
        reg_btn.grid(row=9, column=0, columnspan=2, sticky="ew", pady=6)
        reg_btn.configure(command=guarded_button_call(reg_btn, self.on_register))

        self.columnconfigure(1, weight=1)
        self.refresh_zones()

    def refresh_zones(self):
        zones = self.app.admin_service.list_zones()
        self.zones = {f"{z['zone_id']} - {z['zone_name']}": z['zone_id'] for z in zones}
        values = [""] + list(self.zones.keys())
        self.zone_combo["values"] = values
        self.zone_combo.current(0)

    def on_login(self):
        user = handle_action(self, lambda: self.app.auth_service.login(self.user_id_entry.get(), self.password_entry.get()))
        if user:
            self.app.open_dashboard(user)

    def on_register(self):
        zone_choice = self.zone_combo.get().strip()
        zone_id = self.zones.get(zone_choice) if zone_choice else None

        new_id = handle_action(
            self,
            lambda: self.app.auth_service.register_resident(self.reg_name.get(), self.reg_pwd.get(), zone_id),
        )
        if new_id:
            messagebox.showinfo("Registered", f"Resident account created. Your user_id is {new_id}.")
