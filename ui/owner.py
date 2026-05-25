"""Pełna karta zdrowia z perspektywy właściciela."""

from tkinter import messagebox

import customtkinter as ctk

import vetchain_db as db
from vetchain_crypto import VetChainCrypto

from .base import BaseScreen


class ScreenWlasciciel(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        actor = controller.current_actor or {}

        self.setup_header(
            btn_text="🔒 Wyloguj",
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text=f"● {actor.get('name', 'Właściciel')} (Pełny Dostęp)",
            title="Karta Zdrowia Zwierzęcia"
        )

        content_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)

        animals = db.list_animals_by_owner(actor.get("key", ""))
        if not animals:
            ctk.CTkLabel(content_frame, text="[Brak zwierząt przypisanych do konta]",
                         text_color="gray").pack(pady=40)
            return

        animal = animals[0]
        self.chip = animal["chip_id"]

        profile = ctk.CTkFrame(content_frame, fg_color="#a3aea3")
        profile.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(profile, text=f"🐕 {animal['name']} ({animal['species']})",
                      font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(profile, text=f"ID mikroczipu: {animal['chip_id']}",
                      font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(0, 10))

        ctk.CTkButton(content_frame, text="🔑 Generuj tymczasowy klucz dostępu dla kupującego (Ważny 24h)",
                      width=500, height=45,
                      command=self.action_generate_zkp_key).pack(pady=10)

        ctk.CTkLabel(content_frame, text="Pełna Historia Zabiegów (deszyfrowana sekcja med + fin):",
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        timeline = ctk.CTkScrollableFrame(content_frame, fg_color="#a3aea3")
        timeline.pack(fill="both", expand=True)

        visits = db.get_visits_for_animal(self.chip)
        if not visits:
            ctk.CTkLabel(timeline, text="[Brak wpisów]", text_color="gray",
                         font=ctk.CTkFont(slant="italic")).pack(pady=20)
            return

        for v in visits:
            med = VetChainCrypto.decrypt_section(animal["shared_key"], v["med_data"])
            fin = VetChainCrypto.decrypt_section(animal["shared_key"], v["fin_data"])
            if not v["doc_hash"]:
                status, color = "⏳ OCZEKUJE REVEAL", "#3498db"
            elif db.has_medical_exception_covering(self.chip, v["visit_date"]):
                status, color = "⚠️ WYJĄTEK OK", "#e67e22"
            else:
                status, color = "🔒 ZWERYFIKOWANO", "black"
            text = f"{v['visit_date']} | {v['visit_type']}\n{med}\n💰 {fin}"
            self.add_timeline_item(timeline, text, status, color)

    def add_timeline_item(self, parent, text, status, color):
        item = ctk.CTkFrame(parent)
        item.pack(fill="x", pady=3, padx=5)
        ctk.CTkLabel(item, text=text, justify="left").pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(item, text=status, text_color=color, font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=10)

    def action_generate_zkp_key(self):
        actor = self.controller.current_actor or {}
        token = db.create_temp_key(self.chip, actor.get("key", ""))
        self.clipboard_clear()
        self.clipboard_append(token)
        messagebox.showinfo(
            "Zarządzanie Prywatnością",
            f"Sukces!\n\nWygenerowano jednorazowy klucz tymczasowy (24h).\n"
            f"Token skopiowany do schowka:\n{token}\n\n"
            "Kupujący wpisze go w ekranie weryfikacji - zobaczy tylko sekcję medyczną."
        )
