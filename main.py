import base64

import customtkinter as ctk
from tkinter import messagebox

from vetchain_crypto import VetChainCrypto

# ==========================================
# POMOCNICZE OKNO BAZOWE
# ==========================================
class BaseScreen(ctk.CTkFrame):
    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        # Wrapper i główny panel
        self.wrapper = ctk.CTkFrame(self, fg_color="transparent")
        self.wrapper.pack(fill="both", expand=True, padx=50, pady=(50, 80))
        
        self.panel = ctk.CTkFrame(self.wrapper, corner_radius=20, fg_color="#b4beb4")
        self.panel.pack(fill="both", expand=True)
        
        # Konfiguracja grida: 0=Nagłówek, 1=Tytuł, 2=Treść
        self.panel.grid_columnconfigure(0, weight=1)
        self.panel.grid_rowconfigure(0, weight=0) # Nagłówek
        self.panel.grid_rowconfigure(1, weight=0) # Tytuł
        self.panel.grid_rowconfigure(2, weight=1) # Główna treść

        # NAGŁÓWEK (row 0)
        self.header = ctk.CTkFrame(self.panel, fg_color="transparent", height=50)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header.grid_columnconfigure(0, weight=1)
        self.btn_nav = ctk.CTkButton(self.header, width=90, fg_color="#333333", hover_color="#1a1a1a")
        self.lbl_info = ctk.CTkLabel(self.header, font=ctk.CTkFont(weight="bold"))

        # TYTUŁ EKRANU (row 1)
        self.lbl_page_title = ctk.CTkLabel(self.panel, font=ctk.CTkFont(size=22, weight="bold"))
        self.lbl_page_title.grid(row=1, column=0, pady=(10, 20))

    def setup_header(self, btn_text=None, btn_cmd=None, info_text=None, title=None):
        # Nagłówek
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

        # Tytuł (row 1)
        if title:
            self.lbl_page_title.configure(text=title)
        else:
            self.lbl_page_title.grid_forget()

