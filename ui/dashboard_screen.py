import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox, simpledialog, ttk

from services.validation_service import validate_pickup_datetime, validate_password, validate_user_id
from ui.base_screen import BaseScreen

CATEGORIES = ["Plastic", "Paper", "Glass", "Metal", "E-Waste", "Organic", "Other"]


class DashboardScreen(BaseScreen):
    def __init__(self, master, app, user_id: str, **kwargs):
        super().__init__(master, app, **kwargs)
        self.user_id = user_id
        self.user = self.app.db.get_user(user_id)
        self.recycle_image = ""
        self.evidence_image = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.add_top_bar(back_command=self.app.go_back)

        top = ttk.Frame(self)
        top.grid(row=1, column=0, sticky="nsew", padx=10, pady=8)
        top.grid_columnconfigure(0, weight=1)
        ttk.Label(top, text=f"Welcome {self.user['name'] or self.user_id}", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(top, text="Logout", command=lambda: self.app.show_screen("Login")).grid(row=0, column=1, sticky="e")

        self.nb = ttk.Notebook(top)
        self.nb.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=8)
        if self.user["role"] == "Resident":
            self._resident_view()
        elif self.user["role"] == "WasteCollector":
            self._collector_view()
        else:
            self._admin_view()

    def _resident_view(self):
        tab1 = ttk.Frame(self.nb, padding=8)
        tab2 = ttk.Frame(self.nb, padding=8)
        tab3 = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab1, text="Create Pickup Request")
        self.nb.add(tab2, text="My Pickups")
        self.nb.add(tab3, text="Stats & Notifications")

        ttk.Label(tab1, text="Pickup Date").grid(row=0, column=0, sticky="w")
        self.date_entry = ttk.Entry(tab1, width=12)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.grid(row=1, column=0, sticky="w")
        ttk.Label(tab1, text="Pickup Time").grid(row=0, column=1, sticky="w")
        times = [(datetime(2000, 1, 1, 8, 0) + timedelta(minutes=30 * i)).strftime("%H:%M") for i in range(21)]
        self.time_combo = ttk.Combobox(tab1, values=times, state="readonly", width=8)
        self.time_combo.set("08:00")
        self.time_combo.grid(row=1, column=1, sticky="w", padx=8)

        ttk.Label(tab1, text="Category").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.cat_combo = ttk.Combobox(tab1, values=CATEGORIES, state="readonly")
        self.cat_combo.set("Plastic")
        self.cat_combo.grid(row=3, column=0, sticky="w")
        ttk.Label(tab1, text="Weight (kg)").grid(row=2, column=1, sticky="w", pady=(10, 0))
        self.weight_entry = ttk.Entry(tab1, width=10)
        self.weight_entry.grid(row=3, column=1, sticky="w", padx=8)
        ttk.Button(tab1, text="Upload Image (optional)", command=self._pick_recycle_image).grid(row=4, column=0, sticky="w", pady=8)
        ttk.Button(tab1, text="Submit Pickup + Recycling", command=self._submit_pickup).grid(row=5, column=0, sticky="w")

        self.pickup_tree = ttk.Treeview(tab2, columns=("id", "zone", "dt", "status", "updated", "points"), show="headings", height=12)
        for c in ("id", "zone", "dt", "status", "updated", "points"):
            self.pickup_tree.heading(c, text=c.upper())
        self.pickup_tree.pack(fill="both", expand=True)
        ttk.Button(tab2, text="Cancel Selected", command=self._cancel_pickup).pack(anchor="w", pady=6)

        self.stats_lbl = ttk.Label(tab3, text="")
        self.stats_lbl.pack(anchor="w")
        self.note_tree = ttk.Treeview(tab3, columns=("title", "message", "time"), show="headings", height=8)
        for c in ("title", "message", "time"):
            self.note_tree.heading(c, text=c.title())
        self.note_tree.pack(fill="both", expand=True)
        self._refresh_resident()

    def _pick_recycle_image(self):
        self.recycle_image = filedialog.askopenfilename(title="Select image")

    def _submit_pickup(self):
        try:
            dt = validate_pickup_datetime(self.date_entry.get(), self.time_combo.get()).strftime("%Y-%m-%d %H:%M")
            weight = float(self.weight_entry.get())
            if not (0 < weight <= 200):
                raise ValueError("Weight must be more than 0 and no more than 200kg.")
            self.app.db.create_pickup_with_recycling(self.user_id, dt, self.cat_combo.get(), weight, self.recycle_image)
            messagebox.showinfo("Success", "Pickup request submitted")
            self._refresh_resident()
        except Exception as exc:
            messagebox.showerror("Validation", str(exc))

    def _refresh_resident(self):
        for i in self.pickup_tree.get_children():
            self.pickup_tree.delete(i)
        for row in self.app.db.list_resident_pickups(self.user_id):
            self.pickup_tree.insert("", "end", values=(row["pickup_id"], row["zone"], row["requested_datetime"], row["current_status"], row["last_update"], row["points_awarded"]))
        stats = self.app.db.get_resident_stats(self.user_id)
        self.stats_lbl.config(text=f"Total: {stats['total']} | Completed: {stats['completed']} | Cancelled: {stats['cancelled']} | Failed: {stats['failed']} | Completed Weight: {stats['weight']}kg | Rate: {stats['rate']:.2%}")
        for i in self.note_tree.get_children():
            self.note_tree.delete(i)
        for n in self.app.db.get_notifications(self.user_id):
            self.note_tree.insert("", "end", values=(n["title"], n["message"], n["created_at"]))

    def _cancel_pickup(self):
        sel = self.pickup_tree.selection()
        if not sel:
            return
        pid = int(self.pickup_tree.item(sel[0], "values")[0])
        reason = simpledialog.askstring("Cancel reason", "Please provide cancellation reason (min 5 chars):")
        if not reason or len(reason.strip()) < 5:
            messagebox.showerror("Error", "Cancellation reason too short.")
            return
        self.app.db.cancel_resident_pickup(self.user_id, pid, reason)
        self._refresh_resident()

    def _collector_view(self):
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Assigned Pickup Requests")
        self.ctree = ttk.Treeview(tab, columns=("id", "resident", "zone", "dt", "status"), show="headings", height=12)
        for c in ("id", "resident", "zone", "dt", "status"):
            self.ctree.heading(c, text=c.title())
        self.ctree.pack(fill="both", expand=True)

        btns = ttk.Frame(tab)
        btns.pack(fill="x", pady=6)
        for col, status in enumerate(["ACCEPTED", "IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED"]):
            ttk.Button(btns, text=status, command=lambda s=status: self._collector_update(s)).grid(row=0, column=col, padx=3)
        ttk.Button(btns, text="Evidence Image", command=self._pick_evidence).grid(row=0, column=5, padx=4)
        self._refresh_collector()

    def _pick_evidence(self):
        self.evidence_image = filedialog.askopenfilename(title="Evidence image")

    def _collector_update(self, status):
        sel = self.ctree.selection()
        if not sel:
            return
        pid = int(self.ctree.item(sel[0], "values")[0])
        comment = ""
        if status in ("FAILED", "CANCELLED", "COMPLETED"):
            comment = simpledialog.askstring("Comment", "Enter comment/reason:") or ""
        try:
            self.app.db.collector_update_pickup(self.user_id, pid, status, comment, self.evidence_image)
            self._refresh_collector()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _refresh_collector(self):
        for i in self.ctree.get_children():
            self.ctree.delete(i)
        for row in self.app.db.list_collector_tasks(self.user_id):
            self.ctree.insert("", "end", values=(row["pickup_id"], row["resident_id"], row["zone"], row["requested_datetime"], row["current_status"]))

    def _admin_view(self):
        t1 = ttk.Frame(self.nb, padding=8)
        t2 = ttk.Frame(self.nb, padding=8)
        t3 = ttk.Frame(self.nb, padding=8)
        self.nb.add(t1, text="Overview")
        self.nb.add(t2, text="Users & Zones")
        self.nb.add(t3, text="Notifications")

        self.overview = ttk.Label(t1, text="")
        self.overview.pack(anchor="w")

        self.user_tree = ttk.Treeview(t2, columns=("id", "name", "role", "zone", "active", "points"), show="headings", height=9)
        for c in ("id", "name", "role", "zone", "active", "points"):
            self.user_tree.heading(c, text=c)
        self.user_tree.pack(fill="both", expand=True)

        form = ttk.Frame(t2)
        form.pack(fill="x", pady=6)
        self.u_login = ttk.Entry(form, width=12)
        self.u_name = ttk.Entry(form, width=12)
        self.u_pwd = ttk.Entry(form, width=12)
        self.u_role = ttk.Combobox(form, values=["Resident", "WasteCollector", "MunicipalAdmin"], width=14, state="readonly")
        self.u_zone = ttk.Combobox(form, width=12, state="readonly")
        for i, (label, widget) in enumerate([("User ID", self.u_login), ("Name", self.u_name), ("Password", self.u_pwd), ("Role", self.u_role), ("Zone", self.u_zone)]):
            ttk.Label(form, text=label).grid(row=0, column=i, sticky="w")
            widget.grid(row=1, column=i, padx=2)
        ttk.Button(form, text="Create", command=self._admin_create_user).grid(row=1, column=5, padx=3)
        ttk.Button(form, text="Update", command=self._admin_update_user).grid(row=1, column=6, padx=3)
        ttk.Button(form, text="Deactivate", command=self._admin_deactivate).grid(row=1, column=7, padx=3)

        zf = ttk.Frame(t2)
        zf.pack(fill="x", pady=6)
        self.z_id = ttk.Entry(zf, width=6)
        self.z_name = ttk.Entry(zf, width=20)
        ttk.Label(zf, text="Zone ID").grid(row=0, column=0, sticky="w")
        self.z_id.grid(row=1, column=0, padx=2)
        ttk.Label(zf, text="Zone Name").grid(row=0, column=1, sticky="w")
        self.z_name.grid(row=1, column=1, padx=2)
        ttk.Button(zf, text="Add Zone", command=self._admin_add_zone).grid(row=1, column=2, padx=3)
        ttk.Button(zf, text="Rename/Set Active", command=self._admin_update_zone).grid(row=1, column=3, padx=3)

        ttk.Label(t3, text="Target User ID").grid(row=0, column=0, sticky="w")
        ttk.Label(t3, text="OR Target Zone").grid(row=0, column=1, sticky="w")
        ttk.Label(t3, text="Title").grid(row=0, column=2, sticky="w")
        ttk.Label(t3, text="Message").grid(row=0, column=3, sticky="w")
        self.n_user = ttk.Entry(t3, width=14)
        self.n_zone = ttk.Combobox(t3, width=12, state="readonly")
        self.n_title = ttk.Entry(t3, width=20)
        self.n_msg = ttk.Entry(t3, width=30)
        self.n_user.grid(row=1, column=0); self.n_zone.grid(row=1, column=1); self.n_title.grid(row=1, column=2); self.n_msg.grid(row=1, column=3)
        ttk.Button(t3, text="Send", command=self._admin_send_note).grid(row=1, column=4)
        self._refresh_admin()

    def _refresh_admin(self):
        ov = self.app.db.get_admin_overview()
        self.overview.config(text=f"Users: {ov['users']} | Pickups: {ov['pickups']} | Recycling Logs: {ov['recycling_logs']} | Notifications: {ov['notifications']}")
        zones = self.app.db.list_zones()
        self.zone_map = {f"{z['zone_id']}:{z['name']}": z['zone_id'] for z in zones}
        self.u_zone["values"] = [""] + list(self.zone_map.keys())
        self.n_zone["values"] = [""] + list(self.zone_map.keys())
        for i in self.user_tree.get_children():
            self.user_tree.delete(i)
        for u in self.app.db.list_users():
            self.user_tree.insert("", "end", values=(u["user_login_id"], u["name"], u["role"], u["zone_name"], u["is_active"], u["total_points"]))

    def _admin_create_user(self):
        validate_user_id(self.u_login.get())
        validate_password(self.u_pwd.get(), self.u_login.get())
        zid = self.zone_map.get(self.u_zone.get())
        self.app.db.add_user(self.u_login.get(), self.u_name.get(), self.u_pwd.get(), self.u_role.get(), zid)
        self._refresh_admin()

    def _admin_update_user(self):
        zid = self.zone_map.get(self.u_zone.get())
        self.app.db.update_user(self.u_login.get(), self.u_name.get(), self.u_role.get(), zid, self.u_pwd.get())
        self._refresh_admin()

    def _admin_deactivate(self):
        sel = self.user_tree.selection()
        if not sel:
            return
        uid = self.user_tree.item(sel[0], "values")[0]
        u = self.app.db.get_user(uid)
        self.app.db.update_user(uid, u["name"], u["role"], u["zone_id"], "", 0)
        self._refresh_admin()

    def _admin_add_zone(self):
        self.app.db.create_zone(self.z_name.get())
        self._refresh_admin()

    def _admin_update_zone(self):
        self.app.db.update_zone(int(self.z_id.get()), self.z_name.get(), 1)
        self._refresh_admin()

    def _admin_send_note(self):
        if self.n_user.get():
            self.app.db.conn.execute("INSERT INTO notification(user_id,type,title,message) VALUES(?,?,?,?)", (self.n_user.get(), "SYSTEM", self.n_title.get(), self.n_msg.get()))
            self.app.db.conn.commit()
        elif self.n_zone.get():
            self.app.db.send_notification_by_zone(self.zone_map[self.n_zone.get()], self.n_title.get(), self.n_msg.get())
        self._refresh_admin()
