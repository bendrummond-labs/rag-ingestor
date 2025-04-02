import logging
from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # File processing
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB default

    # Embedder service
    EMBEDDER_URL: HttpUrl = "http://embedder-service:8080/api/v1"
    EMBEDDER_TIMEOUT: float = 60.0
    EMBEDDER_MAX_RETRIES: int = 3
    EMBEDDER_BATCH_SIZE: int = 50

    # Processing settings
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 100

    @field_validator("MAX_FILE_SIZE")
    def validate_max_file_size(cls, v):
        if v <= 0:
            raise ValueError("MAX_FILE_SIZE must be positive")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
