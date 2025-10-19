from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

def health(_): return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("tracker.urls")),
    path("", health),                 # GET /
    path("health/", health),          # GET /health/
]

