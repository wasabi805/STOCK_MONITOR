import os
import json
import urllib.parse
import urllib.request

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from dotenv import load_dotenv


@require_GET
def youtube_search(request):
    """
    GET /api/youtube/search/?q=...
    Returns: { "items": [ {videoId,title,channelTitle,thumb}, ... ] }
    """

    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"items": []})

    # Load env from repo root backend.env (safe on server)
    # backend/ is one level below repo root
    load_dotenv("../backend.env")

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        return JsonResponse({"error": "Missing YOUTUBE_API_KEY on server"}, status=500)

    params = {
        "part": "snippet",
        "q": q,
        "type": "video",
        "maxResults": "12",
        "regionCode": "US",
        "safeSearch": "none",
        "key": api_key,
    }

    url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return JsonResponse({"error": f"YouTube API request failed: {e}"}, status=502)

    items = []
    for it in data.get("items", []):
        vid = (it.get("id") or {}).get("videoId")
        sn = it.get("snippet") or {}
        if not vid:
            continue

        thumbs = sn.get("thumbnails") or {}
        thumb = (thumbs.get("medium") or thumbs.get("default") or {}).get("url") or ""

        items.append({
            "videoId": vid,
            "title": sn.get("title") or "",
            "channelTitle": sn.get("channelTitle") or "",
            "thumb": thumb,
        })

    return JsonResponse({"items": items})

