"""Kupujący / adoptujący — wpisuje token i widzi tylko sekcję medyczną."""

from tkinter import messagebox

import customtkinter as ctk

import vetchain_db as db
from vetchain_crypto import VetChainCrypto

from .base import BaseScreen


class ScreenKupujacy(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.setup_header(
            btn_text="🔒 Wyloguj",
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text="● Rola: Weryfikator / Kupujący (ZKP View)",
            title="Karta Zdrowia Zwierzęcia (ZKP)"
        )

        content_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)

        token_box = ctk.CTkFrame(content_frame, fg_color="#a3aea3")
        token_box.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(token_box, text="🔑 Wklej jednorazowy token udostępniony przez właściciela/schronisko:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        token_row = ctk.CTkFrame(token_box, fg_color="transparent")
        token_row.pack(fill="x", padx=15, pady=(0, 10))
        self.entry_token = ctk.CTkEntry(token_row, placeholder_text="np. 4xkR9...", height=35)
        self.entry_token.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(token_row, text="Odszyfruj 🔓", width=120, height=35,
                      command=self.action_consume_token).pack(side="right")

        self.profile_frame = ctk.CTkFrame(content_frame, fg_color="#a3aea3")
        self.profile_frame.pack(fill="x", pady=(0, 10))
        self._render_locked()

        ctk.CTkLabel(content_frame, text="Zweryfikowana Historia Medyczna (Dane publiczne ZKP):",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        self.timeline = ctk.CTkScrollableFrame(content_frame, fg_color="#a3aea3")
        self.timeline.pack(fill="both", expand=True)
        self._placeholder_timeline()

    def _render_locked(self):
        for w in self.profile_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.profile_frame, text="🔒 Karta zaszyfrowana",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(self.profile_frame, text="Aby zobaczyć historię medyczną, wpisz token od właściciela.",
                     text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=(0, 10))

    def _placeholder_timeline(self):
        for w in self.timeline.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.timeline, text="[Token nie został zweryfikowany]",
                     text_color="gray", font=ctk.CTkFont(slant="italic")).pack(pady=20)

    def action_consume_token(self):
        token = self.entry_token.get().strip()
        if not token:
            messagebox.showwarning("Brak tokenu", "Wpisz token udostępniony przez właściciela.")
            return
        try:
            data = db.consume_temp_key(token)
        except db.TempKeyError as e:
            messagebox.showerror("Odrzucono token", str(e))
            return

        chip = data["chip_id"]
        key = data["key_bytes"]
        animal = db.get_animal(chip)
        if not animal:
            messagebox.showerror("Błąd", "Zwierzę powiązane z tokenem nie istnieje w sieci.")
            return

        for w in self.profile_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.profile_frame, text=f"🐕 {animal['name']} ({animal['species']})",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(self.profile_frame,
                     text=f"ID mikroczipu: {animal['chip_id']} | Dane finansowe: [UKRYTE]",
                     text_color="#e74c3c", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(0, 10))

        for w in self.timeline.winfo_children():
            w.destroy()
        visits = db.get_visits_for_animal(chip)
        if not visits:
            ctk.CTkLabel(self.timeline, text="[Brak wpisów medycznych]",
                         text_color="gray", font=ctk.CTkFont(slant="italic")).pack(pady=20)
            return

        for v in visits:
            decrypted_med = VetChainCrypto.decrypt_section(key, v["med_data"])
            decrypted_fin = VetChainCrypto.decrypt_section(b"\x00" * 32, v["fin_data"])
            display_text = f"{v['visit_date']} | {v['visit_type']}\n{decrypted_med}\nFinanse: {decrypted_fin}"
            if not v["doc_hash"]:
                self.add_timeline_item(self.timeline, display_text, "⏳ OCZEKUJE REVEAL", "#3498db")
            else:
                self.add_timeline_item(self.timeline, display_text, "🔒 ZWERYFIKOWANO", "black")

        messagebox.showinfo("Token zużyty",
                            "Klucz tymczasowy został właśnie skonsumowany.\nKolejne próby zostaną odrzucone.")

    def add_timeline_item(self, parent, text, status, color):
        item = ctk.CTkFrame(parent)
        item.pack(fill="x", pady=3, padx=5)
        ctk.CTkLabel(item, text=text, justify="left").pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(item, text=status, text_color=color, font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=10)
