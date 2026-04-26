import httpx
import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

CATEGORY_QUERIES = {
    "tech":    "python programming tutorial 2025",
    "sports":  "football highlights 2025",
    "finance": "stock market investing 2025",
    "health":  "workout fitness guide 2025",
}

async def fetch_youtube_videos(category: str, max_results: int = 5) -> list:
    if not YOUTUBE_API_KEY:
        return []  # falls back to seeded content automatically

    query = CATEGORY_QUERIES.get(category, category)
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "relevanceLanguage": "en",
        "safeSearch": "moderate"
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