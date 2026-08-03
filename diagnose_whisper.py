"""
Diagnose the Whisper + FFmpeg issue directly in Python (no HTTP layer).
Runs whisper.transcribe on the test WAV and captures the full traceback.
"""
import sys, os, traceback

# Force UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=== Whisper + FFmpeg Direct Diagnosis ===\n")

# 1. Check which ffmpeg Whisper can find
print("1. Checking PATH for ffmpeg...")
import shutil
ffmpeg_path = shutil.which("ffmpeg")
print(f"   shutil.which('ffmpeg') = {ffmpeg_path}")

# 2. Check Whisper's own ffmpeg detection
print("\n2. Checking whisper.audio.find_audio_files / ffmpeg usage...")
try:
    import whisper
    import whisper.audio as wa
    print(f"   whisper version: {getattr(whisper, '__version__', 'unknown')}")
    print(f"   whisper.audio module: {wa.__file__}")
except Exception as e:
    print(f"   ERROR importing whisper: {e}")

# 3. Try to run ffmpeg subprocess from Python directly
print("\n3. Running ffmpeg subprocess test...")
import subprocess
try:
    result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True, text=True, timeout=10
    )
    print(f"   returncode: {result.returncode}")
    print(f"   stdout: {result.stdout[:100]}")
except FileNotFoundError as e:
    print(f"   FAIL - FileNotFoundError: {e}")
except Exception as e:
    print(f"   FAIL - {e}")

# 4. Load Whisper base model
print("\n4. Loading Whisper 'base' model...")
try:
    model = whisper.load_model("base")
    print("   Model loaded OK")
except Exception as e:
    print(f"   ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

# 5. Transcribe the test wav
print("\n5. Running model.transcribe on test_audio.wav...")
try:
    result = model.transcribe("test_audio.wav", fp16=False, language=None, verbose=True)
    print(f"   Transcript: '{result.get('text', '').strip()}'")
    print("   [PASS] Transcription succeeded!")
except Exception as e:
    print(f"   [FAIL] Transcription error: {e}")
    traceback.print_exc()

print("\n=== Diagnosis complete ===")
