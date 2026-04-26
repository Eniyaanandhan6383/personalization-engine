from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import get_db
from models.models import UserProfile, User
from services.ml_engine import SEEDED_CONTENT, CATEGORIES
from services.youtube_service import fetch_youtube_videos
from dotenv import load_dotenv
import json, os

load_dotenv()
router = APIRouter(tags=["intelligence"])
bearer = HTTPBearer()
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


@router.get("/recommend")
async def recommend(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        return {"recommendations": [], "message": "Track some events first"}

    data = json.loads(profile.interest_scores)

    # Support both old and new profile structure
    if "hybrid_scores" in data:
        hybrid_scores   = data["hybrid_scores"]
        personal_scores = data.get("personal_scores", hybrid_scores)
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

    # Sort categories by hybrid score
    ranked_categories = sorted(hybrid_scores, key=hybrid_scores.get, reverse=True)
    top_category      = ranked_categories[0]
    second_category   = ranked_categories[1] if len(ranked_categories) > 1 else None

    # ── Try YouTube first, fall back to seeded ────────────────────────────
    youtube_results = await fetch_youtube_videos(top_category, max_results=4)

    if youtube_results:
        # 4 from top personal category (YouTube)
        primary_results = youtube_results

        # 1 discovery item from cluster's second category (seeded fallback)
        discovery = []
        if second_category and cluster_scores:
            discovery = SEEDED_CONTENT.get(second_category, [])[:1]

        all_results = primary_results + discovery
        source_used = "youtube + seeded"
    else:
        # All seeded — 70% from top category, 30% from second
        primary   = SEEDED_CONTENT.get(top_category, [])[:4]
        discovery = SEEDED_CONTENT.get(second_category, [])[:1] if second_category else []
        all_results = primary + discovery
        source_used = "seeded"

    return {
        "recommendations":  all_results,
        "explanation": {
            "top_category":    top_category,
            "second_category": second_category,
            "hybrid_scores":   hybrid_scores,
            "personal_weight": weights.get("personal", 0.7),
            "cluster_weight":  weights.get("cluster", 0.3),
            "algorithm":       algorithm,
            "cluster_label":   cluster_info.get("cluster_label", "N/A"),
            "source":          source_used,
        }
    }