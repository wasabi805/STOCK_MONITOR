# backend/tracker/consumers.py

import json
import logging
from datetime import datetime, timezone
from channels.generic.websocket import AsyncWebsocketConsumer

# These come from the manager we created in symbol_stream.py
from .symbol_stream import ensure_stream, release_stream, group_name_for

log = logging.getLogger("tracker")


class QuoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Symbol from the URL: /ws/quotes/<symbol>/
        self.symbol = (self.scope["url_route"]["kwargs"].get("symbol") or "").upper()
        if not self.symbol:
            await self.close(code=4001)
            return

        self.group_name = group_name_for(self.symbol)

        # Join group first so we don't miss early messages
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Ensure a shared upstream Finnhub WS is running for this symbol
        await ensure_stream(self.symbol, self.channel_layer)
        log.info("WS client joined %s (%s)", self.symbol, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await release_stream(self.symbol)
        log.info("WS client left %s (%s)", self.symbol, self.channel_name)

    async def quote_message(self, event):
        """
        event = {
            "type": "quote.message",
            "text": "<raw JSON from finnhub>",
            "symbol": "AAPL"
        }
        """

        try:
            raw = json.loads(event.get("text", "{}"))
            if raw.get("type") == "trade" and raw.get("data"):
                ticks = []
                for trade in raw["data"]:
                    ts = trade.get("t")
                    iso = None
                    if ts:
                        try:
                            iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
                        except Exception:
                            iso = None
                    ticks.append({
                        "type": "tick",
                        "symbol": trade.get("s"),
                        "price": trade.get("p"),
                        "ts": ts,
                        "iso": iso
                    })
                if ticks:
                    await self.send(text_data=json.dumps(ticks[-1]))  # only send latest
                    return
        except Exception as e:
            log.debug("Failed to normalize tick: %s", e)

        # fallback — send raw if not parsed
        await self.send(text_data=event.get("text", "{}"))

    async def receive(self, text_data=None, bytes_data=None):
        # Reserved for future browser messages (like changing symbols)
        pass
    async def connect(self):
        # Symbol from the URL: /ws/quotes/<symbol>/
        self.symbol = (self.scope["url_route"]["kwargs"].get("symbol") or "").upper()
        if not self.symbol:
            await self.close(code=4001)
            return

        # Group all clients for this symbol together
        self.group_name = group_name_for(self.symbol)

        # Join group first (so we don't miss early messages), then accept
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Ensure a single upstream Finnhub WS is running for this symbol
        await ensure_stream(self.symbol, self.channel_layer)
        log.info("WS client joined %s (%s)", self.symbol, self.channel_name)

    async def disconnect(self, close_code):
        # Leave the symbol group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        # Decrement subscriber count; stop upstream when last client leaves
        await release_stream(self.symbol)
        log.info("WS client left %s (%s)", self.symbol, self.channel_name)

    # Receive messages from the group (sent by symbol_stream._run_stream)
    async def quote_message(self, event):
        """
        event = {
            "type": "quote.message",
            "text": "<raw json string from finnhub>",
            "symbol": "AAPL"
        }
        """
        # Pass-through (you can normalize here if you prefer)
        await self.send(text_data=event.get("text", "{}"))

    # Optional: handle messages sent from the browser (not used here)
    async def receive(self, text_data=None, bytes_data=None):
        # You could add client commands here (e.g., switch symbol)
        pass