# ==========================================
# EKRAN LOGOWANIA
# ==========================================
class ScreenLogin(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Nagłówek (bez przycisku nawigacji, bo to ekran startowy)
        # Tytuł automatycznie trafi do row=1 zgodnie z nową strukturą BaseScreen
        self.setup_header(
            title="VetChain System"
        )

        # 2. Główna treść (row 2)
        # Używamy self.panel (od row 2), ponieważ row 0 i 1 są zajęte przez BaseScreen
        login_content = ctk.CTkFrame(self.panel, fg_color="transparent")
        login_content.grid(row=2, column=0, sticky="nsew", pady=20)
        login_content.grid_columnconfigure(0, weight=1)

        # Opis
        ctk.CTkLabel(login_content, text="Wprowadź swój Kryptograficzny Klucz Prywatny:", 
                     font=ctk.CTkFont(size=14)).pack(pady=5)
        
        # Pole wejściowe
        self.entry_key = ctk.CTkEntry(login_content, placeholder_text="Wpisz lub wklej klucz (np. 0x71C7...)", width=600, height=45)
        self.entry_key.pack(pady=15)

        # Przycisk
        btn_login = ctk.CTkButton(login_content, text="🔓 Autoryzuj i Wejdź do Systemu", width=300, height=50, 
                                  font=ctk.CTkFont(size=15, weight="bold"),
                                  command=self.validate_and_login)
        btn_login.pack(pady=25)

        # Linia dekoracyjna
        ctk.CTkFrame(login_content, height=2, width=600, fg_color="#a3aea3").pack(pady=30)

        # Sekcja Demo
        ctk.CTkLabel(login_content, text="Szybkie uzupełnianie kluczy (Demo):", font=ctk.CTkFont(size=12), text_color="#1c2826").pack(pady=5)
        
        demo_buttons_frame = ctk.CTkFrame(login_content, fg_color="transparent")
        demo_buttons_frame.pack(pady=(5, 20))

        buttons = [("🩺 Weterynarz", "0xWET_9921_KILW"), ("🏠 Hodowca", "0xHOD_8821_ZKWP"), 
                   ("🐾 Schronisko", "0xSCHR_1102_GOV"), ("👤 Właściciel", "0xOWN_9912_USER"), 
                   ("🔍 Kupujący", "0xBUY_5532_VIEW")]
        
        for text, key in buttons:
            ctk.CTkButton(demo_buttons_frame, text=text, width=120, height=30, 
                          command=lambda k=key: self.inject_key(k)).pack(side="left", padx=5)

    def inject_key(self, key_to_paste):
        self.entry_key.delete(0, 'end')
        self.entry_key.insert(0, key_to_paste)

    def validate_and_login(self):
        entered_key = self.entry_key.get().strip()
        if not entered_key:
            messagebox.showwarning("Błąd autoryzacji", "Klucz prywatny węzła nie może być pusty!")
            return

        mapping = {
            "WET": "ScreenWeterynarzMain",
            "HOD": "ScreenHodowca",
            "SCHR": "ScreenSchronisko",
            "OWN": "ScreenWlasciciel",
            "BUY": "ScreenKupujacy"
        }
        
        target = next((val for key, val in mapping.items() if key in entered_key), "ScreenKupujacy")

        messagebox.showinfo("Autentykacja Blockchain", f"Podpis cyfrowy dla węzła:\n{entered_key}\nzostał pomyślnie zweryfikowany.")
        self.controller.show_frame(target)

# ==========================================
# SEKCJA 1: WETERYNARZ (WIDOK GŁÓWNY)
# ==========================================
class ScreenWeterynarzMain(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Zastąpienie ręcznego nagłówka metodą bazową
        self.setup_header(
            btn_text="🔒 Wyloguj",
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text="● Rola: Lekarz Weterynarii (KILW)",
            title="Panel Zarządzania Wizytami Weterynaryjnymi"
        )

        # 2. Kontener główny (row 2, bo 0 to nagłówek, 1 to tytuł)
        main_columns = ctk.CTkFrame(self.panel, fg_color="transparent")
        main_columns.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(2, weight=1) # Treść rozciąga się w dół
        main_columns.grid_columnconfigure(0, weight=1)
        main_columns.grid_columnconfigure(1, weight=1)

        # --- LEWA KOLUMNA ---
        left_col = ctk.CTkFrame(main_columns, fg_color="#b4beb4")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        
        inner_left = ctk.CTkFrame(left_col, fg_color="transparent")
        inner_left.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkButton(inner_left, text="➕   DODAJ NOWĄ WIZYTĘ (Commit)", height=45, 
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: controller.show_frame("ScreenWeterynarzDodaj")).pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(inner_left, text="📋 OCZEKUJĄCE REVEAL (max 8h):", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.pending_table = ctk.CTkScrollableFrame(inner_left, fg_color="#a3aea3")
        self.pending_table.pack(fill="both", expand=True)
        
        self.create_pending_row("Czip: ...1234567\nTyp: Szczepienie wścieklizna", "3h 12m")
        self.create_pending_row("Czip: ...9876543\nTyp: Badanie RTG stawów", "5h 44m")

        # --- PRAWA KOLUMNA ---
        right_col = ctk.CTkFrame(main_columns, fg_color="#b4beb4") 
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)

        inner_right = ctk.CTkFrame(right_col, fg_color="transparent")
        inner_right.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(inner_right, text="🔍 Przeszukaj Ewidencję VetChain", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        
        search_frame = ctk.CTkFrame(inner_right, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Wpisz pełny nr czipu (ISO)...", height=32)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(search_frame, text="Szukaj 🔎", width=70, height=32, 
                      command=self.action_search_chip).pack(side="right")

        ctk.CTkLabel(inner_right, text="⏳ Ostatnio zamknięte transakcje:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(5, 5))
        
        self.history_table = ctk.CTkScrollableFrame(inner_right, fg_color="#a3aea3")
        self.history_table.pack(fill="both", expand=True)
        
        self.create_history_row("2026-05-24 | Czip: ISO-...555 | Kastracja (Sukces)")
        self.create_history_row("2026-05-23 | Czip: ISO-...234 | Odrobaczenie (Sukces)")

    def create_pending_row(self, text, time_left):
        row = ctk.CTkFrame(self.pending_table)
        row.pack(fill="x", pady=4, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=11), justify="left").pack(side="left", padx=10, pady=5)
        ctk.CTkButton(row, text=f"Uzupełnij 🔑\n({time_left})", width=95, height=32, 
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=self.go_to_uzupelnij).pack(side="right", padx=5, pady=5)

    def create_history_row(self, text):
        row = ctk.CTkFrame(self.history_table)
        row.pack(fill="x", pady=3, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=11), justify="left").pack(side="left", padx=10, pady=6)

    def go_to_uzupelnij(self):
        self.controller.show_frame("ScreenWeterynarzUzupelnij")

    def action_search_chip(self):
        messagebox.showinfo("Blockchain", f"Szukam: {self.search_entry.get()}")

# ==========================================
# SEKCJA 1A: DODAWANIE WIZYTY
# ==========================================
class ScreenWeterynarzDodaj(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Nagłówek i Tytuł (automatycznie ustawia row 0 i row 1)
        self.setup_header(
            btn_text="← Anuluj",
            btn_cmd=lambda: controller.show_frame("ScreenWeterynarzMain"),
            info_text="● Rola: Lekarz Weterynarii (KILW)",
            title="Inicjowanie Nowej Wizyty w Blockchain"
        )

        # 2. Kontener główny (row 2)
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=20)
        self.panel.grid_rowconfigure(2, weight=1)

        # Pola formularza
        self.entry_chip = ctk.CTkEntry(form_frame, placeholder_text="Numer mikroczipu (ISO)...", width=400, height=35)
        self.entry_chip.grid(row=0, column=0, pady=8)

        self.dropdown_type = ctk.CTkComboBox(form_frame, values=[
            "Obowiązkowe szczepienie (Wścieklizna)", 
            "Badanie ogólne / Kontrola", 
            "Wyjątek medyczny (Choroba - Opóźnienie szczepienia)"
        ], width=400, height=35)
        self.dropdown_type.grid(row=1, column=0, pady=8)

        self.entry_desc = ctk.CTkEntry(form_frame, placeholder_text="Zastosowane leki / Opis...", width=400, height=35)
        self.entry_desc.grid(row=2, column=0, pady=8)

        ctk.CTkLabel(form_frame, text="Kryptograficzny Hash Dokumentacji Medycznej (Opcjonalnie):", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=3, column=0, pady=(10, 2), sticky="w")
        
        self.entry_hash = ctk.CTkEntry(form_frame, placeholder_text="np. 2cf24dba5...", width=400, height=35)
        self.entry_hash.grid(row=4, column=0, pady=5)

        # Kontener na przyciski aktywacji
        actions_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        actions_frame.grid(row=5, column=0, pady=30)

        # Przycisk A
        btn_full = ctk.CTkButton(actions_frame, text="🔒 Podpisz i Wyślij\n(Pełny Commit + Reveal)", 
                                 fg_color="#333333", hover_color="#1a1a1a", width=200, height=50, 
                                 font=ctk.CTkFont(weight="bold"),
                                 command=self.action_full_submit)
        btn_full.grid(row=0, column=0, padx=10)

        # Przycisk B
        btn_later = ctk.CTkButton(actions_frame, text="⏳ Tylko zarejestruj czas\n(Commit, Hash później)", 
                                  width=200, height=50, font=ctk.CTkFont(weight="bold"),
                                  command=self.action_later_submit)
        btn_later.grid(row=0, column=1, padx=10)

    def action_full_submit(self):
        if not self.entry_chip.get():
            messagebox.showwarning("Błąd", "Wprowadź numer czipu!")
            return
        messagebox.showinfo("Sukces Blockchain", "Wizyta autoryzowana w całości (Commit + Reveal wykonane razem).")
        self.controller.show_frame("ScreenWeterynarzMain")

    def action_later_submit(self):
        if not self.entry_chip.get():
            messagebox.showwarning("Błąd", "Wprowadź numer czipu!")
            return
        messagebox.showinfo("Rejestracja Commit", "Znacznik czasu zabezpieczony w bloku sieci.\nWizyta oczekuje na uzupełnienie hashu (Reveal).")
        self.controller.show_frame("ScreenWeterynarzMain")

# ==========================================
# SEKCJA 1B: UZUPEŁNIANIE HASHU (REVEAL)
# ==========================================
class ScreenWeterynarzUzupelnij(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Nagłówek i automatyczny Tytuł w row=1
        self.setup_header(
            btn_text="← Anuluj",
            btn_cmd=lambda: controller.show_frame("ScreenWeterynarzMain"),
            info_text="● Rola: Lekarz Weterynarii (KILW)",
            title="Protokół Reveal: Uzupełnianie Hashu Dokumentacji"
        )

        # 2. Główna treść (zaczynamy od row=2)
        content_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", pady=20)
        self.panel.grid_rowconfigure(2, weight=1)

        # Kontener formularza
        form_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(pady=20)

        # Dane wizyty (zablokowane)
        ctk.CTkLabel(form_frame, text="Dane zarejestrowanego bloku wizyty:", 
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", pady=(0, 2))
        
        self.entry_chip_mock = ctk.CTkEntry(form_frame, width=400, height=35)
        self.entry_chip_mock.insert(0, "ISO-967000001234567")
        self.entry_chip_mock.configure(state="disabled")
        self.entry_chip_mock.pack(pady=5)

        self.entry_type_mock = ctk.CTkEntry(form_frame, width=400, height=35)
        self.entry_type_mock.insert(0, "Typ: Obowiązkowe szczepienie (Wścieklizna)")
        self.entry_chip_mock.configure(state="disabled")
        self.entry_type_mock.pack(pady=5)

        # Hash wejściowy
        ctk.CTkLabel(form_frame, text="Wklej kryptograficzny SHA-256 hash pełnej dokumentacji:", 
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(20, 5))
        
        self.entry_reveal_hash = ctk.CTkEntry(form_frame, placeholder_text="Wpisz wynikowy hash...", width=400, height=38)
        self.entry_reveal_hash.pack(pady=5)

        # Przycisk akcji
        btn_auth = ctk.CTkButton(form_frame, text="🔒 Autoryzuj Reveal i Zamknij Wizytę", 
                                 width=400, height=45, 
                                 font=ctk.CTkFont(weight="bold"),
                                 command=self.submit_reveal)
        btn_auth.pack(pady=30)

    def submit_reveal(self):
        if not self.entry_reveal_hash.get():
            messagebox.showwarning("Błąd Reveal", "Musisz podać hash dokumentacji!")
            return
        
        messagebox.showinfo("Reveal Zweryfikowany", "Sukces! Stan zdrowia zwierzęcia zaktualizowany.")
        self.controller.show_frame("ScreenWeterynarzMain")

# ==========================================
# SEKCJA 2: HODOWCA (WIDOK GŁÓWNY)
# ==========================================
class ScreenHodowca(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Nagłówek i Tytuł (automatycznie row 0 i row 1)
        self.setup_header(
            btn_text="🔒 Wyloguj",
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text="● Rola: Hodowca zarejestrowany (ZKwP / PKR)",
            title="Panel Zarządzania Hodowlą"
        )

        # 2. Główna treść (row 2)
        content_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)

        # Przycisk dodawania
        btn_dodaj = ctk.CTkButton(content_frame, text="➕   DODAJ NOWE ZWIERZĘ / MIOT",
                                  width=400, height=50, font=ctk.CTkFont(size=14, weight="bold"),
                                  command=lambda: controller.show_frame("ScreenHodowcaDodaj"))
        btn_dodaj.pack(pady=(0, 20))

        # Etykieta tabeli
        ctk.CTkLabel(content_frame, text="📋 ZWIERZĘTA W HODOWLI:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))

        # Tabelka
        table_frame = ctk.CTkScrollableFrame(content_frame, fg_color="#a3aea3")
        table_frame.pack(fill="both", expand=True)

        # Dane zwierząt DEMO
        self.create_animal_row(table_frame, "DEMO  Imię: Reksio  |  Płeć: Samiec  |  Wiek: 2 lata  |  Czip: ISO-967000001234567", "ScreenHodowcaProfilReksio")
        self.create_animal_row(table_frame, "DEMO  Imię: Luna    |  Płeć: Samica  |  Wiek: 3 mies. |  Czip: [BRAK - Oczekuje]", "ScreenHodowcaProfilLuna")
        self.create_animal_row(table_frame, "DEMO  Imię: Ares    |  Płeć: Samiec  |  Wiek: 1 rok   |  Czip: ISO-967000008888888", "ScreenHodowcaProfilAres")

    def create_animal_row(self, parent, text, target_profile_frame):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=4, padx=5)
        
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12)).pack(side="left", padx=15, pady=8)
        
        btn = ctk.CTkButton(row, text="Profil 🐕", width=100, height=26,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             command=lambda: self.controller.show_frame(target_profile_frame))
        btn.pack(side="right", padx=10)

# ==========================================
# SEKCJA 2A: DODAWANIE ZWIERZĘCIA
# ==========================================
class ScreenHodowcaDodaj(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Nagłówek i Tytuł (automatycznie ustawia row 0 i row 1)
        self.setup_header(
            btn_text="← Powrót",
            btn_cmd=lambda: controller.show_frame("ScreenHodowca"),
            info_text="● Rola: Hodowca zarejestrowany (ZKwP / PKR)",
            title="Rejestracja Nowego Zwierzęcia w Księdze Rodowodowej"
        )

        # 2. Kontener formularza (row 2)
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=20)
        self.panel.grid_rowconfigure(2, weight=1)

        # Pola formularza
        self.entry_name = ctk.CTkEntry(form_frame, placeholder_text="Imię zwierzęcia (przydomek hodowlany)...", width=400, height=35)
        self.entry_name.grid(row=0, column=0, pady=8)

        self.dropdown_sex = ctk.CTkComboBox(form_frame, values=["Samiec", "Samica"], width=400, height=35)
        self.dropdown_sex.grid(row=1, column=0, pady=8)

        self.entry_birth = ctk.CTkEntry(form_frame, placeholder_text="Data urodzenia (RRRR-MM-DD)...", width=400, height=35)
        self.entry_birth.grid(row=2, column=0, pady=8)

        # Informacja o mikroczipie
        info_chip = ctk.CTkTextbox(form_frame, width=400, height=80, font=ctk.CTkFont(size=11), text_color="gray")
        info_chip.insert("0.0", "ℹ️ NUMER MIKROCZIPU:\nZwierzę rejestrowane jest w bazie hodowli przed znakowaniem. Unikalny numer mikroczipu zostanie trwale powiązany z tym profilem przez uprawnionego weterynarza podczas pierwszej wizyty.")
        info_chip.configure(state="disabled")
        info_chip.grid(row=3, column=0, pady=10)

        # Przycisk zapisu
        btn_save = ctk.CTkButton(form_frame, text="💾 Zapisz w Lokalnym Węźle Hodowli",
                                 width=400, height=45, font=ctk.CTkFont(weight="bold"),
                                 command=self.action_save_animal)
        btn_save.grid(row=4, column=0, pady=15)

    def action_save_animal(self):
        if not self.entry_name.get():
            messagebox.showwarning("Błąd", "Wprowadź imię zwierzęcia!")
            return
        
        messagebox.showinfo("Sukces", "Profil zwierzęcia został utworzony lokalnie.\nOczekuje na przypisanie mikroczipu.")
        self.controller.show_frame("ScreenHodowca")

# ==========================================
# SEKCJA 2B: PROFIL ZWIERZECIA
# ==========================================
class BaseAnimalProfileScreen(BaseScreen):
    def __init__(self, parent, controller, animal_data):
        super().__init__(parent, controller)
        self.animal_data = animal_data 

        self.setup_header(
            btn_text="← Powrót",
            btn_cmd=lambda: controller.show_frame("ScreenHodowca"),
            info_text="● Rola: Hodowca zarejestrowany (ZKwP / PKR)",
            title="Karta Profilowa Zwierzęcia"
        )

        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=10)

        self.create_disabled_field(form_frame, "Imię:", animal_data["name"], 0)
        self.create_disabled_field(form_frame, "Płeć:", animal_data["sex"], 1)
        self.create_disabled_field(form_frame, "Data urodzenia:", animal_data["birth"], 2)
        self.create_disabled_field(form_frame, "Numer Mikroczipu:", animal_data["chip"], 3)

        # Logika sprawdzająca gotowość (tylko do zmiany koloru przycisku)
        has_chip = animal_data.get("chip") and "BRAK" not in animal_data.get("chip", "").upper()
        pedigree_list = animal_data.get("pedigree_check", [False, False, False])
        is_ready = has_chip and all(pedigree_list)

        # Przycisk: kolor zmienia się w zależności od gotowości, 
        # ale ZAWSZE wywołuje validate_and_generate, żeby pokazać komunikat błędu
        btn_rodowod = ctk.CTkButton(
            self.panel, 
            text="💎 GENERUJ RODOWÓD CYFROWY (SBT)", 
            width=400, 
            height=38, 
            font=ctk.CTkFont(weight="bold"),
            state="normal" if is_ready else "disabled",
            command=self.validate_and_generate 
        )
        btn_rodowod.grid(row=3, column=0, pady=20)

        # Sekcja historii
        ctk.CTkLabel(self.panel, text="🩺 Historia leczenia:", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=4, column=0, sticky="w", padx=50, pady=(10, 0))
        
        history_frame = ctk.CTkScrollableFrame(self.panel, fg_color="#a3aea3")
        history_frame.grid(row=5, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(5, weight=1)

        if not animal_data.get("history"):
            ctk.CTkLabel(history_frame, text="[Brak wpisów]", text_color="gray", font=ctk.CTkFont(slant="italic")).pack(pady=20)
        else:
            for entry in animal_data["history"]:
                self.create_history_row(history_frame, entry)

    def validate_and_generate(self):
        """Weryfikacja z wyświetlaniem komunikatów o błędach."""
        has_chip = self.animal_data.get("chip") and "BRAK" not in self.animal_data.get("chip", "").upper()
        pedigree_status = self.animal_data.get("pedigree_check", [False, False, False])
        
        if not has_chip:
            messagebox.showerror("Błąd", "Brak mikroczipu!")
        elif not all(pedigree_status):
            failed_gen = pedigree_status.index(False) + 1
            gen_names = ["rodziców", "dziadków", "pradziadków"]
            messagebox.showerror("Odrzucono", f"Błąd weryfikacji pokolenia {failed_gen} ({gen_names[failed_gen-1]}).")
        else:
            self.generate_pedigree_success()

    def generate_pedigree_success(self):
        messagebox.showinfo("Sukces", "Walidacja zakończona pomyślnie. Wyemitowano Soulbound Token (SBT).")
        self.controller.show_frame("ScreenHodowca")

    def create_disabled_field(self, parent, label_text, value_text, row_idx):
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=12), text_color="gray").grid(row=row_idx, column=0, sticky="e", padx=10, pady=3)
        entry = ctk.CTkEntry(parent, width=300, height=28)
        entry.insert(0, value_text)
        entry.configure(state="disabled")
        entry.grid(row=row_idx, column=1, pady=3)

    def create_history_row(self, parent, text):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=2, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12), justify="left").pack(side="left", padx=10, pady=5)

