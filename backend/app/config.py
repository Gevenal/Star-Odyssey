"""Application configuration settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_env: str = "development"
    debug: bool = True

    # AI
    gemini_api_key: str

    # Database
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "odyssey7"

    # Cache
    redis_url: str = "redis://localhost:6379"

    # CORS
    cors_origins: str = "http://localhost:5173"

    # Config directory
    config_dir: Optional[str] = None

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def config_directory(self) -> Path:
        """
        Get config directory path.
        
        Priority:
        1. Environment variable CONFIG_DIR
        2. app/game_data (current location) 
        3. backend/config
        4. /mnt/project (for development)
        """
        if self.config_dir:
            return Path(self.config_dir)
        
        # Priority 1: app/game_data (where JSON files actually are)
        app_dir = Path(__file__).parent  # backend/app/
        game_data_path = app_dir / "game_data"
        
        if game_data_path.exists():
            return game_data_path  
        
        # Priority 2: backend/config
        backend_dir = app_dir.parent
        config_path = backend_dir / "config"
        
        if config_path.exists():
            return config_path
        
        # Priority 3: /mnt/project for development
        fallback = Path("/mnt/project")
        if fallback.exists():
            return fallback
        
        # Last resort: current directory
        return Path(".")


# Global settings instance
settings = Settings()