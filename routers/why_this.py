from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import get_db
from models.models import UserProfile, BehaviorLog, User
from services.ml_engine import CATEGORIES
from dotenv import load_dotenv
import json, os

load_dotenv()
router  = APIRouter(tags=["intelligence"])
bearer  = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "changethis")
ALGORITHM  = "HS256"


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


@router.get("/why-this")
def why_this(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile found")

    data = json.loads(profile.interest_scores)

    if "hybrid_scores" in data:
        hybrid_scores   = data["hybrid_scores"]
        personal_scores = data.get("personal_scores", {})
        cluster_scores  = data.get("cluster_scores", {})
        cluster_info    = data.get("cluster", {})
        algorithm       = data.get("algorithm", "scoring")
        weights         = data.get("weights", {"personal": 1.0, "cluster": 0.0})
    else:
        hybrid_scores   = data
        personal_scores = data
        cluster_scores  = {}
        cluster_info    = {}
        algorithm       = "scoring"
        weights         = {"personal": 1.0, "cluster": 0.0}

    top_category = max(hybrid_scores, key=hybrid_scores.get)

    # Count events per category for this user
    event_counts = {}
    for cat in CATEGORIES:
        count = db.query(BehaviorLog).filter(
            BehaviorLog.user_id == user.id,
            BehaviorLog.category == cat
        ).count()
        if count > 0:
            event_counts[cat] = count

    top_count = event_counts.get(top_category, 0)

    # Build human-readable explanation
    if algorithm == "hybrid_kmeans" and cluster_info:
        cluster_label = cluster_info.get("cluster_label", "your group")
        cluster_size  = cluster_info.get("cluster_size", 0)
        personal_pct  = int(weights.get("personal", 0.7) * 100)
        cluster_pct   = int(weights.get("cluster",  0.3) * 100)

        reason = (
            f"You personally engaged with {top_count} {top_category} item(s). "
            f"You've been grouped with {cluster_size} similar users in the '{cluster_label}' cluster. "
            f"Your recommendations are {personal_pct}% based on your own behavior "
            f"and {cluster_pct}% influenced by what your group watches — "
            f"helping you discover content you might have missed."
        )
    else:
        reason = (
            f"You engaged with {top_count} {top_category} item(s) recently. "
            f"Recommendations are based on your personal behavior. "
            f"K-Means clustering activates once {3} or more users are in the system."
        )

    return {
        "reason":           reason,
        "top_interest":     top_category,
        "hybrid_scores":    hybrid_scores,
        "personal_scores":  personal_scores,
        "cluster_scores":   cluster_scores,
        "event_counts":     event_counts,
        "ml_info": {
            "algorithm":       algorithm,
            "cluster":         cluster_info,
            "weights":         weights,
        }
    }