import tkinter as tk
from tkinter import ttk


class BaseScreen(tk.Frame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.widgets = []

    def add_top_bar(self, back_command=None):
        bar = tk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        bar.grid_columnconfigure(2, weight=1)

        self.back_btn = None
        if back_command is not None:
            self.back_btn = tk.Button(bar, text="← Back", command=back_command, bd=0, cursor="hand2", padx=10, pady=4)
            self.back_btn.grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.theme_btn = tk.Button(bar, command=self.app.toggle_theme, bd=0, cursor="hand2")
        self.theme_btn.grid(row=0, column=1, sticky="w")

        self.logo_lbl = tk.Label(bar, text="♻️", font=("Segoe UI Emoji", 24))
        self.logo_lbl.grid(row=0, column=2)

        self.lang_btn = ttk.Menubutton(bar, text="🌍")
        self.lang_menu = tk.Menu(self.lang_btn, tearoff=0)
        self.lang_btn.configure(menu=self.lang_menu)
        self.lang_btn.grid(row=0, column=3, sticky="e")
        self.lang_menu.add_command(label="English", command=lambda: self.app.set_language("en"))
        self.lang_menu.add_command(label="Malay", command=lambda: self.app.set_language("ms"))

        self.widgets.extend([bar, self.theme_btn, self.logo_lbl])

    def style_entry(self, entry: tk.Entry, error: bool = False):
        theme = self.app.theme
        border = "#D64545" if error else theme["border"]
        entry.configure(
            bg=theme["entry_bg"],
            fg=theme["entry_fg"],
            insertbackground=theme["entry_fg"],
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=border,
            relief="flat",
        )

    def refresh_ui(self):
        theme = self.app.theme
        self.configure(bg=theme["bg"])
        if self.back_btn is not None:
            self.back_btn.configure(bg=theme["secondary_bg"], fg=theme["secondary_fg"], activebackground=theme["secondary_bg"])
        self.theme_btn.configure(text=theme["icon"], bg=theme["bg"], fg=theme["text"], activebackground=theme["bg"])
        self.logo_lbl.configure(bg=theme["bg"], fg=theme["text"])
