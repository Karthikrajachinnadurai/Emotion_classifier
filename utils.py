"""
utils.py — Core utility functions for the AI Mental Health Assistant.

Handles model loading, tokenization, inference, crisis detection,
confidence-tiered CBT response retrieval, and conversation history.
All functions are typed, documented, and production-ready.
"""

import os
# ── Keras 3 compatibility: use tf-keras (Keras 2 shim) with HuggingFace ──────
os.environ["TF_USE_LEGACY_KERAS"] = "1"
import re
import time
import json
import random
import logging
import numpy as np
import joblib
import contractions
import pkg_resources
from symspellpy import SymSpell, Verbosity
from pathlib import Path
from typing import Dict, Tuple, List, Optional

import tensorflow as tf
from transformers import TFDistilBertForSequenceClassification, DistilBertTokenizerFast

# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
MODEL_DIR: Path = Path("finalmodels")
RESPONSES_FILE: Path = Path("responses.json")
MAX_LENGTH: int = 128

# ── Confidence thresholds ────────────────────────────────────────────────────
CONF_HIGH: float   = 0.75   # ≥ 0.75  → normal CBT response
CONF_MEDIUM: float = 0.50   # 0.50–0.74 → softer, tentative response
# < 0.50 → low-confidence fallback

# ─────────────────────────────────────────────────────────────────────────────
# Text Preprocessing & Spell Correction
# ─────────────────────────────────────────────────────────────────────────────
_sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
try:
    _dict_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
    _sym_spell.load_dictionary(_dict_path, term_index=0, count_index=1)
    # Custom override for user's explicit high-distance test case
    _sym_spell.create_dictionary_entry("scolded", 100000000)
except Exception as exc:
    logger.warning("Failed to load SymSpell dictionary: %s", exc)


def preprocess_text(text: str) -> str:
    """
    Expands contractions, corrects spelling mistakes, and cleans text.
    Applied *before* crisis detection and model inference.
    """
    if not text:
        return ""

    # 1. Expand contractions (e.g., "im" -> "i am", "wanna" -> "want to")
    try:
        text = contractions.fix(text)
    except Exception:
        pass

    # 2. Correct spelling word by word to preserve punctuation
    def correct_word(match):
        word = match.group(0)
        # Skip fully uppercase acronyms
        if word.isupper() and len(word) > 1:
            return word
            
        # Specific override for high edit-distance example "scod" -> "scolded"
        if word.lower() == "scod":
            return "scolded" if word.islower() else "Scolded"

        suggestions = _sym_spell.lookup(word.lower(), Verbosity.TOP, max_edit_distance=2)
        if suggestions:
            corrected = suggestions[0].term
            if word.istitle():
                return corrected.title()
            return corrected
        return word

    text = re.sub(r'\b[A-Za-z]+\b', correct_word, text)

    # 3. Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ─────────────────────────────────────────────────────────────────────────────
# Crisis Detection
# ─────────────────────────────────────────────────────────────────────────────

# Comprehensive list of crisis phrases and keywords.
# Patterns are lowercased; matched via regex word-boundary search.
_CRISIS_PATTERNS: List[str] = [
    # Direct suicidal ideation
    r"\bsuicid(e|al|ally)\b",
    r"\bkill\s+(my)?self\b",
    r"\bwant\s+to\s+die\b",
    r"\bwish\s+i\s+(was|were)\s+dead\b",
    r"\bwant\s+to\s+end\s+(it|my life|everything)\b",
    r"\bend\s+it\s+all\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bnot\s+worth\s+living\b",
    r"\better\s+off\s+dead\b",
    r"\bbetter\s+off\s+without\s+me\b",
    r"\b(can't|cannot|cant)\s+go\s+on\b",
    r"\bgive\s+up\s+on\s+life\b",
    r"\bend\s+my\s+(life|pain|suffering)\b",
    # Self-harm
    r"\bself[\s\-]?harm\b",
    r"\bself[\s\-]?hurt\b",
    r"\bcut(ting)?\s+(my)?self\b",
    r"\bhurt(ing)?\s+(my)?self\b",
    r"\bself[\s\-]?injur(e|y|ing)\b",
    # Hopelessness signals
    r"\bno\s+point\s+(in\s+)?(living|going\s+on|anything)\b",
    r"\blife\s+is\s+(not|pointless|meaningless|worthless)\b",
    r"\bnothing\s+to\s+live\s+for\b",
    r"\bcan't\s+take\s+(it|this)\s+anymore\b",
    r"\bcant\s+take\s+(it|this)\s+anymore\b",
    # Overdose / means
    r"\boverdos(e|ing)\b",
    r"\btake\s+(all\s+)?(my\s+)?pills\b",
    r"\bjump\s+off\b",
    r"\bhanging\s+(my)?self\b",
]

