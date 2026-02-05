from tkinter import ttk, messagebox

from ui.common_widgets import handle_action, guarded_button_call


class CollectorDashboard(ttk.Frame):
    def __init__(self, master, app, user):
        super().__init__(master, padding=10)
        self.app = app
        self.user = user
        self.grid(sticky="nsew")

        head = ttk.Frame(self)
        head.pack(fill="x")
        ttk.Label(head, text=f"Collector Dashboard - {user['name']} (Zone {user['zone_id']})", font=("Arial", 13, "bold")).pack(side="left")
        ttk.Button(head, text="Logout", command=self.app.show_login).pack(side="right")

        self.tree = ttk.Treeview(self, columns=("id", "resident", "dt", "status"), show="headings", height=12)
        for c, t in [("id", "Pickup ID"), ("resident", "Resident"), ("dt", "Requested"), ("status", "Status")]:
            self.tree.heading(c, text=t)
        self.tree.pack(fill="both", expand=True, pady=8)

        frm = ttk.Frame(self)
        frm.pack(fill="x")
        ttk.Label(frm, text="New Status").grid(row=0, column=0)
        self.status_combo = ttk.Combobox(frm, values=["COMPLETED", "FAILED"], state="readonly", width=12)
        self.status_combo.grid(row=0, column=1, padx=4)
        self.status_combo.current(0)
        ttk.Label(frm, text="Comment").grid(row=0, column=2)
        self.comment_entry = ttk.Entry(frm, width=26)
        self.comment_entry.grid(row=0, column=3, padx=4)
        ttk.Label(frm, text="Evidence image (optional)").grid(row=0, column=4)
        self.evidence_entry = ttk.Entry(frm, width=25)
        self.evidence_entry.grid(row=0, column=5, padx=4)

        update_btn = ttk.Button(frm, text="Update Status")
        update_btn.grid(row=0, column=6, padx=4)
        update_btn.configure(command=guarded_button_call(update_btn, self.update_status))

        ttk.Button(frm, text="View Selected History", command=self.show_history).grid(row=0, column=7, padx=4)
        ttk.Button(frm, text="Refresh", command=self.refresh).grid(row=0, column=8, padx=4)

        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = handle_action(self, lambda: self.app.pickup_service.get_collector_requests(self.user))
        if rows:
            for r in rows:
                self.tree.insert("", "end", values=(r["pickup_id"], r["resident_name"], r["requested_datetime"], r["status"]))

    def update_status(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a pickup request first.")
            return
        pickup_id = self.tree.item(sel[0], "values")[0]
        done = handle_action(
            self,
            lambda: self.app.pickup_service.update_pickup_status(
                self.user,
                pickup_id,
                self.status_combo.get(),
                self.comment_entry.get(),
                self.evidence_entry.get(),
            ),
            "Pickup status updated",
        )
        if done is None:
            self.refresh()

    def show_history(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a pickup request first.")
            return
        pickup_id = self.tree.item(sel[0], "values")[0]
        rows = handle_action(self, lambda: self.app.pickup_service.get_status_history(pickup_id))
        if rows is None:
            return
        history = "\n".join([f"{r['timestamp']} - {r['new_status']} by {r['collector_name']} ({r['comment'] or ''})" for r in rows])
        messagebox.showinfo("Status History", history or "No history.")
