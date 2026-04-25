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

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.query(User).filter(User.id == payload.get("sub")).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

FAKE_ADS = [
    {"ad_id": "a001", "title": "Learn AWS in 30 days",         "category": "tech",    "url": "https://example.com/aws",     "body": "Master cloud with hands-on labs"},
    {"ad_id": "a002", "title": "GitHub Copilot Pro",            "category": "tech",    "url": "https://example.com/copilot", "body": "AI pair programmer for developers"},
    {"ad_id": "a003", "title": "Nike Running Shoes Sale",       "category": "sports",  "url": "https://example.com/nike",    "body": "Up to 40% off this weekend"},
    {"ad_id": "a004", "title": "Dream11 — Win Big Today",       "category": "sports",  "url": "https://example.com/d11",     "body": "Join 10 crore+ players"},
    {"ad_id": "a005", "title": "Zerodha — Start Investing",     "category": "finance", "url": "https://example.com/zerodha", "body": "India's largest stock broker"},
    {"ad_id": "a006", "title": "Groww Mutual Funds",            "category": "finance", "url": "https://example.com/groww",   "body": "Start SIP with just ₹100"},
    {"ad_id": "a007", "title": "Cult.fit Membership",           "category": "health",  "url": "https://example.com/cult",    "body": "Workout, nutrition and more"},
    {"ad_id": "a008", "title": "HealthifyMe Pro",               "category": "health",  "url": "https://example.com/hfm",     "body": "AI diet and fitness coach"},
]

@router.get("/ads")
def get_ads(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        return {"ads": [], "message": "No profile yet — track some events first"}
    scores = json.loads(profile.interest_scores)
    top_category = max(scores, key=scores.get)
    matched_ads = [a for a in FAKE_ADS if a["category"] == top_category]
    return {
        "ads": matched_ads,
        "targeted_for": top_category,
        "confidence": scores[top_category]
    }