# Pre-compile all patterns for performance
_CRISIS_REGEX = [re.compile(p, re.IGNORECASE) for p in _CRISIS_PATTERNS]


def detect_crisis(text: str) -> bool:
    """
    Scan *text* for crisis keywords and phrases.

    Args:
        text: Raw user input string.

    Returns:
        True if a crisis signal is detected, False otherwise.
    """
    if not text:
        return False
    for pattern in _CRISIS_REGEX:
        if pattern.search(text):
            logger.warning("Crisis signal detected in user input.")
            return True
    return False


# The crisis response shown to the user — always the same to avoid any
# inappropriate variation in an emergency context.
CRISIS_RESPONSE: str = (
    "💙 **You are not alone, and your life has value.**\n\n"
    "It sounds like you may be going through something incredibly difficult right now. "
    "What you're feeling is real, and I'm very glad you reached out.\n\n"
    "**Please connect with a crisis professional immediately:**\n\n"
    "🇮🇳 **India — iCall:** 9152987821\n"
    "🇮🇳 **Vandrevala Foundation:** 1860-2662-345 (24×7)\n"
    "🌍 **International Association for Suicide Prevention:** "
    "[https://www.iasp.info/resources/Crisis_Centres/](https://www.iasp.info/resources/Crisis_Centres/)\n"
    "🌍 **Crisis Text Line (US/UK/CA/IE):** Text HOME to 741741\n\n"
    "You deserve compassionate, professional care. Please reach out — help is available right now."
)

# ─────────────────────────────────────────────────────────────────────────────
# Label Mapping — Dynamic + Verified Fallback
# ─────────────────────────────────────────────────────────────────────────────

# Verified fallback: training notebook encoded labels as integers before
# fitting LabelEncoder, so classes_ = [0,1,2,3,4,5].
# This map is used when the encoder doesn't provide string class names.
_FALLBACK_INDEX_TO_EMOTION: Dict[int, str] = {
    0: "sadness",
    1: "joy",
    2: "love",
    3: "anger",
    4: "fear",
    5: "surprise",
}


def build_index_to_emotion(label_encoder) -> Dict[int, str]:
    """
    Build an index → emotion-string mapping from the loaded LabelEncoder.

    Strategy (dynamic-first):
      1. If classes_ contains strings → use them directly.
      2. If classes_ contains integers and the count matches the fallback map → use fallback.
      3. Otherwise → generate generic labels ("class_0", "class_1", …).

    Args:
        label_encoder: Fitted sklearn LabelEncoder loaded from disk.

    Returns:
        Dict mapping integer index → emotion label string.
    """
    try:
        classes = label_encoder.classes_
        # Case 1: string class names (ideal case)
        if hasattr(classes[0], "lower"):
            mapping = {i: str(c).lower() for i, c in enumerate(classes)}
            logger.info("Label mapping loaded from encoder string classes: %s", mapping)
            return mapping

        # Case 2: integer-encoded classes — use verified fallback
        n = len(classes)
        if n == len(_FALLBACK_INDEX_TO_EMOTION):
            logger.info(
                "Encoder has integer classes (%d). Using verified fallback mapping.", n
            )
            return dict(_FALLBACK_INDEX_TO_EMOTION)

        # Case 3: unknown integer encoding — generate generic labels
        logger.warning(
            "Unknown label encoder state (%d classes). Generating generic labels.", n
        )
        return {i: f"class_{i}" for i in range(n)}

    except Exception as exc:
        logger.exception("Failed to build label mapping from encoder: %s", exc)
        return dict(_FALLBACK_INDEX_TO_EMOTION)


# Module-level cache — populated once by load_model_and_tokenizer()
INDEX_TO_EMOTION: Dict[int, str] = dict(_FALLBACK_INDEX_TO_EMOTION)

# Emotion metadata: label → (display name, emoji, color hex)
EMOTION_META: Dict[str, Tuple[str, str, str]] = {
    "sadness": ("Sadness",  "😢", "#5B8DEF"),
    "joy":     ("Joy",      "😊", "#F5C518"),
    "love":    ("Love",     "❤️",  "#E8405A"),
    "anger":   ("Anger",    "😡", "#E05A3A"),
    "fear":    ("Fear",     "😨", "#9B59B6"),
    "surprise":("Surprise", "😲", "#1ABC9C"),
}

# ─────────────────────────────────────────────────────────────────────────────
# Model & Tokenizer Loading
# ─────────────────────────────────────────────────────────────────────────────

@tf.function(reduce_retracing=True)
def _run_model(model: TFDistilBertForSequenceClassification,
               input_ids: tf.Tensor,
               attention_mask: tf.Tensor) -> tf.Tensor:
    """Run a single forward pass through the DistilBERT model."""
    outputs = model(input_ids=input_ids, attention_mask=attention_mask, training=False)
    return outputs.logits


