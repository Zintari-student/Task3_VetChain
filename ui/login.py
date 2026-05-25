"""Ekran logowania — wpisanie hex priv key, weryfikacja podpisu, set_session_key."""

from tkinter import messagebox

import customtkinter as ctk

import vetchain_chain as db
from vetchain_chain import keys
from vetchain_chain.seed import load_demo_keys

from .base import BaseScreen


DEMO_LABELS = [
    ("🩺 Weterynarz",       "vet_anna"),
    ("🩺 Weterynarz (2)",   "vet_piotr"),
    ("🏠 Hodowca",          "breeder_gorska"),
    ("🐾 Schronisko",       "shelter_centrum"),
    ("👤 Właściciel",       "owner_jan"),
    ("🔍 Kupujący",         "buyer_maria"),
]


class ScreenLogin(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.setup_header(title="VetChain System")

        login_content = ctk.CTkFrame(self.panel, fg_color="transparent")
        login_content.grid(row=2, column=0, sticky="nsew", pady=20)
        login_content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(login_content,
                     text="Wprowadź swój kryptograficzny klucz prywatny (64-znakowy hex secp256k1):",
                     font=ctk.CTkFont(size=14)).pack(pady=5)

        self.entry_key = ctk.CTkEntry(login_content,
                                       placeholder_text="np. 7d8f9a... (64 znaki hex)",
                                       width=720, height=45)
        self.entry_key.pack(pady=15)

        ctk.CTkButton(login_content, text="🔓 Podpisz i Wejdź do Systemu",
                      width=300, height=50, font=ctk.CTkFont(size=15, weight="bold"),
                      command=self.validate_and_login).pack(pady=25)

        ctk.CTkFrame(login_content, height=2, width=600, fg_color="#a3aea3").pack(pady=30)

        ctk.CTkLabel(login_content,
                     text="Szybkie wstrzykiwanie kluczy demo (.demo_keys/):",
                     font=ctk.CTkFont(size=12), text_color="#1c2826").pack(pady=5)

        demo_buttons_frame = ctk.CTkFrame(login_content, fg_color="transparent")
        demo_buttons_frame.pack(pady=(5, 20))

        self.demo_keys = load_demo_keys()
        for text, label in DEMO_LABELS:
            ctk.CTkButton(demo_buttons_frame, text=text, width=130, height=30,
                          command=lambda lab=label: self.inject_key(lab)).pack(side="left", padx=5)

    def inject_key(self, label: str):
        hex_priv = self.demo_keys.get(label)
        if not hex_priv:
            messagebox.showwarning("Brak klucza demo",
                                    f"Nie znaleziono .demo_keys/{label}.priv. "
                                    "Usuń vetchain_chain.jsonl i odpal app aby się wygenerowały.")
            return
        self.entry_key.delete(0, "end")
        self.entry_key.insert(0, hex_priv)

    def validate_and_login(self):
        entered = self.entry_key.get().strip()
        if not entered:
            messagebox.showwarning("Błąd autoryzacji", "Klucz prywatny nie może być pusty.")
            return

        try:
            priv_pem = keys.priv_from_hex(entered)
        except Exception as e:
            messagebox.showerror("Nieprawidłowy klucz",
                                  f"Klucz musi być 64-znakowym ciągiem hex.\n{e}")
            return

        address = keys.address_from_priv(priv_pem)
        actor = db.lookup_actor(address)
        if not actor:
            messagebox.showerror(
                "Odrzucono przez sieć",
                f"Adres {address}\nnie figuruje w rejestrze aktorów."
            )
            return

        if actor["role"] == db.ROLE_VET and not actor.get("signed_by_izba"):
            messagebox.showerror(
                "Łańcuch zaufania",
                "Klucz weterynarza bez podpisu Krajowej Izby (KILW)."
            )
            return

        if actor["role"] == db.ROLE_BREEDER and not actor.get("registered"):
            messagebox.showerror(
                "Status hodowli",
                "Hodowla bez aktywnego statusu (ZKwP/PKR)."
            )
            return

        db.set_session_key(priv_pem)
        self.controller.current_actor = actor

        # Routing per rola; buyer to specjalny widok dla owner Maria
        role_target = {
            db.ROLE_VET: "ScreenWeterynarzMain",
            db.ROLE_BREEDER: "ScreenHodowca",
            db.ROLE_SHELTER: "ScreenSchronisko",
            db.ROLE_OWNER: "ScreenWlasciciel",
        }
        # Jeśli aktor to "Maria Nowak" — to nasz demo buyer
        if actor["name"] == "Maria Nowak":
            target = "ScreenKupujacy"
        else:
            target = role_target[actor["role"]]

        messagebox.showinfo(
            "Autentykacja Blockchain",
            f"Podpis zweryfikowany.\n\n"
            f"Aktor: {actor['name']}\n"
            f"Adres: {address}\n"
            f"Rola: {actor['role']}"
        )
        self.controller.show_frame(target)
