from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email      = Column(String, unique=True, nullable=False)
    password   = Column(String, nullable=False)
    api_key    = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)

class BehaviorLog(Base):
    __tablename__ = "behavior_logs"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String, ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)   # click, watch, search
    content_id = Column(String, nullable=False)
    category   = Column(String, nullable=False)   # tech, sports, finance, health
    value      = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id          = Column(String, ForeignKey("users.id"), primary_key=True)
    interest_scores  = Column(Text, default="{}")  # stored as JSON string
    updated_at       = Column(DateTime, default=datetime.utcnow)

class Ad(Base):
    __tablename__ = "ads"
    id       = Column(Integer, primary_key=True, autoincrement=True)
    title    = Column(String, nullable=False)
    category = Column(String, nullable=False)
    url      = Column(String)
    body     = Column(String)