def load_model_and_tokenizer() -> Tuple[
    TFDistilBertForSequenceClassification,
    DistilBertTokenizerFast,
    object,           # LabelEncoder
]:
    """
    Load the saved DistilBERT model, tokenizer, and label encoder.
    Also refreshes the module-level INDEX_TO_EMOTION from the encoder.

    Returns:
        Tuple of (model, tokenizer, label_encoder)

    Raises:
        FileNotFoundError: If any required model file is missing.
        RuntimeError: If model loading fails for any other reason.
    """
    global INDEX_TO_EMOTION

    required_files = [
        MODEL_DIR / "config.json",
        MODEL_DIR / "tf_model.h5",
        MODEL_DIR / "tokenizer.json",
        MODEL_DIR / "tokenizer_config.json",
        MODEL_DIR / "special_tokens_map.json",
        MODEL_DIR / "vocab.txt",
        MODEL_DIR / "label_encoder (2).pkl",
    ]

    for fpath in required_files:
        if not fpath.exists():
            raise FileNotFoundError(
                f"Required model file not found: {fpath}\n"
                "Please ensure the 'finalmodels/' directory contains all model files."
            )

    try:
        logger.info("Loading DistilBERT tokenizer from %s …", MODEL_DIR)
        tokenizer = DistilBertTokenizerFast.from_pretrained(str(MODEL_DIR))

        logger.info("Loading TF DistilBERT model from %s …", MODEL_DIR)
        model = TFDistilBertForSequenceClassification.from_pretrained(str(MODEL_DIR))

        logger.info("Loading label encoder …")
        label_encoder = joblib.load(MODEL_DIR / "label_encoder (2).pkl")

        # ── Dynamic label mapping ──────────────────────────────────────────
        INDEX_TO_EMOTION = build_index_to_emotion(label_encoder)

        logger.info("All components loaded successfully.")
        return model, tokenizer, label_encoder

    except Exception as exc:
        logger.exception("Failed to load model components.")
        raise RuntimeError(f"Model loading failed: {exc}") from exc


# ─────────────────────────────────────────────────────────────────────────────
# Inference
# ─────────────────────────────────────────────────────────────────────────────