# ==========================================
# SEKCJA 2B-1 DEMO: REKSIO (SUKCES RODOWODU)
# ==========================================
class ScreenHodowcaProfilReksio(BaseAnimalProfileScreen):
    def __init__(self, parent, controller):
        data = {
            "name": "Reksio (Z Górskiej Doliny)",
            "sex": "Samiec",
            "birth": "2024-03-12",
            "chip": "ISO-967000001234567",
            "pedigree_check": [True, True, True],
            "history": [
                "2026-05-24 | Lekarz: KILW-9921 | Zabieg: Szczepienie wścieklizna",
                "2026-04-10 | Lekarz: KILW-9921 | Zabieg: Konsultacja (Zapalenie jelit)"
            ]
        }
        super().__init__(parent, controller, data)

# ==========================================
# SEKCJA 2B-2 DEMO: LUNA (BRAK CZIPU)
# ==========================================
class ScreenHodowcaProfilLuna(BaseAnimalProfileScreen):
    def __init__(self, parent, controller):
        data = {
            "name": "Luna (Z Górskiej Doliny)",
            "sex": "Samica",
            "birth": "2026-02-15",
            "chip": "[BRAK - Oczekuje na identyfikację]",
            "pedigree_check": [True, True, True], 
            "history": [] 
        }
        super().__init__(parent, controller, data)

