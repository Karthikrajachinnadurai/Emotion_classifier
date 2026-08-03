"""
Test the exact PATH available inside the uvicorn worker process by hitting
a debug endpoint we can temporarily check via the existing backend.
Instead: just show what PATH is available in a venv Python WITHOUT the 
manual $env:PATH injection (simulating what uvicorn worker sees).
"""
import sys, os, shutil

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("PATH entries:")
for p in os.environ.get("PATH","").split(os.pathsep):
    print(f"  {p}")

print("\nffmpeg via shutil.which:", shutil.which("ffmpeg"))
