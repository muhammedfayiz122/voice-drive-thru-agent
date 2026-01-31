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
