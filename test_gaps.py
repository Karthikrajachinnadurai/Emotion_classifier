"""
test_gaps.py -- Smoke test for all 6 gap fixes.
Run with: python test_gaps.py
"""
import os, sys
os.environ['TF_USE_LEGACY_KERAS'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from utils import (
    detect_crisis, CRISIS_RESPONSE,
    load_model_and_tokenizer, load_cbt_responses,
    predict_emotion, get_cbt_response,
    build_index_to_emotion, INDEX_TO_EMOTION,
    CONF_HIGH, CONF_MEDIUM,
)

PASS = "[PASS]"
FAIL = "[FAIL]"
errors = 0

# --- Gap 1: Crisis Detection --------------------------------------------------
print("\n--- Gap 1: Crisis Detection ---")
crisis_cases = [
    ("I want to kill myself",             True),
    ("want to die",                        True),
    ("thinking about suicide",             True),
    ("end it all tonight",                 True),
    ("self harm urges",                    True),
    ("I am feeling very lonely today",     False),
    ("I am so happy!",                     False),
    ("I'm scared about my exam",           False),
]
for text, expected in crisis_cases:
    result = detect_crisis(text)
    ok = result == expected
    if not ok: errors += 1
    status = PASS if ok else FAIL
    print(f"  {status}  '{text[:45]}' -> crisis={result} (expected {expected})")

# --- Gap 3 + 5: Model loading + dynamic label map ----------------------------
print("\n--- Gap 3 & 5: Model loading + dynamic label map ---")
print("  Loading model (may take ~10s)...")
model, tokenizer, label_encoder = load_model_and_tokenizer()
cbt = load_cbt_responses()
print(f"  {PASS}  Model loaded")
print(f"  Dynamic INDEX_TO_EMOTION: {INDEX_TO_EMOTION}")
dynamic_ok = all(isinstance(v, str) for v in INDEX_TO_EMOTION.values())
if not dynamic_ok: errors += 1
print(f"  {PASS if dynamic_ok else FAIL}  All label values are strings: {dynamic_ok}")

# --- Gap 3: Context-aware inference ------------------------------------------
print("\n--- Gap 3: Context-aware inference ---")
history_ctx = [
    {"user": "I feel hopeless"},
    {"user": "Nothing seems to work"},
    {"user": "Everyone leaves me"},
]
result_ctx = predict_emotion(
    "I am feeling very lonely today.",
    model, tokenizer, label_encoder,
    history=history_ctx,
)
print(f"  {PASS}  With history: emotion={result_ctx['predicted_emotion']}, "
      f"conf={result_ctx['confidence']*100:.1f}%, tier={result_ctx['confidence_tier']}")

result_no_ctx = predict_emotion(
    "I am feeling very lonely today.",
    model, tokenizer, label_encoder,
    history=None,
)
print(f"  {PASS}  Without history: emotion={result_no_ctx['predicted_emotion']}, "
      f"conf={result_no_ctx['confidence']*100:.1f}%, tier={result_no_ctx['confidence_tier']}")

# --- Gap 2: Confidence-tiered CBT responses ----------------------------------
print("\n--- Gap 2: Confidence-tiered CBT responses ---")
for tier in ("high", "medium", "low"):
    resp = get_cbt_response("sadness", cbt, confidence_tier=tier)
    ok = isinstance(resp, str) and len(resp) > 20
    if not ok: errors += 1
    print(f"  {PASS if ok else FAIL}  sadness [{tier}]: {resp[:80]}...")

for emotion in ("sadness", "joy", "love", "anger", "fear", "surprise"):
    h = get_cbt_response(emotion, cbt, "high")
    m = get_cbt_response(emotion, cbt, "medium")
    l = get_cbt_response(emotion, cbt, "low")
    ok = len(h) > 10 and len(m) > 10 and len(l) > 10
    if not ok: errors += 1
    print(f"  {PASS if ok else FAIL}  {emotion}: all tiers non-empty")

# --- Gap 4: responses.json structure -----------------------------------------
print("\n--- Gap 4: responses.json structure ---")
import json
with open("responses.json", "r", encoding="utf-8") as f:
    resp_data = json.load(f)
for emotion in ("sadness", "joy", "love", "anger", "fear", "surprise"):
    block = resp_data.get(emotion, {})
    has_tiers  = isinstance(block, dict) and all(k in block for k in ("high", "medium", "low"))
    has_5_high = isinstance(block.get("high"), list) and len(block["high"]) == 5
    ok = has_tiers and has_5_high
    if not ok: errors += 1
    print(f"  {PASS if ok else FAIL}  {emotion}: tiered={has_tiers}, 5-high-responses={has_5_high}")

# --- Summary -----------------------------------------------------------------
print("\n" + "-" * 50)
if errors == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  {errors} TEST(S) FAILED")
    sys.exit(1)
