"""
Deep debug version of STT boilerplate to identify issues
"""
import threading
import os
import pyaudio
import time
import struct
from dotenv import load_dotenv

load_dotenv()

# Use device 1 with proper stereo capture, then convert to mono
MIC_DEVICE_INDEX = 1  # AMD Audio Device
RATE = 16000
CHANNELS = 2  # Capture stereo (device native)
FORMAT = pyaudio.paInt16
CHUNK = 2560  # ~80 ms at 16kHz mono 16-bit (recommended for Flux)
CONVERT_TO_MONO = True  # Convert stereo to mono before sending

# Debug counters
audio_chunks_sent = 0
messages_received = 0
last_audio_time = None

def main():
    global audio_chunks_sent, messages_received, last_audio_time
    
    print("=" * 60)
    print("🔍 DEEP DEBUG STT SESSION")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("DEEPGRAM_API_KEY")
    print(f"\n🔑 API Key check:")
    print(f"   Present: {bool(api_key)}")
    if api_key:
        print(f"   Length: {len(api_key)}")
        print(f"   Starts with: {api_key[:10]}...")
    else:
        print("   ❌ ERROR: No API key found! Set DEEPGRAM_API_KEY in .env")
        return

    # Import Deepgram
    print("\n📦 Importing Deepgram SDK...")
    try:
        from deepgram import DeepgramClient
        print("   ✅ DeepgramClient imported")
    except ImportError as e:
        print(f"   ❌ Failed to import DeepgramClient: {e}")
        return
    
    try:
        from deepgram.core.events import EventType
        print(f"   ✅ EventType imported")
        print(f"   Available event types: {[e for e in dir(EventType) if not e.startswith('_')]}")
    except ImportError as e:
        print(f"   ❌ Failed to import EventType: {e}")
        return

    # Create client
    print("\n🔌 Creating Deepgram client...")
    try:
        client = DeepgramClient(api_key=api_key)
        print(f"   ✅ Client created: {type(client)}")
    except Exception as e:
        print(f"   ❌ Failed to create client: {e}")
        import traceback
        traceback.print_exc()
        return

    # Set up PyAudio
    print("\n🎤 Setting up PyAudio...")
    p = pyaudio.PyAudio()
    
    # List all audio devices
    print("\n📋 Available audio INPUT devices:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            marker = "👉" if i == MIC_DEVICE_INDEX else "  "
            print(f"   {marker} [{i}] {dev['name']}")
            print(f"         Channels: {dev['maxInputChannels']}, Rate: {dev['defaultSampleRate']}")
    
    # Open microphone
    print(f"\n🎙️ Opening microphone device index {MIC_DEVICE_INDEX}...")
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=MIC_DEVICE_INDEX,
            frames_per_buffer=CHUNK,
        )
        print(f"   ✅ Microphone stream opened")
        print(f"   Stream active: {stream.is_active()}")
        print(f"   Stream stopped: {stream.is_stopped()}")
    except Exception as e:
        print(f"   ❌ Failed to open microphone: {e}")
        import traceback
        traceback.print_exc()
        p.terminate()
        return

    # Test reading audio
    print("\n🧪 Testing audio read (3 chunks)...")
    for i in range(3):
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            samples = struct.unpack(f'{len(data)//2}h', data)
            max_amp = max(abs(s) for s in samples) if samples else 0
            avg_amp = sum(abs(s) for s in samples) // len(samples) if samples else 0
            print(f"   Chunk {i+1}: {len(data)} bytes, max_amp={max_amp}, avg_amp={avg_amp}")
        except Exception as e:
            print(f"   ❌ Failed to read chunk {i+1}: {e}")

    stop_flag = threading.Event()

    # === EVENT HANDLERS ===
    # NOTE: Deepgram v2 callbacks only take (event) not (self, event)
    ready = threading.Event()  # Wait for connection to be ready
    
    def on_open(event):
        print(f"\n🟢 === CONNECTION OPENED ===")
        ready.set()  # Signal that we can start sending audio
    
    def on_close(event):
        print(f"\n🔴 === CONNECTION CLOSED ===")
        print(f"   event: {event}")
    
    def on_error(event):
        print(f"\n❌ === ERROR EVENT ===")
        print(f"   event: {event}")

    def on_message(result):
        global messages_received
        messages_received += 1
        
        # Extract Flux-specific fields
        event = getattr(result, "event", None)
        turn_index = getattr(result, "turn_index", None)
        eot_confidence = getattr(result, "end_of_turn_confidence", None)
        transcript = getattr(result, "transcript", None)
        
        if event == "StartOfTurn":
            print(f"\n🗣️ --- StartOfTurn (Turn {turn_index}) ---")
        
        if transcript:
            print(f"📝 {transcript}")
        
        if event == "EndOfTurn":
            print(f"\n✅ --- EndOfTurn (Turn {turn_index}, Confidence: {eot_confidence}) ---")
        
        # Debug: print all attributes
        if messages_received <= 5:  # Only first few messages
            print(f"\n   [DEBUG msg#{messages_received}] type={type(result)}")
            for attr in ['type', 'event', 'transcript', 'turn_index', 'end_of_turn_confidence', 'speech_final', 'is_final']:
                if hasattr(result, attr):
                    print(f"   .{attr} = {getattr(result, attr)}")

    # Create connection - MUST use context manager properly!
    print("\n🔌 Creating Deepgram connection...")
    print("   Using model: flux-general-en")
    print("   Encoding: linear16")
    print(f"   Sample rate: {RATE}")
    
    print(f"\n   client.listen attributes: {[a for a in dir(client.listen) if not a.startswith('_')]}")
    
    if hasattr(client.listen, 'v2'):
        print(f"   client.listen.v2 attributes: {[a for a in dir(client.listen.v2) if not a.startswith('_')]}")

    # The key insight: v2.connect() returns a context manager
    # We need to use it with `with` to get the actual connection
    print("\n   Using context manager pattern with client.listen.v2.connect()...")
    
    ctx_manager = client.listen.v2.connect(
        model="flux-general-en",
        eot_threshold=0.7,
        eot_timeout_ms=5000,
        encoding="linear16",
        sample_rate=RATE,
    )
    print(f"   Context manager type: {type(ctx_manager)}")
    
    # Enter context to get the actual connection
    connection = ctx_manager.__enter__()
    print(f"   ✅ Actual connection type: {type(connection)}")
    print(f"   Connection methods: {[m for m in dir(connection) if not m.startswith('_')]}")
    print(f"   Send methods: {[m for m in dir(connection) if 'send' in m.lower()]}")

    # Register event handlers
    print("\n📝 Registering event handlers...")
    
    connection.on(EventType.OPEN, on_open)
    print("   ✅ Registered OPEN")
    connection.on(EventType.CLOSE, on_close)
    print("   ✅ Registered CLOSE")
    connection.on(EventType.ERROR, on_error)
    print("   ✅ Registered ERROR")
    connection.on(EventType.MESSAGE, on_message)
    print("   ✅ Registered MESSAGE")

    # Audio streaming function - runs in background thread
    def audio_stream():
        global audio_chunks_sent, last_audio_time
        print("🎵 Audio thread: Waiting for connection to be ready...")
        ready.wait()  # Wait for OPEN event
        print("🎵 Audio thread: Connection ready! Starting to send audio...")
        
        try:
            while not stop_flag.is_set():
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    
                    # Convert stereo to mono if needed
                    if CONVERT_TO_MONO and CHANNELS == 2:
                        # Stereo: interleaved L,R,L,R samples (each 2 bytes)
                        samples = struct.unpack(f'{len(data)//2}h', data)
                        # Average left and right channels
                        mono_samples = []
                        for i in range(0, len(samples), 2):
                            left = samples[i]
                            right = samples[i+1] if i+1 < len(samples) else samples[i]
                            mono = (left + right) // 2
                            mono_samples.append(mono)
                        data = struct.pack(f'{len(mono_samples)}h', *mono_samples)
                    
                    # Analyze audio level
                    if len(data) > 0:
                        samples = struct.unpack(f'{len(data)//2}h', data)
                        max_amp = max(abs(s) for s in samples) if samples else 0
                        
                        # Print audio level bar for significant audio
                        if max_amp > 300 and audio_chunks_sent % 10 == 0:
                            level = min(max_amp // 500, 50)
                            bar = "█" * level + "░" * (50 - level)
                            print(f"\r🔊 [{bar}] {max_amp:5d}", end="", flush=True)
                    
                    # Send to Deepgram
                    connection.send_media(data)
                    audio_chunks_sent += 1
                    last_audio_time = time.time()
                    
                except Exception as e:
                    print(f"\n❌ Audio error: {e}")
                    time.sleep(0.1)
        except Exception as e:
            print(f"\n❌ Audio thread error: {e}")

    # Start audio thread (background)
    audio_thread = threading.Thread(target=audio_stream, daemon=True)
    audio_thread.start()
    print("✅ Audio thread started (waiting for connection)")

    print("\n" + "=" * 60)
    print("🎤 Starting listener - Speak into your microphone!")
    print("=" * 60)
    print("\nPress Ctrl+C to stop.\n")

    # start_listening() is BLOCKING - runs in main thread
    try:
        connection.start_listening()
    except KeyboardInterrupt:
        print("\n\n⌨️ Interrupted!")
        stop_flag.set()
    finally:
        print("\n🧹 Cleaning up...")
        try:
            ctx_manager.__exit__(None, None, None)
        except Exception as e:
            print(f"   Error closing connection: {e}")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("✅ Done!")

if __name__ == "__main__":
    main()
