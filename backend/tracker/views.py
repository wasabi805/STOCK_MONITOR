from django.shortcuts import render


# Create your views here.
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services.finnhub_service import get_quote, get_candles, FinnhubError, FinnhubRateLimit

@api_view(["GET"])
def quote_view(request, symbol: str):
    try:
        data = get_quote(symbol)
        # Hint to caller it’s cached/short-lived
        return Response(data, headers={"Cache-Control": "public, max-age=5"})
    except FinnhubRateLimit:
        return Response({"error": "Upstream rate limited, try again shortly."}, status=429)
    except FinnhubError as e:
        return Response({"error": str(e)}, status=400)
    except Exception:
        return Response({"error": "Unexpected error"}, status=500)

@api_view(["GET"])
def history_view(request, symbol: str):
    res = request.GET.get("resolution", "1")
    days = int(request.GET.get("days", 5))
    to_ = int(datetime.utcnow().timestamp())
    frm_ = int((datetime.utcnow() - timedelta(days=days)).timestamp())
    try:
        data = get_candles(symbol, resolution=res, frm=frm_, to=to_)
        return Response(data, headers={"Cache-Control": "public, max-age=60"})
    except FinnhubRateLimit:
        return Response({"error": "Upstream rate limited, try again shortly."}, status=429)
    except FinnhubError as e:
        return Response({"error": str(e)}, status=400)
    except Exception:
        return Response({"error": "Unexpected error"}, status=500)
