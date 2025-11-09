# monitor.py

import requests
import smtplib
import time
import datetime
import ssl
import sqlite3
import os
from email.message import EmailMessage

try:
    import config
except ImportError:
    print("Hiba: Nem található a 'config.py' fájl.")
    print("Kérlek, hozd létre a config.py fájlt az SMTP beállításokkal.")
    exit()

# --- Alap Beállítások ---
API_URL = "https://schpincer.sch.bme.hu/api/items"
#API_URL = "http://127.0.0.1:5000/api/items" # Teszteléshez
POLL_INTERVAL_SECONDS = 600

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
        print(f"Hiba a dátum formázása közben: {e}")
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
        print(f"ADATBÁZIS HIBA: {e}")
        print(f"Ellenőrizd, hogy a '{DATABASE_FILE}' létezik-e, és lefuttattad-e a 'db_setup.py'-t.")
    except sqlite3.Error as e:
        print(f"Hiba az adatbázis olvasása közben: {e}")
    finally:
        # Mindig bezárjuk a kapcsolatot
        if conn:
            conn.close()

    return recipients_list


def send_notification_email(circle_name, opening_date_str):
    """
    E-mailt küld a configban megadott címzetteknek.
    """
    if not config.RECIPIENT_EMAILS:
        print(f"Nincsenek címzettek beállítva a config.py-ban a(z) {circle_name} értesítéshez.")
        return

    print(f"E-mail küldése indul: {circle_name} megnyílt...")

    # Az e-mail üzenet összeállítása
    msg = EmailMessage()
    msg['Subject'] = f"SCH Pincér Értesítő: A(z) {circle_name} megnyílt!"
    msg['From'] = config.EMAIL_SENDER
    msg['To'] = ", ".join(config.RECIPIENT_EMAILS) # Címzettek listája vesszővel elválasztva

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
            print(f"E-mail sikeresen elküldve a(z) {circle_name} nyitásáról.")
    except smtplib.SMTPException as e:
        print(f"Hiba az e-mail küldése közben: {e}")
    except Exception as e:
        print(f"Ismeretlen hiba az e-mail küldés során: {e}")


def check_for_openings():
    """
    Lekérdezi az API-t és ellenőrzi a nyitásokat.
    (Ez a funkció nem változott)
    """
    global notified_circles
    print(f"({datetime.datetime.now().strftime('%H:%M:%S')}) API ellenőrzése...")

    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        items = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Hiba az API lekérdezése közben: {e}")
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

    notified_circles.update(new_openings)
    notified_circles.difference_update(closed_openings)

    if not new_openings and not closed_openings:
        print("Nincs változás.")


# --- MÓDOSÍTOTT MAIN FUNKCIÓ ---
def main():
    """
    A fő programciklus, ami futtatja az ellenőrzést.
    """
    print("SCH Pincér Monitor elindítva...")
    # MÓDOSÍTÁS: Az üdvözlő üzenet frissítése
    print(f"Címzettek a(z) '{DATABASE_FILE}' adatbázisból lesznek beolvasva.")
    print(f"Ellenőrzési intervallum: {POLL_INTERVAL_SECONDS} másodperc")
    print("--------------------------------------------------")
    try:
        while True:
            check_for_openings()
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nProgram leállítva (Ctrl+C). Viszlát!")


if __name__ == "__main__":
    main()