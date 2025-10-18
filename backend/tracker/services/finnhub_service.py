import os, logging, time
from datetime import datetime, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.conf import settings
from django.core.cache import cache

log = logging.getLogger("tracker")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
FINNHUB_BASE = "https://finnhub.io/api/v1"

class FinnhubError(Exception): ...
class FinnhubRateLimit(Exception): ...

# --- shared requests session with retry/backoff ---
_session = requests.Session()
_session.headers.update({"User-Agent": "stock-monitor/1.0"})
retries = Retry(
    total=3,               # overall retries
    backoff_factor=0.5,    # 0.5s, 1s, 2s
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET",)
)
_session.mount("https://", HTTPAdapter(max_retries=retries))

def _get(url, params):
    if not FINNHUB_API_KEY:
        raise FinnhubError("FINNHUB_API_KEY missing")
    params = {**params, "token": FINNHUB_API_KEY}
    resp = _session.get(url, params=params, timeout=10)
    if resp.status_code == 429:
        # Finnhub throttling
        log.warning("Finnhub 429 (rate limit): %s %s", url, params.get("symbol"))
        raise FinnhubRateLimit("Rate limited by Finnhub")
    if resp.status_code != 200:
        log.error("Finnhub error %s: %s", resp.status_code, resp.text[:200])
        raise FinnhubError(f"HTTP {resp.status_code}")
    return resp.json()

def get_quote(symbol: str):
    """Latest snapshot; cached briefly to avoid spikes."""
    symbol = symbol.upper()
    cache_key = f"quote:{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{FINNHUB_BASE}/quote"
    data = _get(url, {"symbol": symbol})

    iso_ts = None
    if data.get("t"):
        iso_ts = datetime.fromtimestamp(data["t"], tz=timezone.utc).isoformat()

    payload = {
        "symbol": symbol,
        "current": data.get("c"),
        "change": data.get("d"),
        "percent": data.get("dp"),
        "high": data.get("h"),
        "low": data.get("l"),
        "open": data.get("o"),
        "prev_close": data.get("pc"),
        "ts": data.get("t"),
        "iso_ts": iso_ts,
    }
    cache.set(cache_key, payload, timeout=getattr(settings, "QUOTE_TTL", 5))
    return payload

def get_candles(symbol: str, resolution="1", frm=None, to=None):
    """Historical candles; safe to cache longer."""
    symbol = symbol.upper()
    cache_key = f"candles:{symbol}:{resolution}:{frm}:{to}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"{FINNHUB_BASE}/stock/candle"
    data = _get(url, {"symbol": symbol, "resolution": resolution, "from": frm, "to": to})

    cache.set(cache_key, data, timeout=getattr(settings, "CANDLES_TTL", 60))
    return data
