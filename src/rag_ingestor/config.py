import logging
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # File processing
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB default

    # Kafka settings
    ENABLE_KAFKA: bool = True
    KAFKA_BROKER_URL: str = "localhost:9092"
    KAFKA_TOPIC_EMBEDDINGS: str = "embedding-jobs"

    # Processing settings
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 100

    @field_validator("MAX_FILE_SIZE")
    def validate_max_file_size(cls, v):
        if v <= 0:
            raise ValueError("MAX_FILE_SIZE must be positive")
        return v

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