# ==========================================
# SEKCJA 2B-3 DEMO: ARES (BŁĄD WALIDACJI RODOWODU)
# ==========================================
class ScreenHodowcaProfilAres(BaseAnimalProfileScreen):
    def __init__(self, parent, controller):
        data = {
            "name": "Ares",
            "sex": "Samiec",
            "birth": "2025-05-10",
            "chip": "ISO-967000008888888",
            # Poniżej: [Rodzice, Dziadkowie, Pradziadkowie]
            "pedigree_check": [True, True, False], 
            "history": ["2025-11-12 | Lekarz: KILW-1105 | Zabieg: Profilaktyka pasożytnicza"]
        }
        super().__init__(parent, controller, data)    

# ==========================================
# SEKCJA 3: SCHRONISKO / FUNDACJA (WIDOK GŁÓWNY)
# ==========================================
class ScreenSchronisko(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Nagłówek i Tytuł (automatycznie row 0 i row 1)
        self.setup_header(
            btn_text="🔒 Wyloguj", 
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text="● Rola: Schronisko / Fundacja (Autoryzowany Węzeł)",
            title="Panel Zarządzania Azylem i Adopcjami"
        )

        # 2. Główna treść (row 2)
        content = ctk.CTkFrame(self.panel, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Przycisk dodawania
        btn_dodaj = ctk.CTkButton(content, text="➕   REJESTRUJ NOWE ZWIERZĘ (Przyjęcie do azylu)",
                                  width=400, height=50, font=ctk.CTkFont(size=14, weight="bold"),
                                  command=lambda: controller.show_frame("ScreenSchroniskoDodaj"))
        btn_dodaj.pack(pady=(0, 20))

        # Etykieta tabeli
        ctk.CTkLabel(content, text="📋 ZWIERZĘTA W AZYLU:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20)

        # Tabelka (ScrollableFrame)
        table_frame = ctk.CTkScrollableFrame(content, fg_color="#a3aea3")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Dane zwierząt
        self.create_shelter_row(table_frame, "DEMO Imię: Bary   |  Gatunek: Pies  |  Płeć: Samiec  |  Wiek: ok. 2020  |  Status: Gotowy", "ScreenSchroniskoProfilBary")
        self.create_shelter_row(table_frame, "DEMO Imię: Sonia   |  Gatunek: Pies  |  Płeć: Samica  |  Wiek: ok. 2023  |  Status: Kwarantanna", "ScreenSchroniskoProfilSonia")

    def create_shelter_row(self, parent, text, target_frame):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=4, padx=5)
        
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12)).pack(side="left", padx=15, pady=8)
        
        btn = ctk.CTkButton(row, text="Karta 🐾", width=100, height=26, 
                             font=ctk.CTkFont(size=11, weight="bold"),
                             command=lambda: self.controller.show_frame(target_frame))
        btn.pack(side="right", padx=10)

