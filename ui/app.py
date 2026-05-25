"""Główny kontroler aplikacji — rejestracja stron, nawigacja, skróty."""

import customtkinter as ctk

import vetchain_chain as db

from .breeder import ScreenHodowca, ScreenHodowcaDodaj, ScreenHodowcaProfil
from .buyer import ScreenKupujacy
from .login import ScreenLogin
from .owner import ScreenWlasciciel
from .shelter import (
    ScreenSchronisko,
    ScreenSchroniskoDodaj,
    ScreenSchroniskoProfil,
)
from .vet import (
    ScreenWeterynarzCzipowanie,
    ScreenWeterynarzDodaj,
    ScreenWeterynarzMain,
    ScreenWeterynarzUzupelnij,
)


class VetChainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VetChain - Zdecentralizowana Karta Zdrowia Zwierząt")
        self.geometry("1440x900")
        self.minsize(1000, 700)
        self.resizable(True, True)

        self.attributes("-fullscreen", False)
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

        self.container = ctk.CTkFrame(self, fg_color="#a3aea3")
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Stan dzielony pomiędzy ekranami
        self.current_actor = None
        self.current_animal_chip = None
        self.pending_reveal_id = None

        self.pages = {
            "ScreenLogin": ScreenLogin,
            "ScreenWeterynarzMain": ScreenWeterynarzMain,
            "ScreenWeterynarzDodaj": ScreenWeterynarzDodaj,
            "ScreenWeterynarzUzupelnij": ScreenWeterynarzUzupelnij,
            "ScreenWeterynarzCzipowanie": ScreenWeterynarzCzipowanie,
            "ScreenHodowca": ScreenHodowca,
            "ScreenHodowcaDodaj": ScreenHodowcaDodaj,
            "ScreenHodowcaProfil": ScreenHodowcaProfil,
            "ScreenSchronisko": ScreenSchronisko,
            "ScreenSchroniskoDodaj": ScreenSchroniskoDodaj,
            "ScreenSchroniskoProfil": ScreenSchroniskoProfil,
            "ScreenWlasciciel": ScreenWlasciciel,
            "ScreenKupujacy": ScreenKupujacy,
        }

        self.current_frame = None
        self.show_frame("ScreenLogin")

    def show_frame(self, page_name: str) -> None:
        if page_name == "ScreenLogin":
            db.clear_session()
            self.current_actor = None
            self.current_animal_chip = None
            self.pending_reveal_id = None

        if self.current_frame is not None:
            self.current_frame.destroy()

        frame_class = self.pages[page_name]
        self.current_frame = frame_class(parent=self.container, controller=self)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def toggle_fullscreen(self, _event=None):
        is_full = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_full)

    def exit_fullscreen(self, _event=None):
        self.attributes("-fullscreen", False)
