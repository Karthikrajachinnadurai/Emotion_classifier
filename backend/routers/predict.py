from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, crud, dependencies, ml

router = APIRouter(prefix="", tags=["predict"])

MOOD_SCORE_MAP = {
    "joy": 5,
    "love": 5,
    "surprise": 4,
    "sadness": 2,
    "fear": 1,
    "anger": 1,
    "crisis": 1
}

@router.post("/predict", response_model=schemas.PredictResponse)
def predict(
    request: schemas.PredictRequest,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_user)
):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    ml.init_ml()
    text = ml.preprocess_text(request.text)
    
    is_crisis = ml.detect_crisis(text)
    if is_crisis:
        emotion = "crisis"
        confidence = 1.0
        probabilities = {"crisis": 1.0}
        cbt_response = ml.CRISIS_RESPONSE
        inference_time = 0.0
    else:
        # fetch last 5 histories for context display (UI)
        histories = db.query(models.EmotionHistory).filter(
            models.EmotionHistory.user_id == current_user.id
        ).order_by(models.EmotionHistory.created_at.desc()).limit(5).all()
        
        # Do not feed history to model to avoid prediction drift
        result = ml.predict_emotion(text, ml.model, ml.tokenizer, ml.label_encoder)
        emotion = result["predicted_emotion"]
        confidence = result["confidence"]
        probabilities = result["probabilities"]
        cbt_response = ml.get_smart_response(emotion, confidence, text)
        inference_time = result["inference_time_ms"]

    mood_score = MOOD_SCORE_MAP.get(emotion, 3)

    # Save history
    import json
    prob_str = json.dumps(probabilities) if probabilities else None
    
    new_history = models.EmotionHistory(
        user_id=current_user.id,
        original_message=request.text,
        predicted_emotion=emotion,
        confidence=confidence,
        mood_score=mood_score,
        cbt_response=cbt_response,
        inference_time=inference_time,
        probability_distribution=prob_str,
        is_crisis=is_crisis
    )
    db.add(new_history)
    db.commit()
    db.refresh(new_history)

    # Gamification
    points_earned, badges_earned = crud.check_and_award_gamification(db, current_user.id, mood_score)

    return schemas.PredictResponse(
        emotion=emotion,
        confidence=confidence,
        mood_score=mood_score,
        cbt_response=cbt_response,
        points_earned=points_earned,
        badges_earned=badges_earned,
        probability_distribution=probabilities,
        inference_time=inference_time,
        is_crisis=is_crisis
    )
