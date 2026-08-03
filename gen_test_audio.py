"""Generate a test WAV audio file with a 440Hz tone for API testing."""
import struct
import math

sample_rate = 16000
duration = 3
frequency = 440
amplitude = 32767

samples = []
for i in range(sample_rate * duration):
    t = i / sample_rate
    value = int(amplitude * math.sin(2 * math.pi * frequency * t))
    samples.append(struct.pack('<h', value))

audio_data = b''.join(samples)

wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
    b'RIFF', 36 + len(audio_data), b'WAVE',
    b'fmt ', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16,
    b'data', len(audio_data)
)

wav_bytes = wav_header + audio_data

with open('test_audio.wav', 'wb') as f:
    f.write(wav_bytes)

print(f"test_audio.wav written: {len(wav_bytes)} bytes, {duration}s @ {sample_rate}Hz")