# ==========================================
# SEKCJA 3A: DODAWANIE ZWIERZĘCIA (SCHRONISKO)
# ==========================================
class ScreenSchroniskoDodaj(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Nagłówek i Tytuł
        self.setup_header(
            btn_text="← Anuluj",
            btn_cmd=lambda: controller.show_frame("ScreenSchronisko"),
            info_text="● Rola: Schronisko / Fundacja (Autoryzowany Węzeł)",
            title="Formularz Przyjęcia Zwierzęcia do Schroniska"
        )

        # 2. Kontener formularza
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=20)
        self.panel.grid_rowconfigure(2, weight=1)

        # Pola formularza
        self.entry_name = ctk.CTkEntry(form_frame, placeholder_text="Imię robocze zwierzęcia...", width=400, height=35)
        self.entry_name.grid(row=0, column=0, pady=8)

        # NOWOŚĆ: Wybór gatunku
        self.dropdown_species = ctk.CTkComboBox(form_frame, values=["Pies", "Kot", "Inne"], width=400, height=35)
        self.dropdown_species.set("Pies") # Wartość domyślna
        self.dropdown_species.grid(row=1, column=0, pady=8)

        self.dropdown_sex = ctk.CTkComboBox(form_frame, values=["Samiec", "Samica"], width=400, height=35)
        self.dropdown_sex.grid(row=2, column=0, pady=8)

        # Szacowany rok urodzenia
        ctk.CTkLabel(form_frame, text="Szacowany rok urodzenia:", font=ctk.CTkFont(size=12), text_color="gray").grid(row=3, column=0, sticky="w", pady=(5, 2))
        lata = [str(rok) for rok in range(2010, 2027)]
        self.dropdown_year = ctk.CTkComboBox(form_frame, values=lata, width=400, height=35)
        self.dropdown_year.set("2022")
        self.dropdown_year.grid(row=4, column=0, pady=5)

        self.entry_chip = ctk.CTkEntry(form_frame, placeholder_text="Numer czipu (zostaw puste jeśli brak)...", width=400, height=35)
        self.entry_chip.grid(row=5, column=0, pady=12)

        # Przycisk zapisu
        btn_save = ctk.CTkButton(form_frame, text="📝 Rejestruj przyjęcie w Ledgerze", 
                                 width=400, height=45, font=ctk.CTkFont(weight="bold"),
                                 command=self.action_save_shelter)
        btn_save.grid(row=6, column=0, pady=15)

    def action_save_shelter(self):
        if not self.entry_name.get():
            messagebox.showwarning("Błąd", "Wprowadź imię zwierzęcia!")
            return
        
        # 1. DANE LOKALNE (Off-chain)
        # Przechowujemy imię, gatunek i inne detale w bazie serwera schroniska
        local_data = {
            "name": self.entry_name.get(),
            "species": self.dropdown_species.get(),
            "sex": self.dropdown_sex.get(),
            "birth_year": self.dropdown_year.get()
        }
        
        # 2. DANE DO BLOCKCHAINA (On-chain)
        # Zgodnie z zasadą commit-reveal: rejestrujemy fakt przyjęcia i czip (jeśli istnieje)
        blockchain_record = {
            "chip_id": self.entry_chip.get() if self.entry_chip.get() else "NO_CHIP",
            "shelter_id": "SHELTER_PK_001", # ID Twojej placówki
            "status": "in_shelter"
        }
        
        # Tutaj symulujemy wysyłkę do Twojego Smart Contractu
        print(f"Blockchain Commit: {blockchain_record}")
        
        messagebox.showinfo("Sukces", f"Zarejestrowano: {local_data['species']} - {local_data['name']}.\nWygenerowano alert o znalezieniu w Ledgerze.")
        self.controller.show_frame("ScreenSchronisko")


