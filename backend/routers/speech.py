"""
speech.py — Speech-to-Text Router
===================================
Provides the POST /speech-to-text endpoint.

Accepts an audio file upload, transcribes it using OpenAI Whisper,
and returns only the recognized text as JSON.

Does NOT:
  - Call the emotion prediction model (DistilBERT)
  - Preprocess text
  - Save anything to the database
  - Modify authentication or any other module

Future use:
  The returned transcript can be passed to POST /predict by the frontend
  when the user chooses to submit it.
"""

import io
import logging
import tempfile
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from .. import dependencies, models

logger = logging.getLogger(__name__)

# ── Windows PATH fix ──────────────────────────────────────────────────────────
# On Windows, winget/installers update PATH in the registry but running
# processes (like uvicorn) don't see the change until restarted in a fresh
# shell.  We read the system PATH from the registry at import time so that
# tools like ffmpeg (required by Whisper) are always resolvable via subprocess.
if sys.platform == "win32":
    try:
        import winreg
        _path_parts: list[str] = []
        for _hive, _subkey in [
            (winreg.HKEY_LOCAL_MACHINE,
             r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            (winreg.HKEY_CURRENT_USER,
             r"Environment"),
        ]:
            try:
                with winreg.OpenKey(_hive, _subkey) as _key:
                    _val, _ = winreg.QueryValueEx(_key, "PATH")
                    _path_parts.append(_val)
            except FileNotFoundError:
                pass
        if _path_parts:
            _registry_path = os.pathsep.join(_path_parts)
            _current_path = os.environ.get("PATH", "")
            # Prepend registry PATH so newly-installed tools are found first
            os.environ["PATH"] = _registry_path + os.pathsep + _current_path
            logger.info("Windows PATH refreshed from registry (ffmpeg support).")
    except Exception as _e:
        logger.warning(f"Could not refresh Windows PATH from registry: {_e}")

# ── Constants ────────────────────────────────────────────────────────────────
SUPPORTED_AUDIO_FORMATS = {
    ".webm", ".wav", ".mp3", ".ogg", ".m4a", ".flac", ".mp4"
}

# Maximum audio file size: 25 MB (Whisper's practical limit for reasonable speed)
MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024

# Whisper model size. Options: "tiny", "base", "small", "medium", "large"
# "base" offers the best speed/accuracy balance for production use.
WHISPER_MODEL_SIZE = "base"

# ── Lazy model loader ─────────────────────────────────────────────────────────
_whisper_model = None


def _get_whisper_model():
    """
    Lazily load the Whisper model on first request.
    This avoids loading the model at startup alongside the ML pipeline.
    """
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper  # openai-whisper
            logger.info(f"Loading Whisper '{WHISPER_MODEL_SIZE}' model...")
            _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
            logger.info("Whisper model loaded successfully.")
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "OpenAI Whisper is not installed. "
                    "Run: pip install openai-whisper"
                ),
            )
        except Exception as exc:
            logger.exception("Failed to load Whisper model.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Whisper model could not be loaded: {str(exc)}",
            )
    return _whisper_model


# ── Router ────────────────────────────────────────────────────────────────────
router = APIRouter(
    prefix="",
    tags=["speech"],
)


# ── Helper ────────────────────────────────────────────────────────────────────
def _validate_audio_file(file: UploadFile) -> str:
    """
    Validate the uploaded audio file.

    Returns the file extension on success.
    Raises HTTPException with a descriptive message on failure.
    """
    if file.filename:
        ext = Path(file.filename).suffix.lower()
    else:
        # Browser MediaRecorder often omits filenames; default to .webm
        ext = ".webm"

    if ext not in SUPPORTED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported audio format '{ext}'. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}"
            ),
        )

    return ext


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.post(
    "/speech-to-text",
    summary="Transcribe audio to text using Whisper",
    response_description="JSON object containing the recognized transcript",
    responses={
        200: {
            "description": "Successful transcription",
            "content": {
                "application/json": {
                    "example": {"transcript": "I feel anxious about tomorrow."}
                }
            },
        },
        400: {"description": "Empty audio file or no speech detected"},
        415: {"description": "Unsupported audio format"},
        413: {"description": "Audio file exceeds size limit"},
        503: {"description": "Whisper model unavailable"},
    },
)
async def speech_to_text(
    audio: UploadFile = File(
        ...,
        description=(
            "Audio recording file. Supported formats: "
            ".webm, .wav, .mp3, .ogg, .m4a, .flac, .mp4"
        ),
    ),
    current_user: models.User = Depends(dependencies.get_current_user),
):
    """
    **POST /speech-to-text**

    Transcribes an uploaded audio file using OpenAI Whisper.

    - Requires a valid JWT Bearer token (same auth as /predict)
    - Accepts multipart/form-data with field name `audio`
    - Returns `{"transcript": "<recognized text>"}`
    - Does NOT trigger emotion prediction or modify any user data
    """

    # ── 1. Validate format ────────────────────────────────────────────────
    file_ext = _validate_audio_file(audio)

    # ── 2. Read audio bytes ───────────────────────────────────────────────
    try:
        audio_bytes = await audio.read()
    except Exception as exc:
        logger.exception("Failed to read uploaded audio file.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read audio file. Please try again.",
        ) from exc

    # ── 3. Check file is not empty ────────────────────────────────────────
    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file is empty. Please record some audio before uploading.",
        )

    # ── 4. Enforce size limit ─────────────────────────────────────────────
    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Audio file is too large ({len(audio_bytes) / 1024 / 1024:.1f} MB). "
                f"Maximum allowed size is {MAX_AUDIO_SIZE_BYTES // 1024 // 1024} MB."
            ),
        )

    # ── 5. Write to temp file (Whisper needs a filepath) ─────────────────
    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=file_ext,
            delete=False,
            dir=tempfile.gettempdir(),
        ) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name

        logger.info(
            f"Processing audio for user '{current_user.email}': "
            f"{len(audio_bytes)} bytes, format '{file_ext}'"
        )

        # ── 6. Load Whisper & transcribe ──────────────────────────────────
        model = _get_whisper_model()

        try:
            result = model.transcribe(
                tmp_path,
                fp16=False,          # Disable FP16 for CPU compatibility
                language=None,       # Auto-detect language
                verbose=False,
            )
        except Exception as exc:
            logger.exception("Whisper transcription failed.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Whisper transcription failed. "
                    "Please ensure ffmpeg is installed and the audio is valid."
                ),
            ) from exc

        # ── 7. Extract & validate transcript ─────────────────────────────
        transcript: str = result.get("text", "").strip()

        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "No speech detected in the recording. "
                    "Please speak clearly and try again."
                ),
            )

        logger.info(
            f"Transcription successful for user '{current_user.email}': "
            f"'{transcript[:60]}{'...' if len(transcript) > 60 else ''}'"
        )

        # ── 8. Return result ──────────────────────────────────────────────
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"transcript": transcript},
        )

    finally:
        # Always clean up the temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                logger.warning(f"Could not remove temp file: {tmp_path}")
