from sqlalchemy.orm import Session
from database import SessionLocal
from models.models import BehaviorLog, UserProfile
from datetime import datetime
import json

def build_user_profile(user_id: str):
    db = SessionLocal()
    try:
        logs = db.query(BehaviorLog).filter(BehaviorLog.user_id == user_id).all()
        if not logs:
            return
        scores = {}
        now = datetime.utcnow()
        for log in logs:
            age_days = (now - log.created_at).days
            recency_weight = 1 / (1 + age_days * 0.1)
            scores[log.category] = scores.get(log.category, 0) + (log.value * recency_weight)
        total = sum(scores.values())
        normalized = {k: round(v / total, 3) for k, v in scores.items()}
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            profile.interest_scores = json.dumps(normalized)
            profile.updated_at = datetime.utcnow()
        else:
            profile = UserProfile(user_id=user_id, interest_scores=json.dumps(normalized))
            db.add(profile)
        db.commit()
    finally:
        db.close()