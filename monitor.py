# monitor.py

import requests
import smtplib
import time
import datetime
import ssl
import sqlite3
import os
import logging
import sys
from email.message import EmailMessage

try:
    import config
except ImportError:
    sys.exit("Hiba: Nem található a 'config.py' fájl.")

logging.basicConfig(
    level=logging.INFO, # Beállítjuk, hogy az INFO szinttől felfelé mindent írjon ki
    format='%(asctime)s - %(levelname)s - %(message)s', # Időbélyeg - Szint - Üzenet
    handlers=[
        logging.StreamHandler(sys.stdout) # A kimenetet a szabványos kimenetre irányítjuk (ezt látja a Docker)
    ]
)

# --- Alap Beállítások ---
#API_URL = "https://schpincer.sch.bme.hu/api/items"
API_URL = "http://192.168.1.155:5000/api/items"# Teszteléshez
POLL_INTERVAL_SECONDS = 10

# A .txt fájl helyett az adatbázist használjuk (ÚJ)
DATABASE_FILE = os.getenv("DATABASE_PATH", "pincer_monitor.db")

notified_circles = set()


def format_opening_date(timestamp_ms):
    """
    Átalakítja az ezredmásodperc alapú időbélyeget
    olvasható dátum formátumra.
    """
    try:
        timestamp_sec = int(timestamp_ms) / 1000
        dt_object = datetime.datetime.fromtimestamp(timestamp_sec)
        return dt_object.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logging.error(f"Hiba a dátum formázása közben: {e}")
        return str(timestamp_ms)


# --- TELJESEN KICSERÉLT FUNKCIÓ ---
def get_recipients():
    """
    Beolvassa a címzetteket az 'sqlite3' adatbázis 'recipients' táblájából.
    """
    recipients_list = []
    conn = None
    try:
        # Minden alkalommal frissen csatlakozunk
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Lekérdezzük az összes e-mail címet
        cursor.execute("SELECT email FROM recipients")

        # A fetchall() tuple-ök listáját adja, pl: [('cim1@email.com',), ('cim2@email.com',)]
        # Ezért kell a 'row[0]'-val kinyerni a címet
        rows = cursor.fetchall()
        recipients_list = [row[0] for row in rows]

    except sqlite3.OperationalError as e:
        logging.error(f"ADATBÁZIS HIBA: {e}")
    except sqlite3.Error as e:
        logging.error(f"Hiba az adatbázis olvasása közben: {e}")
    finally:
        # Mindig bezárjuk a kapcsolatot
        if conn:
            conn.close()

    return recipients_list


def send_notification_email(circle_name, opening_date_str):
    """
    E-mailt küld a configban megadott címzetteknek.
    """
    recipients_list = get_recipients()

    if not recipients_list:
        logging.warning(f"Nincsenek címzettek az adatbázisban a(z) {circle_name} értesítéshez.")
        return

    logging.info(f"E-mail küldése indul ({len(recipients_list)} címzettnek): {circle_name} megnyílt...")

    # Az e-mail üzenet összeállítása
    msg = EmailMessage()
    msg['Subject'] = f"SCH Pincér Értesítő: A(z) {circle_name} megnyílt!"
    msg['From'] = config.EMAIL_SENDER
    msg['To'] = ", ".join(recipients_list) # Címzettek listája vesszővel elválasztva

    # Az üzenet törzse
    msg.set_content(
f"""Szia!

A(z) "{circle_name}" körnél új rendelési lehetőség nyílt a SCH Pincér oldalon.

Nyitás (várható) ideje: {opening_date_str}

Siess, nehogy lemaradj!

Üdv,
A Te Python Botod
"""
    )

    context = ssl.create_default_context()

    # Küldés SMTP-n keresztül
    try:
        with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, context=context) as server:
            server.ehlo()  # Kapcsolat tesztelése
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.send_message(msg)
            logging.info(f"E-mail SIKERESEN elküldve: {circle_name}")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP Hiba az e-mail küldése közben: {e}")
    except Exception as e:
        logging.error(f"Ismeretlen hiba az e-mail küldés során: {e}")


def check_for_openings():
    """
    Lekérdezi az API-t és ellenőrzi a nyitásokat.
    (Ez a funkció nem változott)
    """
    global notified_circles

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        items = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Hiba az API lekérdezése közben: {e}")
        return

    currently_orderable_circles = set()
    opening_data = {}

    for item in items:
        if item.get("orderable") is True and "circleName" in item and "nextOpeningDate" in item:
            circle = item["circleName"]
            date_ms = item["nextOpeningDate"]

            currently_orderable_circles.add(circle)
            opening_data[circle] = date_ms

    new_openings = currently_orderable_circles - notified_circles
    closed_openings = notified_circles - currently_orderable_circles

    for circle_name in new_openings:
        opening_date_ms = opening_data[circle_name]
        formatted_date = format_opening_date(opening_date_ms)
        send_notification_email(circle_name, formatted_date)

    if closed_openings:
        logging.info(f"Bezárt körök (értesítés resetelve): {', '.join(closed_openings)}")

    notified_circles.update(new_openings)
    notified_circles.difference_update(closed_openings)

def db_setup():
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

        logging.info(f"Adatbázis ('{DATABASE_FILE}') és 'recipients' tábla sikeresen létrehozva/ellenőrizve.")

        # --- Opcionális: Pár példa cím hozzáadása ---
        # A 'OR IGNORE' miatt nem dob hibát, ha már létezik a cím
        cursor.execute("INSERT OR IGNORE INTO recipients (email) VALUES (?)", ("pelda@pelda.com",))

        conn.commit()  # Változtatások mentése
        logging.info("Példa e-mail címek hozzáadva (ha még nem léteztek).")

    except sqlite3.Error as e:
        logging.error(f"Hiba történt az adatbázis beállítása közben: {e}")
    finally:
        if conn:
            conn.close()


# --- MÓDOSÍTOTT MAIN FUNKCIÓ ---
def main():
    """
    A fő programciklus, ami futtatja az ellenőrzést.
    """
    logging.info("Adatbázis ellenőrzése/létrehozása")
    db_setup()

    logging.info("SCH Pincér Monitor INDÍTÁSA...")
    logging.info(f"Adatbázis: {DATABASE_FILE}")
    logging.info(f"Intervallum: {POLL_INTERVAL_SECONDS} másodperc")
    try:
        while True:
            check_for_openings()
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logging.info("Program leállítva (Ctrl+C). Viszlát!")


if __name__ == "__main__":
    main()