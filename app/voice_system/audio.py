"""
Audio I/O - Microphone input and speaker output using PyAudio.

1. AudioRecorder: Captures audio from microphone
2. AudioPlayer: Plays audio through speakers
3. Handles audio format conversion

Note: Requires PyAudio and PortAudio installed.
"""

import io
import wave
import struct
import threading
import queue
from typing import Optional, Callable
import pyaudio

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Audio format constants
FORMAT = pyaudio.paInt16
SAMPLE_RATE = settings.audio_sample_rate
CHUNK_SIZE = settings.audio_chunk_size

# Microphone configuration - IMPORTANT!
# Most mics are stereo-only, so we capture stereo and convert to mono
MIC_DEVICE_INDEX = 1  # AMD Audio Device (adjust if needed)
MIC_CHANNELS = 2  # Capture stereo (device native)
CONVERT_TO_MONO = True  # Convert to mono for STT


class AudioRecorder:
    """
    Records audio from microphone in real-time.
    
    1. Opens microphone stream (stereo)
    2. Converts to mono for STT compatibility
    3. Yields audio chunks for streaming to STT
    4. Supports start/stop control
    
    Note: Captures at 16kHz, outputs mono 16-bit PCM.
    """
    
    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        input_channels: int = MIC_CHANNELS,
        chunk_size: int = CHUNK_SIZE,
        device_index: int = MIC_DEVICE_INDEX,
        convert_to_mono: bool = CONVERT_TO_MONO,
    ):
        """
        Initializes audio recorder.
        
        Args:
            sample_rate: Audio sample rate (default 16000)
            input_channels: Mic input channels (default 2 = stereo)
            chunk_size: Frames per buffer (default 1024)
            device_index: PyAudio device index (default 1)
            convert_to_mono: Convert stereo to mono (default True)
        """
        self.sample_rate = sample_rate
        self.input_channels = input_channels
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.convert_to_mono = convert_to_mono
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        self._audio_queue = queue.Queue()
    
    def start(self):
        """
        Starts recording from microphone.
        
        Opens PyAudio stream and begins capturing audio.
        """
        if self.is_recording:
            return
        
        self.is_recording = True
        self._audio_queue = queue.Queue()
        
        # Use blocking mode with a background thread instead of callback
        self.stream = self.audio.open(
            format=FORMAT,
            channels=self.input_channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk_size,
        )
        
        # Start reader thread
        self._reader_thread = threading.Thread(target=self._read_audio, daemon=True)
        self._reader_thread.start()
        
        logger.info(f"Microphone recording started (device={self.device_index}, channels={self.input_channels})")
    
    def _read_audio(self):
        """Background thread to read audio from stream."""
        while self.is_recording and self.stream:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Convert stereo to mono if needed
                if self.convert_to_mono and self.input_channels == 2:
                    data = self._stereo_to_mono(data)
                
                self._audio_queue.put(data)
            except Exception as e:
                if self.is_recording:
                    logger.error(f"Audio read error: {e}")
                break
    
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
    
    def stop(self):
        """
        Stops recording from microphone.
        
        Closes PyAudio stream.
        """
        if not self.is_recording:
            return
        
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        logger.info("Microphone recording stopped")
    
    def get_audio_chunk(self, timeout: float = 0.1) -> Optional[bytes]:
        """
        Gets next audio chunk from queue.
        
        Args:
            timeout: Max time to wait for chunk
        
        Returns:
            bytes: Audio data or None if timeout
        """
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def iter_chunks(self):
        """
        Generator that yields audio chunks while recording.
        
        Yields:
            bytes: Raw audio chunks
        """
        while self.is_recording:
            chunk = self.get_audio_chunk()
            if chunk:
                yield chunk
    
    def close(self):
        """
        Cleans up PyAudio resources.
        """
        self.stop()
        self.audio.terminate()
        logger.info("AudioRecorder closed")


