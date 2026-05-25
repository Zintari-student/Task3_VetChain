"""Ekrany weterynarza: panel główny, dodawanie wizyty, reveal, czipowanie."""

from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

import vetchain_chain as db

from .base import BaseScreen


VISIT_TYPES = [
    "Obowiązkowe szczepienie (Wścieklizna)",
    "Szczepienie kompleksowe (DHPPi)",
    "Kastracja / Sterylizacja",
    "Badanie ogólne / Kontrola",
    "Wyjątek medyczny (Choroba - Opóźnienie szczepienia)",
]
EXCEPTION_TYPE = "Wyjątek medyczny (Choroba - Opóźnienie szczepienia)"


class ScreenWeterynarzMain(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        actor = controller.current_actor or {}
        self.vet_key = actor.get("key", "")

        self.setup_header(
            btn_text="🔒 Wyloguj",
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text=f"● {actor.get('name', 'Weterynarz')} | KILW-podpis ✓",
            title="Panel Zarządzania Wizytami Weterynaryjnymi"
        )

        main_columns = ctk.CTkFrame(self.panel, fg_color="transparent")
        main_columns.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)
        main_columns.grid_columnconfigure(0, weight=1)
        main_columns.grid_columnconfigure(1, weight=1)

        left_col = ctk.CTkFrame(main_columns, fg_color="#b4beb4")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        inner_left = ctk.CTkFrame(left_col, fg_color="transparent")
        inner_left.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkButton(inner_left, text="➕   DODAJ NOWĄ WIZYTĘ (Commit)", height=45,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: controller.show_frame("ScreenWeterynarzDodaj")).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(inner_left, text="🏷️  PRZYPISZ CZIP (Czipowanie)", height=38,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=lambda: controller.show_frame("ScreenWeterynarzCzipowanie")).pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(inner_left, text="📋 OCZEKUJĄCE REVEAL (max 8h):",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.pending_table = ctk.CTkScrollableFrame(inner_left, fg_color="#a3aea3")
        self.pending_table.pack(fill="both", expand=True)
        self._render_pending()

        right_col = ctk.CTkFrame(main_columns, fg_color="#b4beb4")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        inner_right = ctk.CTkFrame(right_col, fg_color="transparent")
        inner_right.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(inner_right, text="🔍 Przeszukaj Ewidencję VetChain",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))

        search_frame = ctk.CTkFrame(inner_right, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Wpisz fragment lub pełny nr czipu (ISO)...", height=32)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(search_frame, text="Szukaj 🔎", width=70, height=32,
                      command=self.action_search_chip).pack(side="right")

        ctk.CTkLabel(inner_right, text="⏳ Ostatnio zamknięte transakcje:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 5))

        self.history_table = ctk.CTkScrollableFrame(inner_right, fg_color="#a3aea3")
        self.history_table.pack(fill="both", expand=True)
        self._render_history()

    def _render_pending(self):
        rows = db.pending_reveals(self.vet_key) if self.vet_key else []
        if not rows:
            ctk.CTkLabel(self.pending_table, text="[Brak oczekujących bloków]",
                         text_color="gray", font=ctk.CTkFont(slant="italic")).pack(pady=15)
            return
        for r in rows:
            self._create_pending_row(r["id"], r["chip_id"], r["visit_type"], r["block_ts"])

    def _create_pending_row(self, visit_id, chip, vtype, block_ts):
        row = ctk.CTkFrame(self.pending_table)
        row.pack(fill="x", pady=4, padx=5)
        try:
            age = datetime.now() - datetime.fromisoformat(block_ts)
            hours_left = max(0, 8 - int(age.total_seconds() // 3600))
            mins_left = max(0, 60 - int((age.total_seconds() % 3600) // 60))
            time_left = f"{hours_left}h {mins_left}m"
        except Exception:
            time_left = "?"
        ctk.CTkLabel(row, text=f"Czip: {chip}\nTyp: {vtype}", font=ctk.CTkFont(size=11), justify="left").pack(side="left", padx=10, pady=5)
        ctk.CTkButton(row, text=f"Uzupełnij 🔑\n({time_left})", width=95, height=32,
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=lambda vid=visit_id: self.go_to_uzupelnij(vid)).pack(side="right", padx=5, pady=5)

    def _render_history(self):
        rows = db.recent_closed_visits(self.vet_key) if self.vet_key else []
        if not rows:
            ctk.CTkLabel(self.history_table, text="[Brak zamkniętych transakcji]",
                         text_color="gray", font=ctk.CTkFont(slant="italic")).pack(pady=15)
            return
        for r in rows:
            self._create_history_row(f"{r['visit_date']} | Czip: {r['chip_id']} | {r['visit_type']}")

    def _create_history_row(self, text):
        row = ctk.CTkFrame(self.history_table)
        row.pack(fill="x", pady=3, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=11), justify="left").pack(side="left", padx=10, pady=6)

    def go_to_uzupelnij(self, visit_id):
        self.controller.pending_reveal_id = visit_id
        self.controller.show_frame("ScreenWeterynarzUzupelnij")

    def action_search_chip(self):
        q = self.search_entry.get().strip()
        if not q:
            return
        results = db.search_chip(q)
        if not results:
            messagebox.showinfo("Wyszukiwanie czipu", f"Brak wyników dla: {q}")
            return
        lines = [f"{r['chip_id']} — {r['name']} ({r['species']})" for r in results]
        messagebox.showinfo("Wyszukiwanie czipu", "\n".join(lines))


class ScreenWeterynarzDodaj(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.setup_header(
            btn_text="← Anuluj",
            btn_cmd=lambda: controller.show_frame("ScreenWeterynarzMain"),
            info_text="● Rola: Lekarz Weterynarii (KILW)",
            title="Inicjowanie Nowej Wizyty w Blockchain"
        )

        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=20)
        self.panel.grid_rowconfigure(2, weight=1)

        self.entry_chip = ctk.CTkEntry(form_frame, placeholder_text="Numer mikroczipu (ISO)...", width=400, height=35)
        self.entry_chip.grid(row=0, column=0, pady=8)

        self.dropdown_type = ctk.CTkComboBox(form_frame, values=VISIT_TYPES, width=400, height=35)
        self.dropdown_type.grid(row=1, column=0, pady=8)

        self.entry_date = ctk.CTkEntry(form_frame, width=400, height=35)
        self.entry_date.insert(0, db.today_iso())
        self.entry_date.grid(row=2, column=0, pady=8)
        ctk.CTkLabel(form_frame, text="Data wizyty (RRRR-MM-DD). Smart kontrakt odrzuci datę wsteczną.",
                     font=ctk.CTkFont(size=10), text_color="gray").grid(row=3, column=0, sticky="w", padx=2)

        self.entry_desc = ctk.CTkEntry(form_frame, placeholder_text="Zastosowane leki / Opis (sekcja medyczna)...", width=400, height=35)
        self.entry_desc.grid(row=4, column=0, pady=8)

        self.entry_cost = ctk.CTkEntry(form_frame, placeholder_text="Koszt w PLN (sekcja finansowa, szyfrowana osobno)...", width=400, height=35)
        self.entry_cost.grid(row=5, column=0, pady=8)

        ctk.CTkLabel(form_frame, text="Kryptograficzny Hash Dokumentacji Medycznej (Opcjonalnie):",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=6, column=0, pady=(10, 2), sticky="w")
        self.entry_hash = ctk.CTkEntry(form_frame, placeholder_text="np. 2cf24dba5...", width=400, height=35)
        self.entry_hash.grid(row=7, column=0, pady=5)

        actions_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        actions_frame.grid(row=8, column=0, pady=30)

        ctk.CTkButton(actions_frame, text="🔒 Podpisz i Wyślij\n(Pełny Commit + Reveal)",
                      fg_color="#333333", hover_color="#1a1a1a", width=200, height=50,
                      font=ctk.CTkFont(weight="bold"),
                      command=self.action_full_submit).grid(row=0, column=0, padx=10)

        ctk.CTkButton(actions_frame, text="⏳ Tylko zarejestruj czas\n(Commit, Hash później)",
                      width=200, height=50, font=ctk.CTkFont(weight="bold"),
                      command=self.action_later_submit).grid(row=0, column=1, padx=10)

    def _validate_date(self, raw: str):
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date().isoformat()
        except ValueError:
            messagebox.showwarning("Błąd daty", "Format daty musi być RRRR-MM-DD.")
            return None

    def _vet_key(self) -> str:
        actor = self.controller.current_actor
        if not actor or actor["role"] != db.ROLE_VET:
            raise RuntimeError("Brak zalogowanego weterynarza")
        return actor["key"]

    def action_full_submit(self):
        chip = self.entry_chip.get().strip()
        if not chip:
            messagebox.showwarning("Błąd", "Wprowadź numer czipu!")
            return
        visit_date = self._validate_date(self.entry_date.get().strip())
        if not visit_date:
            return
        vtype = self.dropdown_type.get()

        if vtype == EXCEPTION_TYPE:
            reason = self.entry_desc.get().strip() or "Wyjątek medyczny"
            try:
                db.add_medical_exception(chip, self._vet_key(), visit_date, visit_date, reason)
            except db.UnknownChipError as e:
                messagebox.showerror("Czip nieznany", str(e))
                return
            messagebox.showinfo(
                "Wyjątek zapisany",
                "Podpisany wpis o chorobie zwierzęcia zapisany w bloku.\n"
                "Opóźnienia szczepień w tym okresie zostaną uznane za legalne."
            )
            self.controller.show_frame("ScreenWeterynarzMain")
            return

        med_text = f"{visit_date} | {vtype}\n{self.entry_desc.get().strip()}"
        fin_text = f"Koszt: {self.entry_cost.get().strip() or '—'} PLN"
        try:
            db.add_visit(chip, self._vet_key(), visit_date, vtype, med_text, fin_text,
                         doc_hash=self.entry_hash.get().strip() or None)
        except db.BackdateError as e:
            messagebox.showerror("Odrzucone przez sieć (wsteczna data)", str(e))
            return
        except db.UnknownChipError as e:
            messagebox.showerror("Czip nieznany", str(e))
            return

        messagebox.showinfo("Sukces Blockchain", "Wizyta autoryzowana w całości (Commit + Reveal wykonane razem).")
        self.controller.show_frame("ScreenWeterynarzMain")

    def action_later_submit(self):
        chip = self.entry_chip.get().strip()
        if not chip:
            messagebox.showwarning("Błąd", "Wprowadź numer czipu!")
            return
        visit_date = self._validate_date(self.entry_date.get().strip())
        if not visit_date:
            return
        vtype = self.dropdown_type.get()
        med_text = f"{visit_date} | {vtype}\n{self.entry_desc.get().strip()}"
        fin_text = f"Koszt: {self.entry_cost.get().strip() or '—'} PLN"
        try:
            visit_id = db.add_commit_only_visit(
                chip, self._vet_key(), visit_date, vtype, med_text, fin_text
            )
        except db.BackdateError as e:
            messagebox.showerror("Odrzucone przez sieć (wsteczna data)", str(e))
            return
        except db.UnknownChipError as e:
            messagebox.showerror("Czip nieznany", str(e))
            return
        self.controller.pending_reveal_id = visit_id
        messagebox.showinfo(
            "Rejestracja Commit",
            f"Znacznik czasu zabezpieczony w bloku (id={visit_id}).\n"
            "Sekcje med/fin zaszyfrowane. Hash dokumentacji uzupełnisz w Reveal."
        )
        self.controller.show_frame("ScreenWeterynarzMain")


class ScreenWeterynarzUzupelnij(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.setup_header(
            btn_text="← Anuluj",
            btn_cmd=lambda: controller.show_frame("ScreenWeterynarzMain"),
            info_text="● Rola: Lekarz Weterynarii (KILW)",
            title="Protokół Reveal: Uzupełnianie Hashu Dokumentacji"
        )

        self.visit_id = getattr(controller, "pending_reveal_id", None)
        visit_row = None
        if self.visit_id:
            conn = db.get_conn()
            try:
                visit_row = conn.execute(
                    "SELECT chip_id, visit_type FROM visits WHERE id = ?", (self.visit_id,)
                ).fetchone()
            finally:
                conn.close()

        content_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", pady=20)
        self.panel.grid_rowconfigure(2, weight=1)

        form_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(pady=20)

        ctk.CTkLabel(form_frame, text="Dane zarejestrowanego bloku wizyty:",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(0, 2))

        chip_value = visit_row["chip_id"] if visit_row else "[brak wybranego bloku]"
        type_value = f"Typ: {visit_row['visit_type']}" if visit_row else "Typ: [brak]"

        self.entry_chip_mock = ctk.CTkEntry(form_frame, width=400, height=35)
        self.entry_chip_mock.insert(0, chip_value)
        self.entry_chip_mock.configure(state="disabled")
        self.entry_chip_mock.pack(pady=5)

        self.entry_type_mock = ctk.CTkEntry(form_frame, width=400, height=35)
        self.entry_type_mock.insert(0, type_value)
        self.entry_type_mock.configure(state="disabled")
        self.entry_type_mock.pack(pady=5)

        ctk.CTkLabel(form_frame, text="Wklej kryptograficzny SHA-256 hash pełnej dokumentacji:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(20, 5))

        self.entry_reveal_hash = ctk.CTkEntry(form_frame, placeholder_text="Wpisz wynikowy hash...", width=400, height=38)
        self.entry_reveal_hash.pack(pady=5)

        ctk.CTkButton(form_frame, text="🔒 Autoryzuj Reveal i Zamknij Wizytę",
                      width=400, height=45, font=ctk.CTkFont(weight="bold"),
                      command=self.submit_reveal).pack(pady=30)

    def submit_reveal(self):
        hash_val = self.entry_reveal_hash.get().strip()
        if not hash_val:
            messagebox.showwarning("Błąd Reveal", "Musisz podać hash dokumentacji!")
            return
        if not self.visit_id:
            messagebox.showwarning("Błąd Reveal", "Brak wybranego bloku do uzupełnienia.")
            return

        db.reveal_visit_hash(self.visit_id, hash_val)
        self.controller.pending_reveal_id = None
        messagebox.showinfo("Reveal Zweryfikowany", "Sukces! Hash dokumentacji zapisany w bloku.")
        self.controller.show_frame("ScreenWeterynarzMain")


class ScreenWeterynarzCzipowanie(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.setup_header(
            btn_text="← Powrót",
            btn_cmd=lambda: controller.show_frame("ScreenWeterynarzMain"),
            info_text="● Rola: Lekarz Weterynarii (KILW)",
            title="Czipowanie: Przypisanie Mikroczipu do Zwierzęcia"
        )

        content = ctk.CTkFrame(self.panel, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=30, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            content,
            text="Zwierzęta zarejestrowane przez hodowcę/schronisko, oczekujące na czip:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        self.table = ctk.CTkScrollableFrame(content, fg_color="#a3aea3")
        self.table.pack(fill="both", expand=True)
        self._render_rows()

    def _render_rows(self):
        for w in self.table.winfo_children():
            w.destroy()

        rows = db.list_pending_animals()
        if not rows:
            ctk.CTkLabel(
                self.table, text="[Brak zwierząt oczekujących na czipowanie]",
                text_color="gray", font=ctk.CTkFont(slant="italic")
            ).pack(pady=20)
            return

        for r in rows:
            self._create_row(r)

    def _create_row(self, r):
        row = ctk.CTkFrame(self.table)
        row.pack(fill="x", pady=4, padx=5)

        info = (
            f"Imię: {r['name']}  |  Gatunek: {r['species']}  |  "
            f"Płeć: {r['sex']}  |  Ur.: {r['birth_date']}"
        )
        ctk.CTkLabel(row, text=info, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15, pady=(8, 4))

        action = ctk.CTkFrame(row, fg_color="transparent")
        action.pack(fill="x", padx=15, pady=(0, 8))

        entry_chip = ctk.CTkEntry(action, placeholder_text="Wpisz numer mikroczipu (ISO)...", height=32)
        entry_chip.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            action, text="🏷️ Przypisz", width=120, height=32,
            font=ctk.CTkFont(weight="bold"),
            command=lambda pid=r["id"], e=entry_chip: self._assign(pid, e)
        ).pack(side="right")

    def _assign(self, pending_id, entry):
        chip = entry.get().strip()
        if not chip:
            messagebox.showwarning("Błąd", "Wpisz numer mikroczipu.")
            return
        if not chip.upper().startswith("ISO"):
            messagebox.showwarning(
                "Błąd formatu",
                "Numer mikroczipu powinien zaczynać się od 'ISO-' (standard)."
            )
            return
        if db.get_animal(chip):
            messagebox.showerror(
                "Konflikt czipu",
                f"Czip {chip} jest już przypisany do innego zwierzęcia w rejestrze."
            )
            return

        try:
            db.assign_chip_to_pending(pending_id, chip)
        except db.UnknownChipError as e:
            messagebox.showerror("Błąd", str(e))
            return

        messagebox.showinfo(
            "Czipowanie zakończone",
            f"Mikroczip {chip} został trwale powiązany ze zwierzęciem.\n"
            "Wpis zapisany w bloku - zwierzę jest teraz aktywne w rejestrze."
        )
        self._render_rows()
