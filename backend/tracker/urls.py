from django.urls import path
from .views import quote_view, history_view
from .views_youtube import youtube_search

urlpatterns = [
    path("stock/<str:symbol>/", quote_view),
    path("history/<str:symbol>/", history_view),
    path("youtube/search/", youtube_search),
]
