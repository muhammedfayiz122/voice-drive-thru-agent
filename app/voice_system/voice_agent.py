"""
Voice agent - main voice conversation loop for drive-thru.
Flow:
1. Play greeting
2. Listen for customer speech (STT)
3. Process through LangGraph agent
4. Speak response (TTS) - mic muted to prevent echo
5. Repeat until order complete
"""

import time
import queue
import threading
import struct

from typing import Optional
from app.agent.graph import build_graph
from app.agent.utils.menu_cache import MenuCache
from app.voice_system.audio import AudioRecorder, AudioPlayer
from app.voice_system.stt import DeepgramSTT
from app.voice_system.tts import DeepgramTTS
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VoiceAgent:
    """
    Voice-agent for drive-thru which manages communication with user.
    1. Manages STT/TTS components
    2. Maintains conversation state
    3. Coordinates agent invocations
    """
    def __init__(self):
        """
        Initializes voice agent components.
        """
        # Initialize cache first (critical for latency)
        logger.info("Initializing MenuCache...")
        MenuCache.initialize()
        
        # Build LangGraph agent
        logger.info("Building agent graph...")
        self.agent = build_graph()
        
        # Build keywords from menu for STT accuracy
        stt_keywords = self._build_stt_keywords()
        logger.info(f"Loaded {len(stt_keywords)} STT keywords from menu")
        
        # Initialize audio components
        logger.info("Initializing audio components...")
        self.recorder = AudioRecorder()
        self.player = AudioPlayer()
        
        # Audio is already converted to mono by AudioRecorder, so set input_channels=1
        self.stt = DeepgramSTT(input_channels=1, convert_to_mono=False, keywords=stt_keywords)
        self.tts = DeepgramTTS()
        
        # Conversation state
        self.cart_items = []
        self.cart_total = 0.0
        self.conversation_history = []
        self.is_running = False
        
        # Mic mute during TTS (prevents echo/feedback from corrupting transcription)
        self._mute_mic = False
        
        logger.info("VoiceAgent initialized")
    
    def _build_stt_keywords(self) -> list:
        """
        Builds keyword list from menu for STT accuracy boosting.
        Fetches menu items from MenuCache and formats for Deepgram.
        """
        keywords = []
        # Add menu item names with boost
        for item in MenuCache.get_menu():
            name = item.get("name", "")
            if name:
                # Add full name and individual words
                keywords.append(f"{name}:2")
                for word in name.lower().split():
                    if len(word) > 3:  # Skip short words
                        keywords.append(f"{word}:2")
        
        # Add common ordering phrases
        keywords.extend(["order:1", "menu:1", "cancel:1", "remove:1", "done:1"])
        
        # Remove duplicates
        return list(set(keywords))
    
    def speak(self, text: str, blocking: bool = True):
        """
        Speaks text through TTS with streaming for low latency.
        Mic is muted during playback to prevent echo corruption.
        
        Args:
            text: Text to speak
            blocking: Wait for playback to complete
        """
        if not text:
            return
        
        try:
            # Mute mic to prevent echo (speaker audio corrupts STT)
            self._mute_mic = True
            
            # Create audio queue for streaming playback
            audio_queue = queue.Queue()
            
            # Start TTS generation in background (streams chunks to queue)
            self.tts.speak_pcm_async(text, audio_queue, sample_rate=24000)
            
            # Play audio from queue (streaming = low latency start)
            self.player.play_streaming(audio_queue, sample_rate=24000)
            
            # Grace period after TTS ends before listening again
            # This prevents tail-end echo from being picked up
            time.sleep(0.3)
            self._mute_mic = False
            
        except Exception as e:
            self._mute_mic = False
            logger.error(f"Speak failed: {e}")
            print(f"[TTS Error - displaying text]: {text}")
    
    def listen(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Listens for customer speech.
        Args:
            timeout: max time to wait for speech (None = infinite)
        Returns:
            str: transcribed text or None
        """
        print("Listening...", end="", flush=True)
        transcript = self.stt.get_transcript(timeout=timeout)
        if transcript:
            print(" done")
        elif timeout is not None:
            print(" (timeout)")
        return transcript
    
    def process(self, user_input: str) -> str:
        """
        Processes user input through agent.  
        Args:
            user_input: customer's speech text
        Returns:
            str: agent's response text
        """
        try:
            start_time = time.perf_counter()
            
            result = self.agent.invoke({
                "user_input": user_input,
                "cart_items": self.cart_items,
                "cart_total": self.cart_total,
                "conversation_history": self.conversation_history,
            })
            
            latency = (time.perf_counter() - start_time) * 1000
            logger.info(f"Agent latency: {latency:.0f}ms")
            
            # Update state
            self.cart_items = result.get("cart_items", self.cart_items)
            self.cart_total = result.get("cart_total", self.cart_total)
            
            # Update history
            response = result.get("response_text", "")
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": response
            })
            
            # Check if conversation complete
            if result.get("conversation_complete"):
                self._reset_conversation()
            
            return response
            
        except Exception as e:
            logger.error(f"Process error: {e}")
            print(str(e)) # for debug stage
            return "Sorry, something went wrong. Could you repeat that?"
    
    def _reset_conversation(self):
        """
        Resets conversation state after order completion.
        """
        logger.info("Resetting conversation state")
        self.cart_items = []
        self.cart_total = 0.0
        self.conversation_history = []
    
    def run(self):
        """
        Main conversation loop.
        1. Start STT + audio streaming (keep alive)
        2. Greets customer
        3. Listen → Process → Speak loop
        4. Continues until Ctrl+C
        """
        self.is_running = True
        
        # Start STT and audio streaming (keep alive for whole conversation)
        if not self.stt.start():
            print("Failed to start STT")
            return
        
        self.recorder.start()
        self._start_audio_streaming()
        
        # Initial greeting
        greeting = "Hi there! Welcome to QuickBite. What can I get for you today?"
        print(f"Agent: {greeting}")
        self.speak(greeting)
        
        try:
            while self.is_running:
                # Listen for customer (infinite wait - no timeout prompts)
                user_input = self.listen(timeout=None)
                
                if not user_input:
                    # No speech detected - just keep listening silently
                    continue
                
                print(f"Customer: {user_input}")
                
                # Process through agent
                response = self.process(user_input)
                if response:
                    print(f"Agent: {response}")
                    self.speak(response)
                    
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            self.is_running = False
        finally:
            self.shutdown()
    
    def _start_audio_streaming(self):
        """Start background thread to stream audio to STT."""
        def stream_audio():
            while self.is_running:
                # Always get audio to prevent queue buildup
                chunk = self.recorder.get_audio_chunk(timeout=0.1)
                if chunk and not self._mute_mic:
                    # Only send to STT when not muted (TTS not playing)
                    self.stt.send_audio(chunk)
                # When muted, audio is discarded to prevent echo
        
        self._audio_thread = threading.Thread(target=stream_audio, daemon=True)
        self._audio_thread.start()
    
    def shutdown(self):
        """
        Cleans up resources.
        """
        logger.info("Shutting down VoiceAgent...")
        self.is_running = False
        self.stt.stop()
        self.recorder.close()
        self.player.close()
        logger.info("VoiceAgent shutdown complete")


def run_voice_agent():
    """
    Entry point for voice agent.
    """
    agent = VoiceAgent()
    agent.run()


if __name__ == "__main__":
    run_voice_agent()
