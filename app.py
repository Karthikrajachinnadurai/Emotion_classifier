"""
app.py — AI Mental Health Assistant
====================================
Production-ready Streamlit application that uses a fine-tuned DistilBERT
model to detect emotions in user text and provide CBT-based responses.

Author  : Karthik Raja
Model   : DistilBERT (TensorFlow / HuggingFace Transformers)
Accuracy: 93.48%
"""

# ─────────────────────────────────────────────────────────────────────────────
# Standard Library
# ─────────────────────────────────────────────────────────────────────────────
import os
import time
import datetime
from pathlib import Path
from typing import Dict, List

# ── Keras 3 / HuggingFace compatibility fix (must be before any TF import) ───
os.environ["TF_USE_LEGACY_KERAS"]    = "1"
# Suppress TF INFO / WARNING logs
os.environ["TF_CPP_MIN_LOG_LEVEL"]   = "3"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ─────────────────────────────────────────────────────────────────────────────
# Third-party
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────────────────────
# Local
# ─────────────────────────────────────────────────────────────────────────────
from utils import (
    load_model_and_tokenizer,
    load_cbt_responses,
    predict_emotion,
    get_cbt_response,
    get_emotion_display,
    format_confidence,
    export_chat_history,
    detect_crisis,
    preprocess_text,
    CRISIS_RESPONSE,
    EMOTION_META,
    INDEX_TO_EMOTION,
    CONF_HIGH,
    CONF_MEDIUM,
)

# ─────────────────────────────────────────────────────────────────────────────
# Page Config (must be FIRST Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Mental Health Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/karthikraja",
        "Report a bug": "https://github.com/karthikraja",
        "About": "AI Mental Health Assistant — Emotion Detection using DistilBERT (93.48% accuracy)",
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# CSS Injection
# ─────────────────────────────────────────────────────────────────────────────
def inject_css() -> None:
    """Load and inject the custom stylesheet into the Streamlit app."""
    css_path = Path("assets/style.css")
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Custom stylesheet not found at assets/style.css")


inject_css()