# ==========================================
# SEKCJA 3B: KARTA ADOPCYJNA
# ==========================================
class ShelterAnimalProfileScreen(BaseScreen):
    def __init__(self, parent, controller, animal_data):
        super().__init__(parent, controller)
        self.animal_data = animal_data 
        
        # Flaga gotowości do ZKP (szczepienia + kastracja)
        self.is_ready = animal_data.get("vaccines_ok", False) and animal_data.get("neutered", False)

        # 1. Nagłówek
        self.setup_header(
            btn_text="← Powrót",
            btn_cmd=lambda: controller.show_frame("ScreenSchronisko"),
            info_text="● Rola: Schronisko / Fundacja (Autoryzowany Węzeł)",
            title="Profil Zwierzęcia (Azyl)"
        )

        # 2. Kontener danych (Grid)
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=2, column=0, pady=10)

        self.create_disabled_field(form_frame, "Imię:", animal_data.get("name", "Brak"), 0)
        self.create_disabled_field(form_frame, "Gatunek:", animal_data.get("species", "Nieokreślony"), 1)
        self.create_disabled_field(form_frame, "Płeć:", animal_data.get("sex", "Brak"), 2)
        self.create_disabled_field(form_frame, "Rok urodzenia:", animal_data.get("birth", "Brak"), 3)
        self.create_disabled_field(form_frame, "Numer Mikroczipu:", animal_data.get("chip", "Brak"), 4)

        status_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        status_frame.grid(row=3, column=0, pady=10)

        # Szczepienia
        vax_color = "black" if animal_data.get("vaccines_ok") else "#e74c3c"
        vax_text = "💉 Szczepienia: AKTUALNE" if animal_data.get("vaccines_ok") else "💉 Szczepienia: NIEAKTUALNE ⚠️"
        ctk.CTkLabel(status_frame, text=vax_text, text_color=vax_color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15)

        # Kastracja
        neut_color = "black" if animal_data.get("neutered") else "#e74c3c"
        neut_text = "✂️ Kastracja: WYKONANO" if animal_data.get("neutered") else "✂️ Kastracja: BRAK ⚠️"
        ctk.CTkLabel(status_frame, text=neut_text, text_color=neut_color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=15)

        # 3. Przycisk ZKP (aktywny tylko przy pełnych wymogach)
        self.btn_zkp = ctk.CTkButton(
            self.panel, text="🔑 Generuj klucz weryfikacji ZKP", 
            width=400, height=35, font=ctk.CTkFont(weight="bold"),
            state="normal" if self.is_ready else "disabled",
            command=self.generate_zkp
        )
        self.btn_zkp.grid(row=4, column=0, pady=(10, 10))

        # 4. Historia medyczna (zawsze widoczna na dole)
        ctk.CTkLabel(self.panel, text="🩺 Historia medyczna z Ledgera:", 
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=4, column=0, sticky="w", padx=50, pady=(10, 0))
        
        history_frame = ctk.CTkScrollableFrame(self.panel, fg_color="#a3aea3")
        history_frame.grid(row=5, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(5, weight=1)

        history = animal_data.get("history", [])
        if not history:
            ctk.CTkLabel(history_frame, text="[Brak wpisów]", text_color="gray", font=ctk.CTkFont(slant="italic")).pack(pady=20)
        else:
            for entry in history:
                self.create_history_row(history_frame, entry)

    def generate_zkp(self):
        if not self.is_ready:
            messagebox.showerror("Błąd", "Zwierzę nie spełnia wymogów (szczepienia/kastracja).")
            return
        
        token = f"0xZKP_{self.animal_data.get('name', 'ANIMAL').upper()}_2026_VALID"
        messagebox.showinfo("Wygenerowano Klucz ZKP", f"Sukces!\n\nKlucz dostępu:\n{token}")

    def create_disabled_field(self, parent, label_text, value_text, row_idx):
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=12), text_color="gray").grid(row=row_idx, column=0, sticky="e", padx=10, pady=3)
        entry = ctk.CTkEntry(parent, width=300, height=28)
        entry.insert(0, value_text)
        entry.configure(state="disabled")
        entry.grid(row=row_idx, column=1, pady=3)

    def create_history_row(self, parent, text):
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", pady=2, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12), justify="left").pack(side="left", padx=10, pady=5)

