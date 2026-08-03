"""
Add a quick debug endpoint to our backend to reveal exactly what the 
uvicorn worker process's environment looks like.
"""
import urllib.request, urllib.parse, json, sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000"
login_data = urllib.parse.urlencode({"username": "test@test.com", "password": "test123"}).encode()
resp = urllib.request.urlopen(urllib.request.Request(BASE+"/login", data=login_data, 
    headers={"Content-Type":"application/x-www-form-urlencoded"}))
token = json.loads(resp.read())["access_token"]

# Call /debug-env if it exists (it won't, but let's see the 404)
# Instead: let's test the actual whisper call via a synthetic approach
# We'll use the whisper transcription with a speech-containing WAV

# First, generate a WAV that has actual speech-like content (random noise)
# Actually, let's try the 440Hz tone first to see if we get 400 or 500
import urllib.error
req = urllib.request.Request(BASE+"/speech-to-text",
    data=b"",  # empty - will get 400
    headers={"Authorization":"Bearer "+token, "Content-Type":"multipart/form-data; boundary=X"})
try:
    urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print(f"Empty body: HTTP {e.code}: {e.read().decode()}")
