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
print(f"[DEBUG] SECRET_KEY loaded as: {SECRET_KEY}")
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
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
    log = BehaviorLog(
        user_id    = user.id,
        event_type = event.event_type,
        content_id = event.content_id,
        category   = event.category,
        value      = event.value
    )
    db.add(log)
    db.commit()
    background_tasks.add_task(build_user_profile, user.id)
    
    return {"status": "tracked", "category": event.category}
    