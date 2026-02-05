import hashlib
import shutil
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from services.validation_service import validate_password, validate_pickup_datetime, validate_user_id
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
        self.wrap.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        self.wrap.grid_columnconfigure(0, weight=1)
        self.wrap.grid_rowconfigure(2, weight=1)

        self.title_lbl = tk.Label(self.wrap, font=("Segoe UI", 22, "bold"))
        self.title_lbl.grid(row=0, column=0, sticky="w")
        self.sub_lbl = tk.Label(self.wrap, font=("Segoe UI", 11))
        self.sub_lbl.grid(row=1, column=0, sticky="w")

        self.content = ttk.Notebook(self.wrap)
        self.content.grid(row=2, column=0, sticky="nsew", pady=10)

        self.logout_btn = tk.Button(self.wrap, bd=0, width=20, pady=8, command=lambda: self.app.show_screen("Login"))
        self.logout_btn.grid(row=3, column=0, sticky="w")
        self._build_role_view()

    def _build_role_view(self):
        role = self.user["role"]
        if role == "Resident":
            self._build_resident_tabs()
            self.app.db.send_upcoming_pickup_reminders(self.user_id)
        elif role == "WasteCollector":
            self._build_collector_tabs()
        else:
            self._build_admin_tabs()

    def _upload_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png *.jpg *.jpeg")])
        if not path:
            return ""
        src = Path(path)
        if src.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            raise ValueError("Only .png/.jpg/.jpeg files are allowed.")
        if src.stat().st_size > 5 * 1024 * 1024:
            raise ValueError("Image must be <= 5MB.")
        target_dir = Path("uploads")
        target_dir.mkdir(exist_ok=True)
        safe = hashlib.sha1(str(src).encode()).hexdigest()[:10] + src.suffix.lower()
        target = target_dir / safe
        shutil.copy2(src, target)
        return str(target)

    # Resident
    def _build_resident_tabs(self):
        self.tab_pickup = ttk.Frame(self.content, padding=8)
        self.tab_recycle = ttk.Frame(self.content, padding=8)
        self.tab_rewards = ttk.Frame(self.content, padding=8)
        self.tab_notifications = ttk.Frame(self.content, padding=8)
        self.tab_metrics = ttk.Frame(self.content, padding=8)
        self.content.add(self.tab_pickup, text="Pickup Requests")
        self.content.add(self.tab_recycle, text="Recycling Log")
        self.content.add(self.tab_rewards, text="Rewards")
        self.content.add(self.tab_notifications, text="Notifications")
        self.content.add(self.tab_metrics, text="Dashboard")

        ttk.Label(self.tab_pickup, text="Requested Date/Time (YYYY-MM-DD HH:MM)").pack(anchor="w")
        self.pickup_dt_entry = ttk.Entry(self.tab_pickup, width=24)
        self.pickup_dt_entry.pack(anchor="w", pady=4)
        ttk.Button(self.tab_pickup, text="Create Pickup Request", command=self._resident_create_pickup).pack(anchor="w", pady=4)
        self.pickup_tree = ttk.Treeview(self.tab_pickup, columns=("id", "zone", "dt", "status"), show="headings", height=8)
        for c in ("id", "zone", "dt", "status"):
            self.pickup_tree.heading(c, text=c.title())
        self.pickup_tree.pack(fill="both", expand=True)
        ttk.Button(self.tab_pickup, text="View Selected History", command=self._resident_show_history).pack(anchor="w", pady=4)

        ttk.Label(self.tab_recycle, text="Category").grid(row=0, column=0, sticky="w")
        self.recycle_category = ttk.Combobox(self.tab_recycle, values=["Plastic", "Paper", "Glass", "Metal", "Other"], state="readonly")
        self.recycle_category.grid(row=1, column=0, padx=4, pady=4)
        self.recycle_category.set("Plastic")
        ttk.Label(self.tab_recycle, text="Weight (kg, 0.1 - 200)").grid(row=0, column=1, sticky="w")
        self.recycle_weight = ttk.Entry(self.tab_recycle)
        self.recycle_weight.grid(row=1, column=1, padx=4, pady=4)
        self.recycle_image_path = ""
        ttk.Button(self.tab_recycle, text="Upload Image", command=self._resident_pick_recycling_image).grid(row=1, column=2, padx=4)
        ttk.Button(self.tab_recycle, text="Submit Recycling Log", command=self._resident_submit_recycling).grid(row=1, column=3, padx=4)

        self.rewards_lbl = ttk.Label(self.tab_rewards, text="")
        self.rewards_lbl.pack(anchor="w")
        self.recycling_tree = ttk.Treeview(self.tab_rewards, columns=("category", "weight", "points", "at"), show="headings", height=10)
        for c in ("category", "weight", "points", "at"):
            self.recycling_tree.heading(c, text=c.title())
        self.recycling_tree.pack(fill="both", expand=True)

        self.note_tree = ttk.Treeview(self.tab_notifications, columns=("type", "title", "message", "time", "read"), show="headings", height=10)
        for c in ("type", "title", "message", "time", "read"):
            self.note_tree.heading(c, text=c.title())
        self.note_tree.pack(fill="both", expand=True)
        ttk.Button(self.tab_notifications, text="Mark All Read", command=self._resident_mark_read).pack(anchor="w", pady=4)

        self.metrics_lbl = ttk.Label(self.tab_metrics, text="Simulated metrics for prototype.")
        self.metrics_lbl.pack(anchor="w")
        self._refresh_resident()

    def _resident_create_pickup(self):
        try:
            validate_pickup_datetime(self.pickup_dt_entry.get())
            self.app.db.create_pickup_request(self.user_id, self.pickup_dt_entry.get().strip())
            messagebox.showinfo("Success", "Pickup request created.")
            self._refresh_resident()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _resident_show_history(self):
        sel = self.pickup_tree.selection()
        if not sel:
            return
        pickup_id = int(self.pickup_tree.item(sel[0], "values")[0])
        history = self.app.db.get_pickup_updates(pickup_id)
        text = "\n".join(f"{h['timestamp']} - {h['new_status']} - {h['comment'] or '-'}" for h in history) or "No updates yet."
        messagebox.showinfo("Pickup History", text)

    def _resident_pick_recycling_image(self):
        try:
            self.recycle_image_path = self._upload_image()
        except Exception as exc:
            messagebox.showerror("Upload Error", str(exc))

    def _resident_submit_recycling(self):
        try:
            weight = float(self.recycle_weight.get())
            if not (0.1 <= weight <= 200):
                raise ValueError("Weight must be between 0.1 and 200 kg.")
            points = self.app.db.create_recycling_log(self.user_id, self.recycle_category.get(), weight, self.recycle_image_path)
            messagebox.showinfo("Success", f"Recycling submitted. Points added: {points}")
            self.recycle_weight.delete(0, tk.END)
            self.recycle_image_path = ""
            self._refresh_resident()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _resident_mark_read(self):
        self.app.db.mark_notifications_read(self.user_id)
        self._refresh_resident()

    def _refresh_resident(self):
        for i in self.pickup_tree.get_children():
            self.pickup_tree.delete(i)
        for row in self.app.db.list_resident_pickups(self.user_id):
            self.pickup_tree.insert("", "end", values=(row["pickup_id"], row["zone_name"], row["requested_datetime"], row["status"]))

        for i in self.recycling_tree.get_children():
            self.recycling_tree.delete(i)
        logs = self.app.db.list_recycling_logs(self.user_id)
        for row in logs:
            self.recycling_tree.insert("", "end", values=(row["category"], row["weight_kg"], row["points_added"], row["logged_at"]))
        u = self.app.db.get_user(self.user_id)
        self.rewards_lbl.configure(text=f"Total Points: {u['total_points']}")

        for i in self.note_tree.get_children():
            self.note_tree.delete(i)
        for n in self.app.db.get_notifications(self.user_id):
            self.note_tree.insert("", "end", values=(n["type"], n["title"], n["message"], n["created_at"], "Yes" if n["read_at"] else "No"))

        m = self.app.db.get_dashboard_metrics()
        self.metrics_lbl.configure(text=f"Simulated metrics for prototype. Total pickups={m['pickups']} (completed={m['completed']}), Total recycled weight={m['recycled_weight']:.1f}kg, Recycling rate={m['recycling_rate']:.1f}%")

    # Collector
    def _build_collector_tabs(self):
        self.c_tab = ttk.Frame(self.content, padding=8)
        self.content.add(self.c_tab, text="Pickup Worklist")
        filters = ttk.Frame(self.c_tab)
        filters.pack(fill="x")
        ttk.Label(filters, text="Status").pack(side="left")
        self.collector_status = ttk.Combobox(filters, values=["", "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"], state="readonly", width=14)
        self.collector_status.pack(side="left", padx=4)
        self.collector_status.set("")
        ttk.Label(filters, text="Sort").pack(side="left")
        self.collector_sort = ttk.Combobox(filters, values=["requested", "created"], state="readonly", width=10)
        self.collector_sort.pack(side="left", padx=4)
        self.collector_sort.set("requested")
        ttk.Button(filters, text="Apply", command=self._refresh_collector).pack(side="left")
        ttk.Button(filters, text="Prepare Execution Order", command=self._prepare_route_order).pack(side="left", padx=8)

        self.collector_tree = ttk.Treeview(self.c_tab, columns=("order", "id", "resident", "zone", "address", "dt", "status"), show="headings", height=12)
        for c in ("order", "id", "resident", "zone", "address", "dt", "status"):
            self.collector_tree.heading(c, text=c.title())
        self.collector_tree.pack(fill="both", expand=True, pady=6)

        edit = ttk.Frame(self.c_tab)
        edit.pack(fill="x")
        self.collector_comment = ttk.Entry(edit, width=40)
        self.collector_comment.pack(side="left", padx=4)
        ttk.Button(edit, text="Evidence Image", command=self._collector_pick_evidence).pack(side="left", padx=4)
        ttk.Button(edit, text="Start", command=lambda: self._collector_update("IN_PROGRESS")).pack(side="left", padx=4)
        ttk.Button(edit, text="Complete", command=lambda: self._collector_update("COMPLETED")).pack(side="left", padx=4)
        ttk.Button(edit, text="Fail", command=lambda: self._collector_update("FAILED")).pack(side="left", padx=4)
        self.collector_evidence = ""
        self._refresh_collector()

    def _prepare_route_order(self):
        rows = self.app.db.get_collector_requests(self.user_id, self.collector_status.get().strip(), self.collector_sort.get().strip())
        ordered = sorted(rows, key=lambda r: (r["requested_datetime"], hashlib.md5((r["address"] or "x").encode()).hexdigest()))
        for i in self.collector_tree.get_children():
            self.collector_tree.delete(i)
        for idx, row in enumerate(ordered, start=1):
            self.collector_tree.insert("", "end", values=(idx, row["pickup_id"], row["resident_name"], row["zone_name"], row["address"], row["requested_datetime"], row["status"]))

    def _collector_pick_evidence(self):
        try:
            self.collector_evidence = self._upload_image()
        except Exception as exc:
            messagebox.showerror("Upload Error", str(exc))

    def _collector_update(self, status: str):
        sel = self.collector_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a pickup request.")
            return
        pickup_id = int(self.collector_tree.item(sel[0], "values")[1])
        comment = self.collector_comment.get().strip()
        if status == "FAILED" and not comment:
            messagebox.showwarning("Required", "Failure reason is required.")
            return
        try:
            self.app.db.update_pickup_status(self.user_id, pickup_id, status, comment, self.collector_evidence)
            self.collector_comment.delete(0, tk.END)
            self.collector_evidence = ""
            self._refresh_collector()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _refresh_collector(self):
        for i in self.collector_tree.get_children():
            self.collector_tree.delete(i)
        rows = self.app.db.get_collector_requests(self.user_id, self.collector_status.get().strip(), self.collector_sort.get().strip())
        for row in rows:
            self.collector_tree.insert("", "end", values=("-", row["pickup_id"], row["resident_name"], row["zone_name"], row["address"], row["requested_datetime"], row["status"]))

    # Admin
    def _build_admin_tabs(self):
        self.a_users = ttk.Frame(self.content, padding=8)
        self.a_zones = ttk.Frame(self.content, padding=8)
        self.a_assign = ttk.Frame(self.content, padding=8)
        self.a_notes = ttk.Frame(self.content, padding=8)
        self.a_monitor = ttk.Frame(self.content, padding=8)
        for tab, title in ((self.a_users, "Manage Users"), (self.a_zones, "Manage Zones"), (self.a_assign, "Collector Assignment"), (self.a_notes, "Notifications Center"), (self.a_monitor, "Monitoring")):
            self.content.add(tab, text=title)

        self.admin_user_tree = ttk.Treeview(self.a_users, columns=("id", "name", "role", "zone", "phone", "email", "active"), show="headings", height=10)
        for c in ("id", "name", "role", "zone", "phone", "email", "active"):
            self.admin_user_tree.heading(c, text=c.title())
        self.admin_user_tree.pack(fill="both", expand=True)
        f = ttk.Frame(self.a_users); f.pack(fill="x", pady=4)
        self.u = {k: ttk.Entry(f, width=14) for k in ("user_id", "password", "full_name", "telephone", "email", "address")}
        self.u["password"].configure(show="*")
        self.u_role = ttk.Combobox(f, values=["Resident", "WasteCollector", "MunicipalAdmin"], state="readonly", width=14); self.u_role.set("Resident")
        self.u_zone = ttk.Combobox(f, values=[""], state="readonly", width=14)
        for idx, key in enumerate(("user_id", "password", "full_name", "telephone", "email", "address")):
            ttk.Label(f, text=key).grid(row=0, column=idx, sticky="w"); self.u[key].grid(row=1, column=idx, padx=2)
        ttk.Label(f, text="role").grid(row=0, column=6, sticky="w"); self.u_role.grid(row=1, column=6, padx=2)
        ttk.Label(f, text="zone").grid(row=0, column=7, sticky="w"); self.u_zone.grid(row=1, column=7, padx=2)
        ttk.Button(f, text="Add", command=self._admin_add_user).grid(row=1, column=8, padx=4)
        ttk.Button(f, text="Update", command=self._admin_update_user).grid(row=1, column=9, padx=4)
        ttk.Button(f, text="Delete", command=self._admin_delete_user).grid(row=1, column=10, padx=4)

        self.zone_tree = ttk.Treeview(self.a_zones, columns=("name",), show="headings", height=10)
        self.zone_tree.heading("name", text="Zone")
        self.zone_tree.pack(fill="both", expand=True)
        zf = ttk.Frame(self.a_zones); zf.pack(fill="x", pady=4)
        self.zone_entry = ttk.Entry(zf, width=22); self.zone_entry.pack(side="left")
        ttk.Button(zf, text="Add", command=lambda: self._zone_action("add")).pack(side="left", padx=4)
        ttk.Button(zf, text="Rename", command=lambda: self._zone_action("rename")).pack(side="left", padx=4)
        ttk.Button(zf, text="Delete", command=lambda: self._zone_action("delete")).pack(side="left", padx=4)

        af = ttk.Frame(self.a_assign); af.pack(anchor="w")
        self.assign_col = ttk.Combobox(af, values=[""], state="readonly", width=20); self.assign_col.grid(row=1, column=0, padx=4)
        self.assign_zone = ttk.Combobox(af, values=[""], state="readonly", width=20); self.assign_zone.grid(row=1, column=1, padx=4)
        ttk.Label(af, text="Collector").grid(row=0, column=0, sticky="w")
        ttk.Label(af, text="Zone").grid(row=0, column=1, sticky="w")
        ttk.Button(af, text="Assign", command=self._assign_collector).grid(row=1, column=2, padx=4)

        nf = ttk.Frame(self.a_notes); nf.pack(fill="x")
        self.note_user = ttk.Entry(nf, width=12); self.note_user.grid(row=1, column=0)
        self.note_type = ttk.Combobox(nf, values=["RECYCLING_TIP", "PICKUP_REMINDER", "SYSTEM"], state="readonly", width=16); self.note_type.set("RECYCLING_TIP"); self.note_type.grid(row=1, column=1)
        self.note_title = ttk.Entry(nf, width=18); self.note_title.grid(row=1, column=2)
        self.note_msg = ttk.Entry(nf, width=40); self.note_msg.grid(row=1, column=3)
        for i,t in enumerate(("User ID","Type","Title","Message")): ttk.Label(nf,text=t).grid(row=0,column=i,sticky="w")
        ttk.Button(nf, text="Send", command=self._admin_send_notification).grid(row=1, column=4, padx=4)
        self.admin_note_tree = ttk.Treeview(self.a_notes, columns=("user", "type", "title", "message", "time"), show="headings", height=8)
        for c in ("user", "type", "title", "message", "time"): self.admin_note_tree.heading(c, text=c.title())
        self.admin_note_tree.pack(fill="both", expand=True, pady=4)

        self.monitor_lbl = ttk.Label(self.a_monitor, text="")
        self.monitor_lbl.pack(anchor="w")
        self.top_tree = ttk.Treeview(self.a_monitor, columns=("user", "name", "points"), show="headings", height=8)
        for c in ("user", "name", "points"): self.top_tree.heading(c, text=c.title())
        self.top_tree.pack(fill="both", expand=True)

        self._refresh_admin()

    def _admin_add_user(self):
        try:
            uid = validate_user_id(self.u["user_id"].get())
            pwd = validate_password(self.u["password"].get(), uid)
            self.app.db.add_user({"user_id": uid, "password": pwd, "full_name": self.u["full_name"].get().strip(), "role": self.u_role.get(), "zone": self.u_zone.get(), "telephone": self.u["telephone"].get().strip(), "email": self.u["email"].get().strip(), "address": self.u["address"].get().strip()})
            self._refresh_admin()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _admin_update_user(self):
        uid = self.u["user_id"].get().strip()
        if not uid:
            return
        updates = {"full_name": self.u["full_name"].get().strip(), "role": self.u_role.get(), "zone": self.u_zone.get(), "telephone": self.u["telephone"].get().strip(), "email": self.u["email"].get().strip(), "address": self.u["address"].get().strip()}
        if self.u["password"].get().strip():
            updates["password"] = validate_password(self.u["password"].get().strip(), uid)
        try:
            self.app.db.update_user(uid, {k: v for k, v in updates.items() if v != ""})
            self._refresh_admin()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _admin_delete_user(self):
        uid = self.u["user_id"].get().strip()
        if not uid:
            return
        if messagebox.askyesno("Confirm", f"Delete {uid}?"):
            self.app.db.delete_user(uid)
            self._refresh_admin()

    def _zone_action(self, action: str):
        try:
            zone = self.zone_entry.get().strip()
            if action == "add":
                self.app.db.create_zone(zone)
            elif action == "rename":
                sel = self.zone_tree.selection()
                old = self.zone_tree.item(sel[0], "values")[0]
                self.app.db.update_zone(old, zone)
            else:
                sel = self.zone_tree.selection()
                old = self.zone_tree.item(sel[0], "values")[0]
                self.app.db.delete_zone(old)
            self._refresh_admin()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _assign_collector(self):
        try:
            self.app.db.assign_collector_zone(self.assign_col.get(), self.assign_zone.get())
            self._refresh_admin()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _admin_send_notification(self):
        try:
            self.app.db.add_notification(self.note_user.get().strip(), self.note_type.get(), self.note_title.get().strip(), self.note_msg.get().strip())
            self._refresh_admin()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _refresh_admin(self):
        for i in self.admin_user_tree.get_children(): self.admin_user_tree.delete(i)
        users = self.app.db.list_users("name")
        for u in users:
            self.admin_user_tree.insert("", "end", values=(u["user_id"], u["name"] or "", u["role"], u["zone"], u["phone"] or "", u["email"] or "", "Yes" if u["is_active"] else "No"))

        for i in self.zone_tree.get_children(): self.zone_tree.delete(i)
        zones = [z["name"] for z in self.app.db.list_zones()]
        for z in zones: self.zone_tree.insert("", "end", values=(z,))
        self.u_zone.configure(values=[""] + zones)

        collectors = [u["user_id"] for u in users if u["role"] == "WasteCollector"]
        self.assign_col.configure(values=collectors)
        self.assign_zone.configure(values=zones)

        for i in self.admin_note_tree.get_children(): self.admin_note_tree.delete(i)
        for n in self.app.db.get_admin_notifications():
            self.admin_note_tree.insert("", "end", values=(n["user_id"], n["type"], n["title"], n["message"], n["created_at"]))

        stats = self.app.db.get_admin_stats()
        self.monitor_lbl.configure(text=f"Total Users={stats['users']} | Pickups P/I/C/F={stats['PENDING']}/{stats['IN_PROGRESS']}/{stats['COMPLETED']}/{stats['FAILED']} | Recycled Weight={stats['recycling_weight']:.1f}kg")
        for i in self.top_tree.get_children(): self.top_tree.delete(i)
        for row in self.app.db.get_top_recyclers():
            self.top_tree.insert("", "end", values=(row["user_id"], row["name"] or "", row["total_points"]))

    def refresh_ui(self):
        super().refresh_ui()
        th = self.app.theme
        self.wrap.configure(bg=th["bg"])
        self.title_lbl.configure(text=f"Dashboard ({self.user_id})", bg=th["bg"], fg=th["text"])
        self.sub_lbl.configure(text=f"Role: {self.user['role']}", bg=th["bg"], fg=th["muted"])
        self.logout_btn.configure(text=self.app.translate("logout"), bg=th["primary_bg"], fg=th["primary_fg"], activebackground=th["primary_bg"])
