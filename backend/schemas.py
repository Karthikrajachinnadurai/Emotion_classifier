from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    daily_reminder: bool
    data_privacy: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    emotion: str
    confidence: float
    mood_score: int
    cbt_response: str
    points_earned: int
    badges_earned: List[str] = []
    probability_distribution: Optional[dict] = None
    inference_time: float
    is_crisis: bool

class EmotionHistoryResponse(BaseModel):
    id: int
    original_message: str
    predicted_emotion: str
    confidence: float
    mood_score: int
    cbt_response: str
    probability_distribution: Optional[str] = None
    inference_time: float
    is_crisis: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardResponse(BaseModel):
    total_points: int
    streak: int
    recent_mood: str
    history_count: int

class BadgeResponse(BaseModel):
    id: int
    badge_name: str
    earned_at: datetime

    class Config:
        from_attributes = True