# ==========================================
# SEKCJA 3B-1 DEMO: BARY (SUKCES)
# ==========================================
class ScreenSchroniskoProfilBary(ShelterAnimalProfileScreen):
    def __init__(self, parent, controller):
        bary_data = {
            "name": "Bary", 
            "species": "Pies", 
            "sex": "Samiec", 
            "birth": "2020",
            "chip": "ISO-96700000888888",
            "vaccines_ok": True,  # Spełnia wymogi
            "neutered": True,     # Spełnia wymogi
            "history": [
                "2026-05-10 | Przyjęcie", 
                "2026-05-15 | Kastracja"
            ]
        }
        # Klasa nadrzędna sama zajmie się renderowaniem pól, 
        # statusów oraz przycisku ZKP (będzie aktywny)
        super().__init__(parent, controller, bary_data)

# ==========================================
# SEKCJA 3B-2 DEMO: SONIA (BLOKADA)
# ==========================================
class ScreenSchroniskoProfilSonia(ShelterAnimalProfileScreen):
    def __init__(self, parent, controller):
        sonia_data = {
            "name": "Sonia",
            "species": "Pies",
            "sex": "Samica",
            "birth": "2023",
            "chip": "ISO-96700000444444",
            "vaccines_ok": False,  # Blokuje przycisk ZKP
            "neutered": False,     # Blokuje przycisk ZKP
            "history": ["2026-05-20 | Przyjęcie do schroniska"]
        }
        # Klasa nadrzędna automatycznie ustawi przycisk ZKP w stan "disabled"
        # oraz wyświetli czerwone ostrzeżenia o brakach
        super().__init__(parent, controller, sonia_data)

