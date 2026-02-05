"""App entry for Smart Waste Collection and Recycling System prototype."""
import tkinter as tk
from tkinter import ttk
from db.database import Database
from dao.user_dao import UserDAO
from dao.zone_dao import ZoneDAO
from dao.pickup_request_dao import PickupRequestDAO
from dao.pickup_status_update_dao import PickupStatusUpdateDAO
from dao.recycling_log_dao import RecyclingLogDAO
from dao.notification_dao import NotificationDAO

from services.auth_service import AuthService
from services.pickup_service import PickupService
from services.recycling_service import RecyclingService
from services.notification_service import NotificationService
from services.admin_service import AdminService

from ui.login_window import LoginWindow
from ui.resident_dashboard import ResidentDashboard
from ui.collector_dashboard import CollectorDashboard
from ui.admin_dashboard import AdminDashboard
from ui import sv_ttk


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Waste Collection and Recycling System")
        self.geometry("1100x700")

        self.style = ttk.Style(self)
        self._init_theme(default_mode="light")

        self.db = Database()
        self.db.init_schema_and_seed()

        self.user_dao = UserDAO(self.db)
        self.zone_dao = ZoneDAO(self.db)
        self.pickup_dao = PickupRequestDAO(self.db)
        self.status_dao = PickupStatusUpdateDAO(self.db)
        self.recycling_dao = RecyclingLogDAO(self.db)
        self.notification_dao = NotificationDAO(self.db)

        self.auth_service = AuthService(self.user_dao)
        self.pickup_service = PickupService(self.db, self.pickup_dao, self.status_dao, self.auth_service)
        self.recycling_service = RecyclingService(self.db, self.recycling_dao, self.user_dao, self.auth_service)
        self.notification_service = NotificationService(self.notification_dao, self.auth_service)
        self.admin_service = AdminService(self.db, self.user_dao, self.zone_dao, self.auth_service)

        self.current = None
        self.show_login()

    def _init_theme(self, default_mode="light"):
        """Load and apply Sun Valley theme so every ttk screen inherits it."""
        sv_ttk.set_theme(default_mode, root=self)

    def set_theme_mode(self, mode):
        """Allow runtime switch between light/dark modes when needed."""
        if mode in {"light", "dark"}:
            sv_ttk.set_theme(mode, root=self)

    def clear_current(self):
        if self.current is not None:
            self.current.destroy()

    def show_login(self):
        self.clear_current()
        self.current = LoginWindow(self, self)

    def open_dashboard(self, user):
        self.clear_current()
        if user["role"] == "Resident":
            self.current = ResidentDashboard(self, self, user)
        elif user["role"] == "WasteCollector":
            self.current = CollectorDashboard(self, self, user)
        elif user["role"] == "MunicipalAdmin":
            self.current = AdminDashboard(self, self, user)


if __name__ == "__main__":
    app = App()
    app.mainloop()
