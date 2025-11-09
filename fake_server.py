# fake_server.py

from flask import Flask, jsonify

app = Flask(__name__)

# --- Innen kezdődik a szimuláció ---

# Ez a mi "adatbázisunk". Kezdetben minden zárva van.
MOCK_DATA = [
    {
        "id": 1,
        "circleName": "Egyik Zárt Kör",
        "orderable": False,
        "nextOpeningDate": 1762887600000
    },
    {
        "id": 2,
        "circleName": "TESZT KÖR (amit nyitni fogunk)",
        "orderable": False,  # Fontos: 'False'-szal indul!
        "nextOpeningDate": 1762887600000
    }
]


@app.route('/api/items')
def get_fake_items():
    """
    Ez az "ál" API végpont, amit a monitor.py figyelni fog.
    """
    print(f"API kérés érkezett. Jelenlegi állapot: TESZT KÖR 'orderable' = {MOCK_DATA[1]['orderable']}")
    return jsonify(MOCK_DATA)


@app.route('/toggle')
def toggle_orderable_state():
    """
    Ezt a címet böngészőből megnyitva tudod VÁLTOZTATNI a teszt kör állapotát.
    """
    global MOCK_DATA

    # Átváltjuk a "TESZT KÖR" 'orderable' állapotát az ellenkezőjére
    current_state = MOCK_DATA[1]['orderable']
    MOCK_DATA[1]['orderable'] = not current_state

    new_status_str = "NYITOTT" if MOCK_DATA[1]['orderable'] else "ZÁRT"

    print(f"ÁLLAPOT VÁLTOZÁS: A 'TESZT KÖR' mostantól {new_status_str}")
    return f"<h1>A 'TESZT KÖR' állapota sikeresen átváltva: {new_status_str}</h1>"


if __name__ == '__main__':
    print("--- Hamis SCH Pincér API Szerver ---")
    print("A szerver fut a http://127.0.0.1:5000 címen.")
    print("\nFigyelmeztetés: A monitor.py-ban állítsd át az API_URL-t erre: 'http://127.0.0.1:5000/api/items'")
    print("\nA 'TESZT KÖR' nyitásához/zárásához nyisd meg a böngésződben:")
    print("http://127.0.0.1:5000/toggle")
    print("\nCtrl+C-vel állíthatod le a szervert.")

    # A szerver futtatása a localhost:5000 porton
    app.run(host='127.0.0.1', port=5000)