import threading
import os
import pyaudio
from dotenv import load_dotenv

load_dotenv()

MIC_DEVICE_INDEX = 9
RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 2560  # ~80 ms at 16kHz mono 16‑bit (recommended for Flux)

def main():
    from deepgram import DeepgramClient
    from deepgram.core.events import EventType
    from deepgram.extensions.types.sockets import ListenV2SocketClientResponse

    client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

    # Set up PyAudio
    p = pyaudio.PyAudio()
    print("Opening microphone device index:", MIC_DEVICE_INDEX)
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=MIC_DEVICE_INDEX,
        frames_per_buffer=CHUNK,
    )

    stop_flag = threading.Event()

    def on_flux_message(message: ListenV2SocketClientResponse) -> None:
        # Turn-based: only react to EndOfTurn
        if getattr(message, "type", None) == "TurnInfo" and getattr(message, "event", None) == "EndOfTurn":
            if getattr(message, "transcript", None):
                text = message.transcript.strip()
                if text:
                    print(f"\nEndOfTurn transcript: {text}\n")

    # Connect to Flux /v2/listen
    with client.listen.v2.connect(
        model="flux-general-en",
        encoding="linear16",
        sample_rate=RATE,
    ) as connection:
        connection.on(EventType.MESSAGE, on_flux_message)

        # Start listening loop in background thread [[Flux agent](https://developers.deepgram.com/docs/flux/agent#endofturn-only-voice-agent-example)]
        listener_thread = threading.Thread(
            target=connection.start_listening,
            daemon=True,
        )
        listener_thread.start()

        print("Speak into your microphone. (This example runs until process exit)\n")

        def audio_loop():
            try:
                while not stop_flag.is_set():
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    # Send raw PCM to Flux
                    connection.send_media(data)
            finally:
                # Send CloseStream so server finalizes and closes [[Close stream](https://developers.deepgram.com/docs/flux/close-stream)]
                try:
                    connection.send_json({"type": "CloseStream"})
                except Exception:
                    pass
                stream.stop_stream()
                stream.close()
                p.terminate()
                print("Stopped audio and requested Flux CloseStream.")

        audio_thread = threading.Thread(target=audio_loop, daemon=True)
        audio_thread.start()

        # In your real app, you’d set stop_flag from your own logic (e.g., call end, timeout, etc.)
        # Here we just block forever; kill the process to stop.
        audio_thread.join()

if __name__ == "__main__":
    main()