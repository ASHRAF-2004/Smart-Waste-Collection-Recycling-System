from tkinter import ttk, messagebox

from ui.common_widgets import handle_action, guarded_button_call


class AdminDashboard(ttk.Frame):
    def __init__(self, master, app, user):
        super().__init__(master, padding=10)
        self.app = app
        self.user = user
        self.grid(sticky="nsew")

        head = ttk.Frame(self)
        head.pack(fill="x")
        ttk.Label(head, text=f"Admin Dashboard - {user['name']}", font=("Arial", 13, "bold")).pack(side="left")
        ttk.Button(head, text="Logout", command=self.app.show_login).pack(side="right")

        self.overview_label = ttk.Label(self, text="Overview")
        self.overview_label.pack(anchor="w", pady=4)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self._zones_tab(nb)
        self._users_tab(nb)
        self._notes_tab(nb)
        self.refresh_all()

    def _zones_tab(self, nb):
        tab = ttk.Frame(nb, padding=8)
        nb.add(tab, text="Zones")
        self.zone_tree = ttk.Treeview(tab, columns=("id", "name"), show="headings", height=8)
        self.zone_tree.heading("id", text="Zone ID")
        self.zone_tree.heading("name", text="Zone Name")
        self.zone_tree.pack(fill="both", expand=True)

        f = ttk.Frame(tab)
        f.pack(fill="x", pady=5)
        self.zone_name_entry = ttk.Entry(f, width=25)
        self.zone_name_entry.grid(row=0, column=0, padx=4)
        add_btn = ttk.Button(f, text="Add Zone")
        add_btn.grid(row=0, column=1)
        add_btn.configure(command=guarded_button_call(add_btn, self.add_zone))
        up_btn = ttk.Button(f, text="Update Selected Zone")
        up_btn.grid(row=0, column=2, padx=4)
        up_btn.configure(command=guarded_button_call(up_btn, self.update_zone))

    def _users_tab(self, nb):
        tab = ttk.Frame(nb, padding=8)
        nb.add(tab, text="Users")
        self.user_tree = ttk.Treeview(tab, columns=("id", "name", "role", "zone", "points"), show="headings", height=10)
        for c, t in [("id", "User ID"), ("name", "Name"), ("role", "Role"), ("zone", "Zone"), ("points", "Points")]:
            self.user_tree.heading(c, text=t)
        self.user_tree.pack(fill="both", expand=True)

        f = ttk.Frame(tab)
        f.pack(fill="x", pady=6)
        self.u_name = ttk.Entry(f, width=16)
        self.u_pwd = ttk.Entry(f, width=12)
        self.u_role = ttk.Combobox(f, values=["WasteCollector", "MunicipalAdmin", "Resident"], width=16, state="readonly")
        self.u_zone = ttk.Combobox(f, width=16, state="readonly")
        self.u_id = ttk.Entry(f, width=8)
        for i, (lbl, widget) in enumerate(
            [
                ("User ID(for update)", self.u_id),
                ("Name", self.u_name),
                ("Password", self.u_pwd),
                ("Role", self.u_role),
                ("Zone", self.u_zone),
            ]
        ):
            ttk.Label(f, text=lbl).grid(row=0, column=i)
            widget.grid(row=1, column=i, padx=3)

        create_btn = ttk.Button(f, text="Create User")
        create_btn.grid(row=1, column=5, padx=5)
        create_btn.configure(command=guarded_button_call(create_btn, self.create_user))
        upd_btn = ttk.Button(f, text="Update User")
        upd_btn.grid(row=1, column=6, padx=5)
        upd_btn.configure(command=guarded_button_call(upd_btn, self.update_user))

    def _notes_tab(self, nb):
        tab = ttk.Frame(nb, padding=8)
        nb.add(tab, text="Notifications")
        ttk.Label(tab, text="Target User ID").grid(row=0, column=0)
        ttk.Label(tab, text="Title").grid(row=0, column=1)
        ttk.Label(tab, text="Message").grid(row=0, column=2)
        self.n_user = ttk.Entry(tab, width=10)
        self.n_title = ttk.Entry(tab, width=20)
        self.n_msg = ttk.Entry(tab, width=36)
        self.n_user.grid(row=1, column=0, padx=4)
        self.n_title.grid(row=1, column=1, padx=4)
        self.n_msg.grid(row=1, column=2, padx=4)
        send_btn = ttk.Button(tab, text="Send Notification")
        send_btn.grid(row=1, column=3, padx=4)
        send_btn.configure(command=guarded_button_call(send_btn, self.send_notification))

    def refresh_all(self):
        counts = handle_action(self, lambda: self.app.admin_service.get_overview_counts(self.user))
        if counts:
            self.overview_label.config(
                text=f"Users: {counts['users']} | Pickups: {counts['pickup_requests']} | Recycling Logs: {counts['recycling_logs']} | Notifications: {counts['notifications']}"
            )
        self.refresh_zones()
        self.refresh_users()

    def refresh_zones(self):
        zones = self.app.admin_service.list_zones()
        self.zone_map = {f"{z['zone_id']} - {z['zone_name']}": z["zone_id"] for z in zones}
        self.u_zone["values"] = [""] + list(self.zone_map.keys())

        for i in self.zone_tree.get_children():
            self.zone_tree.delete(i)
        for z in zones:
            self.zone_tree.insert("", "end", values=(z["zone_id"], z["zone_name"]))

    def refresh_users(self):
        for i in self.user_tree.get_children():
            self.user_tree.delete(i)
        rows = self.app.admin_service.list_users()
        for u in rows:
            self.user_tree.insert("", "end", values=(u["user_id"], u["name"], u["role"], u["zone_name"], u["total_points"]))

    def add_zone(self):
        zid = handle_action(self, lambda: self.app.admin_service.add_zone(self.user, self.zone_name_entry.get()))
        if zid:
            messagebox.showinfo("Success", f"Zone created with id {zid}")
            self.refresh_all()

    def update_zone(self):
        sel = self.zone_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a zone.")
            return
        zone_id = self.zone_tree.item(sel[0], "values")[0]
        done = handle_action(self, lambda: self.app.admin_service.update_zone(self.user, zone_id, self.zone_name_entry.get()), "Zone updated")
        if done is None:
            self.refresh_all()

    def create_user(self):
        zone_id = self.zone_map.get(self.u_zone.get()) if self.u_zone.get() else None
        uid = handle_action(
            self,
            lambda: self.app.admin_service.create_staff_user(
                self.user, self.u_name.get(), self.u_pwd.get(), self.u_role.get(), zone_id
            ),
        )
        if uid:
            messagebox.showinfo("Success", f"User created with id {uid}")
            self.refresh_all()

    def update_user(self):
        zone_choice = self.u_zone.get()
        zone_id = self.zone_map.get(zone_choice) if zone_choice else ""
        done = handle_action(
            self,
            lambda: self.app.admin_service.update_user(
                self.user,
                self.u_id.get(),
                name=self.u_name.get() or None,
                password=self.u_pwd.get() or None,
                role=self.u_role.get() or None,
                zone_id=zone_id,
            ),
            "User updated",
        )
        if done is None:
            self.refresh_all()

    def send_notification(self):
        note_id = handle_action(
            self,
            lambda: self.app.notification_service.send_to_user(
                self.user, self.n_user.get(), self.n_title.get(), self.n_msg.get()
            ),
        )
        if note_id:
            messagebox.showinfo("Success", f"Notification {note_id} sent")
            self.refresh_all()
