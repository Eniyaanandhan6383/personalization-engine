from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import get_db
from models.models import UserProfile, BehaviorLog, User
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

@router.get("/why-this")
def why_this(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile found — track some events first")

    scores = json.loads(profile.interest_scores)
    top_category = max(scores, key=scores.get)

    # Count per category
    all_counts = {}
    for category in scores.keys():
        count = db.query(BehaviorLog).filter(
            BehaviorLog.user_id == user.id,
            BehaviorLog.category == category
        ).count()
        all_counts[category] = count

    top_count = all_counts[top_category]

    return {
        "reason": f"You engaged with {top_count} {top_category} item(s) recently, making it your top interest.",
        "top_interest": top_category,
        "interest_score": scores[top_category],
        "all_interests": scores,
        "event_counts": all_counts
    }