# ==========================================
# WIDOK 4: KARTA ZDROWIA - PEŁNY WŁAŚCICIEL
# ==========================================
class ScreenWlasciciel(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Nagłówek i Tytuł (automatycznie row 0 i row 1)
        self.setup_header(
            btn_text="🔒 Wyloguj",
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text="● Rola: Właściciel (Pełny Dostęp)",
            title="Karta Zdrowia Zwierzęcia"
        )

        # 2. Główna treść (row 2)
        content_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)

        # Karta zdrowia (wyświetlana w content_frame)
        profile = ctk.CTkFrame(content_frame, fg_color="#a3aea3")
        profile.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(profile, text="🐕 Reksio (Owczarek)", 
                      font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(profile, text="ID mikroczipu: ISO-967000001234567 | Koszt utrzymania (YTD): 1,420 PLN", 
                      font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(0, 10))

        # Przycisk generowania klucza
        btn_key = ctk.CTkButton(content_frame, text="🔑 Generuj tymczasowy klucz dostępu dla kupującego (Ważny 24h)", 
                                width=500, height=45,
                                command=self.action_generate_zkp_key)
        btn_key.pack(pady=10)

        # Sekcja historii
        ctk.CTkLabel(content_frame, text="Pełna Historia Zabiegów (Blockchain):", 
                      font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        timeline = ctk.CTkScrollableFrame(content_frame, fg_color="#a3aea3")
        timeline.pack(fill="both", expand=True)

        # Wiersze historii
        self.add_timeline_item(timeline, "24.05.2026 | Szczepienie wścieklizna (Rabisin) - 120 PLN", "🔒 ZWERYFIKOWANO", "black")
        self.add_timeline_item(timeline, "10.04.2026 | Odroczenie szczepień (Zapalenie jelit) - 150 PLN", "⚠️ WYJĄTEK OK", "#e67e22")
        self.add_timeline_item(timeline, "15.03.2026 | RTG Stawów (Badanie kliniczne) - 450 PLN", "✓ SPÓJNY HASH", "#3498db")

    def add_timeline_item(self, parent, text, status, color):
        item = ctk.CTkFrame(parent)
        item.pack(fill="x", pady=3, padx=5)
        
        ctk.CTkLabel(item, text=text, justify="left").pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(item, text=status, text_color=color, font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=10)

    def action_generate_zkp_key(self):
        mock_pet_key = b"12345678901234567890123456789012"
        token_for_buyer = base64.b64encode(mock_pet_key).decode('utf-8')
        
        # Kopiowanie do schowka
        self.clipboard_clear()
        self.clipboard_append(token_for_buyer)
        
        messagebox.showinfo(
            "Zarządzanie Prywatnością (KILW)", 
            f"Sukces!\n\nWygenerowano tymczasowy klucz deszyfrujący dla kupującego.\n"
            f"Klucz skopiowano do schowka:\n{token_for_buyer[:15]}..."
        )

# ==========================================
# WIDOK 5: KARTA ZDROWIA - UKRYTY KUPUJĄCY
# ==========================================
class ScreenKupujacy(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Nagłówek i Tytuł (automatycznie row 0 i row 1)
        self.setup_header(
            btn_text="🔒 Wyloguj",
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text="● Rola: Weryfikator / Kupujący (ZKP View)",
            title="Karta Zdrowia Zwierzęcia (ZKP)"
        )

        # Dane do demo
        self.blockchain_mock_data = [
            {"med": "24.05.2026 | Szczepienie wścieklizna aktywne.\nAutoryzacja weterynarza: Pomyślna.", "fin": "Koszt: 120 PLN"},
            {"med": "10.04.2026 | Odroczenie szczepień (Wskazania medyczne).\nPowód: Leczenie gastryczne.", "fin": "Koszt: 150 PLN"},
            {"med": "15.03.2026 | Wykonano badanie RTG stawów.\nDowód kryptograficzny: ZGODNY.", "fin": "Koszt: 450 PLN"}
        ]

        # 2. Główna treść (row 2)
        content_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(2, weight=1)

        # Karta zdrowia
        profile = ctk.CTkFrame(content_frame, fg_color="#a3aea3")
        profile.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(profile, text="🐕 Reksio (Owczarek)", 
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        ctk.CTkLabel(profile, text="ID mikroczipu: ISO-967000001234567 | Dane finansowe: [ZABLOKOWANE DLA ZKP]", 
                     text_color="#e74c3c", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(0, 10))

        # Sekcja historii
        ctk.CTkLabel(content_frame, text="Zweryfikowana Historia Medyczna (Dane publiczne ZKP):", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        self.timeline = ctk.CTkScrollableFrame(content_frame, fg_color="#a3aea3")
        self.timeline.pack(fill="both", expand=True)

        self.decrypt_and_render_timeline()

    def decrypt_and_render_timeline(self):
        # Symulacja klucza (w realnym użyciu pobierany z controller.current_key)
        secret_key = b"12345678901234567890123456789012" 
        wrong_key = b"wrong_key_32_bytes_long_bad_bad"
        
        for item in self.blockchain_mock_data:
            encrypted = VetChainCrypto.encrypt_visit_data(secret_key, item["med"], item["fin"])
            
            decrypted_med = VetChainCrypto.decrypt_section(secret_key, encrypted["med_data"])
            decrypted_fin = VetChainCrypto.decrypt_section(wrong_key, encrypted["fin_data"])
            
            display_text = f"{decrypted_med}\nFinanse: {decrypted_fin}"
            self.add_timeline_item(self.timeline, display_text, "🔒 ZWERYFIKOWANO", "black")

    def add_timeline_item(self, parent, text, status, color):
        item = ctk.CTkFrame(parent)
        item.pack(fill="x", pady=3, padx=5)
        
        ctk.CTkLabel(item, text=text, justify="left").pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(item, text=status, text_color=color, font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=10)

# ==========================================
# GŁÓWNA KLASA ZARZĄDZAJĄCA APLIKACJĄ
# ==========================================
class VetChainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VetChain - Zdecentralizowana Karta Zdrowia Zwierząt")
        self.geometry("1440x900")
        self.minsize(1000, 700)
        self.resizable(True, True)
        
        self.attributes('-fullscreen', False)
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)

        # Kontener główny
        self.container = ctk.CTkFrame(self, fg_color="#a3aea3") # Stały kolor tła
        self.container.pack(side="top", fill="both", expand=True)  
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "ScreenLogin": ScreenLogin,
            "ScreenWeterynarzMain": ScreenWeterynarzMain,
            "ScreenWeterynarzDodaj": ScreenWeterynarzDodaj,
            "ScreenWeterynarzUzupelnij": ScreenWeterynarzUzupelnij,
            "ScreenHodowca": ScreenHodowca,
            "ScreenHodowcaDodaj": ScreenHodowcaDodaj,
            "ScreenHodowcaProfilReksio": ScreenHodowcaProfilReksio,
            "ScreenHodowcaProfilLuna": ScreenHodowcaProfilLuna,
            "ScreenHodowcaProfilAres": ScreenHodowcaProfilAres,
            "ScreenSchronisko": ScreenSchronisko,
            "ScreenSchroniskoDodaj": ScreenSchroniskoDodaj,
            "ScreenSchroniskoProfilBary": ScreenSchroniskoProfilBary,
            "ScreenSchroniskoProfilSonia": ScreenSchroniskoProfilSonia,
            "ScreenWlasciciel": ScreenWlasciciel,
            "ScreenKupujacy": ScreenKupujacy
        }

        self.current_frame = None
        self.show_frame("ScreenLogin")

    def show_frame(self, page_name):
        if self.current_frame is not None:
            self.current_frame.destroy()

        frame_class = self.pages[page_name]
        self.current_frame = frame_class(parent=self.container, controller=self)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def toggle_fullscreen(self, event=None):
        is_full = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_full)

    def exit_fullscreen(self, event=None):
        self.attributes("-fullscreen", False)

# Uruchomienie aplikacji
if __name__ == "__main__":
    ctk.set_appearance_mode("Light") 
    
    try:
        ctk.set_default_color_theme("vetchain_theme.json")
    except Exception as e:
        print(f"⚠️ Nie znaleziono pliku motywu vetchain_theme.json: {e}")

    app = VetChainApp()
    app.mainloop()