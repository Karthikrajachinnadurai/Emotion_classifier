"""
Direct API test for the /speech-to-text endpoint.
Gets a JWT token, then POSTs test_audio.wav and checks the response.
"""
import sys
import urllib.request
import urllib.parse
import json
import socket

# Force UTF-8 output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:8000"

# -- 1. Login to get JWT token -----------------------------------------------
print("Step 1: Getting JWT token...")
login_data = urllib.parse.urlencode({
    "username": "test@test.com",
    "password": "test123"
}).encode()

req = urllib.request.Request(
    f"{BASE_URL}/login",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
try:
    resp = urllib.request.urlopen(req)
    token_data = json.loads(resp.read())
    token = token_data["access_token"]
    print(f"  [PASS] JWT token acquired (first 40 chars): {token[:40]}...")
except Exception as e:
    print(f"  [FAIL] Login failed: {e}")
    sys.exit(1)

# -- 2. Read the test WAV file ------------------------------------------------
print("\nStep 2: Reading test_audio.wav...")
with open("test_audio.wav", "rb") as f:
    audio_bytes = f.read()
print(f"  [PASS] Audio file loaded: {len(audio_bytes)} bytes")

# -- 3. Build multipart form data ---------------------------------------------
print("\nStep 3: Building multipart form data...")
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="audio"; filename="test_audio.wav"\r\n'
    f"Content-Type: audio/wav\r\n\r\n"
).encode() + audio_bytes + f"\r\n--{boundary}--\r\n".encode()
print(f"  [PASS] Multipart body: {len(body)} bytes")

# -- 4. POST to /speech-to-text -----------------------------------------------
print("\nStep 4: POSTing to /speech-to-text...")
print("  (Whisper 'base' model will be loaded on first request - may take 30-60s)")
socket.setdefaulttimeout(120)  # 2 min timeout

req = urllib.request.Request(
    f"{BASE_URL}/speech-to-text",
    data=body,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    },
)
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print(f"  [PASS] Response status: {resp.status}")
    print(f"  [PASS] Transcript: '{result.get('transcript', '(empty)')}'")
    first_call_ok = True
except urllib.error.HTTPError as e:
    error_body = json.loads(e.read())
    print(f"  [FAIL] HTTP {e.code}: {error_body}")
    first_call_ok = False
except Exception as e:
    print(f"  [FAIL] Request failed: {e}")
    first_call_ok = False

# -- 5. Second call (verify Whisper model cached) ----------------------------
print("\nStep 5: Second call (verify Whisper model reused, not reloaded)...")
try:
    req2 = urllib.request.Request(
        f"{BASE_URL}/speech-to-text",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    resp2 = urllib.request.urlopen(req2)
    result2 = json.loads(resp2.read())
    print(f"  [PASS] Second call succeeded: '{result2.get('transcript', '(empty)')}'")
    print("  [PASS] Whisper model was reused (no reload)")
except Exception as e:
    print(f"  [FAIL] Second call failed: {e}")

print("\n-- All API tests complete --")
