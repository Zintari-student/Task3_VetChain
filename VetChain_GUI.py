import customtkinter as ctk
from tkinter import messagebox


ctk.set_default_color_theme("sage-teal_theme.json")



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
        self.panel.grid_columnconfigure(0, weight=1)
        self.panel.grid_rowconfigure(1, weight=1) # Row 1 to treść

        # NAGŁÓWEK
        self.header = ctk.CTkFrame(self.panel, fg_color="transparent", height=50)
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        # Kolumna 0: Przycisk (lewa), Kolumna 1: ID/Rola (prawa)
        # Weight 1 dla kolumny 0 sprawia, że przycisk jest po lewej, a label się do niego nie klei
        self.header.grid_columnconfigure(0, weight=1) 

        # Inicjalizacja komponentów
        self.btn_nav = ctk.CTkButton(self.header, width=90, fg_color="#333333")
        self.lbl_info = ctk.CTkLabel(self.header, font=ctk.CTkFont(weight="bold"))

    def setup_header(self, btn_text=None, btn_cmd=None, info_text=None):
        # Przycisk (lewy)
        if btn_text and btn_cmd:
            self.btn_nav.configure(text=btn_text, command=btn_cmd)
            self.btn_nav.grid(row=0, column=0, sticky="w")
        else:
            self.btn_nav.grid_forget()

        # ID/Rola (prawy)
        if info_text:
            self.lbl_info.configure(text=info_text)
            self.lbl_info.grid(row=0, column=1, sticky="e")
        else:
            self.lbl_info.grid_forget()

