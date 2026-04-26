from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from database import get_db
from models.models import BehaviorLog, User
from schemas.schemas import TrackEvent
from services.ml_engine import build_user_profile
from dotenv import load_dotenv
import os

load_dotenv()
router = APIRouter(tags=["tracking"])
bearer = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "changethis")
ALGORITHM = "HS256"

VALID_CATEGORIES = {
    "tech", "sports", "finance", "health",
    "gaming", "music", "education", "food",
    "travel", "fashion", "news", "science"
}
VALID_EVENT_TYPES = {"click", "watch", "search"}


def normalize_category(raw: str) -> str:
    """Fix spelling mistakes and common variations — returns normalized category."""
    raw = raw.lower().strip()
    mapping = {
        # tech
        "tech": "tech", "technology": "tech", "coding": "tech",
        "programming": "tech", "software": "tech", "it": "tech", "developer": "tech",
        # sports
        "sport": "sports", "sports": "sports", "football": "sports",
        "cricket": "sports", "basketball": "sports", "game": "sports", "ipl": "sports",
        # finance
        "finance": "finance", "financial": "finance", "money": "finance",
        "investing": "finance", "investment": "finance", "stock": "finance", "crypto": "finance",
        # health
        "health": "health", "healthy": "health", "wellness": "health",
        "medical": "health", "workout": "health", "diet": "health", "fitness": "health",
        # gaming
        "gaming": "gaming", "games": "gaming", "videogames": "gaming",
        "esports": "gaming", "playstation": "gaming", "xbox": "gaming",
        # music
        "music": "music", "songs": "music", "audio": "music",
        "beats": "music", "playlist": "music", "singing": "music",
        # education
        "education": "education", "learning": "education", "study": "education",
        "tutorial": "education", "course": "education", "academic": "education",
        # food
        "food": "food", "cooking": "food", "recipe": "food",
        "eating": "food", "cuisine": "food", "restaurant": "food",
        # travel
        "travel": "travel", "travelling": "travel", "tourism": "travel",
        "vacation": "travel", "trip": "travel", "vlog": "travel",
        # fashion
        "fashion": "fashion", "style": "fashion", "clothing": "fashion",
        "outfit": "fashion", "skincare": "fashion", "beauty": "fashion",
        # news
        "news": "news", "current affairs": "news", "politics": "news",
        "world": "news", "breaking": "news", "media": "news",
        # science
        "science": "science", "scientific": "science", "physics": "science",
        "biology": "science", "space": "science", "astronomy": "science",
    }
    return mapping.get(raw, raw)  # returns original if no match — caught by validator below


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


@router.post("/track")
def track_event(
    event: TrackEvent,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Normalize first — fixes spelling and casing
    category   = normalize_category(event.category)
    event_type = event.event_type.lower().strip()

    # Validate category AFTER normalization
    if category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid category '{event.category}'",
                "valid_categories": sorted(list(VALID_CATEGORIES)),
                "hint": "Check spelling. We also accept variations like 'coding' → tech, 'fitness' → health"
            }
        )

    # Validate event_type
    if event_type not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid event_type '{event.event_type}'",
                "valid_event_types": list(VALID_EVENT_TYPES),
                "hint": "Use: click, watch, or search"
            }
        )

    # Validate value
    if event.value is not None and event.value <= 0:
        raise HTTPException(
            status_code=400,
            detail={"error": "value must be greater than 0"}
        )

    log = BehaviorLog(
        user_id    = user.id,
        event_type = event_type,
        content_id = event.content_id.strip(),
        category   = category,
        value      = event.value or 1.0
    )
    db.add(log)
    db.commit()

    background_tasks.add_task(build_user_profile, user.id)

    return {
        "status":     "tracked",
        "category":   category,
        "event_type": event_type,
        "normalized": category != event.category.lower().strip()
    }