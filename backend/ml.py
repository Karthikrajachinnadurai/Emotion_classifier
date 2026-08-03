import sys
import os
import json
import random

# Add the parent directory to sys.path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    load_model_and_tokenizer,
    predict_emotion,
    preprocess_text
)

# Global variables to hold model instances
model = None
tokenizer = None
label_encoder = None
responses_data = None

CRISIS_KEYWORDS = [
    "suicide",
    "kill myself",
    "end my life",
    "self harm",
    "hopeless forever"
]

CRISIS_RESPONSE = (
    "🚨 EMERGENCY SUPPORT NEEDED 🚨\n\n"
    "It sounds like you are going through an incredibly difficult time. "
    "Please know that you are not alone and there is help available right now. "
    "Please reach out to a crisis hotline or go to the nearest emergency room immediately.\n\n"
    "National Suicide Prevention Lifeline: 988\n"
    "Crisis Text Line: Text HOME to 741741"
)

def init_ml():
    global model, tokenizer, label_encoder, responses_data
    if model is None:
        model, tokenizer, label_encoder = load_model_and_tokenizer()
        
        responses_file = os.path.join(os.path.dirname(__file__), "responses.json")
        with open(responses_file, "r") as f:
            responses_data = json.load(f)

def detect_crisis(text):
    text_lower = text.lower()
    for kw in CRISIS_KEYWORDS:
        if kw in text_lower:
            return True
    return False

def get_smart_response(emotion, confidence, text):
    # Determine confidence level
    if confidence >= 0.90:
        conf_level = "high"
    elif confidence >= 0.70:
        conf_level = "medium"
    else:
        conf_level = "low"
        
    emotion_responses = responses_data.get(emotion, responses_data.get("sadness"))
    level_responses = emotion_responses.get(conf_level, emotion_responses.get("low"))
    
    # Check keywords in text
    text_lower = text.lower()
    chosen_category = "default"
    for kw in level_responses.keys():
        if kw != "default" and kw in text_lower:
            chosen_category = kw
            break
            
    possible_responses = level_responses.get(chosen_category, level_responses.get("default"))
    
    disclaimer = "\n\n*Disclaimer: I am an AI, not a medical professional. This is an AI prediction, not a diagnosis.*"
    return random.choice(possible_responses) + disclaimer