# ==========================================
# EKRAN LOGOWANIA
# ==========================================
class ScreenLogin(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
                
        # UI Logowania (treść zaczynamy od row 1, ponieważ nagłówek zajmuje row 0)
        # Używamy kontenera pomocniczego wewnątrz self.panel, aby łatwo wszystko wycentrować
        login_content = ctk.CTkFrame(self.panel, fg_color="transparent")
        login_content.grid(row=1, column=0, sticky="nsew", pady=20)
        login_content.grid_columnconfigure(0, weight=1)

        # Nagłówek główny
        ctk.CTkLabel(login_content, text="VetChain System", 
                     font=ctk.CTkFont(size=42, weight="bold")).pack(pady=(20, 10))

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

        # 1. Nagłówek (grid wewnątrz self.panel)
        header = ctk.CTkFrame(self.panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(header, text="🔒 Wyloguj", width=80, fg_color="#333333", hover_color="#1a1a1a",
              command=lambda: controller.show_frame("ScreenLogin")).grid(row=0, column=0, padx=0, pady=10, sticky="w")

        ctk.CTkLabel(header, text="● Rola: Lekarz Weterynarii (KILW)", 
             font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=0, pady=10, sticky="e")

        # 2. Tytuł
        ctk.CTkLabel(self.panel, text="Panel Zarządzania Wizytami Weterynaryjnymi", 
                      font=ctk.CTkFont(size=22, weight="bold")).grid(row=1, column=0, pady=(5, 10))

        # 3. Kontener główny (podział na kolumny)
        main_columns = ctk.CTkFrame(self.panel, fg_color="transparent")
        main_columns.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        self.panel.grid_rowconfigure(2, weight=1)
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

        ctk.CTkLabel(inner_right, text="🔍 Przeszukaj Ewidencję Blockchain", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        
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

        header = ctk.CTkFrame(self.panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(header, text="← Anuluj", width=80, fg_color="#333333", hover_color="#1a1a1a",
              command=lambda: controller.show_frame("ScreenWeterynarzMain")).grid(row=0, column=0, padx=0, pady=10, sticky="w")

        ctk.CTkLabel(header, text="● Rola: Lekarz Weterynarii (KILW)", 
             font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=0, pady=10, sticky="e")

        # Nagłówek
        ctk.CTkLabel(self.panel, text="Inicjowanie Nowej Wizyty w Blockchain", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Kontener na formularz - wyśrodkowany
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=1, column=0, pady=20)

        # Pola formularza
        self.entry_chip = ctk.CTkEntry(form_frame, placeholder_text="Numer mikroczipu (ISO)...", width=400, height=35)
        self.entry_chip.grid(row=0, column=0, pady=8)

        self.dropdown_type = ctk.CTkComboBox(form_frame, values=["Obowiązkowe szczepienie (Wścieklizna)", "Badanie ogólne / Kontrola", "Wyjątek medyczny (Choroba - Opóźnienie szczepienia)"], width=400, height=35)
        self.dropdown_type.grid(row=1, column=0, pady=8)

        self.entry_desc = ctk.CTkEntry(form_frame, placeholder_text="Zastosowane leki / Opis...", width=400, height=35)
        self.entry_desc.grid(row=2, column=0, pady=8)

        ctk.CTkLabel(form_frame, text="Kryptograficzny Hash Dokumentacji Medycznej (Opcjonalnie):", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=3, column=0, pady=(10, 2), sticky="w")
        self.entry_hash = ctk.CTkEntry(form_frame, placeholder_text="np. 2cf24dba5...", width=400, height=35)
        self.entry_hash.grid(row=4, column=0, pady=5)

        # Kontener na przyciski aktywacji
        actions_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        actions_frame.grid(row=5, column=0, pady=30)

        # Przycisk A
        btn_full = ctk.CTkButton(actions_frame, text="🔒 Podpisz i Wyślij\n(Pełny Commit + Reveal)", fg_color="#333333", hover_color="#1a1a1a", width=200, height=50, font=ctk.CTkFont(weight="bold"),
                                 command=self.action_full_submit)
        btn_full.grid(row=0, column=0, padx=10)

        # Przycisk B
        btn_later = ctk.CTkButton(actions_frame, text="⏳ Tylko zarejestruj czas\n(Commit, Hash później)", width=200, height=50, font=ctk.CTkFont(weight="bold"),
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

        # Nagłówek - przycisk anuluj w lewym górnym rogu
        ctk.CTkButton(self.panel, text="← Anuluj", width=80, 
                      command=lambda: controller.show_frame("ScreenWeterynarzMain")).grid(row=0, column=0, padx=20, pady=20, sticky="nw")

        ctk.CTkLabel(self.panel, text="Protokół Reveal: Uzupełnianie Hashu Dokumentacji", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Kontener formularza
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=1, column=0, pady=20)

        # Dane wizyty (zablokowane)
        ctk.CTkLabel(form_frame, text="Dane zarejestrowanego bloku wizyty (Zablokowane):", font=ctk.CTkFont(size=12), text_color="gray").grid(row=0, column=0, sticky="w", pady=(0, 2))
        
        self.entry_chip_mock = ctk.CTkEntry(form_frame, width=400, height=35)
        self.entry_chip_mock.insert(0, "ISO-967000001234567")
        self.entry_chip_mock.configure(state="disabled")
        self.entry_chip_mock.grid(row=1, column=0, pady=5)

        self.entry_type_mock = ctk.CTkEntry(form_frame, width=400, height=35)
        self.entry_type_mock.insert(0, "Typ: Obowiązkowe szczepienie (Wścieklizna)")
        self.entry_type_mock.configure(state="disabled")
        self.entry_type_mock.grid(row=2, column=0, pady=5)

        # Hash wejściowy
        ctk.CTkLabel(form_frame, text="Wklej kryptograficzny SHA-256 hash pełnej dokumentacji:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#e67e22").grid(row=3, column=0, pady=(20, 5), sticky="w")
        
        self.entry_reveal_hash = ctk.CTkEntry(form_frame, placeholder_text="Wpisz wynikowy hash dokumentacji (64 znaki Hex)...", width=400, height=38)
        self.entry_reveal_hash.grid(row=4, column=0, pady=5)

        # Przycisk akcji
        btn_auth = ctk.CTkButton(form_frame, text="🔒 Autoryzuj Reveal i Zamknij Wizytę", fg_color="#e67e22", hover_color="#d35400", width=400, height=45, font=ctk.CTkFont(weight="bold"),
                                 command=self.submit_reveal)
        btn_auth.grid(row=5, column=0, pady=30)

    def submit_reveal(self):
        if not self.entry_reveal_hash.get():
            messagebox.showwarning("Błąd Reveal", "Musisz podać hash dokumentacji, aby dokonać ujawnienia danych!")
            return
        
        messagebox.showinfo("Reveal Zweryfikowany", "Sukces! Hash dopasowany do pierwotnego znacznika czasu (Commit).\nStan zdrowia zwierzęcia został zaktualizowany.")
        self.controller.show_frame("ScreenWeterynarzMain")

# ==========================================
# SEKCJA 2: HODOWCA (WIDOK GŁÓWNY)
# ==========================================
class ScreenHodowca(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Naglowek
        header = ctk.CTkFrame(self.panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        header.grid_columnconfigure(1, weight=1)
        
        ctk.CTkButton(header, text="🔒 Wyloguj", width=80, fg_color="#333333", hover_color="#1a1a1a",
              command=lambda: controller.show_frame("ScreenLogin")).grid(row=0, column=0, padx=0, pady=10, sticky="w")

        ctk.CTkLabel(header, text="● Rola: Hodowca zarejestrowany (ZKwP / PKR)",
             font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=0, pady=10, sticky="e")

        # 2. Tytuł panelu
        ctk.CTkLabel(self.panel, text="Panel Zarządzania Hodowlą", 
                     font=ctk.CTkFont(size=22, weight="bold")).grid(row=1, column=0, pady=15)

        # 3. Przycisk dodawania
        btn_dodaj = ctk.CTkButton(self.panel, text="➕   DODAJ NOWE ZWIERZĘ / MIOT",
                                  width=400, height=50, font=ctk.CTkFont(size=14, weight="bold"),
                                  command=lambda: controller.show_frame("ScreenHodowcaDodaj"))
        btn_dodaj.grid(row=2, column=0, pady=20)

        # 4. Kontener tabeli
        table_container = ctk.CTkFrame(self.panel, fg_color="transparent")
        table_container.grid(row=3, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(table_container, text="📋 ZWIERZĘTA W HODOWLI:", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        # 5. Tabelka
        table_frame = ctk.CTkScrollableFrame(table_container, fg_color="#a3aea3")
        table_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Dane zwierząt DEMO
        self.create_animal_row(table_frame, "Imię: Reksio  |  Płeć: Samiec  |  Wiek: 2 lata  |  Czip: ISO-967000001234567", "ScreenHodowcaProfilReksio")
        self.create_animal_row(table_frame, "Imię: Luna    |  Płeć: Samica  |  Wiek: 3 mies. |  Czip: [BRAK - Oczekuje]", "ScreenHodowcaProfilLuna")
        self.create_animal_row(table_frame, "Imię: Ares    |  Płeć: Samiec  |  Wiek: 1 rok   |  Czip: ISO-967000008888888", "ScreenHodowcaProfilAres")

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

        # Nagłówek i przycisk powrotu
        ctk.CTkButton(self.panel, text="← Anuluj", width=80, fg_color="#333333", hover_color="#1a1a1a", 
                      command=lambda: controller.show_frame("ScreenHodowca")).grid(row=0, column=0, padx=20, pady=20, sticky="nw")

        ctk.CTkLabel(self.panel, text="Rejestracja Nowego Zwierzęcia w Księdze Rodowodowej", 
                      font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Kontener formularza
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=1, column=0, pady=20)

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
        btn_save = ctk.CTkButton(form_frame, text="💾 Zapisz w Lokalnym Węźle Hodowli", width=400, height=45, font=ctk.CTkFont(weight="bold"),
                                 command=self.action_save_animal)
        btn_save.grid(row=4, column=0, pady=15)

    def action_save_animal(self):
        if not self.entry_name.get():
            messagebox.showwarning("Błąd", "Wprowadź imię zwierzęcia!")
            return
        
        messagebox.showinfo("Sukces", "Profil zwierzęcia został utworzony lokalnie.\nOczekuje na przypisanie mikroczipu.")
        self.controller.show_frame("ScreenHodowca")


# ==========================================
# SEKCJA 2B: PROFIL - REKSIO (SUKCES RODOWODU)
# ==========================================
class ScreenHodowcaProfilReksio(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Przycisk Powrót
        ctk.CTkButton(self.panel, text="← Powrót", width=80, 
                      command=lambda: controller.show_frame("ScreenHodowca")).grid(row=0, column=0, padx=20, pady=20, sticky="nw")

        ctk.CTkLabel(self.panel, text="Karta Profilowa Zwierzęcia", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Kontener danych
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=1, column=0, pady=10)

        self.create_disabled_field(form_frame, "Imię:", "Reksio (Z Górskiej Doliny)", 0)
        self.create_disabled_field(form_frame, "Płeć:", "Samiec", 1)
        self.create_disabled_field(form_frame, "Data urodzenia:", "2024-03-12", 2)
        self.create_disabled_field(form_frame, "Numer Mikroczipu:", "ISO-967000001234567", 3)

        # Przycisk rodowodu
        btn_rodowod = ctk.CTkButton(self.panel, text="💎 GENERUJ RODOWÓD CYFROWY (SBT)", fg_color="#1f538d", hover_color="#14375e", 
                                    width=400, height=38, font=ctk.CTkFont(weight="bold"),
                                    command=self.generate_pedigree_success)
        btn_rodowod.grid(row=2, column=0, pady=20)

        # Sekcja historii
        ctk.CTkLabel(self.panel, text="🩺 Historia leczenia (Surowe wpisy Blockchain):", 
                      font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=3, column=0, sticky="w", padx=50, pady=(10, 0))
        
        history_frame = ctk.CTkScrollableFrame(self.panel, fg_color="#a3aea3")
        history_frame.grid(row=4, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(4, weight=1)

        self.create_history_row(history_frame, "2026-05-24 | Lekarz: KILW-9921 | Zabieg: Szczepienie wścieklizna")
        self.create_history_row(history_frame, "2026-04-10 | Lekarz: KILW-9921 | Zabieg: Konsultacja (Zapalenie jelit)")

    def create_disabled_field(self, parent, label_text, value_text, row_idx):
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=11), text_color="gray").grid(row=row_idx, column=0, sticky="e", padx=10, pady=3)
        entry = ctk.CTkEntry(parent, width=300, height=28)
        entry.insert(0, value_text)
        entry.configure(state="disabled")
        entry.grid(row=row_idx, column=1, pady=3)

    def create_history_row(self, parent, text):
        # Wewnątrz ScrollableFrame nadal używamy pack dla wierszy
        row = ctk.CTkFrame(parent, fg_color="#34495e")
        row.pack(fill="x", pady=2, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=11), justify="left").pack(side="left", padx=10, pady=5)

    def generate_pedigree_success(self):
        messagebox.showinfo("Smart Contract: Sukces", "Walidacja zakończona pomyślnie. Wyemitowano Soulbound Token (SBT).")
        self.controller.show_frame("ScreenHodowca")


# ==========================================
# SEKCJA 2C: PROFIL - LUNA (BRAK CZIPU)
# ==========================================
class ScreenHodowcaProfilLuna(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Przycisk Powrót
        ctk.CTkButton(self.panel, text="← Powrót", width=80, 
                      command=lambda: controller.show_frame("ScreenHodowca")).grid(row=0, column=0, padx=20, pady=20, sticky="nw")

        ctk.CTkLabel(self.panel, text="Karta Profilowa Zwierzęcia", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Kontener danych
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=1, column=0, pady=10)

        self.create_disabled_field(form_frame, "Imię:", "Luna (Z Górskiej Doliny)", 0)
        self.create_disabled_field(form_frame, "Płeć:", "Samica", 1)
        self.create_disabled_field(form_frame, "Data urodzenia:", "2026-02-15", 2)
        self.create_disabled_field(form_frame, "Numer Mikroczipu:", "[BRAK - Oczekuje na identyfikację]", 3)

        # Przycisk wyłączony
        btn_rodowod = ctk.CTkButton(self.panel, text="💎 GENERUJ RODOWÓD CYFROWY (SBT)", fg_color="#7f8c8d", 
                                    state="disabled", width=400, height=38, font=ctk.CTkFont(weight="bold"))
        btn_rodowod.grid(row=2, column=0, pady=20)

        # Sekcja historii
        ctk.CTkLabel(self.panel, text="🩺 Historia leczenia (Surowe wpisy Blockchain):", 
                      font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=3, column=0, sticky="w", padx=50, pady=(10, 0))
        
        history_frame = ctk.CTkScrollableFrame(self.panel, fg_color="#a3aea3")
        history_frame.grid(row=4, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(4, weight=1)

        # Brak wpisów
        ctk.CTkLabel(history_frame, text="[Brak wpisów - Zwierzę nie zostało jeszcze zidentyfikowane przez lekarza weterynarii]", 
                      text_color="gray", font=ctk.CTkFont(slant="italic")).pack(pady=20)

    def create_disabled_field(self, parent, label_text, value_text, row_idx):
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=11), text_color="gray").grid(row=row_idx, column=0, sticky="e", padx=10, pady=3)
        entry = ctk.CTkEntry(parent, width=300, height=28)
        entry.insert(0, value_text)
        entry.configure(state="disabled")
        entry.grid(row=row_idx, column=1, pady=3)


# ==========================================
# SEKCJA 2D: PROFIL - ARES (BŁĄD WALIDACJI RODOWODU)
# ==========================================
class ScreenHodowcaProfilAres(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Przycisk Powrót
        ctk.CTkButton(self.panel, text="← Powrót", width=80, 
                      command=lambda: controller.show_frame("ScreenHodowca")).grid(row=0, column=0, padx=20, pady=20, sticky="nw")

        ctk.CTkLabel(self.panel, text="Karta Profilowa Zwierzęcia", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Kontener danych
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=1, column=0, pady=10)

        self.create_disabled_field(form_frame, "Imię:", "Ares", 0)
        self.create_disabled_field(form_frame, "Płeć:", "Samiec", 1)
        self.create_disabled_field(form_frame, "Data urodzenia:", "2025-05-10", 2)
        self.create_disabled_field(form_frame, "Numer Mikroczipu:", "ISO-967000008888888", 3)

        # Przycisk generowania rodowodu (Błąd walidacji)
        btn_rodowod = ctk.CTkButton(self.panel, text="💎 GENERUJ RODOWÓD CYFROWY (SBT)", fg_color="#1f538d", hover_color="#14375e", 
                                    width=400, height=38, font=ctk.CTkFont(weight="bold"),
                                    command=self.generate_pedigree_fail)
        btn_rodowod.grid(row=2, column=0, pady=20)

        # Sekcja historii
        ctk.CTkLabel(self.panel, text="🩺 Historia leczenia (Surowe wpisy Blockchain):", 
                      font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").grid(row=3, column=0, sticky="w", padx=50, pady=(10, 0))
        
        history_frame = ctk.CTkScrollableFrame(self.panel, fg_color="#a3aea3")
        history_frame.grid(row=4, column=0, sticky="nsew", padx=40, pady=10)
        self.panel.grid_rowconfigure(4, weight=1)

        self.create_history_row(history_frame, "2025-11-12 | Lekarz: KILW-1105 | Zabieg: Profilaktyka pasożytnicza")

    def create_disabled_field(self, parent, label_text, value_text, row_idx):
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=11), text_color="gray").grid(row=row_idx, column=0, sticky="e", padx=10, pady=3)
        entry = ctk.CTkEntry(parent, width=300, height=28)
        entry.insert(0, value_text)
        entry.configure(state="disabled")
        entry.grid(row=row_idx, column=1, pady=3)

    def create_history_row(self, parent, text):
        row = ctk.CTkFrame(parent, fg_color="#34495e")
        row.pack(fill="x", pady=2, padx=5)
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=11), justify="left").pack(side="left", padx=10, pady=5)

    def generate_pedigree_fail(self):
        messagebox.showerror("Smart Contract: Odrzucono transakcję", "BŁĄD WALIDACJI DRZEWA GENEALOGICZNEGO!\n\nPradziadek ze strony ojca nie posiada certyfikatu.")
    

# ==========================================
# SEKCJA 3: SCHRONISKO / FUNDACJA (WIDOK GŁÓWNY)
# ==========================================
class ScreenSchronisko(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # 1. Konfiguracja nagłówka przez metodę bazową
        self.setup_header(
            btn_text="🔒 Wyloguj", 
            btn_cmd=lambda: controller.show_frame("ScreenLogin"),
            info_text="● Rola: Schronisko / Fundacja (Autoryzowany Węzeł)"
        )

        # 2. Treść panelu (row 1, bo row 0 zajmuje nagłówek)
        # Tworzymy kontener na treść, aby utrzymać ładny padding
        content = ctk.CTkFrame(self.panel, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Tytuł sekcji
        ctk.CTkLabel(content, text="Panel Zarządzania Azylem i Adopcjami", 
                     font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, pady=(0, 20))

        # Przycisk dodawania
        btn_dodaj = ctk.CTkButton(content, text="➕   REJESTRUJ NOWE ZWIERZĘ (Przyjęcie do azylu)", 
                                  fg_color="#333333", hover_color="#1a1a1a", 
                                  width=400, height=50, font=ctk.CTkFont(size=14, weight="bold"),
                                  command=lambda: controller.show_frame("ScreenSchroniskoDodaj"))
        btn_dodaj.grid(row=1, column=0, pady=(0, 20))

        # Etykieta tabeli
        ctk.CTkLabel(content, text="📋 ZWIERZĘTA W AZYLU:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, sticky="w", padx=20)

        # Tabelka (ScrollableFrame)
        table_frame = ctk.CTkScrollableFrame(content, fg_color="#a3aea3")
        table_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        content.grid_rowconfigure(3, weight=1)

        # Dane zwierząt
        self.create_shelter_row(table_frame, "Imię: Bary   |  Płeć: Samiec  |  Wiek: ok. 2020  |  Status: Gotowy", "ScreenSchroniskoProfilBary")
        self.create_shelter_row(table_frame, "Imię: Sonia  |  Płeć: Samica  |  Wiek: ok. 2023  |  Status: Kwarantanna", "ScreenSchroniskoProfilSonia")

    def create_shelter_row(self, parent, text, target_frame):
        # Wiersz (fg_color="#2c3e50" dla spójności kolorystycznej)
        row = ctk.CTkFrame(parent, fg_color="#2c3e50")
        row.pack(fill="x", pady=4, padx=5)
        
        ctk.CTkLabel(row, text=text, font=ctk.CTkFont(size=12)).pack(side="left", padx=15, pady=8)
        
        btn = ctk.CTkButton(row, text="Karta 🐾", width=100, height=26, fg_color="#34495e", hover_color="#1f538d", 
                             font=ctk.CTkFont(size=11, weight="bold"),
                             command=lambda: self.controller.show_frame(target_frame))
        btn.pack(side="right", padx=10)


# ==========================================
# SEKCJA 3A: DODAWANIE ZWIERZĘCIA (SCHRONISKO)
# ==========================================
class ScreenSchroniskoDodaj(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Nagłówek i przycisk anuluj
        ctk.CTkButton(self.panel, text="← Anuluj", width=80, fg_color="#c0392b", hover_color="#962d22", 
                      command=lambda: controller.show_frame("ScreenSchronisko")).grid(row=0, column=0, padx=20, pady=20, sticky="nw")

        ctk.CTkLabel(self.panel, text="Formularz Przyjęcia Zwierzęcia do Schroniska", 
                      font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Kontener formularza
        form_frame = ctk.CTkFrame(self.panel, fg_color="transparent")
        form_frame.grid(row=1, column=0, pady=20)

        # Pola formularza
        self.entry_name = ctk.CTkEntry(form_frame, placeholder_text="Imię robocze zwierzęcia...", width=400, height=35)
        self.entry_name.grid(row=0, column=0, pady=8)

        self.dropdown_sex = ctk.CTkComboBox(form_frame, values=["Samiec", "Samica"], width=400, height=35)
        self.dropdown_sex.grid(row=1, column=0, pady=8)

        # Szacowany rok urodzenia
        ctk.CTkLabel(form_frame, text="Szacowany rok urodzenia:", font=ctk.CTkFont(size=12), text_color="gray").grid(row=2, column=0, sticky="w", pady=(5, 2))
        lata = [str(rok) for rok in range(2010, 2027)]
        self.dropdown_year = ctk.CTkComboBox(form_frame, values=lata, width=400, height=35)
        self.dropdown_year.set("2022")
        self.dropdown_year.grid(row=3, column=0, pady=5)

        self.entry_chip_option = ctk.CTkEntry(form_frame, placeholder_text="Numer czipu (zostaw puste jeśli brak)...", width=400, height=35)
        self.entry_chip_option.grid(row=4, column=0, pady=12)

        # Przycisk zapisu
        btn_save = ctk.CTkButton(form_frame, text="📝 Rejestruj przyjęcie w Ledgerze", fg_color="#e67e22", 
                                 hover_color="#d35400", width=400, height=45, font=ctk.CTkFont(weight="bold"),
                                 command=self.action_save_shelter)
        btn_save.grid(row=5, column=0, pady=15)

    def action_save_shelter(self):
        if not self.entry_name.get():
            messagebox.showwarning("Błąd", "Wprowadź imię zwierzęcia!")
            return
        
        messagebox.showinfo("Sukces", "Zwierzę zostało zarejestrowane w systemie azylu.\nWygenerowano alert o odnalezieniu.")
        self.controller.show_frame("ScreenSchronisko")

# ==========================================
# SEKCJA 3B: KARTA ADOPCYJNA - BARY (SUKCES)
# ==========================================
class ScreenSchroniskoProfilBary(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Przycisk powrotu
        ctk.CTkButton(self.panel, text="← Powrót", width=80, 
                      command=lambda: controller.show_frame("ScreenSchronisko")).grid(row=0, column=0, padx=20, pady=20, sticky="nw")

        ctk.CTkLabel(self.panel, text="Karta Adopcyjna Zwierzęcia", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Kontener informacyjny
        info_frame = ctk.CTkFrame(self.panel, fg_color="#2c3e50")
        info_frame.grid(row=1, column=0, pady=10, padx=40, sticky="ew")

        ctk.CTkLabel(info_frame, text="🐾 Imię: Bary | Płeć: Samiec | Wiek ok. 6 lat", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, pady=10)
        
        status_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        status_frame.grid(row=1, column=0, pady=5)
        
        ctk.CTkLabel(status_frame, text="💉 Szczepienia: AKTUALNE", text_color="#2ecc71", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=20)
        ctk.CTkLabel(status_frame, text="✂️ Kastracja: TAK", text_color="#2ecc71", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=20)

        # Przyciski akcji
        btn_info = ctk.CTkButton(self.panel, text="📋 Generuj Pełną Broszurę Adopcyjną (PDF/Print)", fg_color="#34495e", width=500, height=35,
                                  command=lambda: messagebox.showinfo("Broszura", "Wygenerowano dokument adopcyjny."))
        btn_info.grid(row=2, column=0, pady=8)

        btn_key = ctk.CTkButton(self.panel, text="🔑 Generuj klucz weryfikacji dla adoptującego (ZKP)", fg_color="#e67e22", hover_color="#d35400", width=500, height=45, font=ctk.CTkFont(weight="bold"),
                                 command=self.generate_restricted_key)
        btn_key.grid(row=3, column=0, pady=15)

        # Informacja edukacyjna
        info_zkp = ctk.CTkTextbox(self.panel, width=500, height=60, font=ctk.CTkFont(size=11), text_color="gray")
        info_zkp.insert("0.0", "🔒 Kryptograficzna selektywność danych (ZKP):\nUdostępnia adoptującemu wyłącznie wpisy medyczne z ostatnich 12 miesięcy, maskując pełną historię placówki.")
        info_zkp.configure(state="disabled")
        info_zkp.grid(row=4, column=0, pady=5)

    def generate_restricted_key(self):
        token_demo = "0xZKP_BARY_2026_VALID_8h"
        messagebox.showinfo("Wygenerowano Klucz ZKP", f"Sukces!\n\nWygenerowano tymczasowy klucz dostępu:\n{token_demo}")


# ==========================================
# SEKCJA 3C: KARTA ADOPCYJNA - SONIA (BLOKADA)
# ==========================================
class ScreenSchroniskoProfilSonia(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Przycisk powrotu
        ctk.CTkButton(self.panel, text="← Powrót", width=80, 
                      command=lambda: controller.show_frame("ScreenSchronisko")).grid(row=0, column=0, padx=20, pady=20, sticky="nw")

        ctk.CTkLabel(self.panel, text="Karta Adopcyjna Zwierzęcia", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=20)

        # Kontener informacyjny
        info_frame = ctk.CTkFrame(self.panel, fg_color="#2c3e50")
        info_frame.grid(row=1, column=0, pady=10, padx=40, sticky="ew")

        ctk.CTkLabel(info_frame, text="🐾 Imię: Sonia | Płeć: Samica | Wiek ok. 3 lata", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, pady=10)
        
        status_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        status_frame.grid(row=1, column=0, pady=5)
        
        ctk.CTkLabel(status_frame, text="💉 Szczepienia: NIEAKTUALNE ⚠️", text_color="#e74c3c", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=20)
        ctk.CTkLabel(status_frame, text="✂️ Kastracja: BRAK ⚠️", text_color="#e74c3c", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=20)

        # Przycisk info
        btn_info = ctk.CTkButton(self.panel, text="📋 Generuj Pełną Broszurę Adopcyjną (PDF/Print)", fg_color="#34495e", width=500, height=35,
                                  command=lambda: messagebox.showinfo("Broszura", "Wygenerowano kartę roboczą kwarantanny."))
        btn_info.grid(row=2, column=0, pady=8)

        # Przycisk zablokowany
        btn_key = ctk.CTkButton(self.panel, text="🔑 Generuj klucz weryfikacji dla adoptującego (ZKP)", fg_color="#7f8c8d", 
                                width=500, height=45, font=ctk.CTkFont(weight="bold"),
                                command=self.generate_restricted_key_fail)
        btn_key.grid(row=3, column=0, pady=15)

    def generate_restricted_key_fail(self):
        messagebox.showerror("Smart Contract: Odmowa", "BŁĄD: Zwierzę nie może zostać udostępnione do procesu adopcyjnego (brak szczepień/kastracji).")


# ==========================================
# WIDOK 4: KARTA ZDROWIA - PEŁNY WŁAŚCICIEL
# ==========================================
class ScreenWlasciciel(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Nagłówek statusu i wylogowania
        header = ctk.CTkFrame(self.panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkButton(header, text="🔒 Wyloguj", width=80, fg_color="#c0392b", hover_color="#962d22", 
                      command=lambda: controller.show_frame("ScreenLogin")).pack(side="left")
        ctk.CTkLabel(header, text="● Rola: Właściciel (Pełny Dostęp)", 
                      text_color="#3498db", font=ctk.CTkFont(weight="bold")).pack(side="right")

        # Karta zdrowia
        profile = ctk.CTkFrame(self.panel, fg_color="#2c3e50")
        profile.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(profile, text="🐕 KARTA ZDROWIA: Reksio (Owczarek)", 
                      font=ctk.CTkFont(size=20, weight="bold")).pack(pady=5)
        ctk.CTkLabel(profile, text="ID mikroczipu: ISO-967000001234567 | Koszt utrzymania (YTD): 1,420 PLN", 
                      text_color="#2ecc71", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)

        # Przycisk generowania klucza
        btn_key = ctk.CTkButton(self.panel, text="🔑 Generuj tymczasowy klucz dostępu dla kupującego (Ważny 24h)", 
                                fg_color="#e67e22", hover_color="#d35400", width=400, height=45,
                                command=lambda: messagebox.showinfo("Zarządzanie Prywatnością", "Wygenerowano jednorazowy klucz ZKP."))
        btn_key.grid(row=2, column=0, pady=10)

        # Sekcja historii
        ctk.CTkLabel(self.panel, text="Pełna Historia Zabiegów (Blockchain):", 
                      font=ctk.CTkFont(size=14, weight="bold")).grid(row=3, column=0, pady=(10, 5))

        timeline = ctk.CTkScrollableFrame(self.panel, fg_color="#a3aea3")
        timeline.grid(row=4, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(4, weight=1)

        # Wiersze historii
        self.add_timeline_item(timeline, "24.05.2026 | Szczepienie wścieklizna (Rabisin) - 120 PLN", "🔒 ZWERYFIKOWANO", "#2ecc71")
        self.add_timeline_item(timeline, "10.04.2026 | Odroczenie szczepień (Zapalenie jelit) - 150 PLN", "⚠️ WYJĄTEK OK", "#e67e22")
        self.add_timeline_item(timeline, "15.03.2026 | RTG Stawów (Badanie kliniczne) - 450 PLN", "✓ SPÓJNY HASH", "#3498db")

    def add_timeline_item(self, parent, text, status, color):
        # Wewnątrz ScrollableFrame nadal używamy pack dla wierszy
        item = ctk.CTkFrame(parent, fg_color="#34495e")
        item.pack(fill="x", pady=3, padx=5)
        
        ctk.CTkLabel(item, text=text, justify="left").pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(item, text=status, text_color=color, font=ctk.CTkFont(size=11, weight="bold")).pack(side="right", padx=10)


# ==========================================
# WIDOK 5: KARTA ZDROWIA - UKRYTY KUPUJĄCY
# ==========================================
class ScreenKupujacy(BaseScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        # Nagłówek statusu i wylogowania
        header = ctk.CTkFrame(self.panel, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkButton(header, text="🔒 Wyloguj", width=80, fg_color="#c0392b", hover_color="#962d22", 
                      command=lambda: controller.show_frame("ScreenLogin")).pack(side="left")
        ctk.CTkLabel(header, text="● Rola: Weryfikator / Kupujący (ZKP View)", 
                      text_color="#e67e22", font=ctk.CTkFont(weight="bold")).pack(side="right")

        # Karta zdrowia (Podgląd)
        profile = ctk.CTkFrame(self.panel, fg_color="#2c3e50")
        profile.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        ctk.CTkLabel(profile, text="🐕 KARTA ZDROWIA: Reksio (Owczarek)", 
                      font=ctk.CTkFont(size=20, weight="bold")).pack(pady=5)
        ctk.CTkLabel(profile, text="ID mikroczipu: ISO-967000001234567 | Dane finansowe: [ZABLOKOWANE]", 
                      text_color="#e74c3c", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5)

        # Sekcja historii
        ctk.CTkLabel(self.panel, text="Zweryfikowana Historia Medyczna (Dane publiczne ZKP):", 
                      font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, pady=(10, 5))

        timeline = ctk.CTkScrollableFrame(self.panel, fg_color="#a3aea3")
        timeline.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        self.panel.grid_rowconfigure(3, weight=1)

        # Wiersze historii
        self.add_timeline_item(timeline, "24.05.2026 | Szczepienie wścieklizna aktywne.\nAutoryzacja weterynarza: Pomyślna.", "🔒 ZWERYFIKOWANO", "#2ecc71")
        self.add_timeline_item(timeline, "10.04.2026 | Odroczenie szczepień (Wskazania medyczne).\nPowód: Leczenie gastryczne.", "⚠️ WYJĄTEK OK", "#e67e22")
        self.add_timeline_item(timeline, "15.03.2026 | Wykonano badanie RTG stawów.\nDowód kryptograficzny: ZGODNY.", "✓ SPÓJNY HASH", "#3498db")

    def add_timeline_item(self, parent, text, status, color):
        # Wewnątrz ScrollableFrame nadal używamy pack
        item = ctk.CTkFrame(parent, fg_color="#34495e")
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
    app = VetChainApp()
    app.mainloop()