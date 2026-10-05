"""
Core configuration for Nexus OMS Backend.
Loads environment variables and provides typed settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Nexus OMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nexus:nexus_password@nexus-db:5432/nexus_oms"
    
    # Redis
    REDIS_URL: str = "redis://nexus-redis:6379/0"
    
    # Agent Core (Project 1)
    AGENT_CORE_URL: str = "http://host.docker.internal:8000"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8001
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
