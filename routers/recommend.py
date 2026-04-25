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

CONTENT_CATALOGUE = [
    {"content_id": "c001", "title": "Python async explained",        "category": "tech"},
    {"content_id": "c002", "title": "React hooks deep dive",         "category": "tech"},
    {"content_id": "c003", "title": "System design for beginners",   "category": "tech"},
    {"content_id": "c004", "title": "Chelsea vs Arsenal highlights", "category": "sports"},
    {"content_id": "c005", "title": "IPL 2025 match recap",          "category": "sports"},
    {"content_id": "c006", "title": "Bitcoin market analysis",       "category": "finance"},
    {"content_id": "c007", "title": "How to invest at 22",           "category": "finance"},
    {"content_id": "c008", "title": "10-minute HIIT workout",        "category": "health"},
    {"content_id": "c009", "title": "Mediterranean diet guide",      "category": "health"},
    {"content_id": "c010", "title": "Sleep and productivity",        "category": "health"},
]

@router.get("/recommend")
def recommend(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        return {"recommendations": [], "message": "No behavior tracked yet"}
    scores = json.loads(profile.interest_scores)
    top_category = max(scores, key=scores.get)
    results = [c for c in CONTENT_CATALOGUE if c["category"] == top_category][:5]
    return {
        "recommendations": results,
        "based_on": top_category,
        "confidence": scores[top_category]
    }