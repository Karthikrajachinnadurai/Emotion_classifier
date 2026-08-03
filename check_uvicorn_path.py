"""
Test what PATH the uvicorn subprocess actually sees by calling a special
debug endpoint that returns os.environ['PATH'].
"""
import sys, os, urllib.request, urllib.parse, json
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000"

# Login
login_data = urllib.parse.urlencode({"username": "test@test.com", "password": "test123"}).encode()
resp = urllib.request.urlopen(urllib.request.Request(BASE+"/login", data=login_data, headers={"Content-Type":"application/x-www-form-urlencoded"}))
token = json.loads(resp.read())["access_token"]

# Get debug info from backend via a simple predict call that we'll misuse.
# Instead, let's just test if Whisper + ffmpeg works from WITHIN the uvicorn process
# by making a Python subprocess call that mimics the environment exactly.

# Get what the venv Python WITHOUT manual PATH injection sees:
import subprocess
result = subprocess.run(
    [r".\venv\Scripts\python.exe", "-c",
     "import shutil, os; ffmpeg=shutil.which('ffmpeg'); print('ffmpeg:', ffmpeg); print('PATH:', os.environ.get('PATH','')[:300])"],
    capture_output=True, text=True, cwd=os.getcwd()
)
print("=== Venv Python subprocess (inheriting current shell PATH) ===")
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:200])
