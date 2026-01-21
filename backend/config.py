"""
Configuration settings for the Science Chatbot backend.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Settings
    api_title: str = "Science Chatbot API"
    api_version: str = "0.2.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # CORS Settings
    cors_origins: list[str] = ["*"]
    
    # Agent Settings
    default_search_limit: int = 3
    enable_agent_mode: bool = True
    
    # LLM Settings
    openai_api_key: Optional[str] = None  # Replace with your actual API key or set as env variable

    # Logging
    log_level: str = "INFO"

    # Wikimedia bot compliance
    wikimedia_user_agent: Optional[str] = None
    wikimedia_rps: float = 1.0
    WIKIMEDIA_USER_AGENT: str = "science-chatbot/0.2.0 (local for my portfolio; contact: ivanmatiasmongi@gmail.com)"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
