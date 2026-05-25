"""VetChain entrypoint — inicjalizacja DB i odpalenie aplikacji."""

import customtkinter as ctk

import vetchain_db as db
from ui import VetChainApp


def main() -> None:
    ctk.set_appearance_mode("Light")
    try:
        ctk.set_default_color_theme("vetchain_theme.json")
    except Exception as e:
        print(f"⚠️ Nie znaleziono pliku motywu vetchain_theme.json: {e}")

    db.init_db()
    app = VetChainApp()
    app.mainloop()


if __name__ == "__main__":
    main()
