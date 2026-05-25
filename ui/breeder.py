"""Ekrany hodowcy: lista zwierząt, dodawanie miotu, profil + SBT."""

from tkinter import messagebox

import customtkinter as ctk

import vetchain_db as db
from vetchain_crypto import VetChainCrypto

from .base import BaseScreen


class ScreenHodowca(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        actor = controller.current_actor or {}
        breeder_key = actor.get("key", "")

        self.setup_header(
            btn_text="🔒 Wyloguj",
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text=f"● {actor.get('name', 'Hodowca')} | ZKwP-status ✓",
            title="Panel Zarządzania Hodowlą"
        )

        content_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)

        ctk.CTkButton(content_frame, text="➕   DODAJ NOWE ZWIERZĘ / MIOT",
                      width=400, height=50, font=ctk.CTkFont(size=14, weight="bold"),
                      command=lambda: controller.show_frame("ScreenHodowcaDodaj")).pack(pady=(0, 20))

        ctk.CTkLabel(content_frame, text="📋 ZWIERZĘTA W HODOWLI:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))

        table_frame = ctk.CTkScrollableFrame(content_frame, fg_color="#a3aea3")
        table_frame.pack(fill="both", expand=True)

        rows = db.list_animals_by_breeder(breeder_key) if breeder_key else []
        if not rows:
            ctk.CTkLabel(table_frame, text="[Brak zwierząt przypisanych do hodowli]",
                         text_color="gray", font=ctk.CTkFont(slant="italic")).pack(pady=20)
        for r in rows:
            self._create_animal_row(table_frame, r)

    def _create_animal_row(self, parent, r):
        is_pending = "chip_id" not in r.keys()
        chip_text = "[BRAK - Oczekuje]" if is_pending else r["chip_id"]
        text = f"Imię: {r['name']}  |  Płeć: {r['sex']}  |  Ur.: {r['birth_date']}  |  Czip: {chip_text}"

        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=4, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12)).pack(side="left", padx=15, pady=8)

        if is_pending:
            ctk.CTkLabel(row, text="oczekuje czipu od wet.",
                         font=ctk.CTkFont(size=10, slant="italic"), text_color="gray").pack(side="right", padx=10)
        else:
            chip = r["chip_id"]
            ctk.CTkButton(row, text="Profil 🐕", width=100, height=26,
                          font=ctk.CTkFont(size=12, weight="bold"),
                          command=lambda c=chip: self._open_profile(c)).pack(side="right", padx=10)

    def _open_profile(self, chip_id):
        self.controller.current_animal_chip = chip_id
        self.controller.show_frame("ScreenHodowcaProfil")


