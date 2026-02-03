"""
Deepgram Flux V2 STT - Production-grade Speech-to-Text using Deepgram's Flux model.

This module provides:
1. DeepgramSTT class - Turn-based STT with end-of-turn detection
2. Synchronous interface compatible with VoiceAgent
3. Proper WebSocket lifecycle management
4. Thread-safe audio streaming

Architecture:
- Uses Deepgram's synchronous V2 listen API (Flux model)
- Context manager pattern for WebSocket connection
- Background thread for blocking start_listening()
- Queue-based transcript delivery
- Stereo-to-mono conversion for compatibility

Note: Requires DEEPGRAM_API_KEY in environment.
"""

import os
import struct
import threading
import time
from queue import Queue, Empty
from typing import Optional, Callable, Any
from contextlib import contextmanager
from enum import Enum

from deepgram import DeepgramClient
from deepgram.core.events import EventType

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class STTState(Enum):
    """STT connection states."""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    LISTENING = "listening"
    ERROR = "error"
    CLOSED = "closed"


class DeepgramSTT:
    """
    Production-grade Deepgram Flux STT client.
    
    Features:
    - Turn-based transcription with end-of-turn detection
    - Configurable EOT threshold and timeout
    - Thread-safe transcript queue
    - Automatic reconnection support
    - Stereo-to-mono audio conversion
    
    Usage:
        stt = DeepgramSTT()
        stt.start()
        stt.send_audio(audio_bytes)
        transcript = stt.get_transcript(timeout=5.0)
        stt.stop()
    """
    
    # Deepgram configuration from settings
    MODEL = settings.deepgram_stt_model
    ENCODING = "linear16"
    SAMPLE_RATE = settings.audio_sample_rate
    
    # End-of-turn detection settings
    EOT_THRESHOLD = 0.7  # Confidence threshold for end-of-turn
    EOT_TIMEOUT_MS = 5000  # Max silence before forcing end-of-turn
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        sample_rate: int = SAMPLE_RATE,
        eot_threshold: float = EOT_THRESHOLD,
        eot_timeout_ms: int = EOT_TIMEOUT_MS,
        input_channels: int = 2,  # Most mics are stereo
        convert_to_mono: bool = True,
        on_transcript: Optional[Callable[[str], None]] = None,
        on_partial: Optional[Callable[[str], None]] = None,
        keywords: Optional[list] = None,
        debug: bool = False,
    ):
        """
        Initialize Deepgram STT client.
        
        Args:
            api_key: Deepgram API key (defaults to env var)
            sample_rate: Audio sample rate (default 16000)
            eot_threshold: End-of-turn confidence threshold (0.0-1.0)
            eot_timeout_ms: Max silence before end-of-turn (ms)
            input_channels: Number of input audio channels
            convert_to_mono: Convert stereo to mono before sending
            on_transcript: Callback for completed transcripts
            on_partial: Callback for partial/interim transcripts
            keywords: List of keywords to boost (e.g., ["pizza:2", "ice cream:2"])
            debug: Enable debug logging
        """
        self._api_key = api_key or settings.deepgram_api_key
        if not self._api_key:
            raise ValueError("DEEPGRAM_API_KEY not set")
        
        self._sample_rate = sample_rate
        self._eot_threshold = eot_threshold
        self._eot_timeout_ms = eot_timeout_ms
        self._input_channels = input_channels
        self._convert_to_mono = convert_to_mono
        self._on_transcript = on_transcript
        self._on_partial = on_partial
        self._keywords = keywords or []
        self._debug = debug
        
        # Connection state
        self._state = STTState.IDLE
        self._client: Optional[DeepgramClient] = None
        self._connection: Optional[Any] = None
        self._ctx_manager: Optional[Any] = None
        self._needs_reconnect = False
        
        # Threading
        self._listener_thread: Optional[threading.Thread] = None
        self._ready_event = threading.Event()
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        # Transcript queue
        self._transcript_queue: Queue[str] = Queue()
        self._current_turn_index: int = 0
        
        # Stats
        self._chunks_sent = 0
        self._messages_received = 0
        self._last_transcript_time: Optional[float] = None
        
        logger.info(f"DeepgramSTT initialized (model={self.MODEL}, sample_rate={sample_rate})")
    
    @property
    def is_listening(self) -> bool:
        """Check if STT is actively listening."""
        return self._state == STTState.LISTENING
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._state in (STTState.CONNECTED, STTState.LISTENING)
    
    @property
    def state(self) -> STTState:
        """Current connection state."""
        return self._state
    
    def start(self) -> bool:
        """
        Start STT session.
        
        Opens WebSocket connection and begins listening for audio.
        Non-blocking - returns immediately after connection established.
        
        Returns:
            bool: True if started successfully
        """
        with self._lock:
            if self._state != STTState.IDLE:
                logger.warning(f"Cannot start STT in state {self._state}")
                return False
            
            self._state = STTState.CONNECTING
        
        try:
            # Create client
            self._client = DeepgramClient(api_key=self._api_key)
            
            # Create connection via context manager
            # Note: v2 API (Flux) doesn't support keywords - uses context-aware model instead
            self._ctx_manager = self._client.listen.v2.connect(
                model=self.MODEL,
                encoding=self.ENCODING,
                sample_rate=self._sample_rate,
                eot_threshold=self._eot_threshold,
                eot_timeout_ms=self._eot_timeout_ms,
            )
            
            # Enter context to get actual connection
            self._connection = self._ctx_manager.__enter__()
            
            # Reset state
            self._ready_event.clear()
            self._stop_event.clear()
            self._transcript_queue = Queue()
            self._chunks_sent = 0
            self._messages_received = 0
            
            # Register event handlers
            self._connection.on(EventType.OPEN, self._on_open)
            self._connection.on(EventType.CLOSE, self._on_close)
            self._connection.on(EventType.ERROR, self._on_error)
            self._connection.on(EventType.MESSAGE, self._on_message)
            
            # Start listener thread (blocking call runs in background)
            self._listener_thread = threading.Thread(
                target=self._listener_loop,
                name="DeepgramSTT-Listener",
                daemon=True,
            )
            self._listener_thread.start()
            
            # Wait for connection to be ready
            if not self._ready_event.wait(timeout=10.0):
                logger.error("STT connection timeout")
                self._cleanup()
                return False
            
            with self._lock:
                self._state = STTState.LISTENING
            
            logger.info("STT started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start STT: {e}")
            self._cleanup()
            return False
    
    def stop(self):
        """
        Stop STT session.
        
        Closes WebSocket connection and cleans up resources.
        """
        if self._state == STTState.IDLE:
            return
        
        logger.info("Stopping STT...")
        self._stop_event.set()
        self._cleanup()
        
        with self._lock:
            self._state = STTState.IDLE
        
        logger.info("STT stopped")
    
    def send_audio(self, audio_data: bytes):
        """
        Send audio data to Deepgram for transcription.
        
        Args:
            audio_data: Raw PCM audio bytes (16-bit signed)
        
        Note:
            - Automatically converts stereo to mono if configured
            - Silently drops audio if not connected
            - Auto-reconnects if connection was lost
        """
        # Check if we need to reconnect
        if self._needs_reconnect:
            logger.info("Auto-reconnecting STT...")
            self._needs_reconnect = False
            self._cleanup()
            with self._lock:
                self._state = STTState.IDLE
            if not self.start():
                logger.error("Auto-reconnect failed")
                return
        
        if not self.is_listening or not self._connection:
            return
        
        try:
            # Convert stereo to mono if needed
            if self._convert_to_mono and self._input_channels == 2:
                audio_data = self._stereo_to_mono(audio_data)
            
            # Send to Deepgram
            self._connection.send_media(audio_data)
            self._chunks_sent += 1
            
        except Exception as e:
            if self._debug:
                logger.debug(f"Send audio error: {e}")
    
    def get_transcript(self, timeout: Optional[float] = 5.0) -> Optional[str]:
        """
        Get next completed transcript from queue.
        
        Args:
            timeout: Max seconds to wait for transcript (None = infinite)
        
        Returns:
            str: Transcript text or None if timeout
        """
        try:
            transcript = self._transcript_queue.get(block=True, timeout=timeout)
            self._last_transcript_time = time.time()
            return transcript
        except Empty:
            return None
    
    def get_transcript_nowait(self) -> Optional[str]:
        """
        Get transcript without blocking.
        
        Returns:
            str: Transcript text or None if queue empty
        """
        try:
            return self._transcript_queue.get_nowait()
        except Empty:
            return None
    
    # === Private Methods ===
    
    def _listener_loop(self):
        """Background thread running blocking start_listening()."""
        try:
            if self._debug:
                logger.debug("Listener thread started")
            self._connection.start_listening()
        except Exception as e:
            if not self._stop_event.is_set():
                logger.error(f"Listener error: {e}")
        finally:
            if self._debug:
                logger.debug("Listener thread exited")
    
    def _on_open(self, event):
        """Handle WebSocket open event."""
        logger.info("Deepgram WebSocket connected")
        self._ready_event.set()
    
    def _on_close(self, event):
        """Handle WebSocket close event."""
        logger.info("Deepgram WebSocket closed")
        with self._lock:
            if self._state != STTState.IDLE:
                self._state = STTState.CLOSED
                # Set flag for auto-reconnect
                self._needs_reconnect = True

    def _on_error(self, event):
        """Handle WebSocket error event."""
        logger.error(f"Deepgram WebSocket error: {event}")
        with self._lock:
            self._state = STTState.ERROR
    
    def _on_message(self, result):
        """
        Handle incoming Deepgram message.
        
        Flux model sends:
        - Connected: Initial connection confirmation
        - TurnInfo with event=Update: Partial transcript updates
        - TurnInfo with event=StartOfTurn: Speech started
        - TurnInfo with event=EndOfTurn: Speech ended (final transcript)
        """
        self._messages_received += 1
        
        msg_type = getattr(result, "type", None)
        event_type = getattr(result, "event", None)
        transcript = getattr(result, "transcript", None)
        turn_index = getattr(result, "turn_index", None)
        eot_confidence = getattr(result, "end_of_turn_confidence", None)
        
        if self._debug:
            logger.debug(f"Message: type={msg_type}, event={event_type}, transcript={transcript[:50] if transcript else None}")
        
        # Handle different message types
        if msg_type == "Connected":
            logger.info("Flux STT connected and ready")
            
        elif msg_type == "TurnInfo":
            if event_type == "StartOfTurn":
                self._current_turn_index = turn_index or 0
                if self._debug:
                    logger.debug(f"Turn {self._current_turn_index} started")
                    
            elif event_type == "Update":
                # Partial transcript - call callback if set
                if transcript and self._on_partial:
                    self._on_partial(transcript)
                    
            elif event_type == "EndOfTurn":
                # Final transcript for this turn
                if transcript:
                    transcript = transcript.strip()
                    if transcript:
                        logger.info(f"Turn {turn_index} complete: {transcript}")
                        self._transcript_queue.put(transcript)
                        
                        # Call callback if set
                        if self._on_transcript:
                            self._on_transcript(transcript)
    
    def _stereo_to_mono(self, audio_data: bytes) -> bytes:
        """
        Convert stereo audio to mono by averaging channels.
        
        Args:
            audio_data: Stereo PCM audio (interleaved L,R samples)
        
        Returns:
            bytes: Mono PCM audio
        """
        try:
            # Unpack stereo samples (16-bit signed)
            samples = struct.unpack(f'{len(audio_data)//2}h', audio_data)
            
            # Average left and right channels
            mono_samples = []
            for i in range(0, len(samples), 2):
                left = samples[i]
                right = samples[i + 1] if i + 1 < len(samples) else samples[i]
                mono = (left + right) // 2
                mono_samples.append(mono)
            
            # Pack back to bytes
            return struct.pack(f'{len(mono_samples)}h', *mono_samples)
            
        except Exception as e:
            logger.warning(f"Stereo to mono conversion failed: {e}")
            return audio_data
    
    def _cleanup(self):
        """Clean up resources."""
        # Stop listener thread
        self._stop_event.set()
        
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2.0)
        
        # Close connection
        if self._ctx_manager:
            try:
                self._ctx_manager.__exit__(None, None, None)
            except Exception as e:
                if self._debug:
                    logger.debug(f"Context manager exit error: {e}")
        
        self._connection = None
        self._ctx_manager = None
        self._client = None
        self._listener_thread = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False
    
    def get_stats(self) -> dict:
        """
        Get STT statistics.
        
        Returns:
            dict: Stats including chunks sent, messages received, etc.
        """
        return {
            "state": self._state.value,
            "chunks_sent": self._chunks_sent,
            "messages_received": self._messages_received,
            "queue_size": self._transcript_queue.qsize(),
            "current_turn": self._current_turn_index,
            "last_transcript_time": self._last_transcript_time,
        }


