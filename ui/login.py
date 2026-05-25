"""Ekran logowania — wybór roli, walidacja klucza przez DB."""

from tkinter import messagebox

import customtkinter as ctk

import vetchain_db as db

from .base import BaseScreen


DEMO_KEYS = [
    ("🩺 Weterynarz", "0xWET_9921_KILW"),
    ("🏠 Hodowca", "0xHOD_8821_ZKWP"),
    ("🐾 Schronisko", "0xSCHR_1102_GOV"),
    ("👤 Właściciel", "0xOWN_9912_USER"),
    ("🔍 Kupujący", "0xBUY_5532_VIEW"),
]


class ScreenLogin(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.setup_header(title="VetChain System")

        login_content = ctk.CTkFrame(self.panel, fg_color="transparent")
        login_content.grid(row=2, column=0, sticky="nsew", pady=20)
        login_content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(login_content, text="Wprowadź swój Kryptograficzny Klucz Prywatny:",
                     font=ctk.CTkFont(size=14)).pack(pady=5)

        self.entry_key = ctk.CTkEntry(login_content,
                                       placeholder_text="Wpisz lub wklej klucz (np. 0x71C7...)",
                                       width=600, height=45)
        self.entry_key.pack(pady=15)

        ctk.CTkButton(login_content, text="🔓 Autoryzuj i Wejdź do Systemu",
                      width=300, height=50, font=ctk.CTkFont(size=15, weight="bold"),
                      command=self.validate_and_login).pack(pady=25)

        ctk.CTkFrame(login_content, height=2, width=600, fg_color="#a3aea3").pack(pady=30)

        ctk.CTkLabel(login_content, text="Szybkie uzupełnianie kluczy (Demo):",
                     font=ctk.CTkFont(size=12), text_color="#1c2826").pack(pady=5)

        demo_buttons_frame = ctk.CTkFrame(login_content, fg_color="transparent")
        demo_buttons_frame.pack(pady=(5, 20))

        for text, key in DEMO_KEYS:
            ctk.CTkButton(demo_buttons_frame, text=text, width=120, height=30,
                          command=lambda k=key: self.inject_key(k)).pack(side="left", padx=5)

    def inject_key(self, key_to_paste):
        self.entry_key.delete(0, "end")
        self.entry_key.insert(0, key_to_paste)

    def validate_and_login(self):
        entered_key = self.entry_key.get().strip()
        if not entered_key:
            messagebox.showwarning("Błąd autoryzacji",
                                   "Klucz prywatny węzła nie może być pusty!")
            return

        actor = db.lookup_actor(entered_key)
        if not actor:
            messagebox.showerror(
                "Odrzucono przez sieć",
                f"Klucz {entered_key} nie figuruje w żadnym rejestrze VetChain.\n"
                "Podpis cyfrowy nie został zweryfikowany."
            )
            return

        if actor["role"] == db.ROLE_VET and not actor.get("signed_by_izba"):
            messagebox.showerror(
                "Łańcuch zaufania",
                "Klucz weterynarza nie posiada podpisu Krajowej Izby (KILW).\n"
                "Smart kontrakt zablokuje wpisy."
            )
            return

        if actor["role"] == db.ROLE_BREEDER and not actor.get("registered"):
            messagebox.showerror(
                "Status hodowli",
                "Hodowla nie posiada aktywnego statusu w związku kynologicznym (ZKwP/PKR)."
            )
            return

        role_target = {
            db.ROLE_VET: "ScreenWeterynarzMain",
            db.ROLE_BREEDER: "ScreenHodowca",
            db.ROLE_SHELTER: "ScreenSchronisko",
            db.ROLE_OWNER: "ScreenWlasciciel",
        }
        if "BUY" in entered_key:
            target = "ScreenKupujacy"
        else:
            target = role_target[actor["role"]]

        self.controller.current_actor = actor
        messagebox.showinfo(
            "Autentykacja Blockchain",
            f"Podpis cyfrowy dla węzła:\n{actor['name']} ({entered_key})\n"
            f"Rola: {actor['role']}\n"
            "Zweryfikowano pomyślnie."
        )
        self.controller.show_frame(target)
