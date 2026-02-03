from uuid import uuid4
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration settings."""

    app_name: str = "Voice-Drive-Thru Agent"
    version: str = "0.1.0"
    debug: bool = True
    
    log_format: str = Field(default="json")  # Options: "json" or "console"
    
    # MCP Settings
    mcp_base_url: str = Field(default="http://localhost:8001", env="MCP_BASE_URL")
    mcp_timeout: int = Field(default=5, env="MCP_TIMEOUT")
    
    # Legacy system settings
    legacy_system_url: str = Field(default="http://localhost:7000", env="LEGACY_SYSTEM_URL")
    legacy_system_timeout: int = Field(default=5, env="LEGACY_SYSTEM_TIMEOUT")
    
    # LangSmith
    langsmith_api_key: str = Field(default=None, env="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="Voice-Drive-Thru-Agent", env="LANGSMITH_PROJECT")
    langsmith_tracing: bool = Field(default=False, env="LANGSMITH_TRACING")
    
    # Deepgram Voice Settings
    deepgram_api_key: str = Field(default=None, env="DEEPGRAM_API_KEY")
    deepgram_stt_model: str = Field(default="flux-general-en", env="DEEPGRAM_STT_MODEL")
    deepgram_tts_model: str = Field(default="aura-2-thalia-en", env="DEEPGRAM_TTS_MODEL")
    deepgram_tts_voice: str = Field(default="aura-2-thalia-en", env="DEEPGRAM_TTS_VOICE")
    
    # Audio Settings
    audio_sample_rate: int = Field(default=16000, env="AUDIO_SAMPLE_RATE")
    audio_channels: int = Field(default=1, env="AUDIO_CHANNELS")
    audio_chunk_size: int = Field(default=1024, env="AUDIO_CHUNK_SIZE")
    
    # Voice Agent Settings
    silence_threshold: float = Field(default=1.5, env="SILENCE_THRESHOLD")  # seconds of silence to detect end of speech
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = "utf-8"
        extra = "allow"
    
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings()
