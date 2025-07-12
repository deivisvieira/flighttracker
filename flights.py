import requests
import json
import os
from datetime import datetime

# CallMeBot config
PHONE = os.getenv("CALLMEBOT_PHONE")   # +55XXXXXXXXXXX
APIKEY = os.getenv("CALLMEBOT_APIKEY")

# Lista de voos a monitorar
FLIGHTS = ["LA3339", "LA8112", "AM694"]

# Endpoint de scraping da região aproximada (Brasil, México, Pacífico)
URL = "https://data-cloud.flightradar24.com/zones/fcgi/feed.js?bounds=-60,60,-140,-30"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

STATUS_FILE = "last_status.json"

def load_last_status():
    if os.path.exists(STATUS_FILE):
        if os.path.getsize(STATUS_FILE) == 0:
            return {}  # arquivo vazio → retorna dicionário vazio
        with open(STATUS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}  # conteúdo inválido → ignora e começa do zero
    return {}


def save_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def send_whatsapp(flight, new_status):
    msg = f"✈️ Atualização do voo {flight}:\n\nStatus: {new_status}\n⏰ {datetime.utcnow().isoformat()} UTC"
    url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={requests.utils.quote(msg)}&apikey={APIKEY}"
    r = requests.get(url)
    print(f"Enviando WhatsApp: {r.status_code}")

def main():
    print("🔍 Checando voos...")
    response = requests.get(URL, headers=HEADERS)
    flights_data = response.json()

    last_status = load_last_status()

    for flight_data in flights_data.values():
        if not isinstance(flight_data, dict):
            continue
        flight_id = flight_data.get("flight")
        if not flight_id:
            continue
        for target in FLIGHTS:
            if target in flight_id:
                status = flight_data.get("status", "unknown")
                print(f"✈️ {target} status: {status}")
                if last_status.get(target) != status:
                    send_whatsapp(target, status)
                    last_status[target] = status

    save_status(last_status)

if __name__ == "__main__":
    main()
