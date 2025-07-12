import requests
import json
import os
from datetime import datetime

# Configurações via variáveis de ambiente (usadas no GitHub Actions)
PHONE = os.getenv("CALLMEBOT_PHONE")     # +55XXXXXXXXXXX
WHATSAPP_KEY = os.getenv("CALLMEBOT_APIKEY")
AVIATIONSTACK_KEY = os.getenv("AVIATIONSTACK_KEY")

FLIGHTS = ["LA3339", "LA8112", "AM694"]

STATUS_FILE = "last_status.json"

def load_last_status():
    if os.path.exists(STATUS_FILE):
        if os.path.getsize(STATUS_FILE) == 0:
            return {}
        with open(STATUS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def send_whatsapp(flight, status):
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    msg = f"✈️ Atualização do voo {flight}:\n\nStatus: {status}\n⏰ {timestamp}"
    url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={requests.utils.quote(msg)}&apikey={WHATSAPP_KEY}"
    r = requests.get(url)
    print(f"📤 WhatsApp enviado para {flight} (status: {status})")

def get_flight_status(flight_iata):
    url = f"http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": AVIATIONSTACK_KEY,
        "flight_iata": flight_iata
    }
    r = requests.get(url, params=params)
    if r.status_code == 200:
        data = r.json()
        flights = data.get("data", [])
        if flights:
            # Pega o voo mais recente (pode ser refinado)
            return flights[0].get("flight_status", "unknown")
    return "not_found"

def main():
    print("🔍 Checando status dos voos via AviationStack...")
    last_status = load_last_status()
    updated = False

    for flight in FLIGHTS:
        current_status = get_flight_status(flight)
        print(f"✈️ {flight}: {current_status}")
        if last_status.get(flight) != current_status:
            send_whatsapp(flight, current_status)
            last_status[flight] = current_status
            updated = True

    if updated:
        save_status(last_status)

if __name__ == "__main__":
    main()
