import httpx
import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

CATEGORY_QUERIES = {
    "tech":      "programming tutorial 2025",
    "sports":    "sports highlights 2025",
    "finance":   "personal finance investing 2025",
    "health":    "workout fitness health 2025",
    "gaming":    "gaming gameplay 2025",
    "music":     "music hits 2025",
    "education": "educational learning tutorial 2025",
    "food":      "cooking recipes food 2025",
    "travel":    "travel vlog destinations 2025",
    "fashion":   "fashion style outfit 2025",
    "news":      "world news today 2025",
    "science":   "science explained 2025",
}

async def fetch_youtube_videos(category: str, max_results: int = 5) -> list:
    if not YOUTUBE_API_KEY:
        return []

    query = CATEGORY_QUERIES.get(category, f"{category} 2025")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part":             "snippet",
        "q":                query,
        "type":             "video",
        "maxResults":       max_results,
        "key":              YOUTUBE_API_KEY,
        "relevanceLanguage":"en",
        "safeSearch":       "moderate",
        "videoDuration":    "medium",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            data = resp.json()

        if "error" in data:
            print(f"[YOUTUBE] API error: {data['error']['message']}")
            return []

        return [
            {
                "content_id": item["id"]["videoId"],
                "title":      item["snippet"]["title"],
                "category":   category,
                "source":     "youtube",
                "channel":    item["snippet"]["channelTitle"],
                "thumbnail":  item["snippet"]["thumbnails"]["medium"]["url"],
                "url":        f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }
            for item in data.get("items", [])
        ]
    except Exception as e:
        print(f"[YOUTUBE] Fetch failed: {e}")
        return []