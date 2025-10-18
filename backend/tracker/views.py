from django.shortcuts import render


# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .services.finnhub_service import get_quote, FinnhubError

@api_view(["GET"])
def quote_view(request, symbol: str):
    try:
        data = get_quote(symbol)
        return Response(data)
    except FinnhubError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": "Unexpected error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(["GET"])
def history_view(request, symbol: str):
    res = request.GET.get("resolution", "1")  # 1,5,15,30,60, D, W, M
    days = int(request.GET.get("days", 5))
    to_ = int(datetime.utcnow().timestamp())
    frm_ = int((datetime.utcnow() - timedelta(days=days)).timestamp())
    try:
        candles = get_candles(symbol, resolution=res, frm=frm_, to=to_)
        return Response(candles)
    except FinnhubError as e:
        return Response({"error": str(e)}, status=400)
