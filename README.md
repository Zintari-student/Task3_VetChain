## Instalacja

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Uruchomienie

```bash
.venv/bin/python main.py
```

## Klucze demo

Przy pierwszym uruchomieniu generowane deterministycznie w `.demo_keys/*.priv` (gitignored). Każdy plik zawiera 64-znakowy hex klucza prywatnego secp256k1. Login = paste hex → app derywuje adres → szuka aktora na łańcuchu → ustawia sesję podpisującą transakcje.

Demo buttony w UI pastują hex z pliku. Dostępne role: weterynarz, hodowca, schronisko, właściciel, kupujący.
