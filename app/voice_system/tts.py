"""
Text-to-Speech using Deepgram SDK v5.
"""

from typing import Optional
from deepgram import DeepgramClient
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DeepgramTTS:
    """Simple TTS using Deepgram REST API."""
    
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
