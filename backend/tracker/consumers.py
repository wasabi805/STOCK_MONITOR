import os, json, asyncio, logging
from channels.generic.websocket import AsyncWebsocketConsumer
import websockets

log = logging.getLogger("tracker")
FINNHUB_WS = "wss://ws.finnhub.io"
FINNHUB_TOKEN = os.getenv("FINNHUB_API_KEY")

class QuoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.symbol = (self.scope["url_route"]["kwargs"]["symbol"] or "").upper()
        if not self.symbol or not FINNHUB_TOKEN:
            await self.close(code=4001)
            return
        await self.accept()

        # open upstream connection
        self._stop = asyncio.Event()
        self._task = asyncio.create_task(self._stream())

    async def disconnect(self, close_code):
        if hasattr(self, "_stop"):
            self._stop.set()
        if hasattr(self, "_task"):
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self._task, timeout=1.0)

    async def receive(self, text_data=None, bytes_data=None):
        # optional: accept commands from client (noop here)
        pass

    async def _stream(self):
        import contextlib
        url = f"{FINNHUB_WS}?token={FINNHUB_TOKEN}"
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                # subscribe
                sub_msg = json.dumps({"type": "subscribe", "symbol": self.symbol})
                await ws.send(sub_msg)

                while not self._stop.is_set():
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    except asyncio.TimeoutError:
                        # keepalive ping by re-sending subscribe
                        await ws.send(sub_msg)
                        continue

                    try:
                        data = json.loads(raw)
                    except Exception:
                        continue

                    # Finnhub trade payloads: {"type":"trade","data":[{ "s":"AAPL","p":..., "t":... }]}
                    await self.send(text_data=json.dumps(data))

                # unsubscribe on exit
                with contextlib.suppress(Exception):
                    await ws.send(json.dumps({"type": "unsubscribe", "symbol": self.symbol}))
        except websockets.exceptions.ConnectionClosed as e:
            log.warning("Finnhub WS closed: %s", e)
        except Exception as e:
            log.error("Finnhub WS error: %s", e)
            # notify client once
            try:
                await self.send(text_data=json.dumps({"type":"error","message":"upstream unavailable"}))
            except Exception:
                pass
            await asyncio.sleep(0.5)
