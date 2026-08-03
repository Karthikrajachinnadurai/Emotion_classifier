from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    emotion_history = relationship("EmotionHistory", back_populates="user")
    wellness_points = relationship("WellnessPoints", back_populates="user")
    badges = relationship("Badge", back_populates="user")

class EmotionHistory(Base):
    __tablename__ = "emotion_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_message = Column(Text, nullable=False)
    predicted_emotion = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    mood_score = Column(Integer, nullable=False)
    cbt_response = Column(Text, nullable=False)
    inference_time = Column(Float, nullable=False)
    probability_distribution = Column(Text, nullable=True)
    is_crisis = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="emotion_history")

class WellnessPoints(Base):
    __tablename__ = "wellness_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    points = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wellness_points")

class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    badge_name = Column(String(100), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="badges")
