"""Navigation controller and app state."""
import logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from database.sqlite_service import SQLiteService
from services.i18n_service import t
from services.theme_service import THEMES
from services.validation_service import (
    validate_filling_info,
    validate_login,
    validate_registration_step1,
)
from ui.congrats_screen import CongratsScreen
from ui.dashboard_screen import DashboardScreen
from ui.filling_info_screen import FillingInfoScreen
from ui.login_screen import LoginScreen
from ui.registration_screen import RegistrationScreen

Path("logs").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
        self.nav_stack = []

        try:
            self.db = SQLiteService()
        except ValueError as exc:
            messagebox.showerror("Database Error", str(exc))
            self.destroy()
            raise

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


        try:
            from ui import sv_ttk
            sv_ttk.set_theme("light")
        except Exception:
            pass

        self.center_window()
        self.show_screen("Login")

    def center_window(self):
        self.update_idletasks()
        width, height = 980, 700
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    @property
    def theme(self):
        return THEMES[self.theme_mode]

    def translate(self, key: str, **kwargs) -> str:
        msg = t(self.language, key)
        return msg.format(**kwargs) if kwargs else msg

    def set_language(self, language: str):
        self.language = language
        if self.current_frame:
            self.current_frame.refresh_ui()

    def toggle_theme(self):
        self.theme_mode = "dark" if self.theme_mode == "light" else "light"
        try:
            from ui import sv_ttk
            sv_ttk.set_theme("dark" if self.theme_mode == "dark" else "light")
        except Exception:
            pass
        if self.current_frame:
            self.current_frame.refresh_ui()

    def navigate(self, frame_cls, track_history: bool = True, **kwargs):
        if self.current_frame is not None:
            if track_history:
                self.nav_stack.append((self.current_frame.__class__, getattr(self.current_frame, "screen_kwargs", {})))
            self.current_frame.destroy()
        self.current_frame = frame_cls(self, self, **kwargs)
        self.current_frame.screen_kwargs = kwargs
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.refresh_ui()

    def go_back(self):
        if not self.nav_stack:
            return
        frame_cls, kwargs = self.nav_stack.pop()
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame_cls(self, self, **kwargs)
        self.current_frame.screen_kwargs = kwargs
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.refresh_ui()

    def show_screen(self, name: str, **kwargs):
        routes = {
            "Login": LoginScreen,
            "Registration": RegistrationScreen,
            "FillingInfo": FillingInfoScreen,
            "Congrats": CongratsScreen,
            "Dashboard": DashboardScreen,
        }
        if name == "FillingInfo" and not self.pending_user.get("user_id"):
            messagebox.showwarning("Step Required", "Please complete registration details first.")
            name = "Registration"
        if name == "Login":
            self.pending_user = {}
            self.nav_stack = []
        frame_cls = routes[name]
        self.navigate(frame_cls, **kwargs)

    def submit_login(self, user_id: str, password: str):
        try:
            uid, pwd = validate_login(user_id, password)
            ok, status = self.db.verify_credentials(uid, pwd)
            if not ok:
                if status == "locked":
                    raise ValueError(self.translate("account_locked", minutes=10))
                if status and status.startswith("attempts_left:"):
                    left = status.split(":", 1)[1]
                    raise ValueError(self.translate("login_failed_attempts", count=left))
                raise ValueError("Invalid User ID or Password.")
            self.show_screen("Dashboard", user_id=status)
        except ValueError as exc:
            logger.info("Login failed for user_id=%s: %s", user_id, exc)
            messagebox.showerror("Error", str(exc))
        except Exception:
            logger.exception("Unexpected login error")
            messagebox.showerror("Error", "Unexpected error during login.")

    def save_registration_step1(self, user_id: str, password: str, confirm_password: str):
        try:
            uid, pwd = validate_registration_step1(user_id, password, confirm_password)
            self.db.create_basic_user(uid, pwd)
            self.pending_user = {"user_id": uid}
            self.show_screen("FillingInfo")
        except ValueError as exc:
            logger.info("Registration step1 failed for user_id=%s: %s", user_id, exc)
            messagebox.showerror("Error", self.translate(str(exc)) if str(exc).startswith("error_") else str(exc))

    def save_registration_step2(self, form_data: dict):
        try:
            if not self.pending_user.get("user_id"):
                raise ValueError("Registration session expired. Please start again from User Registration.")
            profile = validate_filling_info(form_data)
            payload = {**self.pending_user, **profile}
            self.db.complete_profile(payload)
            self.show_screen("Congrats", user_id=payload["user_id"])
        except ValueError as exc:
            logger.info("Registration step2 failed: %s", exc)
            messagebox.showerror("Error", self.translate(str(exc)) if str(exc).startswith("error_") else str(exc))
        except Exception:
            logger.exception("Unexpected registration error")
            messagebox.showerror("Error", "Unable to complete registration.")
