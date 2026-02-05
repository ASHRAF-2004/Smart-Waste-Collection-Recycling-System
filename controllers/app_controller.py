"""Navigation controller and app state."""
import tkinter as tk
from tkinter import messagebox

from database.sqlite_service import SQLiteService
from services.i18n_service import t
from services.theme_service import THEMES
from services.validation_service import validate_login, validate_registration_form
from ui.login_screen import LoginScreen
from ui.registration_screen import RegistrationScreen
from ui.filling_info_screen import FillingInfoScreen
from ui.congrats_screen import CongratsScreen
from ui.dashboard_screen import DashboardScreen


class SmartWasteApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Waste Collection and Recycling System")
        self.geometry("980x700")
        self.minsize(860, 620)

        self.language = "en"
        self.theme_mode = "light"
        self.current_frame = None
        self.pending_user = {}

        self.db = SQLiteService()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.center_window()
        self.show_login()

    def center_window(self):
        self.update_idletasks()
        width, height = 980, 700
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    @property
    def theme(self):
        return THEMES[self.theme_mode]

    def translate(self, key: str) -> str:
        return t(self.language, key)

    def set_language(self, language: str):
        self.language = language
        if self.current_frame:
            self.current_frame.refresh_ui()

    def toggle_theme(self):
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
        if self.current_frame:
            self.current_frame.refresh_ui()

    def navigate(self, frame_cls, **kwargs):
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_cls(self, self, **kwargs)
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.refresh_ui()

    def show_login(self):
        self.pending_user = {}
        self.navigate(LoginScreen)

    def show_registration(self):
        self.navigate(RegistrationScreen)

    def show_filling_info(self):
        self.navigate(FillingInfoScreen)

    def show_congrats(self, user_id: str):
        self.navigate(CongratsScreen, user_id=user_id)

    def show_dashboard(self, user_id: str):
        self.navigate(DashboardScreen, user_id=user_id)

    def submit_login(self, user_id: str, password: str):
        try:
            uid, pwd = validate_login(user_id, password)
            if not self.db.verify_credentials(uid, pwd):
                raise ValueError("Invalid credentials.")
            self.show_dashboard(uid)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))

    def save_registration_step1(self, user_id: str, password: str):
        try:
            uid, pwd = validate_login(user_id, password)
            self.db.create_basic_user(uid, pwd)
            self.pending_user = {"user_id": uid, "password": pwd}
            self.show_filling_info()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))

    def save_registration_step2(self, form_data: dict):
        try:
            payload = validate_registration_form({**self.pending_user, **form_data})
            self.db.complete_profile(payload)
            self.show_congrats(payload["user_id"])
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
