"""
Text-to-Speech using Deepgram SDK v5.

Features:
- Streaming TTS for low-latency playback
- Non-blocking audio generation
"""

import threading
import queue
from typing import Optional, Generator, Callable
from deepgram import DeepgramClient
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DeepgramTTS:
    """Streaming TTS using Deepgram REST API with chunked playback."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.deepgram_api_key
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not set")
        self.model = model or settings.deepgram_tts_model
        self.client = DeepgramClient(api_key=self.api_key)
        logger.info(f"DeepgramTTS initialized (voice={self.model})")
    
    def speak(self, text: str) -> bytes:
        """Convert text to MP3 audio bytes."""
        if not text.strip():
            return b""
        try:
            response = self.client.speak.v1.audio.generate(
                text=text,
                model=self.model,
            )
            # Response is a generator - collect all bytes
            audio_chunks = []
            for chunk in response:
                audio_chunks.append(chunk)
            audio_data = b"".join(audio_chunks)
            logger.info(f"TTS: {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            raise
    
    def speak_pcm(self, text: str, sample_rate: int = 24000) -> tuple[bytes, int]:
        """Convert text to PCM audio for direct playback."""
        if not text.strip():
            return b"", sample_rate
        try:
            response = self.client.speak.v1.audio.generate(
                text=text,
                model=self.model,
                encoding="linear16",
                sample_rate=sample_rate,
            )
            audio_chunks = []
            for chunk in response:
                audio_chunks.append(chunk)
            audio_data = b"".join(audio_chunks)
            logger.info(f"TTS PCM: {len(audio_data)} bytes")
            return audio_data, sample_rate
        except Exception as e:
            logger.error(f"TTS PCM failed: {e}")
            raise

    def speak_pcm_streaming(
        self, 
        text: str, 
        sample_rate: int = 24000,
        on_chunk: Optional[Callable[[bytes], None]] = None
    ) -> Generator[bytes, None, None]:
        """
        Stream PCM audio chunks for ultra-low latency playback.
        
        Args:
            text: Text to convert to speech
            sample_rate: Audio sample rate (default 24000)
            on_chunk: Optional callback for each chunk
            
        Yields:
            bytes: PCM audio chunks as they arrive
        """
        if not text.strip():
            return
        
        try:
            response = self.client.speak.v1.audio.generate(
                text=text,
                model=self.model,
                encoding="linear16",
                sample_rate=sample_rate,
            )
            
            total_bytes = 0
            for chunk in response:
                if chunk:
                    total_bytes += len(chunk)
                    if on_chunk:
                        on_chunk(chunk)
                    yield chunk
            
            logger.info(f"TTS streaming complete: {total_bytes} bytes")
            
        except Exception as e:
            logger.error(f"TTS streaming failed: {e}")
            raise

    def speak_pcm_async(
        self,
        text: str,
        audio_queue: queue.Queue,
        sample_rate: int = 24000,
        done_event: Optional[threading.Event] = None
    ):
        """
        Generate TTS audio in background thread, pushing chunks to queue.
        
        Args:
            text: Text to speak
            audio_queue: Queue to push audio chunks to
            sample_rate: Audio sample rate
            done_event: Event to set when generation is complete
        """
        def _generate():
            try:
                for chunk in self.speak_pcm_streaming(text, sample_rate):
                    audio_queue.put(chunk)
            except Exception as e:
                logger.error(f"Async TTS error: {e}")
            finally:
                audio_queue.put(None)  # Signal end of audio
                if done_event:
                    done_event.set()
        
        thread = threading.Thread(target=_generate, daemon=True)
        thread.start()
        return thread
