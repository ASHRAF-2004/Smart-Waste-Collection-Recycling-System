import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

from services.validation_service import validate_password, validate_user_id
from ui.base_screen import BaseScreen


class DashboardScreen(BaseScreen):
    def __init__(self, master, app, user_id: str, **kwargs):
        super().__init__(master, app, **kwargs)
        self.user_id = user_id
        self.user = self.app.db.get_user(user_id)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.add_top_bar(back_command=self.app.go_back)

        self.wrap = tk.Frame(self)
        self.wrap.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.wrap.grid_columnconfigure(0, weight=1)
        self.wrap.grid_rowconfigure(2, weight=1)

        self.title_lbl = tk.Label(self.wrap, font=("Segoe UI", 26, "bold"))
        self.title_lbl.grid(row=0, column=0, sticky="w", pady=(5, 8))

        self.sub_lbl = tk.Label(self.wrap, font=("Segoe UI", 12))
        self.sub_lbl.grid(row=1, column=0, sticky="w", pady=(0, 10))

        self.content_area = tk.Frame(self.wrap)
        self.content_area.grid(row=2, column=0, sticky="nsew")

        self.logout_btn = tk.Button(self.wrap, bd=0, width=20, pady=10, command=lambda: self.app.show_screen("Login"))
        self.logout_btn.grid(row=3, column=0, pady=16, sticky="w")

        self._build_role_view()

    def _build_role_view(self):
        role = self.user["role"] if self.user else "Resident"
        if role == "MunicipalAdmin":
            self._build_admin_dashboard()
        elif role == "WasteCollector":
            self._build_collector_dashboard()
        else:
            self._build_resident_dashboard()

    def _build_resident_dashboard(self):
        self.unread_lbl = tk.Label(self.content_area, font=("Segoe UI", 10, "bold"))
        self.unread_lbl.grid(row=0, column=0, sticky="w", pady=4)
        self.mark_read_btn = tk.Button(self.content_area, bd=0, command=self._mark_read)
        self.mark_read_btn.grid(row=0, column=1, sticky="w", padx=8)

        self.leader_title = tk.Label(self.content_area, font=("Segoe UI", 16, "bold"))
        self.leader_title.grid(row=1, column=0, sticky="w", pady=(12, 6))
        self.leader_tree = ttk.Treeview(self.content_area, columns=("zone", "name", "points"), show="headings", height=8)
        for col, text in (("zone", "Zone"), ("name", "Name"), ("points", "Points")):
            self.leader_tree.heading(col, text=text)
        self.leader_tree.grid(row=2, column=0, columnspan=2, sticky="ew")
        self._refresh_resident_data()

    def _refresh_resident_data(self):
        self.unread = self.app.db.unread_count(self.user_id)
        rows = self.app.db.get_zone_leaderboard()
        for item_id in self.leader_tree.get_children():
            self.leader_tree.delete(item_id)
        for row in rows[:20]:
            self.leader_tree.insert("", "end", values=(row["zone"], row["full_name"], row["total_points"]))

    def _mark_read(self):
        self.app.db.mark_notifications_read(self.user_id)
        self._refresh_resident_data()
        self.refresh_ui()

    def _build_admin_dashboard(self):
        self.admin_stats_lbl = tk.Label(self.content_area, font=("Segoe UI", 10, "bold"))
        self.admin_stats_lbl.pack(anchor="w", pady=(0, 8))

        self.admin_notebook = ttk.Notebook(self.content_area)
        self.admin_notebook.pack(fill="both", expand=True)

        self._build_admin_users_tab()
        self._build_admin_zones_tab()
        self._build_admin_notifications_tab()
        self._refresh_admin_data()

    def _build_admin_users_tab(self):
        tab = ttk.Frame(self.admin_notebook, padding=8)
        self.admin_notebook.add(tab, text="Users")

        sorting_bar = ttk.Frame(tab)
        sorting_bar.pack(fill="x", pady=(0, 6))
        ttk.Label(sorting_bar, text="Sort users by").pack(side="left")
        self.admin_sort_combo = ttk.Combobox(sorting_bar, values=["full_name", "role", "zone"], state="readonly", width=12)
        self.admin_sort_combo.pack(side="left", padx=6)
        self.admin_sort_combo.set("full_name")
        ttk.Button(sorting_bar, text="Apply", command=self._refresh_admin_users).pack(side="left")

        self.admin_user_tree = ttk.Treeview(
            tab,
            columns=("user_id", "full_name", "role", "zone", "telephone", "email"),
            show="headings",
            height=9,
        )
        for col, text in (
            ("user_id", "User ID"),
            ("full_name", "Name"),
            ("role", "Role"),
            ("zone", "Zone"),
            ("telephone", "Telephone"),
            ("email", "Email"),
        ):
            self.admin_user_tree.heading(col, text=text)
            self.admin_user_tree.column(col, width=120)
        self.admin_user_tree.pack(fill="both", expand=True)
        self.admin_user_tree.bind("<<TreeviewSelect>>", lambda _e: self._load_selected_user())

        form = ttk.Frame(tab)
        form.pack(fill="x", pady=8)

        self.admin_user_form = {}
        labels = [
            ("user_id", "User ID"),
            ("password", "Password"),
            ("full_name", "Full Name"),
            ("role", "Role"),
            ("zone", "Zone"),
            ("telephone", "Telephone"),
            ("email", "Email"),
            ("address", "Address"),
        ]
        for idx, (field_name, label_text) in enumerate(labels):
            ttk.Label(form, text=label_text).grid(row=idx // 4 * 2, column=idx % 4, sticky="w", padx=4)
            if field_name == "role":
                widget = ttk.Combobox(form, values=["Resident", "WasteCollector", "MunicipalAdmin"], state="readonly", width=16)
                widget.set("Resident")
            elif field_name == "zone":
                widget = ttk.Combobox(form, values=[""], state="readonly", width=16)
            elif field_name == "password":
                widget = ttk.Entry(form, width=18, show="*")
            else:
                widget = ttk.Entry(form, width=18)
            widget.grid(row=idx // 4 * 2 + 1, column=idx % 4, padx=4, pady=(0, 6), sticky="ew")
            self.admin_user_form[field_name] = widget

        button_bar = ttk.Frame(tab)
        button_bar.pack(fill="x", pady=4)
        ttk.Button(button_bar, text="Add User", command=self._admin_add_user).pack(side="left", padx=4)
        ttk.Button(button_bar, text="Update User", command=self._admin_update_user).pack(side="left", padx=4)
        ttk.Button(button_bar, text="Delete User", command=self._admin_delete_user).pack(side="left", padx=4)

    def _build_admin_zones_tab(self):
        tab = ttk.Frame(self.admin_notebook, padding=8)
        self.admin_notebook.add(tab, text="Zones")

        self.zone_tree = ttk.Treeview(tab, columns=("zone",), show="headings", height=10)
        self.zone_tree.heading("zone", text="Zone Name")
        self.zone_tree.pack(fill="both", expand=True, pady=(0, 8))
        self.zone_tree.bind("<<TreeviewSelect>>", lambda _e: self._load_selected_zone())

        zone_form = ttk.Frame(tab)
        zone_form.pack(fill="x")
        ttk.Label(zone_form, text="Zone name").grid(row=0, column=0, sticky="w")
        self.zone_name_entry = ttk.Entry(zone_form, width=20)
        self.zone_name_entry.grid(row=1, column=0, padx=(0, 6), pady=4)
        ttk.Button(zone_form, text="Create", command=self._zone_create).grid(row=1, column=1, padx=4)
        ttk.Button(zone_form, text="Update", command=self._zone_update).grid(row=1, column=2, padx=4)
        ttk.Button(zone_form, text="Delete", command=self._zone_delete).grid(row=1, column=3, padx=4)

    def _build_admin_notifications_tab(self):
        tab = ttk.Frame(self.admin_notebook, padding=8)
        self.admin_notebook.add(tab, text="Notifications")

        form = ttk.Frame(tab)
        form.pack(fill="x", pady=(0, 8))
        ttk.Label(form, text="Target user ID").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="Title").grid(row=0, column=1, sticky="w")
        ttk.Label(form, text="Message").grid(row=0, column=2, sticky="w")
        self.note_user_entry = ttk.Entry(form, width=16)
        self.note_title_entry = ttk.Entry(form, width=20)
        self.note_msg_entry = ttk.Entry(form, width=40)
        self.note_user_entry.grid(row=1, column=0, padx=4)
        self.note_title_entry.grid(row=1, column=1, padx=4)
        self.note_msg_entry.grid(row=1, column=2, padx=4)
        ttk.Button(form, text="Send", command=self._send_notification).grid(row=1, column=3, padx=4)

        self.notification_tree = ttk.Treeview(
            tab,
            columns=("id", "user", "title", "message", "source", "created_at"),
            show="headings",
            height=10,
        )
        for col, text in (
            ("id", "ID"),
            ("user", "User"),
            ("title", "Title"),
            ("message", "Message"),
            ("source", "Source"),
            ("created_at", "Created At"),
        ):
            self.notification_tree.heading(col, text=text)
            self.notification_tree.column(col, width=120)
        self.notification_tree.pack(fill="both", expand=True)

    def _refresh_admin_data(self):
        stats = self.app.db.get_admin_stats()
        self.admin_stats_lbl.configure(
            text=f"Users: {stats['users']} | Pickups: {stats['pickups']} | Zones: {stats['zones']} | Notifications: {stats['notifications']}"
        )
        self._refresh_admin_users()
        self._refresh_admin_zones()
        self._refresh_admin_notifications()

    def _refresh_admin_users(self):
        sort_by = self.admin_sort_combo.get() or "full_name"
        for item_id in self.admin_user_tree.get_children():
            self.admin_user_tree.delete(item_id)
        for user_row in self.app.db.list_users(sort_by=sort_by):
            self.admin_user_tree.insert(
                "",
                "end",
                values=(
                    user_row["user_id"],
                    user_row["full_name"] or "",
                    user_row["role"],
                    user_row["zone"] or "",
                    user_row["telephone"] or "",
                    user_row["email"] or "",
                ),
            )
        zones = [row["zone_name"] for row in self.app.db.list_zones()]
        self.admin_user_form["zone"].configure(values=[""] + zones)

    def _refresh_admin_zones(self):
        for item_id in self.zone_tree.get_children():
            self.zone_tree.delete(item_id)
        for zone_row in self.app.db.list_zones():
            self.zone_tree.insert("", "end", values=(zone_row["zone_name"],))

    def _refresh_admin_notifications(self):
        for item_id in self.notification_tree.get_children():
            self.notification_tree.delete(item_id)
        for note in self.app.db.get_admin_notifications():
            self.notification_tree.insert(
                "",
                "end",
                values=(note["notification_id"], note["user_id"], note["title"], note["message"], note["source_type"], note["created_at"]),
            )

    def _load_selected_user(self):
        selected = self.admin_user_tree.selection()
        if not selected:
            return
        values = self.admin_user_tree.item(selected[0], "values")
        self.admin_user_form["user_id"].delete(0, tk.END)
        self.admin_user_form["user_id"].insert(0, values[0])
        self.admin_user_form["full_name"].delete(0, tk.END)
        self.admin_user_form["full_name"].insert(0, values[1])
        self.admin_user_form["role"].set(values[2])
        self.admin_user_form["zone"].set(values[3])
        self.admin_user_form["telephone"].delete(0, tk.END)
        self.admin_user_form["telephone"].insert(0, values[4])
        self.admin_user_form["email"].delete(0, tk.END)
        self.admin_user_form["email"].insert(0, values[5])

    def _admin_add_user(self):
        try:
            new_user_id = validate_user_id(self.admin_user_form["user_id"].get())
            new_password = validate_password(self.admin_user_form["password"].get(), new_user_id)
            self.app.db.add_user(
                {
                    "user_id": new_user_id,
                    "password": new_password,
                    "full_name": self.admin_user_form["full_name"].get().strip(),
                    "role": self.admin_user_form["role"].get() or "Resident",
                    "zone": self.admin_user_form["zone"].get().strip(),
                    "telephone": self.admin_user_form["telephone"].get().strip(),
                    "email": self.admin_user_form["email"].get().strip(),
                    "address": self.admin_user_form["address"].get().strip(),
                }
            )
            messagebox.showinfo("Success", "User created successfully.")
            self._refresh_admin_data()
        except (ValueError, sqlite3.Error) as exc:
            messagebox.showerror("Error", str(exc))

    def _admin_update_user(self):
        user_id_value = self.admin_user_form["user_id"].get().strip()
        if not user_id_value:
            messagebox.showwarning("Required", "User ID is required for update.")
            return
        updates = {
            "full_name": self.admin_user_form["full_name"].get().strip(),
            "role": self.admin_user_form["role"].get().strip(),
            "zone": self.admin_user_form["zone"].get().strip(),
            "telephone": self.admin_user_form["telephone"].get().strip(),
            "email": self.admin_user_form["email"].get().strip(),
            "address": self.admin_user_form["address"].get().strip(),
        }
        password_update = self.admin_user_form["password"].get().strip()
        if password_update:
            updates["password"] = validate_password(password_update, user_id_value)
        updates = {key: value for key, value in updates.items() if value}
        try:
            self.app.db.update_user(user_id_value, updates)
            messagebox.showinfo("Success", "User updated successfully.")
            self._refresh_admin_data()
        except (ValueError, sqlite3.Error) as exc:
            messagebox.showerror("Error", str(exc))

    def _admin_delete_user(self):
        user_id_value = self.admin_user_form["user_id"].get().strip()
        if not user_id_value:
            messagebox.showwarning("Required", "Select a user to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete user '{user_id_value}'?"):
            return
        try:
            self.app.db.delete_user(user_id_value)
            messagebox.showinfo("Success", "User deleted.")
            self._refresh_admin_data()
        except sqlite3.Error as exc:
            messagebox.showerror("Error", f"Unable to delete user: {exc}")

    def _load_selected_zone(self):
        selected = self.zone_tree.selection()
        if not selected:
            return
        zone_name = self.zone_tree.item(selected[0], "values")[0]
        self.zone_name_entry.delete(0, tk.END)
        self.zone_name_entry.insert(0, zone_name)

    def _zone_create(self):
        zone_name = self.zone_name_entry.get().strip()
        if not zone_name:
            messagebox.showwarning("Required", "Zone name is required.")
            return
        try:
            self.app.db.create_zone(zone_name)
            self._refresh_admin_data()
        except sqlite3.Error as exc:
            messagebox.showerror("Error", f"Unable to create zone: {exc}")

    def _zone_update(self):
        selected = self.zone_tree.selection()
        new_name = self.zone_name_entry.get().strip()
        if not selected or not new_name:
            messagebox.showwarning("Required", "Select a zone and provide a new name.")
            return
        old_name = self.zone_tree.item(selected[0], "values")[0]
        try:
            self.app.db.update_zone(old_name, new_name)
            self._refresh_admin_data()
        except sqlite3.Error as exc:
            messagebox.showerror("Error", f"Unable to update zone: {exc}")

    def _zone_delete(self):
        selected = self.zone_tree.selection()
        if not selected:
            messagebox.showwarning("Required", "Select a zone to delete.")
            return
        zone_name = self.zone_tree.item(selected[0], "values")[0]
        if not messagebox.askyesno("Confirm Delete", f"Delete zone '{zone_name}'?"):
            return
        try:
            self.app.db.delete_zone(zone_name)
            self._refresh_admin_data()
        except sqlite3.Error as exc:
            messagebox.showerror("Error", f"Unable to delete zone: {exc}")

    def _send_notification(self):
        target_user = self.note_user_entry.get().strip()
        title = self.note_title_entry.get().strip()
        message = self.note_msg_entry.get().strip()
        if not target_user or not title or not message:
            messagebox.showwarning("Required", "Target user, title, and message are required.")
            return
        try:
            self.app.db.add_notification(target_user, title, message, source_type="ADMIN")
            messagebox.showinfo("Success", "Notification sent.")
            self._refresh_admin_notifications()
        except sqlite3.Error as exc:
            messagebox.showerror("Error", f"Unable to send notification: {exc}")

    def _build_collector_dashboard(self):
        top_filters = ttk.Frame(self.content_area)
        top_filters.pack(fill="x", pady=(0, 8))
        ttk.Label(top_filters, text="Filter by zone").pack(side="left")
        zones = [zone["zone_name"] for zone in self.app.db.list_zones()]
        self.collector_zone_filter = ttk.Combobox(top_filters, values=[""] + zones, state="readonly", width=14)
        self.collector_zone_filter.pack(side="left", padx=4)
        self.collector_zone_filter.set("")

        ttk.Label(top_filters, text="Status").pack(side="left", padx=(8, 0))
        self.collector_status_filter = ttk.Combobox(top_filters, values=["", "PENDING", "COMPLETED", "FAILED"], state="readonly", width=12)
        self.collector_status_filter.pack(side="left", padx=4)
        self.collector_status_filter.set("")

        ttk.Label(top_filters, text="Sort").pack(side="left", padx=(8, 0))
        self.collector_sort_filter = ttk.Combobox(top_filters, values=["date", "zone"], state="readonly", width=10)
        self.collector_sort_filter.pack(side="left", padx=4)
        self.collector_sort_filter.set("date")
        ttk.Button(top_filters, text="Apply", command=self._refresh_collector_data).pack(side="left", padx=4)

        self.collector_metrics_lbl = tk.Label(self.content_area, font=("Segoe UI", 10, "bold"))
        self.collector_metrics_lbl.pack(anchor="w", pady=(2, 8))

        self.collector_tree = ttk.Treeview(
            self.content_area,
            columns=("pickup_id", "resident", "zone", "requested", "scheduled", "status"),
            show="headings",
            height=9,
        )
        for col, text in (
            ("pickup_id", "Pickup ID"),
            ("resident", "Resident"),
            ("zone", "Zone"),
            ("requested", "Requested"),
            ("scheduled", "Scheduled"),
            ("status", "Status"),
        ):
            self.collector_tree.heading(col, text=text)
            self.collector_tree.column(col, width=120)
        self.collector_tree.pack(fill="both", expand=True)

        update_frame = ttk.Frame(self.content_area)
        update_frame.pack(fill="x", pady=8)
        ttk.Label(update_frame, text="New Status").grid(row=0, column=0, sticky="w")
        self.collector_new_status = ttk.Combobox(update_frame, values=["PENDING", "COMPLETED", "FAILED"], state="readonly", width=12)
        self.collector_new_status.grid(row=1, column=0, padx=4)
        self.collector_new_status.set("COMPLETED")

        ttk.Label(update_frame, text="Comment").grid(row=0, column=1, sticky="w")
        self.collector_comment = ttk.Entry(update_frame, width=24)
        self.collector_comment.grid(row=1, column=1, padx=4)

        ttk.Label(update_frame, text="Evidence image path").grid(row=0, column=2, sticky="w")
        self.collector_evidence = ttk.Entry(update_frame, width=24)
        self.collector_evidence.grid(row=1, column=2, padx=4)

        ttk.Button(update_frame, text="Update Status", command=self._collector_update_status).grid(row=1, column=3, padx=4)

        self._refresh_collector_data()

    def _refresh_collector_data(self):
        for item_id in self.collector_tree.get_children():
            self.collector_tree.delete(item_id)
        rows = self.app.db.get_collector_requests(
            self.user_id,
            zone_filter=self.collector_zone_filter.get().strip(),
            status_filter=self.collector_status_filter.get().strip(),
            sort_by=self.collector_sort_filter.get().strip() or "date",
        )
        for row in rows:
            self.collector_tree.insert(
                "",
                "end",
                values=(
                    row["pickup_id"],
                    row["resident_name"] or row["resident_id"],
                    row["zone"],
                    row["requested_datetime"],
                    row["scheduled_datetime"] or "-",
                    row["status"],
                ),
            )
        metrics = self.app.db.collector_metrics(self.user_id)
        self.collector_metrics_lbl.configure(
            text=f"Completed pickups: {metrics['completed']} | Points rewarded: {metrics['points']} | Avg completion time (hours): {metrics['efficiency_hours']}"
        )

    def _collector_update_status(self):
        selected = self.collector_tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a pickup request.")
            return
        pickup_id = self.collector_tree.item(selected[0], "values")[0]
        try:
            self.app.db.update_pickup_status(
                self.user_id,
                int(pickup_id),
                self.collector_new_status.get(),
                self.collector_comment.get().strip(),
                self.collector_evidence.get().strip(),
            )
            messagebox.showinfo("Success", "Pickup status updated.")
            self._refresh_collector_data()
        except sqlite3.Error as exc:
            messagebox.showerror("Error", f"Unable to update pickup: {exc}")

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.wrap.configure(bg=th["bg"])
        self.content_area.configure(bg=th["bg"])
        self.title_lbl.configure(text=f"{self.app.translate('dashboard')} ({self.user_id})", bg=th["bg"], fg=th["text"])
        role = self.user["role"] if self.user else "Unknown"
        self.sub_lbl.configure(text=f"Role: {role}", bg=th["bg"], fg=th["muted"])
        self.logout_btn.configure(text=self.app.translate("logout"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])

        if role == "Resident":
            self.unread_lbl.configure(text=f"{self.app.translate('unread')}: {self.unread}", bg=th["bg"], fg=th["text"])
            self.mark_read_btn.configure(text=self.app.translate("mark_read"), bg=th["secondary_bg"], fg=th["secondary_fg"], activebackground=th["secondary_bg"])
            self.leader_title.configure(text=self.app.translate("leaderboard"), bg=th["bg"], fg=th["text"])
