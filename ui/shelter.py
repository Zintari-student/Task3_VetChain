"""Ekrany schroniska/fundacji: lista, przyjęcie, karta adopcyjna."""

from tkinter import messagebox

import customtkinter as ctk

import vetchain_db as db
from vetchain_crypto import VetChainCrypto

from .base import BaseScreen


class ScreenSchronisko(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        actor = controller.current_actor or {}
        shelter_key = actor.get("key", "")

        self.setup_header(
            btn_text="🔒 Wyloguj",
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text="● Rola: Schronisko / Fundacja (Autoryzowany Węzeł)",
            title="Panel Zarządzania Azylem i Adopcjami"
        )

        content = ctk.CTkFrame(self.panel, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(content, text="➕   REJESTRUJ NOWE ZWIERZĘ (Przyjęcie do azylu)",
                      width=400, height=50, font=ctk.CTkFont(size=14, weight="bold"),
                      command=lambda: controller.show_frame("ScreenSchroniskoDodaj")).pack(pady=(0, 20))

        ctk.CTkLabel(content, text="📋 ZWIERZĘTA W AZYLU:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20)

        table_frame = ctk.CTkScrollableFrame(content, fg_color="#a3aea3")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        rows = db.list_animals_by_shelter(shelter_key) if shelter_key else []
        if not rows:
            ctk.CTkLabel(table_frame, text="[Brak zwierząt w azylu]",
                         text_color="gray", font=ctk.CTkFont(slant="italic")).pack(pady=20)
        for r in rows:
            self._create_shelter_row(table_frame, r)

    def _create_shelter_row(self, parent, r):
        ready = bool(r["vaccines_ok"]) and bool(r["neutered"])
        status = "Gotowy" if ready else "W przygotowaniu"
        text = (
            f"Imię: {r['name']}  |  Gatunek: {r['species']}  |  Płeć: {r['sex']}  |  "
            f"Ur.: {r['birth_date']}  |  Status: {status}"
        )
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=4, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12)).pack(side="left", padx=15, pady=8)

        chip = r["chip_id"]
        ctk.CTkButton(row, text="Karta 🐾", width=100, height=26,
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=lambda c=chip: self._open_card(c)).pack(side="right", padx=10)

    def _open_card(self, chip_id):
        self.controller.current_animal_chip = chip_id
        self.controller.show_frame("ScreenSchroniskoProfil")


class ScreenSchroniskoDodaj(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.setup_header(
            btn_text="← Anuluj",
            btn_cmd=lambda: controller.show_frame("ScreenSchronisko"),
            info_text="● Rola: Schronisko / Fundacja (Autoryzowany Węzeł)",
            title="Formularz Przyjęcia Zwierzęcia do Schroniska"
        )

        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=20)
        self.panel.grid_rowconfigure(2, weight=1)

        self.entry_name = ctk.CTkEntry(form_frame, placeholder_text="Imię robocze zwierzęcia...", width=400, height=35)
        self.entry_name.grid(row=0, column=0, pady=8)

        self.dropdown_species = ctk.CTkComboBox(form_frame, values=["Pies", "Kot", "Inne", "Egzotyczne"],
                                                width=400, height=35, command=self._on_species_change)
        self.dropdown_species.set("Pies")
        self.dropdown_species.grid(row=1, column=0, pady=8)

        self.dropdown_sex = ctk.CTkComboBox(form_frame, values=["Samiec", "Samica"], width=400, height=35)
        self.dropdown_sex.grid(row=2, column=0, pady=8)

        ctk.CTkLabel(form_frame, text="Szacowany rok urodzenia:", font=ctk.CTkFont(size=12), text_color="gray").grid(row=3, column=0, sticky="w", pady=(5, 2))
        lata = [str(rok) for rok in range(2010, 2027)]
        self.dropdown_year = ctk.CTkComboBox(form_frame, values=lata, width=400, height=35)
        self.dropdown_year.set("2022")
        self.dropdown_year.grid(row=4, column=0, pady=5)

        self.entry_chip = ctk.CTkEntry(form_frame, placeholder_text="Numer czipu (zostaw puste - przydzielimy)...", width=400, height=35)
        self.entry_chip.grid(row=5, column=0, pady=12)

        self.lbl_cites = ctk.CTkLabel(form_frame, text="🛂 Token Certyfikatu Ministerstwa Środowiska (CITES):",
                                       font=ctk.CTkFont(size=12, weight="bold"), text_color="#b56300")
        self.entry_cites = ctk.CTkEntry(form_frame, placeholder_text="Wymagany dla gatunków egzotycznych...",
                                         width=400, height=35)

        ctk.CTkButton(form_frame, text="📝 Rejestruj przyjęcie w Ledgerze",
                      width=400, height=45, font=ctk.CTkFont(weight="bold"),
                      command=self.action_save_shelter).grid(row=8, column=0, pady=15)

    def _on_species_change(self, value):
        if value == "Egzotyczne":
            self.lbl_cites.grid(row=6, column=0, sticky="w", pady=(10, 2))
            self.entry_cites.grid(row=7, column=0, pady=5)
        else:
            self.lbl_cites.grid_forget()
            self.entry_cites.grid_forget()

    def action_save_shelter(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Błąd", "Wprowadź imię zwierzęcia!")
            return

        actor = self.controller.current_actor or {}
        if actor.get("role") != db.ROLE_SHELTER:
            messagebox.showerror("Brak uprawnień", "Tylko autoryzowane schronisko może rejestrować przyjęcia.")
            return

        species = self.dropdown_species.get()
        cites_token = None
        if species == "Egzotyczne":
            cites_token = self.entry_cites.get().strip()
            if not cites_token:
                messagebox.showerror(
                    "CITES wymagane",
                    "Rejestracja zwierzęcia egzotycznego wymaga ważnego tokenu Ministerstwa Środowiska.\n"
                    "Smart kontrakt odrzucił żądanie."
                )
                return

        chip_id = db.register_shelter_animal(
            name=name,
            species=species,
            sex=self.dropdown_sex.get(),
            birth_year=self.dropdown_year.get(),
            chip_id=self.entry_chip.get().strip(),
            shelter_key=actor["key"],
            cites_token=cites_token,
        )

        msg = f"Zarejestrowano: {species} - {name}.\nPrzypisany czip: {chip_id}"
        if cites_token:
            msg += "\n🛂 Token CITES powiązany trwale z ID zwierzęcia."
        messagebox.showinfo("Sukces", msg)
        self.controller.show_frame("ScreenSchronisko")


class ScreenSchroniskoProfil(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        chip = getattr(controller, "current_animal_chip", None)
        animal = db.get_animal(chip) if chip else None

        self.setup_header(
            btn_text="← Powrót",
            btn_cmd=lambda: controller.show_frame("ScreenSchronisko"),
            info_text="● Rola: Schronisko / Fundacja (Autoryzowany Węzeł)",
            title="Profil Zwierzęcia (Azyl)"
        )

        if not animal:
            ctk.CTkLabel(self.panel, text="[Nie znaleziono zwierzęcia w rejestrze]",
                         text_color="gray").grid(row=2, column=0, pady=40)
            return

        self.animal = animal
        self.chip = animal["chip_id"]
        self.is_ready = bool(animal["vaccines_ok"]) and bool(animal["neutered"])
        self.has_cites = db.has_cites_cert(self.chip)

        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=10)

        self._disabled_field(form_frame, "Imię:", animal["name"], 0)
        self._disabled_field(form_frame, "Gatunek:", animal["species"], 1)
        self._disabled_field(form_frame, "Płeć:", animal["sex"] or "-", 2)
        self._disabled_field(form_frame, "Rok urodzenia:", animal["birth_date"] or "-", 3)
        self._disabled_field(form_frame, "Numer Mikroczipu:", animal["chip_id"], 4)
        cites_text = "✓ Aktywny" if self.has_cites else ("— Wymagany" if animal["species"] == "Egzotyczne" else "— N/D")
        self._disabled_field(form_frame, "Certyfikat CITES:", cites_text, 5)

        status_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        status_frame.grid(row=3, column=0, pady=10)

        vax_color = "black" if animal["vaccines_ok"] else "#e74c3c"
        vax_text = "💉 Szczepienia: AKTUALNE" if animal["vaccines_ok"] else "💉 Szczepienia: NIEAKTUALNE ⚠️"
        ctk.CTkLabel(status_frame, text=vax_text, text_color=vax_color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15)

        neut_color = "black" if animal["neutered"] else "#e74c3c"
        neut_text = "✂️ Kastracja: WYKONANO" if animal["neutered"] else "✂️ Kastracja: BRAK ⚠️"
        ctk.CTkLabel(status_frame, text=neut_text, text_color=neut_color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15)

        self.btn_zkp = ctk.CTkButton(
            self.panel, text="🔑 Generuj 24h klucz dostępu dla adoptującego",
            width=400, height=35, font=ctk.CTkFont(weight="bold"),
            state="normal" if self.is_ready else "disabled",
            command=self.generate_token
        )
        self.btn_zkp.grid(row=4, column=0, pady=(10, 10))

        ctk.CTkLabel(self.panel, text="🩺 Historia medyczna (zaszyfrowana sekcja med):",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=5, column=0, sticky="w", padx=50, pady=(10, 0))

        history_frame = ctk.CTkScrollableFrame(self.panel, fg_color="#a3aea3")
        history_frame.grid(row=6, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(6, weight=1)

        visits = db.get_visits_for_animal(self.chip)
        if not visits:
            ctk.CTkLabel(history_frame, text="[Brak wpisów]", text_color="gray",
                         font=ctk.CTkFont(slant="italic")).pack(pady=20)
        else:
            for v in visits:
                med = VetChainCrypto.decrypt_section(animal["shared_key"], v["med_data"])
                badge = " ⏳ Oczekuje Reveal" if not v["doc_hash"] else ""
                self._history_row(history_frame, f"{v['visit_date']} | {v['visit_type']}{badge}\n{med}")

    def generate_token(self):
        if not self.is_ready:
            messagebox.showerror("Błąd", "Zwierzę nie spełnia wymogów (szczepienia/kastracja).")
            return
        actor = self.controller.current_actor or {}
        token = db.create_temp_key(self.chip, actor.get("key", ""))
        self.clipboard_clear()
        self.clipboard_append(token)
        messagebox.showinfo(
            "Wygenerowano Klucz Dostępu (24h)",
            f"Token jednorazowy (skopiowano do schowka):\n{token}\n\n"
            "Adoptujący wpisze go w ekranie weryfikacji, by zobaczyć historię medyczną bez kosztów."
        )

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
