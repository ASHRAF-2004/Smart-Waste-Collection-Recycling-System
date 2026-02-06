"""Common UI helpers."""
import tkinter as tk
from tkinter import messagebox, ttk

from utils.errors import AppError


class ScrollableFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)


def handle_action(root, action, success_message=None):
    try:
        result = action()
        if success_message:
            messagebox.showinfo("Success", success_message)
        return result
    except (AppError, ValueError) as exc:
        messagebox.showerror("Error", str(exc))
    except Exception as exc:
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
