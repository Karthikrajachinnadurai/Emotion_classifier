from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models, crud, dependencies
from datetime import datetime, timedelta

router = APIRouter(prefix="", tags=["gamification"])

@router.get("/history", response_model=List[schemas.EmotionHistoryResponse])
def get_history(db: Session = Depends(dependencies.get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    return db.query(models.EmotionHistory).filter(models.EmotionHistory.user_id == current_user.id).order_by(models.EmotionHistory.created_at.desc()).all()

@router.delete("/history/{id}")
def delete_history(id: int, db: Session = Depends(dependencies.get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    history = db.query(models.EmotionHistory).filter(models.EmotionHistory.id == id, models.EmotionHistory.user_id == current_user.id).first()
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    db.delete(history)
    db.commit()
    return {"message": "History deleted successfully"}

@router.get("/dashboard", response_model=schemas.DashboardResponse)
def get_dashboard(db: Session = Depends(dependencies.get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    total_points = crud.get_total_points(db, current_user.id)
    history_count = db.query(models.EmotionHistory).filter(models.EmotionHistory.user_id == current_user.id).count()
    
    recent = db.query(models.EmotionHistory).filter(models.EmotionHistory.user_id == current_user.id).order_by(models.EmotionHistory.created_at.desc()).first()
    recent_mood = recent.predicted_emotion if recent else "None"
    
    # Calculate streak (simplified: days with checkins)
    streak = 0
    today = datetime.utcnow().date()
    for i in range(365):
        day = today - timedelta(days=i)
        checkin = db.query(models.WellnessPoints).filter(
            models.WellnessPoints.user_id == current_user.id,
            models.WellnessPoints.reason == "Daily Check-in"
        ).filter(models.WellnessPoints.created_at >= day, models.WellnessPoints.created_at < day + timedelta(days=1)).first()
        if checkin:
            streak += 1
        else:
            if i != 0: # allow missing today if not checked in yet, but break if missed yesterday
                break

    return schemas.DashboardResponse(
        total_points=total_points,
        streak=streak,
        recent_mood=recent_mood,
        history_count=history_count
    )

@router.get("/badges", response_model=List[schemas.BadgeResponse])
def get_badges(db: Session = Depends(dependencies.get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    return db.query(models.Badge).filter(models.Badge.user_id == current_user.id).all()

@router.get("/weekly-summary")
def get_weekly_summary(db: Session = Depends(dependencies.get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=7)
    histories = db.query(models.EmotionHistory).filter(
        models.EmotionHistory.user_id == current_user.id,
        models.EmotionHistory.created_at >= start_date
    ).all()
    
    summary = {}
    for i in range(7):
        day = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        summary[day] = []
        
    emotion_counts = {}
    total_conf = 0
    total_score = 0
    positive_days = 0
    difficult_days = 0
    
    for h in histories:
        day_str = h.created_at.date().strftime("%Y-%m-%d")
        if day_str in summary:
            summary[day_str].append(h.mood_score)
            
        emotion_counts[h.predicted_emotion] = emotion_counts.get(h.predicted_emotion, 0) + 1
        total_conf += h.confidence
        total_score += h.mood_score
        if h.mood_score >= 4:
            positive_days += 1
        elif h.mood_score <= 2:
            difficult_days += 1
            
    avg_summary = {}
    for day, scores in summary.items():
        avg_summary[day] = sum(scores) / len(scores) if scores else 0
        
    freq_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "None"
    avg_conf = (total_conf / len(histories)) if histories else 0
    avg_score = (total_score / len(histories)) if histories else 0
    
    suggestions = []
    if difficult_days > 3:
        suggestions.append("You've had a tough week. Please be gentle with yourself.")
    elif positive_days > 4:
        suggestions.append("You've had a very positive week! Keep up the great momentum.")
        
    return {
        "weekly_mood_trend": avg_summary,
        "most_frequent_emotion": freq_emotion,
        "average_mood_score": avg_score,
        "average_confidence": avg_conf,
        "positive_days": positive_days,
        "difficult_days": difficult_days,
        "suggestions": suggestions
    }

@router.get("/insights")
def get_insights(db: Session = Depends(dependencies.get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    last_week_start = today - timedelta(days=7)
    
    def get_avg_for_period(start, end):
        histories = db.query(models.EmotionHistory).filter(
            models.EmotionHistory.user_id == current_user.id,
            models.EmotionHistory.created_at >= start,
            models.EmotionHistory.created_at < end + timedelta(days=1)
        ).all()
        if not histories:
            return None
        return sum(h.mood_score for h in histories) / len(histories)

    today_avg = get_avg_for_period(today, today)
    yesterday_avg = get_avg_for_period(yesterday, yesterday)
    last_week_avg = get_avg_for_period(last_week_start, today)
    
    insights = []
    if today_avg is not None and yesterday_avg is not None:
        if today_avg > yesterday_avg:
            insights.append("You've shown improvement compared with yesterday.")
        elif today_avg == yesterday_avg:
            insights.append("You've maintained a consistent mood since yesterday.")
            
    if today_avg is not None and last_week_avg is not None:
        if today_avg > last_week_avg:
            insights.append("Your mood today is better than your weekly average. Great job!")
            
    if today_avg is not None:
        insights.append("Thank you for checking in today.")
        
    if not insights:
        insights.append("Start checking in regularly to see your progress insights here!")
        
    return {"insights": insights}

@router.get("/analytics")
def get_analytics(db: Session = Depends(dependencies.get_db), current_user: models.User = Depends(dependencies.get_current_user)):
    histories = db.query(models.EmotionHistory).filter(models.EmotionHistory.user_id == current_user.id).all()
    total = len(histories)
    if total == 0:
        return {"emotion_distribution": {}}
        
    dist = {}
    for h in histories:
        dist[h.predicted_emotion] = dist.get(h.predicted_emotion, 0) + 1
        
    for k in dist:
        dist[k] = (dist[k] / total) * 100
        
    return {"emotion_distribution": dist}
