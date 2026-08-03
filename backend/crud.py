from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, timedelta

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str):
    db_user = models.User(name=user.name, email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def add_emotion_history(db: Session, user_id: int, original_message: str, predicted_emotion: str, confidence: float, mood_score: int, cbt_response: str, inference_time: float):
    db_history = models.EmotionHistory(
        user_id=user_id,
        original_message=original_message,
        predicted_emotion=predicted_emotion,
        confidence=confidence,
        mood_score=mood_score,
        cbt_response=cbt_response,
        inference_time=inference_time
    )
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history

def add_wellness_points(db: Session, user_id: int, points: int, reason: str):
    db_points = models.WellnessPoints(user_id=user_id, points=points, reason=reason)
    db.add(db_points)
    db.commit()
    db.refresh(db_points)
    return db_points

def assign_badge(db: Session, user_id: int, badge_name: str):
    existing = db.query(models.Badge).filter(models.Badge.user_id == user_id, models.Badge.badge_name == badge_name).first()
    if not existing:
        new_badge = models.Badge(user_id=user_id, badge_name=badge_name)
        db.add(new_badge)
        db.commit()
        db.refresh(new_badge)
        return True
    return False

def check_and_award_gamification(db: Session, user_id: int, mood_score: int):
    points_earned = 0
    badges_earned = []
    
    # 1. Daily Check-in (+10)
    today = datetime.utcnow().date()
    daily_pts = db.query(models.WellnessPoints).filter(
        models.WellnessPoints.user_id == user_id,
        models.WellnessPoints.reason == "Daily Check-in"
    ).all()
    
    already_checked_in = any(pt.created_at.date() == today for pt in daily_pts)
    if not already_checked_in:
        add_wellness_points(db, user_id, 10, "Daily Check-in")
        points_earned += 10

    # 2. Positive Improvement (+25)
    last_two_histories = db.query(models.EmotionHistory).filter(models.EmotionHistory.user_id == user_id).order_by(models.EmotionHistory.created_at.desc()).limit(2).all()
    if len(last_two_histories) == 2:
        prev_mood = last_two_histories[1].mood_score
        if mood_score > prev_mood:
            add_wellness_points(db, user_id, 25, "Positive Improvement")
            points_earned += 25

    # 3. 7-day Streak (+50)
    past_7_days = [today - timedelta(days=i) for i in range(7)]
    recent_checkins = db.query(models.WellnessPoints).filter(
        models.WellnessPoints.user_id == user_id,
        models.WellnessPoints.reason == "Daily Check-in",
        models.WellnessPoints.created_at >= (datetime.utcnow() - timedelta(days=7))
    ).all()
    unique_days = set(c.created_at.date() for c in recent_checkins)
    if len(unique_days) >= 7:
        streak_awarded_recently = db.query(models.WellnessPoints).filter(
            models.WellnessPoints.user_id == user_id,
            models.WellnessPoints.reason == "7-day Streak",
            models.WellnessPoints.created_at >= (datetime.utcnow() - timedelta(days=7))
        ).first()
        if not streak_awarded_recently:
            add_wellness_points(db, user_id, 50, "7-day Streak")
            points_earned += 50

    # 4. 100 Analyses (+100)
    total_analyses = db.query(models.EmotionHistory).filter(models.EmotionHistory.user_id == user_id).count()
    if total_analyses == 100:
        add_wellness_points(db, user_id, 100, "100 Analyses")
        points_earned += 100

    # Check Badges
    if total_analyses == 1:
        if assign_badge(db, user_id, "🌱 First Reflection"): badges_earned.append("🌱 First Reflection")
    
    if len(unique_days) >= 3:
        if assign_badge(db, user_id, "⭐ Consistency"): badges_earned.append("⭐ Consistency")
        
    total_points = get_total_points(db, user_id)
    if total_points >= 100:
        if assign_badge(db, user_id, "🥉 Bronze Wellness"): badges_earned.append("🥉 Bronze Wellness")
    if total_points >= 500:
        if assign_badge(db, user_id, "🥈 Silver Wellness"): badges_earned.append("🥈 Silver Wellness")
    if total_points >= 1000:
        if assign_badge(db, user_id, "🥇 Gold Wellness"): badges_earned.append("🥇 Gold Wellness")
    
    # 🏆 Wellness Champion badge condition (custom condition e.g. 5000 points)
    if total_points >= 5000:
        if assign_badge(db, user_id, "🏆 Wellness Champion"): badges_earned.append("🏆 Wellness Champion")
    
    return points_earned, badges_earned

def get_total_points(db: Session, user_id: int):
    points = db.query(models.WellnessPoints).filter(models.WellnessPoints.user_id == user_id).all()
    return sum(p.points for p in points)