# === Standalone test function ===

def test_stt():
    """
    Test STT with microphone input.
    
    Run with: python -m app.voice_system.stt
    """
    import pyaudio
    
    # Audio config - match your working device
    MIC_DEVICE_INDEX = 1  # Adjust for your system
    SAMPLE_RATE = 16000
    CHANNELS = 2
    CHUNK = 2560
    
    print("=" * 60)
    print("Deepgram Flux STT Test")
    print("=" * 60)
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # List devices
    print("\nAvailable microphones:")
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            marker = "->" if i == MIC_DEVICE_INDEX else "  "
            print(f"{marker} [{i}] {dev['name']}")
    
    # Open microphone
    print(f"\nOpening microphone [{MIC_DEVICE_INDEX}]...")
    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=MIC_DEVICE_INDEX,
        frames_per_buffer=CHUNK,
    )
    
    # Create STT with callbacks
    def on_partial(text):
        print(f"  {text}", end="\r", flush=True)
    
    def on_final(text):
        print(f"\n{text}")
    
    stt = DeepgramSTT(
        input_channels=CHANNELS,
        convert_to_mono=True,
        on_partial=on_partial,
        on_transcript=on_final,
        debug=True,
    )
    
    # Start STT
    print("\nStarting STT...")
    if not stt.start():
        print("Failed to start STT!")
        return
    
    print("\nSpeak into your microphone (Ctrl+C to stop)...\n")
    
    try:
        while True:
            # Read audio from mic
            audio_data = stream.read(CHUNK, exception_on_overflow=False)
            
            # Send to STT
            stt.send_audio(audio_data)
            
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        stt.stop()
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Print stats
        stats = stt.get_stats()
        print(f"\nStats: {stats}")


if __name__ == "__main__":
    test_stt()