class AudioPlayer:
    """
    Plays audio through speakers with streaming and barge-in support.
    
    1. Accepts raw audio bytes or streaming chunks
    2. Supports interruptible playback (barge-in)
    3. Non-blocking playback option
    
    Note: Supports streaming playback for low latency.
    """
    
    def __init__(self):
        """
        Initializes audio player.
        """
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_playing = False
        self._play_thread: Optional[threading.Thread] = None
        self._stop_requested = False
        self._interrupted = False
    
    @property
    def was_interrupted(self) -> bool:
        """Check if last playback was interrupted."""
        return self._interrupted
    
    def play_audio(self, audio_data: bytes, sample_rate: int = 24000, blocking: bool = True):
        """
        Plays raw PCM audio data.
        
        Args:
            audio_data: Raw PCM audio bytes (16-bit)
            sample_rate: Sample rate of audio (Deepgram TTS uses 24000)
            blocking: If True, wait for playback to complete
        """
        if blocking:
            self._play_sync(audio_data, sample_rate)
        else:
            self._play_thread = threading.Thread(
                target=self._play_sync,
                args=(audio_data, sample_rate),
                daemon=True
            )
            self._play_thread.start()
    
    def _play_sync(self, audio_data: bytes, sample_rate: int):
        """
        Synchronous audio playback.
        """
        try:
            self.is_playing = True
            self._stop_requested = False
            self._interrupted = False
            
            stream = self.audio.open(
                format=FORMAT,
                channels=1,
                rate=sample_rate,
                output=True
            )
            
            # Play in chunks for smoother playback
            chunk_size = 4096
            for i in range(0, len(audio_data), chunk_size):
                if self._stop_requested:
                    self._interrupted = True
                    break
                chunk = audio_data[i:i + chunk_size]
                stream.write(chunk)
            
            stream.stop_stream()
            stream.close()
            self.is_playing = False
            
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
            self.is_playing = False
    
    def play_streaming(
        self, 
        audio_queue: queue.Queue, 
        sample_rate: int = 24000,
        check_interrupt: Optional[callable] = None
    ) -> bool:
        """
        Play audio from a queue with streaming support and barge-in detection.
        
        Args:
            audio_queue: Queue containing audio chunks (None signals end)
            sample_rate: Audio sample rate
            check_interrupt: Callback that returns True if playback should stop
            
        Returns:
            bool: True if played to completion, False if interrupted
        """
        try:
            self.is_playing = True
            self._stop_requested = False
            self._interrupted = False
            
            stream = self.audio.open(
                format=FORMAT,
                channels=1,
                rate=sample_rate,
                output=True
            )
            
            while True:
                # Check for interrupt (barge-in)
                if self._stop_requested or (check_interrupt and check_interrupt()):
                    self._interrupted = True
                    # Drain the queue
                    while True:
                        try:
                            chunk = audio_queue.get_nowait()
                            if chunk is None:
                                break
                        except queue.Empty:
                            break
                    break
                
                try:
                    chunk = audio_queue.get(timeout=0.05)
                    if chunk is None:  # End of audio signal
                        break
                    stream.write(chunk)
                except queue.Empty:
                    continue
            
            stream.stop_stream()
            stream.close()
            self.is_playing = False
            
            return not self._interrupted
            
        except Exception as e:
            logger.error(f"Streaming playback error: {e}")
            self.is_playing = False
            return False
    
    def play_mp3(self, mp3_data: bytes, blocking: bool = True):
        """
        Plays MP3 audio data.
        
        Args:
            mp3_data: MP3 audio bytes
            blocking: If True, wait for playback to complete
        """
        try:
            # Convert MP3 to PCM using pydub
            from pydub import AudioSegment
            
            audio = AudioSegment.from_mp3(io.BytesIO(mp3_data))
            # Convert to raw PCM
            raw_data = audio.raw_data
            sample_rate = audio.frame_rate
            
            self.play_audio(raw_data, sample_rate, blocking)
            
        except ImportError:
            logger.error("pydub not installed. Install with: pip install pydub")
            raise
        except Exception as e:
            logger.error(f"MP3 playback error: {e}")
            raise
    
    def stop(self):
        """
        Stops current playback.
        """
        self.is_playing = False
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=1.0)
    
    def close(self):
        """
        Cleans up PyAudio resources.
        """
        self.stop()
        self.audio.terminate()
        logger.info("AudioPlayer closed")


def list_audio_devices():
    """
    Lists available audio input/output devices.
    
    Useful for debugging audio issues.
    """
    audio = pyaudio.PyAudio()
    print("\n=== Audio Devices ===")
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        print(f"[{i}] {info['name']}")
        print(f"    Input channels: {info['maxInputChannels']}")
        print(f"    Output channels: {info['maxOutputChannels']}")
        print(f"    Sample rate: {info['defaultSampleRate']}")
    audio.terminate()


if __name__ == "__main__":
    # Test audio devices
    list_audio_devices()
