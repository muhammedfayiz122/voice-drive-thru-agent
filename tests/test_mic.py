"""Quick test for microphone + Deepgram STT"""
import pyaudio
from app.config import settings
from deepgram import DeepgramClient

print("=" * 40)
print("  MICROPHONE + DEEPGRAM TEST")
print("=" * 40)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)

print("\n>>> SPEAK NOW for 3 seconds! <<<\n")

frames = []
for i in range(47):  # ~3 seconds
    data = stream.read(1024)
    frames.append(data)
    print(".", end="", flush=True)

print("\n")
stream.stop_stream()
stream.close()
p.terminate()

audio = b''.join(frames)
print(f"Captured: {len(audio)} bytes")
print("Sending to Deepgram...")

client = DeepgramClient(api_key=settings.deepgram_api_key)
response = client.listen.v1.media.transcribe_file(
    request=audio,
    model='nova-2',
    encoding='linear16',
)

if response.results.channels:
    transcript = response.results.channels[0].alternatives[0].transcript
    print(f"\n>>> TRANSCRIPT: {transcript}")
else:
    print("\n>>> NO SPEECH DETECTED")
