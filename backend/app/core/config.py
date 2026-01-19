"""
Application configuration using environment variables.
"""
import os
from typing import List, Union
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Settings:
    """Application settings with environment variable support."""
    
    # API Configuration
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Professional Poker Analyzer")
    VERSION: str = os.getenv("VERSION", "0.1.0")
    DESCRIPTION: str = os.getenv("DESCRIPTION", "Advanced poker hand analysis and statistics platform")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development-secret-key-change-in-production-minimum-32-characters-long")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # OAuth 2.0 PKCE Configuration
    OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "poker-analyzer-client")
    OAUTH_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:3000/auth/callback")
    OAUTH_SCOPE: str = os.getenv("OAUTH_SCOPE", "read write")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/poker_analyzer")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "poker_analyzer")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "password")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # CORS
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """Parse CORS origins from environment variable."""
        origins = os.getenv("BACKEND_CORS_ORIGINS", "")
        if origins:
            return [origin.strip() for origin in origins.split(",")]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]  # Default for development
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_AUTH_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_AUTH_PER_MINUTE", "10"))
    RATE_LIMIT_API_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_API_PER_MINUTE", "60"))
    
    # Security
    CSRF_TOKEN_EXPIRY: int = int(os.getenv("CSRF_TOKEN_EXPIRY", "3600"))  # 1 hour
    SECURITY_HEADERS_ENABLED: bool = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    
    # Encryption
    USE_AES256_ENCRYPTION: bool = os.getenv("USE_AES256_ENCRYPTION", "true").lower() == "true"
    
    # File Upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default


# Global settings instance
settings = Settings()