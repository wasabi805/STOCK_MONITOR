from django.urls import path
from .views import quote_view, history_view

urlpatterns = [
    path("stock/<str:symbol>/", quote_view),
    path("history/<str:symbol>/", history_view),
]
