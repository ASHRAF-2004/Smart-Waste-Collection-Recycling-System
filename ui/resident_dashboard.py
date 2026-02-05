import tkinter as tk
from tkinter import ttk, messagebox

from ui.common_widgets import handle_action, guarded_button_call


class ResidentDashboard(ttk.Frame):
    def __init__(self, master, app, user):
        super().__init__(master, padding=10)
        self.app = app
        self.user = user
        self.grid(sticky="nsew")

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text=f"Resident Dashboard - {user['name']} (ID {user['user_id']})", font=("Arial", 13, "bold")).pack(side="left")
        ttk.Button(header, text="Refresh Profile", command=self.refresh_user).pack(side="left", padx=8)
        ttk.Button(header, text="Logout", command=self.app.show_login).pack(side="right")

        self.points_var = tk.StringVar(value=f"Total Points: {user['total_points']}")
        ttk.Label(self, textvariable=self.points_var, font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w", pady=5)

        nb = ttk.Notebook(self)
        nb.grid(row=2, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_pickups_tab(nb)
        self._build_recycling_tab(nb)
        self._build_notifications_tab(nb)

        self.refresh_all()

    def refresh_user(self):
        self.user = self.app.user_dao.get_by_id(self.user["user_id"])
        self.points_var.set(f"Total Points: {self.user['total_points']}")

    def _build_pickups_tab(self, nb):
        tab = ttk.Frame(nb, padding=8)
        nb.add(tab, text="Pickup Requests")

        form = ttk.Frame(tab)
        form.pack(fill="x")
        ttk.Label(form, text="Requested datetime (ISO)").pack(side="left")
        self.pickup_dt = ttk.Entry(form, width=28)
        self.pickup_dt.pack(side="left", padx=5)
        create_btn = ttk.Button(form, text="Create Pickup Request")
        create_btn.pack(side="left")
        create_btn.configure(command=guarded_button_call(create_btn, self.create_pickup))

        self.pickup_tree = ttk.Treeview(tab, columns=("id", "dt", "status"), show="headings", height=8)
        for c, t in [("id", "Pickup ID"), ("dt", "Requested Datetime"), ("status", "Status")]:
            self.pickup_tree.heading(c, text=t)
        self.pickup_tree.pack(fill="both", expand=True, pady=8)

        hist_btn = ttk.Button(tab, text="View Status History", command=self.show_pickup_history)
        hist_btn.pack(anchor="w")

    def _build_recycling_tab(self, nb):
        tab = ttk.Frame(nb, padding=8)
        nb.add(tab, text="Recycling")

        form = ttk.Frame(tab)
        form.pack(fill="x")
        ttk.Label(form, text="Category").grid(row=0, column=0)
        ttk.Label(form, text="Weight (kg)").grid(row=0, column=1)
        ttk.Label(form, text="Waste image path (optional)").grid(row=0, column=2)
        self.category_entry = ttk.Entry(form, width=20)
        self.weight_entry = ttk.Entry(form, width=12)
        self.waste_img_entry = ttk.Entry(form, width=25)
        self.category_entry.grid(row=1, column=0, padx=3)
        self.weight_entry.grid(row=1, column=1, padx=3)
        self.waste_img_entry.grid(row=1, column=2, padx=3)

        submit_btn = ttk.Button(form, text="Submit Recycling Log")
        submit_btn.grid(row=1, column=3, padx=3)
        submit_btn.configure(command=guarded_button_call(submit_btn, self.submit_recycling))

        self.recycling_tree = ttk.Treeview(tab, columns=("id", "cat", "wt", "at"), show="headings", height=10)
        for c, t in [("id", "Log ID"), ("cat", "Category"), ("wt", "Weight"), ("at", "Logged At")]:
            self.recycling_tree.heading(c, text=t)
        self.recycling_tree.pack(fill="both", expand=True, pady=8)

    def _build_notifications_tab(self, nb):
        tab = ttk.Frame(nb, padding=8)
        nb.add(tab, text="Notifications")

        self.note_tree = ttk.Treeview(tab, columns=("id", "title", "created", "read"), show="headings", height=12)
        for c, t in [("id", "ID"), ("title", "Title"), ("created", "Created"), ("read", "Read At")]:
            self.note_tree.heading(c, text=t)
        self.note_tree.pack(fill="both", expand=True)

        ttk.Button(tab, text="Mark Selected Read", command=self.mark_read).pack(anchor="w", pady=5)

    def refresh_all(self):
        self.refresh_user()
        self.refresh_pickups()
        self.refresh_recycling()
        self.refresh_notifications()

    def refresh_pickups(self):
        for i in self.pickup_tree.get_children():
            self.pickup_tree.delete(i)
        rows = handle_action(self, lambda: self.app.pickup_service.get_resident_requests(self.user))
        if rows:
            for r in rows:
                self.pickup_tree.insert("", "end", values=(r["pickup_id"], r["requested_datetime"], r["status"]))

    def refresh_recycling(self):
        for i in self.recycling_tree.get_children():
            self.recycling_tree.delete(i)
        rows = handle_action(self, lambda: self.app.recycling_service.get_history(self.user))
        if rows:
            for r in rows:
                self.recycling_tree.insert("", "end", values=(r["log_id"], r["category"], r["weight_kg"], r["logged_at"]))

    def refresh_notifications(self):
        for i in self.note_tree.get_children():
            self.note_tree.delete(i)
        rows = handle_action(self, lambda: self.app.notification_service.list_my_notifications(self.user))
        if rows:
            for r in rows:
                self.note_tree.insert("", "end", values=(r["notification_id"], r["title"], r["created_at"], r["read_at"] or "UNREAD"))

    def create_pickup(self):
        result = handle_action(self, lambda: self.app.pickup_service.create_pickup_request(self.user, self.pickup_dt.get()))
        if result:
            messagebox.showinfo("Success", f"Pickup request {result} created.")
            self.refresh_pickups()

    def show_pickup_history(self):
        sel = self.pickup_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a pickup request first.")
            return
        pickup_id = self.pickup_tree.item(sel[0], "values")[0]
        rows = handle_action(self, lambda: self.app.pickup_service.get_status_history(pickup_id))
        if rows is None:
            return
        history = "\n".join([f"{r['timestamp']} - {r['new_status']} by {r['collector_name']} ({r['comment'] or ''})" for r in rows])
        messagebox.showinfo("Status History", history or "No status updates yet.")

    def submit_recycling(self):
        points = handle_action(
            self,
            lambda: self.app.recycling_service.submit_recycling_log(
                self.user, self.category_entry.get(), self.weight_entry.get(), self.waste_img_entry.get()
            ),
        )
        if points is not None:
            messagebox.showinfo("Success", f"Recycling submitted. Points added: {points}")
            self.refresh_user()
            self.refresh_recycling()

    def mark_read(self):
        sel = self.note_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a notification first.")
            return
        note_id = self.note_tree.item(sel[0], "values")[0]
        done = handle_action(self, lambda: self.app.notification_service.mark_read(self.user, note_id), "Marked as read")
        if done is None:
            self.refresh_notifications()
