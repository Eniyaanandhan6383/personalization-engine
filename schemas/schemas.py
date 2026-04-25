from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime

class UserRegister(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TrackEvent(BaseModel):
    event_type: str        # "click", "watch", "search"
    content_id: str
    category: str          # "tech", "sports", "finance", "health"
    value: Optional[float] = 1.0

class ProfileResponse(BaseModel):
    user_id: str
    interest_scores: Dict[str, float]

class RecommendResponse(BaseModel):
    content_id: str
    category: str
    score: float