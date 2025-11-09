# db_setup.py

import sqlite3

DATABASE_FILE = "pincer_monitor.db"


def create_database():
    """
    Létrehozza az adatbázist és a 'recipients' táblát.
    Biztonságosan futtatható többször is ('IF NOT EXISTS').
    """
    conn = None
    try:
        # A connect létrehozza a fájlt, ha nem létezik
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Létrehozzuk a táblát az e-mail címek tárolására
        # A 'UNIQUE' biztosítja, hogy egy e-mail cím csak egyszer szerepelhessen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE
            )
        """)

        print(f"Adatbázis ('{DATABASE_FILE}') és 'recipients' tábla sikeresen létrehozva/ellenőrizve.")

        # --- Opcionális: Pár példa cím hozzáadása ---
        # A 'OR IGNORE' miatt nem dob hibát, ha már létezik a cím
        cursor.execute("INSERT OR IGNORE INTO recipients (email) VALUES (?)", ("30balint@gmail.com",))

        conn.commit()  # Változtatások mentése
        print("Példa e-mail címek hozzáadva (ha még nem léteztek).")

    except sqlite3.Error as e:
        print(f"Hiba történt az adatbázis beállítása közben: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    create_database()