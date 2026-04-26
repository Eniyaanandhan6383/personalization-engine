from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import get_db
from models.models import UserProfile, User
from dotenv import load_dotenv
import json, os

load_dotenv()

router = APIRouter(tags=["intelligence"])
bearer = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "changethis")
ALGORITHM = "HS256"

VALID_CATEGORIES = {"tech", "sports", "finance", "health"}

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.id == payload.get("sub")).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

FAKE_ADS = [
    # tech
    {"ad_id": "a001", "title": "Learn AWS in 30 days",          "category": "tech",      "url": "https://example.com/aws",      "body": "Master cloud with hands-on labs"},
    {"ad_id": "a002", "title": "GitHub Copilot Pro",             "category": "tech",      "url": "https://example.com/copilot",  "body": "AI pair programmer for developers"},
    # sports
    {"ad_id": "a003", "title": "Nike Running Shoes Sale",        "category": "sports",    "url": "https://example.com/nike",     "body": "Up to 40% off this weekend"},
    {"ad_id": "a004", "title": "Dream11 — Win Big Today",        "category": "sports",    "url": "https://example.com/d11",      "body": "Join 10 crore+ players"},
    # finance
    {"ad_id": "a005", "title": "Zerodha — Start Investing",      "category": "finance",   "url": "https://example.com/zerodha",  "body": "India's largest stock broker"},
    {"ad_id": "a006", "title": "Groww Mutual Funds",             "category": "finance",   "url": "https://example.com/groww",    "body": "Start SIP with just ₹100"},
    # health
    {"ad_id": "a007", "title": "Cult.fit Membership",            "category": "health",    "url": "https://example.com/cult",     "body": "Workout, nutrition and more"},
    {"ad_id": "a008", "title": "HealthifyMe Pro",                "category": "health",    "url": "https://example.com/hfm",      "body": "AI diet and fitness coach"},
    # gaming
    {"ad_id": "a009", "title": "Xbox Game Pass Ultimate",        "category": "gaming",    "url": "https://example.com/xbox",     "body": "100+ games for one price"},
    {"ad_id": "a010", "title": "Razer Gaming Headset Deal",      "category": "gaming",    "url": "https://example.com/razer",    "body": "Pro audio for serious gamers"},
    # music
    {"ad_id": "a011", "title": "Spotify Premium — 3 months free","category": "music",     "url": "https://example.com/spotify",  "body": "Ad-free music streaming"},
    {"ad_id": "a012", "title": "Learn Guitar Online",            "category": "music",     "url": "https://example.com/guitar",   "body": "From beginner to pro in 60 days"},
    # education
    {"ad_id": "a013", "title": "Coursera Plus — All Courses",    "category": "education", "url": "https://example.com/coursera", "body": "7000+ courses from top unis"},
    {"ad_id": "a014", "title": "Unacademy Pro Subscription",     "category": "education", "url": "https://example.com/unacad",   "body": "India's best educators live"},
    # food
    {"ad_id": "a015", "title": "Swiggy One — Free Delivery",     "category": "food",      "url": "https://example.com/swiggy",   "body": "Unlimited free delivery all month"},
    {"ad_id": "a016", "title": "Nykaa Kitchen Deals",            "category": "food",      "url": "https://example.com/kitchen",  "body": "Premium cookware at best prices"},
    # travel
    {"ad_id": "a017", "title": "MakeMyTrip Holiday Packages",    "category": "travel",    "url": "https://example.com/mmt",      "body": "Book now, pay later options"},
    {"ad_id": "a018", "title": "Airbnb — ₹2000 off first stay",  "category": "travel",    "url": "https://example.com/airbnb",   "body": "Unique stays worldwide"},
    # fashion
    {"ad_id": "a019", "title": "Myntra End of Season Sale",      "category": "fashion",   "url": "https://example.com/myntra",   "body": "Up to 80% off top brands"},
    {"ad_id": "a020", "title": "Nykaa Beauty — Buy 2 Get 1",     "category": "fashion",   "url": "https://example.com/nykaa",    "body": "Top skincare brands on sale"},
    # news
    {"ad_id": "a021", "title": "The Hindu Digital — ₹99/month",  "category": "news",      "url": "https://example.com/hindu",    "body": "Trusted journalism since 1878"},
    {"ad_id": "a022", "title": "Bloomberg Quint Premium",        "category": "news",      "url": "https://example.com/bq",       "body": "Business and market news"},
    # science
    {"ad_id": "a023", "title": "Brilliant.org — Learn Science",  "category": "science",   "url": "https://example.com/brilliant","body": "Interactive STEM learning"},
    {"ad_id": "a024", "title": "National Geographic Premium",    "category": "science",   "url": "https://example.com/natgeo",   "body": "Science, nature and exploration"},
]

def normalize_category(raw: str) -> str:
    """Fix spelling mistakes and variations."""
    raw = raw.lower().strip()
    mapping = {
        # tech variations
        "tech": "tech", "technology": "tech", "coding": "tech",
        "programming": "tech", "software": "tech", "it": "tech",
        # sports variations
        "sport": "sports", "sports": "sports", "football": "sports",
        "cricket": "sports", "fitness": "sports", "game": "sports",
        # finance variations
        "finance": "finance", "financial": "finance", "money": "finance",
        "investing": "finance", "investment": "finance", "stock": "finance",
        # health variations
        "health": "health", "healthy": "health", "wellness": "health",
        "medical": "health", "workout": "health", "diet": "health",
    }
    return mapping.get(raw, raw)  # returns original if no match found

def extract_scores(data: dict) -> dict:
    """Safely extract scores from any profile structure."""
    if "hybrid_scores" in data:
        scores = data["hybrid_scores"]
    elif "interest_scores" in data:
        scores = data["interest_scores"]
    else:
        scores = data

    if not isinstance(scores, dict):
        return {}

    # Only keep valid categories with score > 0
    return {k: v for k, v in scores.items() if k in VALID_CATEGORIES and v > 0}

@router.get("/ads")
def get_ads(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        return {
            "ads": [],
            "message": "No profile found. Use POST /track to log some behavior first.",
            "hint": "Example: POST /track with category = tech, sports, finance, or health"
        }

    data = json.loads(profile.interest_scores)
    active_scores = extract_scores(data)

    if not active_scores:
        return {
            "ads": [],
            "message": "No valid behavior tracked yet.",
            "hint": f"Valid categories are: {', '.join(VALID_CATEGORIES)}"
        }

    top_category = max(active_scores, key=active_scores.get)
    matched_ads = [a for a in FAKE_ADS if a["category"] == top_category]

    return {
        "ads": matched_ads,
        "targeted_for": top_category,
        "confidence": active_scores[top_category],
        "all_scores": active_scores
    }