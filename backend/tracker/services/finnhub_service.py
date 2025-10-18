import requests
import os
from datetime import datetime, timezone
from django.conf import settings

# FINNHUB_API_KEY = settings.FINNHUB_API_KEY
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE = "https://finnhub.io/api/v1"

class FinnhubError(Exception):
    pass

def get_quote(symbol: str):
    if not FINNHUB_API_KEY:
        raise FinnhubError("Missing Finnhub API key.")

    url = f"{FINNHUB_BASE}/quote"
    params = {"symbol": symbol.upper(), "token": FINNHUB_API_KEY}

    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        raise FinnhubError(f"Error fetching quote for {symbol}: {response.text}")

    data = response.json()

    # 🕒 Convert timestamp to ISO format
    iso_ts = None
    if data.get("t"):
        iso_ts = datetime.fromtimestamp(data["t"], tz=timezone.utc).isoformat()

    return {
        "symbol": symbol.upper(),
        "current": data.get("c"),
        "change": data.get("d"),
        "percent": data.get("dp"),
        "high": data.get("h"),
        "low": data.get("l"),
        "open": data.get("o"),
        "prev_close": data.get("pc"),
        "ts": data.get("t"),
        "iso_ts": iso_ts,  # 👈 new field
    }


def get_candles(symbol: str, resolution="1", frm=None, to=None):
    if not FINNHUB_API_KEY: raise FinnhubError("FINNHUB_API_KEY missing")
    url = f"{FINNHUB_BASE}/stock/candle"
    params = {"symbol": symbol.upper(), "resolution": resolution, "from": frm, "to": to, "token": FINNHUB_API_KEY}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200: raise FinnhubError(f"Candles error [{r.status_code}]: {r.text}")
    return r.json()