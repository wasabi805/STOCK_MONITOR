# ------ sharing one upstream per symbol and broadcasting to all clients -----

# keeps one Finnhub WS per SYMBOL

# broadcasts to all connected clients via a Channels group

# auto-starts the upstream when the first client connects and shuts it down when the last one leaves

# has basic reconnect/backoff

# ------ (END)sharing one upstream per symbol and broadcasting to all clients ------

import os, json, asyncio, logging, contextlib
import websockets
from typing import Dict

FINNHUB_TOKEN = os.getenv("FINNHUB_API_KEY")
FINNHUB_WS = "wss://ws.finnhub.io"
log = logging.getLogger("tracker")

# symbol -> {"task": Task, "stop": Event, "subs": int}
STREAMS: Dict[str, dict] = {}
# ----- SYMOBOL STREM MANAGER -----
def group_name_for(symbol: str) -> str:
    return f"quotes_{symbol.upper()}"

async def ensure_stream(symbol: str, channel_layer):
    """Ensure a single upstream WS per symbol is running."""
    symbol = symbol.upper()
    if symbol not in STREAMS:
        stop = asyncio.Event()
        task = asyncio.create_task(_run_stream(symbol, channel_layer, stop))
        STREAMS[symbol] = {"task": task, "stop": stop, "subs": 0}
        log.info("Started upstream stream for %s", symbol)
    STREAMS[symbol]["subs"] += 1

async def release_stream(symbol: str):
    """Decrease subscriber count; stop when zero."""
    symbol = symbol.upper()
    entry = STREAMS.get(symbol)
    if not entry:
        return
    entry["subs"] = max(0, entry["subs"] - 1)
    if entry["subs"] == 0:
        entry["stop"].set()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(entry["task"], timeout=2.0)
        STREAMS.pop(symbol, None)
        log.info("Stopped upstream stream for %s", symbol)

async def _run_stream(symbol: str, channel_layer, stop_event: asyncio.Event):
    """Connect to Finnhub once and fan-out messages to a Channels group."""
    if not FINNHUB_TOKEN:
        log.error("Missing FINNHUB_API_KEY; cannot start stream.")
        return
    group = group_name_for(symbol)

    backoff = 1.0
    while not stop_event.is_set():
        try:
            url = f"{FINNHUB_WS}?token={FINNHUB_TOKEN}"
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                sub = json.dumps({"type": "subscribe", "symbol": symbol})
                await ws.send(sub)
                backoff = 1.0  # reset after successful connect
                log.info("Upstream connected for %s", symbol)

                while not stop_event.is_set():
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    except asyncio.TimeoutError:
                        # keep-alive
                        await ws.send(sub)
                        continue
                    # broadcast to all consumers in the symbol group
                    await channel_layer.group_send(group, {
                        "type": "quote.message",
                        "text": raw,          # pass-through payload
                        "symbol": symbol,
                    })

                # graceful unsubscribe
                with contextlib.suppress(Exception):
                    await ws.send(json.dumps({"type": "unsubscribe", "symbol": symbol}))
                break  # we were asked to stop; exit loop

        except Exception as e:
            log.warning("Upstream error for %s: %s", symbol, e)
            # backoff and retry unless stop requested
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 10.0)
