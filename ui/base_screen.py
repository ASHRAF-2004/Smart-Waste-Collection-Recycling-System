import tkinter as tk
from tkinter import ttk


class BaseScreen(tk.Frame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.widgets = []

    def add_top_bar(self):
        bar = tk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        bar.grid_columnconfigure(1, weight=1)

        self.theme_btn = tk.Button(bar, command=self.app.toggle_theme, bd=0, cursor="hand2")
        self.theme_btn.grid(row=0, column=0, sticky="w")

        self.logo_lbl = tk.Label(bar, text="♻️", font=("Segoe UI Emoji", 24))
        self.logo_lbl.grid(row=0, column=1)

        self.lang_btn = ttk.Menubutton(bar, text="🌍")
        self.lang_menu = tk.Menu(self.lang_btn, tearoff=0)
        self.lang_btn.configure(menu=self.lang_menu)
        self.lang_btn.grid(row=0, column=2, sticky="e")
        self.lang_menu.add_command(label="English", command=lambda: self.app.set_language("en"))
        self.lang_menu.add_command(label="Malay", command=lambda: self.app.set_language("ms"))

        self.widgets.extend([bar, self.theme_btn, self.logo_lbl])

    def style_entry(self, entry: tk.Entry):
        theme = self.app.theme
        entry.configure(
            bg=theme["entry_bg"],
            fg=theme["entry_fg"],
            insertbackground=theme["entry_fg"],
            highlightthickness=1,
            highlightbackground=theme["border"],
            highlightcolor=theme["border"],
            relief="flat",
        )

    def refresh_ui(self):
        theme = self.app.theme
        self.configure(bg=theme["bg"])
        self.theme_btn.configure(text=theme["icon"], bg=theme["bg"], fg=theme["text"], activebackground=theme["bg"])
        self.logo_lbl.configure(bg=theme["bg"], fg=theme["text"])
