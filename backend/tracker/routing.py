from django.urls import re_path
from .consumers import QuoteConsumer

websocket_urlpatterns = [
    re_path(r"^ws/quotes/(?P<symbol>[A-Za-z0-9\.\-\_]+)/$", QuoteConsumer.as_asgi()),
]