class ScreenHodowcaDodaj(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.setup_header(
            btn_text="← Powrót",
            btn_cmd=lambda: controller.show_frame("ScreenHodowca"),
            info_text="● Rola: Hodowca zarejestrowany (ZKwP / PKR)",
            title="Rejestracja Nowego Zwierzęcia w Księdze Rodowodowej"
        )

        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=20)
        self.panel.grid_rowconfigure(2, weight=1)

        self.entry_name = ctk.CTkEntry(form_frame, placeholder_text="Imię zwierzęcia (przydomek hodowlany)...", width=400, height=35)
        self.entry_name.grid(row=0, column=0, pady=8)

        self.dropdown_sex = ctk.CTkComboBox(form_frame, values=["Samiec", "Samica"], width=400, height=35)
        self.dropdown_sex.grid(row=1, column=0, pady=8)

        self.entry_birth = ctk.CTkEntry(form_frame, placeholder_text="Data urodzenia (RRRR-MM-DD)...", width=400, height=35)
        self.entry_birth.grid(row=2, column=0, pady=8)

        info_chip = ctk.CTkTextbox(form_frame, width=400, height=80, font=ctk.CTkFont(size=11), text_color="gray")
        info_chip.insert("0.0",
            "ℹ️ NUMER MIKROCZIPU:\nZwierzę rejestrowane jest w bazie hodowli przed znakowaniem. "
            "Unikalny numer mikroczipu zostanie trwale powiązany z tym profilem przez uprawnionego "
            "weterynarza podczas pierwszej wizyty."
        )
        info_chip.configure(state="disabled")
        info_chip.grid(row=3, column=0, pady=10)

        ctk.CTkButton(form_frame, text="💾 Zapisz w Lokalnym Węźle Hodowli",
                      width=400, height=45, font=ctk.CTkFont(weight="bold"),
                      command=self.action_save_animal).grid(row=4, column=0, pady=15)

    def action_save_animal(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Błąd", "Wprowadź imię zwierzęcia!")
            return
        birth = self.entry_birth.get().strip() or db.today_iso()
        actor = self.controller.current_actor or {}
        if actor.get("role") != db.ROLE_BREEDER:
            messagebox.showerror("Brak uprawnień", "Tylko hodowca może rejestrować nowe zwierzęta.")
            return

        db.add_pending_animal(
            name=name,
            species="Pies",
            sex=self.dropdown_sex.get(),
            birth_date=birth,
            breeder_key=actor["key"],
        )
        messagebox.showinfo(
            "Sukces",
            "Profil zwierzęcia został utworzony lokalnie.\nOczekuje na przypisanie mikroczipu przez weterynarza."
        )
        self.controller.show_frame("ScreenHodowca")


class ScreenHodowcaProfil(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        chip = getattr(controller, "current_animal_chip", None)
        animal = db.get_animal(chip) if chip else None

        self.setup_header(
            btn_text="← Powrót",
            btn_cmd=lambda: controller.show_frame("ScreenHodowca"),
            info_text="● Rola: Hodowca zarejestrowany (ZKwP / PKR)",
            title="Karta Profilowa Zwierzęcia"
        )

        if not animal:
            ctk.CTkLabel(self.panel, text="[Nie znaleziono zwierzęcia w rejestrze]",
                         text_color="gray").grid(row=2, column=0, pady=40)
            return

        self.animal = animal
        self.chip = animal["chip_id"]

        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=10)

        self._disabled_field(form_frame, "Imię:", animal["name"], 0)
        self._disabled_field(form_frame, "Płeć:", animal["sex"] or "-", 1)
        self._disabled_field(form_frame, "Data urodzenia:", animal["birth_date"] or "-", 2)
        self._disabled_field(form_frame, "Numer Mikroczipu:", animal["chip_id"], 3)

        self.pedigree = db.get_pedigree_status(self.chip)
        is_ready = all(self.pedigree)

        ctk.CTkButton(
            self.panel, text="💎 GENERUJ RODOWÓD CYFROWY (SBT)",
            width=400, height=38, font=ctk.CTkFont(weight="bold"),
            state="normal" if is_ready else "disabled",
            command=self.validate_and_generate
        ).grid(row=3, column=0, pady=20)

        ctk.CTkLabel(self.panel, text="🩺 Historia leczenia (sekcja medyczna z bloku):",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=4, column=0, sticky="w", padx=50, pady=(10, 0))

        history_frame = ctk.CTkScrollableFrame(self.panel, fg_color="#a3aea3")
        history_frame.grid(row=5, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(5, weight=1)

        visits = db.get_visits_for_animal(self.chip)
        if not visits:
            ctk.CTkLabel(history_frame, text="[Brak wpisów]", text_color="gray",
                         font=ctk.CTkFont(slant="italic")).pack(pady=20)
        else:
            for v in visits:
                med = VetChainCrypto.decrypt_section(animal["shared_key"], v["med_data"])
                badge = " ⏳ Oczekuje Reveal" if not v["doc_hash"] else ""
                self._history_row(history_frame, f"{v['visit_date']} | {v['visit_type']}{badge}\n{med}")

    def validate_and_generate(self):
        if not all(self.pedigree):
            failed_gen = self.pedigree.index(False) + 1
            gen_names = ["rodziców", "dziadków", "pradziadków"]
            messagebox.showerror("Odrzucono", f"Błąd weryfikacji pokolenia {failed_gen} ({gen_names[failed_gen-1]}).")
            return

        actor = self.controller.current_actor or {}
        if actor.get("role") != db.ROLE_BREEDER or not actor.get("registered"):
            messagebox.showerror(
                "Brak statusu hodowli",
                "Kontrakt odrzucił żądanie - konto nie posiada aktywnego statusu w związku kynologicznym."
            )
            return

        db.issue_sbt(self.chip, actor["key"])
        messagebox.showinfo(
            "Sukces",
            f"Walidacja zakończona pomyślnie.\nWyemitowano Soulbound Token (SBT) dla czipu {self.chip}.\n"
            "Token non-transferable."
        )
        self.controller.show_frame("ScreenHodowca")

    def _disabled_field(self, parent, label_text, value_text, row_idx):
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=12), text_color="gray").grid(row=row_idx, column=0, sticky="e", padx=10, pady=3)
        entry = ctk.CTkEntry(parent, width=300, height=28)
        entry.insert(0, value_text)
        entry.configure(state="disabled")
        entry.grid(row=row_idx, column=1, pady=3)

    def _history_row(self, parent, text):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=2, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12), justify="left").pack(side="left", padx=10, pady=5)
