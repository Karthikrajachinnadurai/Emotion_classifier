"""
Minimal API test - makes a POST to /speech-to-text with a WAV file
and prints the full response including any error body.
"""
import sys, os, urllib.request, urllib.parse, json, socket
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000"

# Login
print("Logging in...")
login_data = urllib.parse.urlencode({"username": "test@test.com", "password": "test123"}).encode()
resp = urllib.request.urlopen(urllib.request.Request(BASE+"/login", data=login_data, headers={"Content-Type":"application/x-www-form-urlencoded"}))
token = json.loads(resp.read())["access_token"]
print("Token OK")

# Read wav
with open("test_audio.wav", "rb") as f:
    wav = f.read()
print(f"WAV: {len(wav)} bytes")

# Build multipart
boundary = "TESTBOUNDARY12345"
part_header = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="audio"; filename="test_audio.wav"\r\n'
    f"Content-Type: audio/wav\r\n\r\n"
).encode()
part_footer = f"\r\n--{boundary}--\r\n".encode()
body = part_header + wav + part_footer

print(f"Body: {len(body)} bytes")
print("POSTing to /speech-to-text...")
socket.setdefaulttimeout(120)
req = urllib.request.Request(
    BASE + "/speech-to-text",
    data=body,
    headers={
        "Authorization": "Bearer " + token,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
)
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    print(f"SUCCESS: {data}")
except urllib.error.HTTPError as e:
    body = e.read()
    print(f"HTTP {e.code}: {body.decode('utf-8', errors='replace')}")
except Exception as ex:
    print(f"ERROR: {ex}")
