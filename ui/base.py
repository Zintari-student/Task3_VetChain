"""Wspólna klasa bazowa ekranu — grid 3-rzędowy (nagłówek/tytuł/treść)."""

import customtkinter as ctk


class BaseScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.wrapper = ctk.CTkFrame(self, fg_color="transparent")
        self.wrapper.pack(fill="both", expand=True, padx=50, pady=(50, 80))

        self.panel = ctk.CTkFrame(self.wrapper, corner_radius=20, fg_color="#b4beb4")
        self.panel.pack(fill="both", expand=True)

        self.panel.grid_columnconfigure(0, weight=1)
        self.panel.grid_rowconfigure(0, weight=0)
        self.panel.grid_rowconfigure(1, weight=0)
        self.panel.grid_rowconfigure(2, weight=1)

        self.header = ctk.CTkFrame(self.panel, fg_color="transparent", height=50)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header.grid_columnconfigure(0, weight=1)
        self.btn_nav = ctk.CTkButton(self.header, width=90, fg_color="#333333", hover_color="#1a1a1a")
        self.lbl_info = ctk.CTkLabel(self.header, font=ctk.CTkFont(weight="bold"))

        self.lbl_page_title = ctk.CTkLabel(self.panel, font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_page_title.grid(row=1, column=0, pady=(10, 20))

    def setup_header(self, btn_text=None, btn_cmd=None, info_text=None, title=None):
        if btn_text and btn_cmd:
            self.btn_nav.configure(text=btn_text, command=btn_cmd)
            self.btn_nav.grid(row=0, column=0, sticky="w")
        else:
            self.btn_nav.grid_forget()

        if info_text:
            self.lbl_info.configure(text=info_text)
            self.lbl_info.grid(row=0, column=1, sticky="e")
        else:
            self.lbl_info.grid_forget()

        if title:
            self.lbl_page_title.configure(text=title)
        else:
            self.lbl_page_title.grid_forget()
