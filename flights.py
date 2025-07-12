import requests, json, os
from datetime import datetime, timezone
from dateutil import parser as dtparse    # novo!

# ➜ Variáveis de ambiente (configure nos GitHub Secrets)
PHONE            = os.getenv("CALLMEBOT_PHONE")     # +55… ou +1…
WHATSAPP_KEY     = os.getenv("CALLMEBOT_APIKEY")
AVIATIONSTACK_KEY= os.getenv("AVIATIONSTACK_KEY")

# Voos a monitorar
FLIGHTS = ["LA3339", "LA8112", "AMX694"]

STATUS_FILE = "last_status.json"

# ---------- utilidades ---------- #
def load_last():
    if os.path.exists(STATUS_FILE) and os.path.getsize(STATUS_FILE) > 0:
        try:
            with open(STATUS_FILE) as f: return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}

def save_last(data):
    with open(STATUS_FILE, "w") as f: json.dump(data, f)

def fmt(ts_str):
    """Converte ISO da AviationStack em dd/MM HH:mm (hora local do evento)."""
    if not ts_str: return "—"
    dt = dtparse.parse(ts_str)           # contém fuso do aeroporto
    return dt.strftime("%d/%m %H:%M")

def send_whatsapp(msg):
    url = ("https://api.callmebot.com/whatsapp.php"
           f"?phone={PHONE}&text={requests.utils.quote(msg)}&apikey={WHATSAPP_KEY}")
    requests.get(url, timeout=30)

# ---------- consulta à AviationStack ---------- #
def fetch_flight(iata):
    url = "http://api.aviationstack.com/v1/flights"
    r = requests.get(url,
        params={"access_key": AVIATIONSTACK_KEY, "flight_iata": iata, "limit": 1},
        timeout=30)
    r.raise_for_status()
    data = r.json().get("data", [])
    return data[0] if data else None

def build_summary(f):
    """Resumo compacto usado para detectar mudança."""
    return "|".join([
        f.get("flight_status",""),
        f["departure"].get("actual",""),
        f["arrival"].get("estimated","")
    ])

def build_message(iata, f):
    dep = f["departure"]; arr = f["arrival"]
    return (
        f"✈️ {iata} | {dep.get('airport','')} → {arr.get('airport','')}\n"
        f"Status: {f.get('flight_status','')}\n"
        f"Partida prevista: {fmt(dep.get('scheduled'))}  |  "
        f"Real: {fmt(dep.get('actual'))}\n"
        f"Chegada prevista: {fmt(arr.get('scheduled'))}  |  "
        f"Estimada: {fmt(arr.get('estimated'))}\n"
        f"🔄 Atualizado: {datetime.now(timezone.utc).strftime('%d/%m %H:%M UTC')}"
    )

# ---------- programa principal ---------- #
def main():
    print("🔍 Checando voos via AviationStack…")
    last = load_last(); changed = False

    for iata in FLIGHTS:
        f = fetch_flight(iata)
        if not f:
            print(f"❓ {iata}: dados não encontrados"); continue

        summary = build_summary(f)
        if last.get(iata) != summary:
            msg = build_message(iata, f)
            send_whatsapp(msg)
            last[iata] = summary
            changed = True
            print(f"📤 WhatsApp enviado ({iata})")
        else:
            print(f"✅ {iata}: sem mudanças")

    if changed: save_last(last)

if __name__ == "__main__":
    main()
