"""Common UI helpers."""
import tkinter as tk
from tkinter import messagebox

from utils.errors import AppError


def handle_action(root, action, success_message=None):
    try:
        result = action()
        if success_message:
            messagebox.showinfo("Success", success_message)
        return result
    except AppError as exc:
        messagebox.showerror("Error", str(exc))
    except Exception as exc:  # defensive guard for live demo stability
        print(f"[UNEXPECTED] {exc}")
        messagebox.showerror("Error", "Unexpected system error occurred.")
    finally:
        root.update_idletasks()


def guarded_button_call(btn: tk.Widget, callback):
    def _run():
        btn.config(state="disabled")
        try:
            callback()
        finally:
            btn.config(state="normal")
    return _run
