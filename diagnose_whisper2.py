"""
Mimic exactly what speech.py does:
1. Write audio bytes to a NamedTemporaryFile
2. Run whisper.transcribe on that temp path
3. Show any exception with full traceback
"""
import sys, os, tempfile, traceback
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=== Mimicking speech.py backend logic ===\n")

# Read the test WAV
with open("test_audio.wav", "rb") as f:
    audio_bytes = f.read()
print(f"Audio size: {len(audio_bytes)} bytes")

# Write to NamedTemporaryFile (exactly like speech.py)
tmp_path = None
try:
    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False,
        dir=tempfile.gettempdir(),
    ) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = tmp_file.name

    print(f"Temp file: {tmp_path}")

    # Load Whisper base model (same as backend)
    print("Loading Whisper 'base' model...")
    import whisper
    model = whisper.load_model("base")
    print("Model loaded OK")

    # Transcribe exactly as backend does
    print("Transcribing...")
    try:
        result = model.transcribe(
            tmp_path,
            fp16=False,
            language=None,
            verbose=False,
        )
        transcript = result.get("text", "").strip()
        print(f"[PASS] Transcript: '{transcript}'")
        if not transcript:
            print("[NOTE] Empty transcript — audio had no speech (expected for tone). Backend would return HTTP 400 'No speech detected'.")
    except Exception as exc:
        print(f"[FAIL] Transcription exception: {exc}")
        traceback.print_exc()

finally:
    if tmp_path and os.path.exists(tmp_path):
        os.remove(tmp_path)
        print(f"Temp file cleaned up: {tmp_path}")

print("\n=== Done ===")
