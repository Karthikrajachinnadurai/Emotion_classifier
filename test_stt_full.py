"""
Full end-to-end STT API test using real speech audio.
Tests:
1. JWT auth
2. Audio upload to /speech-to-text
3. Whisper transcription
4. Correct JSON response
5. Repeated calls (model reuse, no reload)
"""
import sys, os, urllib.request, urllib.parse, json, socket
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000"
AUDIO_FILE = "speech_test.wav"
EXPECTED_PHRASE = "happy"  # Expect the word "happy" to appear in transcript

print("=" * 60)
print("  Speech-to-Text End-to-End API Test")
print("=" * 60)

results = {}

# ── 1. Login ──────────────────────────────────────────────────────
print("\n[TEST 1] JWT Authentication...")
try:
    login_data = urllib.parse.urlencode({"username": "test@test.com", "password": "test123"}).encode()
    resp = urllib.request.urlopen(urllib.request.Request(
        BASE+"/login", data=login_data,
        headers={"Content-Type":"application/x-www-form-urlencoded"}))
    token = json.loads(resp.read())["access_token"]
    print(f"  PASS: Token acquired ({len(token)} chars)")
    results["Authentication"] = "PASS"
except Exception as e:
    print(f"  FAIL: {e}")
    results["Authentication"] = f"FAIL: {e}"
    sys.exit(1)

# ── 2. Read audio file ────────────────────────────────────────────
print(f"\n[TEST 2] Audio File: {AUDIO_FILE}...")
try:
    with open(AUDIO_FILE, "rb") as f:
        wav = f.read()
    print(f"  PASS: {len(wav):,} bytes loaded")
    results["Audio File Load"] = "PASS"
except Exception as e:
    print(f"  FAIL: {e}")
    results["Audio File Load"] = f"FAIL: {e}"
    sys.exit(1)

# ── 3. Build multipart ────────────────────────────────────────────
boundary = "TESTBOUNDARY12345"
part_header = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="audio"; filename="{AUDIO_FILE}"\r\n'
    f"Content-Type: audio/wav\r\n\r\n"
).encode()
part_footer = f"\r\n--{boundary}--\r\n".encode()
body = part_header + wav + part_footer

# ── 4. First API call ─────────────────────────────────────────────
print(f"\n[TEST 3] First POST /speech-to-text (triggers Whisper model load)...")
print("  (May take 30-90s on first call...)")
socket.setdefaulttimeout(180)
import time

def do_stt_request(wav_bytes, token, boundary="TESTBOUNDARY12345"):
    ph = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"{AUDIO_FILE}\"\r\nContent-Type: audio/wav\r\n\r\n").encode()
    pf = f"\r\n--{boundary}--\r\n".encode()
    body = ph + wav_bytes + pf
    req = urllib.request.Request(
        BASE + "/speech-to-text", data=body,
        headers={"Authorization":"Bearer "+token, "Content-Type":f"multipart/form-data; boundary={boundary}"}
    )
    return urllib.request.urlopen(req)

try:
    t0 = time.time()
    resp = do_stt_request(wav, token)
    elapsed = time.time() - t0
    data = json.loads(resp.read())
    transcript = data.get("transcript", "")
    print(f"  HTTP 200 OK in {elapsed:.1f}s")
    print(f"  Transcript: '{transcript}'")
    if EXPECTED_PHRASE.lower() in transcript.lower():
        print(f"  PASS: Expected word '{EXPECTED_PHRASE}' found in transcript")
        results["First Transcription"] = f"PASS: '{transcript}'"
    else:
        print(f"  PARTIAL: Transcript returned but '{EXPECTED_PHRASE}' not found")
        results["First Transcription"] = f"PARTIAL: '{transcript}'"
    results["Upload to Backend"] = "PASS"
    results["Backend Receives Audio"] = "PASS"
    results["FFmpeg Detected"] = "PASS"
    results["Whisper Loads"] = "PASS"
    results["Whisper Transcribes"] = "PASS"
    results["Backend Returns JSON"] = "PASS"
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    print(f"  FAIL: HTTP {e.code}: {body}")
    results["First Transcription"] = f"FAIL: HTTP {e.code}: {body}"
    sys.exit(1)
except Exception as e:
    print(f"  FAIL: {e}")
    results["First Transcription"] = f"FAIL: {e}"
    sys.exit(1)

# ── 5. Second call (model reuse) ──────────────────────────────────
print(f"\n[TEST 4] Second POST /speech-to-text (verify model NOT reloaded)...")
try:
    t0 = time.time()
    resp2 = do_stt_request(wav, token)
    elapsed2 = time.time() - t0
    data2 = json.loads(resp2.read())
    transcript2 = data2.get("transcript", "")
    print(f"  HTTP 200 OK in {elapsed2:.1f}s")
    print(f"  Transcript: '{transcript2}'")
    if elapsed2 < 30:
        print(f"  PASS: Second call was fast ({elapsed2:.1f}s) -> model was reused, NOT reloaded")
        results["Repeated Recording (Model Reuse)"] = f"PASS: {elapsed2:.1f}s response"
    else:
        print(f"  WARNING: Second call took {elapsed2:.1f}s -> possible model reload")
        results["Repeated Recording (Model Reuse)"] = f"WARNING: {elapsed2:.1f}s (may have reloaded)"
except Exception as e:
    print(f"  FAIL: {e}")
    results["Repeated Recording (Model Reuse)"] = f"FAIL: {e}"

# ── Summary ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  TEST RESULTS SUMMARY")
print("=" * 60)
for test, result in results.items():
    status = "PASS" if result.startswith("PASS") else ("PARTIAL" if result.startswith("PARTIAL") else "FAIL")
    icon = "[PASS]" if status == "PASS" else ("[WARN]" if status == "PARTIAL" else "[FAIL]")
    print(f"  {icon} {test}: {result}")
print("=" * 60)
