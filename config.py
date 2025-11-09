import os
from dotenv import load_dotenv

# .env fájl betöltése a program környezeti változói közé
# A load_dotenv() megkeresi a .env fájlt az aktuális mappában
load_dotenv()

# --- SMTP (Email Küldés) Beállítások ---
# Ezek az adatok nem titkosak, maradhatnak itt
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # TLS esetén általában 587, SSL esetén 465

# --- Hitelesítés (Betöltés .env-ből) ---
# Az os.getenv() segítségével olvassuk ki a betöltött környezeti változókat
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# --- Ellenőrzés ---
# Érdemes ellenőrizni, hogy a betöltés sikeres volt-e,
# mielőtt a program később hibára futna.
if not EMAIL_SENDER or not EMAIL_PASSWORD:
    raise ValueError("HIBA: Az EMAIL_SENDER vagy EMAIL_PASSWORD nincs beállítva a .env fájlban!")

print(f"Config betöltve, küldő email: {EMAIL_SENDER} (Jelszó betöltve, de nem kiírva)")