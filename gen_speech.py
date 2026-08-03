"""
Generate a real speech WAV using Windows SAPI TTS.
Saves as speech_test.wav for use in the STT API test.
"""
import sys, os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import win32com.client
    speak = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    stream.Open("speech_test.wav", 3)  # 3 = SSFMCreateForWrite
    speak.AudioOutputStream = stream
    speak.Rate = -2  # slightly slower for clarity
    speak.Speak("I am feeling happy today")
    stream.Close()
    size = os.path.getsize("speech_test.wav")
    print(f"Generated speech_test.wav: {size} bytes using Windows SAPI TTS")
except Exception as e:
    print(f"SAPI not available: {e}")
    print("Trying alternative: pyttsx3...")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.save_to_file("I am feeling happy today", "speech_test.wav")
        engine.runAndWait()
        size = os.path.getsize("speech_test.wav")
        print(f"Generated speech_test.wav via pyttsx3: {size} bytes")
    except Exception as e2:
        print(f"pyttsx3 not available: {e2}")
        print("Falling back to ffmpeg TTS via text pipe...")
        import subprocess
        # Use ffmpeg to generate a recognizable speech-like audio using lavfi
        # Instead, generate silence with some tones spaced like speech
        result = subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "sine=frequency=300:duration=0.1,sine=frequency=400:duration=0.05",
            "-ar", "16000", "-ac", "1",
            "speech_test.wav"
        ], capture_output=True)
        print(f"ffmpeg exit: {result.returncode}")
        print(result.stderr.decode('utf-8', errors='replace')[:200])