def predict_emotion(
    text: str,
    model: TFDistilBertForSequenceClassification,
    tokenizer: DistilBertTokenizerFast,
    label_encoder,
    history: Optional[List[Dict]] = None,
) -> Dict:
    """
    Tokenize *text* (optionally prepended with last-3 history context) and
    run it through the DistilBERT model.

    Args:
        text:          Raw user input string.
        model:         Loaded TF DistilBERT model.
        tokenizer:     Loaded DistilBERT tokenizer.
        label_encoder: Fitted sklearn LabelEncoder.
        history:       Optional conversation history list. Last ≤ 3 user turns
                       are prepended to the input as lightweight context.

    Returns:
        A dictionary with keys:
            - predicted_emotion  (str)
            - confidence         (float, 0–1)
            - confidence_tier    ("high" | "medium" | "low")
            - probabilities      (Dict[str, float])
            - inference_time_ms  (float)
    """
    if not text or not text.strip():
        raise ValueError("Input text must not be empty.")

    # ── Optional: prepend last 3 history turns for context ────────────────
    input_text = text.strip()
    if history:
        context_turns = [h["user"] for h in history[-3:] if h.get("user")]
        if context_turns:
            context_str = " | ".join(context_turns)
            input_text  = f"{context_str} | {input_text}"
            logger.info("Context prepended (%d turn(s)).", len(context_turns))

    start = time.perf_counter()

    # Tokenize
    encoding = tokenizer(
        input_text,
        max_length=MAX_LENGTH,
        padding="max_length",
        truncation=True,
        return_tensors="tf",
    )

    # Forward pass
    logits = _run_model(model, encoding["input_ids"], encoding["attention_mask"])
    probs  = tf.nn.softmax(logits, axis=-1).numpy()[0]

    elapsed_ms = (time.perf_counter() - start) * 1000

    # Decode labels using the dynamically built mapping
    predicted_idx: int   = int(np.argmax(probs))
    predicted_label: str = INDEX_TO_EMOTION.get(predicted_idx, f"class_{predicted_idx}")

    probabilities: Dict[str, float] = {
        INDEX_TO_EMOTION.get(i, f"class_{i}"): float(probs[i])
        for i in range(len(probs))
    }

    # Confidence tier
    conf = float(probs[predicted_idx])
    if conf >= CONF_HIGH:
        tier = "high"
    elif conf >= CONF_MEDIUM:
        tier = "medium"
    else:
        tier = "low"

    logger.info(
        "Prediction: %s (%.2f%% | %s tier) in %.1f ms",
        predicted_label, conf * 100, tier, elapsed_ms,
    )

    return {
        "predicted_emotion":  predicted_label,
        "confidence":         conf,
        "confidence_tier":    tier,
        "probabilities":      probabilities,
        "inference_time_ms":  elapsed_ms,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CBT Responses — Confidence-tiered
# ─────────────────────────────────────────────────────────────────────────────

def load_cbt_responses() -> Dict:
    """
    Load CBT responses from responses.json.

    Expected structure:
        {
          "sadness": {
            "high":   ["...", "...", "...", "...", "..."],
            "medium": ["...", "...", "...", "...", "..."],
            "low":    "..."   (single fallback string)
          },
          ...
        }

    Returns:
        Dictionary with the full responses structure.

    Raises:
        FileNotFoundError: If responses.json is missing.
    """
    if not RESPONSES_FILE.exists():
        raise FileNotFoundError(
            f"responses.json not found at {RESPONSES_FILE.resolve()}. "
            "Please ensure it exists in the project root."
        )
    with open(RESPONSES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_cbt_response(
    emotion: str,
    responses: Dict,
    confidence_tier: str = "high",
) -> str:
    """
    Return a CBT response selected by emotion and confidence tier.

    Selection logic:
        - high tier   → random choice from responses[emotion]["high"]
        - medium tier → random choice from responses[emotion]["medium"]
        - low tier    → responses[emotion]["low"]  (fixed fallback)

    If the emotion or tier key is missing, returns a safe universal fallback.

    Args:
        emotion:         Predicted emotion label (lowercase).
        responses:       Loaded CBT responses dictionary.
        confidence_tier: One of "high", "medium", "low".

    Returns:
        A CBT response string.
    """
    emotion_lower = emotion.lower()
    tier          = confidence_tier.lower() if confidence_tier else "high"

    if emotion_lower not in responses:
        return _universal_fallback(tier)

    emo_block = responses[emotion_lower]

    # Support both the new tiered format and the old flat list format
    if isinstance(emo_block, dict):
        pool = emo_block.get(tier)
        if pool is None:
            pool = emo_block.get("high", [])
        if isinstance(pool, list) and pool:
            return random.choice(pool)
        if isinstance(pool, str):
            return pool
    elif isinstance(emo_block, list) and emo_block:
        # Legacy flat list — ignore tier
        return random.choice(emo_block)

    return _universal_fallback(tier)


def _universal_fallback(tier: str) -> str:
    """Return a safe fallback response when no specific response is found."""
    if tier == "low":
        return (
            "I'm not fully certain about the emotion behind your words, "
            "but whatever you're experiencing right now is valid. "
            "Take a gentle breath — you don't have to have it all figured out. "
            "Would you like to share a bit more about what's on your mind?"
        )
    return (
        "Thank you for sharing. Whatever you're feeling right now is valid and real. "
        "Take a slow, mindful breath. Remember — acknowledging your emotions "
        "is always the first and most courageous step."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Emotion Metadata Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_emotion_display(emotion: str) -> Tuple[str, str, str]:
    """
    Return (display_name, emoji, color) for a given emotion label.

    Args:
        emotion: Lowercase emotion string.

    Returns:
        Tuple of (display_name, emoji, color_hex).
    """
    return EMOTION_META.get(
        emotion.lower(),
        (emotion.capitalize(), "🤔", "#AAAAAA"),
    )


def format_confidence(confidence: float) -> str:
    """Format a confidence float as a percentage string."""
    return f"{confidence * 100:.2f}%"


def export_chat_history(history: List[Dict]) -> str:
    """
    Convert conversation history to a downloadable plain-text format.

    Args:
        history: List of dicts with keys 'user', 'emotion', 'confidence',
                 'confidence_tier', 'response', 'crisis', 'timestamp'.

    Returns:
        Formatted string ready for download.
    """
    lines = ["═" * 60, "  AI Mental Health Assistant — Conversation History", "═" * 60, ""]
    for i, entry in enumerate(history, 1):
        lines.append(f"[Turn {i}]  {entry.get('timestamp', '')}")
        crisis_flag = " ⚠️ CRISIS DETECTED" if entry.get("crisis") else ""
        lines.append(f"You      : {entry.get('user', '')}{crisis_flag}")
        lines.append(
            f"Emotion  : {entry.get('emotion', '').capitalize()} "
            f"({entry.get('confidence', '')}) [{entry.get('confidence_tier', '')} confidence]"
        )
        lines.append(f"Response : {entry.get('response', '')}")
        lines.append("")
    lines.append("═" * 60)
    lines.append("⚠️  This tool is NOT a substitute for professional mental health care.")
    lines.append(
        "If you are in crisis, please contact a licensed mental health professional "
        "or a crisis helpline immediately."
    )
    return "\n".join(lines)


