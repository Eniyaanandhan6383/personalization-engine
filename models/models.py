from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey
from database import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    id         = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    email      = Column(String(255), unique=True, nullable=False)
    password   = Column(String(255), nullable=False)
    api_key    = Column(String(255), unique=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)

class BehaviorLog(Base):
    __tablename__ = "behavior_logs"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String(255), ForeignKey("users.id"), nullable=False)
    event_type = Column(String(255), nullable=False)
    content_id = Column(String(255), nullable=False)
    category   = Column(String(255), nullable=False)
    value      = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id         = Column(String(255), ForeignKey("users.id"), primary_key=True)
    interest_scores = Column(Text, default="{}")
    updated_at      = Column(DateTime, default=datetime.utcnow)

class Ad(Base):
    __tablename__ = "ads"
    id       = Column(Integer, primary_key=True, autoincrement=True)
    title    = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    url      = Column(String(255))
    body     = Column(String(255))