# ─────────────────────────────────────────────────────────────────────────────
# Session State Initialisation
# ─────────────────────────────────────────────────────────────────────────────
def init_session() -> None:
    """Initialise all required session-state variables."""
    defaults = {
        "model":            None,
        "tokenizer":        None,
        "label_encoder":    None,
        "cbt_responses":    None,
        "model_loaded":     False,
        "model_error":      None,
        "history":          [],       # List[Dict]
        "last_result":      None,     # Dict from predict_emotion
        "input_text":       "",
        "analyze_clicked":  False,
        "crisis_detected":  False,    # True when crisis keywords found
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session()


# ─────────────────────────────────────────────────────────────────────────────
# Model Loading (cached)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_resources():
    """Cache-once loader for the model, tokenizer, label encoder, and CBT data."""
    model, tokenizer, label_encoder = load_model_and_tokenizer()
    cbt = load_cbt_responses()
    return model, tokenizer, label_encoder, cbt


def ensure_model_loaded() -> bool:
    """
    Load model components into session state (only once per session).
    Returns True on success, False on failure.
    """
    if st.session_state.model_loaded:
        return True

    try:
        with st.spinner("🧠 Loading DistilBERT model… this may take a moment on first run."):
            model, tokenizer, label_encoder, cbt = load_resources()

        st.session_state.model         = model
        st.session_state.tokenizer     = tokenizer
        st.session_state.label_encoder = label_encoder
        st.session_state.cbt_responses = cbt
        st.session_state.model_loaded  = True
        st.session_state.model_error   = None
        return True

    except FileNotFoundError as e:
        st.session_state.model_error  = f"Missing file: {e}"
        st.session_state.model_loaded = False
        return False

    except RuntimeError as e:
        st.session_state.model_error  = f"Model loading failed: {e}"
        st.session_state.model_loaded = False
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Plotly Probability Chart
# ─────────────────────────────────────────────────────────────────────────────
def build_probability_chart(probabilities: Dict[str, float]) -> go.Figure:
    """
    Build a beautiful horizontal Plotly bar chart sorted by probability.

    Args:
        probabilities: Dict mapping emotion label → probability (0–1).

    Returns:
        Plotly Figure object.
    """
    sorted_items = sorted(probabilities.items(), key=lambda x: x[1], reverse=False)

    labels, values, colors, emojis = [], [], [], []
    for emo, prob in sorted_items:
        name, emoji, color = get_emotion_display(emo)
        labels.append(f"{emoji}  {name}")
        values.append(round(prob * 100, 2))
        colors.append(color)
        emojis.append(emoji)

    fig = go.Figure()

    # Background bars (track)
    fig.add_trace(go.Bar(
        y=labels,
        x=[100] * len(labels),
        orientation="h",
        marker=dict(color="rgba(255,255,255,0.04)", line=dict(width=0)),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Foreground bars (actual probability)
    fig.add_trace(go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker=dict(
            color=colors,
            opacity=0.85,
            line=dict(width=0),
        ),
        text=[f"<b>{v:.1f}%</b>" for v in values],
        textposition="outside",
        textfont=dict(color="#F0F2FF", size=12, family="Inter"),
        customdata=values,
        hovertemplate="<b>%{y}</b><br>Probability: %{x:.2f}%<extra></extra>",
        showlegend=False,
    ))

    fig.update_layout(
        barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#F0F2FF", size=13),
        margin=dict(l=10, r=60, t=10, b=10),
        height=300,
        xaxis=dict(
            range=[0, 115],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=13, color="#C0C4E0"),
        ),
        hoverlabel=dict(
            bgcolor="rgba(20,22,40,0.95)",
            bordercolor="rgba(108,99,255,0.4)",
            font=dict(color="#F0F2FF", size=13),
        ),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar() -> None:
    """Render the application sidebar with model info, stats, and links."""
    with st.sidebar:
        if st.session_state.model_loaded:
            status_html = "<div style='margin-top: 1rem; margin-bottom: 0.5rem;'><span class='sidebar-badge'>● Model Ready</span></div>"
        else:
            status_html = "<div style='margin-top: 1rem; margin-bottom: 0.5rem;'><span style='background:rgba(224,90,58,0.15);border:1px solid rgba(224,90,58,0.3);color:#E05A3A;border-radius:50px;padding:3px 12px;font-size:0.72rem;font-weight:700;letter-spacing:.06em;'>● Not Loaded</span></div>"

        st.markdown(f"""
        <div style='text-align:center; padding: 0 0 1.5rem 0;'>
            <div style='font-size:3rem; margin-bottom:0.2rem; line-height:1;'>🧠</div>
            <div style='font-family:"Space Grotesk",sans-serif; font-size:1.1rem;
                        font-weight:700; color:#F0F2FF;'>Mental Health AI</div>
            <div style='font-size:0.75rem; color:#5D6080; margin-top:4px;'>
                DistilBERT · TensorFlow · v1.0
            </div>
            {status_html}
        </div>
        """, unsafe_allow_html=True)

        # ── Emotions Legend ───────────────────────────────────────────────
        st.markdown(
            "<div class='section-label' style='font-size:0.7rem;'>🎭 Emotion Classes</div>",
            unsafe_allow_html=True,
        )
        legend_html = "<div style='display:flex; flex-wrap:wrap; gap:8px; padding:0.5rem 0;'>"
        for emo, (name, emoji, color) in EMOTION_META.items():
            legend_html += (
                f"<span style='background:{color}22; border:1px solid {color}55; "
                f"color:{color}; border-radius:50px; padding:3px 10px; "
                f"font-size:0.75rem; font-weight:600;'>{emoji} {name}</span>"
            )
        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)


        # ── Session Stats ─────────────────────────────────────────────────
        if st.session_state.history:
            st.markdown(
                "<div class='section-label' style='font-size:0.7rem;'>📈 Session Stats</div>",
                unsafe_allow_html=True,
            )
            total = len(st.session_state.history)
            emo_counts: Dict[str, int] = {}
            for h in st.session_state.history:
                emo_counts[h["emotion"]] = emo_counts.get(h["emotion"], 0) + 1
            dominant = max(emo_counts, key=emo_counts.get)
            _, dom_emoji, _ = get_emotion_display(dominant)

            c1, c2 = st.columns(2)
            c1.metric("Analyses", str(total))
            c2.metric("Dominant", f"{dom_emoji} {dominant.capitalize()}")

            st.markdown("<br>", unsafe_allow_html=True)

            # Download button
            chat_text = export_chat_history(st.session_state.history)
            st.download_button(
                label="⬇ Download History",
                data=chat_text,
                file_name=f"mental_health_chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
# Hero Header
# ─────────────────────────────────────────────────────────────────────────────
def render_hero() -> None:
    """Render the main title section at the top of the main content area."""
    st.markdown("""
    <div class="glass-card" style="padding: 1.5rem; margin-bottom: 24px; margin-top: 0; display: flex; align-items: center; gap: 16px;">
        <div style="font-size: 48px; line-height: 1;">🧠</div>
        <div style="display: flex; flex-direction: column; justify-content: center;">
            <h1 style="margin: 0; padding: 0; font-size: 42px; font-weight: 800;
                       font-family: 'Space Grotesk', sans-serif;
                       background: linear-gradient(90deg, #9B59B6, #5B8DEF);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       line-height: 1.1;">
                AI Mental Health Assistant
            </h1>
            <div style="color: #9FA3C0; font-size: 1.1rem; margin-top: 6px; font-weight: 500;">
                Your companion for emotional support and well-being.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Input Section
# ─────────────────────────────────────────────────────────────────────────────
def render_input_section() -> None:
    """
    Render the text input area and action buttons.
    Sets st.session_state.analyze_clicked = True when Analyze is clicked.
    """
    st.markdown(
        "<div class='section-label'>✏️ &nbsp; How are you feeling today?</div>",
        unsafe_allow_html=True,
    )

    user_input = st.text_area(
        label="",
        value=st.session_state.input_text,
        height=140,
        max_chars=1000,
        placeholder=(
            'Try: "I am feeling very lonely today." or '
            '"I\'m so happy about the news!" …'
        ),
        key="user_text_area",
        label_visibility="collapsed",
    )

    char_count = len(user_input)
    st.markdown(
        f"<div style='text-align:right; font-size:0.73rem; color:#5D6080; "
        f"margin-top:-0.5rem; margin-bottom:0.8rem;'>{char_count} / 1000</div>",
        unsafe_allow_html=True,
    )

    col_analyze, col_clear, col_spacer = st.columns([2, 1.2, 4])

    with col_analyze:
        analyze = st.button(
            "🔍  Analyze Emotion",
            key="btn_analyze",
            use_container_width=True,
        )

    with col_clear:
        clear = st.button(
            "✕  Clear",
            key="btn_clear",
            use_container_width=True,
        )

    if clear:
        st.session_state.input_text     = ""
        st.session_state.last_result    = None
        st.session_state.analyze_clicked = False
        st.rerun()

    if analyze:
        if not user_input.strip():
            st.warning("⚠️  Please enter some text before analyzing.")
        elif len(user_input.strip()) < 3:
            st.warning("⚠️  Your message is too short. Please write at least a few words.")
        else:
            st.session_state.input_text      = user_input
            st.session_state.analyze_clicked = True


# ─────────────────────────────────────────────────────────────────────────────
# Run Inference + Render Results
# ─────────────────────────────────────────────────────────────────────────────
def run_analysis() -> None:
    """
    Run the DistilBERT inference (with history context) and render results.
    Also performs crisis detection before model inference.
    Called only when st.session_state.analyze_clicked is True.
    """
    raw_text = st.session_state.input_text

    # ── 0. Preprocessing (expand contractions, spell check, clean) ────────
    text = preprocess_text(raw_text)

    # ── 1. Crisis detection (pre-inference, highest priority) ─────────────
    is_crisis = detect_crisis(text)
    st.session_state.crisis_detected = is_crisis

    if is_crisis:
        # Log to history and surface the crisis response — skip model inference
        st.session_state.last_result = {
            "predicted_emotion": "crisis",
            "confidence":        1.0,
            "confidence_tier":   "high",
            "probabilities":     {},
            "inference_time_ms": 0.0,
            "cbt_response":      CRISIS_RESPONSE,
            "is_crisis":         True,
        }
        st.session_state.history.append({
            "user":             text,
            "emotion":          "⚠️ Crisis",
            "confidence":       "N/A",
            "confidence_tier":  "N/A",
            "response":         CRISIS_RESPONSE,
            "crisis":           True,
            "timestamp":        datetime.datetime.now().strftime("%H:%M:%S"),
        })
        st.session_state.analyze_clicked = False
        st.rerun()
        return

    # ── 2. Run model inference with last-3 history context ────────────────
    with st.spinner("⚡ Analysing your emotions…"):
        try:
            result = predict_emotion(
                text,
                st.session_state.model,
                st.session_state.tokenizer,
                st.session_state.label_encoder,
                history=st.session_state.history,   # pass last 3 turns
            )
        except ValueError as ve:
            st.error(f"❌ Input error: {ve}")
            st.session_state.analyze_clicked = False
            return
        except Exception as exc:
            st.error(f"❌ Inference failed: {exc}")
            st.session_state.analyze_clicked = False
            return

    # ── 3. Confidence-tiered CBT response ─────────────────────────────────
    tier     = result.get("confidence_tier", "high")
    cbt_text = get_cbt_response(
        result["predicted_emotion"],
        st.session_state.cbt_responses,
        confidence_tier=tier,
    )
    result["cbt_response"] = cbt_text
    result["is_crisis"]    = False

    # Store in session
    st.session_state.last_result     = result
    st.session_state.analyze_clicked = False

    # Append to history
    st.session_state.history.append({
        "user":             text,
        "emotion":          result["predicted_emotion"],
        "confidence":       format_confidence(result["confidence"]),
        "confidence_tier":  tier,
        "response":         cbt_text,
        "crisis":           False,
        "timestamp":        datetime.datetime.now().strftime("%H:%M:%S"),
    })

    st.rerun()


def _render_crisis_banner() -> None:
    """Display the crisis support banner — shown instead of normal results."""
    st.markdown("""
    <div style='background:rgba(232,64,90,0.1); border:2px solid rgba(232,64,90,0.5);
                border-radius:16px; padding:2rem; margin-top:1.5rem;
                animation: fadeSlideUp 0.5s ease forwards;'>
        <div style='font-size:2rem; margin-bottom:0.5rem;'>🆘</div>
        <div style='font-family:"Space Grotesk",sans-serif; font-weight:800;
                    color:#E8405A; font-size:1.25rem; margin-bottom:1rem;'>
            You Are Not Alone — Crisis Support Available
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(CRISIS_RESPONSE)
    st.markdown("""
    <div style='background:rgba(232,64,90,0.07); border-left:3px solid #E8405A;
                border-radius:0 12px 12px 0; padding:1rem 1.5rem; margin-top:1rem;
                font-size:0.88rem; color:#C0C4E0; line-height:1.7;'>
        <strong style='color:#F0F2FF;'>⚠️ Important:</strong>
        This AI tool is <strong>not</strong> a crisis counsellor.
        Please reach out to a licensed mental health professional or crisis service immediately.
        Your life has value, and trained help is available right now.
    </div>
    """, unsafe_allow_html=True)


def render_results() -> None:
    """Render the crisis banner OR emotion result card, probability chart, and CBT response."""
    result = st.session_state.last_result
    if result is None:
        return

    # ── Crisis path ────────────────────────────────────────────────────────
    if result.get("is_crisis"):
        _render_crisis_banner()
        return

    emotion    = result["predicted_emotion"]
    name, emoji, color = get_emotion_display(emotion)
    confidence = result["confidence"]
    tier       = result.get("confidence_tier", "high")
    probs      = result["probabilities"]
    inf_ms     = result["inference_time_ms"]
    cbt_text   = result.get("cbt_response", "")

    # Tier label & colour for UI badge
    tier_meta = {
        "high":   ("High Confidence",   "#3DD68C", "rgba(61,214,140,0.15)",  "rgba(61,214,140,0.3)"),
        "medium": ("Medium Confidence", "#F5C518", "rgba(245,197,24,0.15)",  "rgba(245,197,24,0.3)"),
        "low":    ("Low Confidence",    "#9FA3C0", "rgba(159,163,192,0.12)", "rgba(159,163,192,0.25)"),
    }
    tier_label, tier_color, tier_bg, tier_border = tier_meta.get(
        tier, tier_meta["high"]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Emotion Result Card ────────────────────────────────────────────────
    st.markdown(f"""
    <div class='emotion-result-card'>
        <span class='emotion-emoji'>{emoji}</span>
        <div class='emotion-label' style='color:{color};'>{name}</div>
        <span class='confidence-badge'>✔ {confidence * 100:.2f}% Confidence</span>
        <span style='display:inline-flex; align-items:center; gap:6px;
                     background:{tier_bg}; border:1px solid {tier_border};
                     border-radius:50px; padding:4px 14px; font-size:0.82rem;
                     font-weight:600; color:{tier_color}; margin-top:0.4rem;
                     margin-left:0.5rem;'>
            {tier_label}
        </span>
        <span class='inference-badge'>⚡ {inf_ms:.0f} ms</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Two-column layout: chart | CBT ────────────────────────────────────
    col_chart, col_cbt = st.columns([1.2, 1], gap="large")

    with col_chart:
        st.markdown(
            "<div class='section-label'>📊 &nbsp; Emotion Probabilities</div>",
            unsafe_allow_html=True,
        )
        fig = build_probability_chart(probs)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_cbt:
        st.markdown(
            "<div class='section-label'>💬 &nbsp; Supportive Response</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"""
        <div class='cbt-box'>
            <div class='cbt-box-title'>🧠 CBT-Based Insight</div>
            {cbt_text}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # All-probabilities mini table
        st.markdown(
            "<div class='section-label' style='font-size:0.68rem;'>All Probabilities</div>",
            unsafe_allow_html=True,
        )
        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        for emo, prob in sorted_probs:
            n, em, col_hex = get_emotion_display(emo)
            bar_w = int(prob * 100)
            st.markdown(f"""
            <div style='display:flex; align-items:center; gap:10px; margin-bottom:6px;'>
                <span style='width:22px; text-align:center; font-size:1rem;'>{em}</span>
                <span style='width:60px; font-size:0.8rem; color:#9FA3C0;'>{n}</span>
                <div style='flex:1; background:rgba(255,255,255,0.05);
                            border-radius:4px; height:6px; overflow:hidden;'>
                    <div style='width:{bar_w}%; height:100%;
                                background:{col_hex}; border-radius:4px;
                                transition: width 0.6s ease;'></div>
                </div>
                <span style='width:44px; font-size:0.8rem; color:#F0F2FF;
                             text-align:right;'>{prob*100:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Conversation History
# ─────────────────────────────────────────────────────────────────────────────
def render_history() -> None:
    """Render the scrollable conversation history section."""
    history = st.session_state.history
    if not history:
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-label'>🕓 &nbsp; Conversation History</div>",
        unsafe_allow_html=True,
    )

    col_title, col_btn = st.columns([5, 1])
    with col_btn:
        if st.button("🗑 Clear All", key="btn_clear_history", use_container_width=True):
            st.session_state.history     = []
            st.session_state.last_result = None
            st.rerun()

    # Show most recent first
    for i, entry in enumerate(reversed(history)):
        n, emoji_h, color_h = get_emotion_display(entry["emotion"])
        turn = len(history) - i
        st.markdown(f"""
        <div class='history-card'>
            <div class='history-user-msg'>💬 &nbsp; {entry['user']}</div>
            <div class='history-meta'>
                <span class='history-emotion-chip'
                      style='background:{color_h}22; border:1px solid {color_h}55;
                             color:{color_h};'>
                    {emoji_h} {n}
                </span>
                <span style='color:#5D6080;'>{entry['confidence']}</span>
                &nbsp;·&nbsp;
                <span style='color:#5D6080;'>Turn {turn}</span>
                &nbsp;·&nbsp;
                <span style='color:#5D6080;'>{entry.get('timestamp','')}</span>
            </div>
            <div style='font-size:0.85rem; color:#9FA3C0; margin-top:0.6rem;
                        padding-top:0.6rem; border-top:1px solid rgba(255,255,255,0.06);'>
                🧠 {entry['response']}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Welcome / Empty State
# ─────────────────────────────────────────────────────────────────────────────
def render_empty_state() -> None:
    """Render a helpful empty-state message when no analysis has been done yet."""
    if st.session_state.last_result is not None or st.session_state.history:
        return

    st.markdown("""
    <div class='glass-card' style='text-align:center; padding:1.5rem 1.5rem; margin-top:0.2rem; margin-bottom:1rem;'>
        <div style='font-size:2.5rem; margin-bottom:0.4rem;'>💭</div>
        <div style='font-family:"Space Grotesk",sans-serif; font-size:1.25rem;
                    font-weight:700; color:#F0F2FF; margin-bottom:0.3rem;'>
            Ready to listen
        </div>
        <div style='color:#5D6080; font-size:0.92rem; max-width:400px; margin:0 auto;
                    line-height:1.5;'>
            Type how you're feeling below and click <strong style='color:#9FA3C0;'>Analyse Emotion</strong>.<br>
            Our DistilBERT model will detect your emotion and offer a personalised,
            evidence-based response.
        </div>
        <div style='display:flex; justify-content:center; gap:12px; flex-wrap:wrap; margin-top:1rem;'>
            <span style='background:rgba(91,141,239,0.12); border:1px solid rgba(91,141,239,0.25);
                         color:#5B8DEF; border-radius:50px; padding:5px 14px; font-size:0.82rem;'>
                😢 Sadness
            </span>
            <span style='background:rgba(245,197,24,0.12); border:1px solid rgba(245,197,24,0.25);
                         color:#F5C518; border-radius:50px; padding:5px 14px; font-size:0.82rem;'>
                😊 Joy
            </span>
            <span style='background:rgba(232,64,90,0.12); border:1px solid rgba(232,64,90,0.25);
                         color:#E8405A; border-radius:50px; padding:5px 14px; font-size:0.82rem;'>
                ❤️ Love
            </span>
            <span style='background:rgba(224,90,58,0.12); border:1px solid rgba(224,90,58,0.25);
                         color:#E05A3A; border-radius:50px; padding:5px 14px; font-size:0.82rem;'>
                😡 Anger
            </span>
            <span style='background:rgba(155,89,182,0.12); border:1px solid rgba(155,89,182,0.25);
                         color:#9B59B6; border-radius:50px; padding:5px 14px; font-size:0.82rem;'>
                😨 Fear
            </span>
            <span style='background:rgba(26,188,156,0.12); border:1px solid rgba(26,188,156,0.25);
                         color:#1ABC9C; border-radius:50px; padding:5px 14px; font-size:0.82rem;'>
                😲 Surprise
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Error Banner
# ─────────────────────────────────────────────────────────────────────────────
def render_model_error() -> None:
    """Display a rich error card when model loading fails."""
    err = st.session_state.model_error
    st.markdown(f"""
    <div class='glass-card' style='border-color:rgba(224,90,58,0.35);
                                    background:rgba(224,90,58,0.07); margin-top:1rem;'>
        <div style='font-size:1.5rem; margin-bottom:0.8rem;'>❌</div>
        <div style='font-family:"Space Grotesk",sans-serif; font-weight:700;
                    color:#E05A3A; margin-bottom:0.5rem; font-size:1.05rem;'>
            Model Loading Failed
        </div>
        <div style='color:#9FA3C0; font-size:0.9rem; line-height:1.7;'>
            {err}<br><br>
            <strong style='color:#F0F2FF;'>Checklist:</strong><br>
            • Ensure the <code>finalmodels/</code> folder is present in the project root<br>
            • It must contain: <code>config.json</code>, <code>tf_model.h5</code>,
              <code>tokenizer.json</code>, <code>tokenizer_config.json</code>,
              <code>special_tokens_map.json</code>, <code>vocab.txt</code>,
              <code>label_encoder (2).pkl</code><br>
            • Verify all Python dependencies are installed: <code>pip install -r requirements.txt</code>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main App Entry Point
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    """
    Main application controller.
    Orchestrates sidebar, model loading, input, inference, and result rendering.
    """
    # 1. Sidebar
    render_sidebar()

    # 2. Main Title Section
    render_hero()

    # 3. Model loading — attempt once per session
    model_ok = ensure_model_loaded()

    if not model_ok:
        render_model_error()
        return

    # 4. Empty state (now acting as the main introduction before input)
    render_empty_state()

    # 5. Input section
    render_input_section()

    # 6. Run inference if triggered
    if st.session_state.analyze_clicked:
        run_analysis()   # this calls st.rerun() at the end

    # 7. Results
    render_results()

    # 8. History
    render_history()

    # 9. Footer
    # ── Strengthened disclaimer ────────────────────────────────────────────
    st.markdown("""
    <div style='background:rgba(232,64,90,0.06); border:1px solid rgba(232,64,90,0.2);
                border-radius:14px; padding:1.2rem 1.8rem; margin-top:2.5rem;
                margin-bottom:2.5rem;'>
        <div style='font-size:0.8rem; font-weight:700; color:#E8405A;
                    letter-spacing:0.06em; text-transform:uppercase;
                    margin-bottom:0.4rem;'>⚠️ Important Disclaimer</div>
        <div style='font-size:0.84rem; color:#9FA3C0; line-height:1.8;'>
            <strong style='color:#F0F2FF;'>This tool is NOT a substitute for professional
            mental health care.</strong> It is an educational AI demonstration only.
            Emotion detection is performed by a machine learning model and may be
            inaccurate. Responses are pre-written and are not personalised clinical advice.<br><br>
            If you are experiencing a mental health crisis, suicidal thoughts, or
            self-harm urges, <strong style='color:#F0F2FF;'>please contact a licensed
            mental health professional or crisis helpline immediately.</strong>
            <br>🇮🇳 India — iCall: <strong>9152987821</strong> &nbsp;|&nbsp;
            Vandrevala Foundation: <strong>1860-2662-345</strong> (24×7)
        </div>
    </div>
    
<div class='main-footer'>
<div class='footer-made-with'>Made with ❤️ by</div>
<div class='footer-name'>Karthik Raja</div>
<div class='footer-role'>AI / ML Engineer</div>
<div class='footer-links'>
<a href='https://github.com/karthikraja' target='_blank' class='footer-link-btn'>
⬡ GitHub
</a>
<a href='https://linkedin.com/in/karthikraja' target='_blank' class='footer-link-btn'>
in LinkedIn
</a>
</div>
<div class='footer-copyright'>© 2026 AI Mental Health Assistant</div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
