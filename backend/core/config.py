from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/gims")
    CHROMADB_HOST: str = Field(default="localhost")
    CHROMADB_PORT: int = Field(default=8000)
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    JWT_SECRET: str = Field(default="change-this-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60)
    SEMANTIC_MEMORY_TTL_DAYS: int = Field(default=365)
    PROCEDURAL_MEMORY_TTL_DAYS: int = Field(default=90)
    EPISODIC_MEMORY_TTL_DAYS: int = Field(default=30)
    EVALUATION_AUTO_STORE_THRESHOLD: float = Field(default=0.85)
    EVALUATION_DEDUP_THRESHOLD: float = Field(default=0.70)
    EVALUATION_HITL_THRESHOLD: float = Field(default=0.50)
    DEDUP_SIMILARITY_THRESHOLD: float = Field(default=0.85)
    RETRIEVAL_TOP_K: int = Field(default=5)
    RETRIEVAL_VECTOR_WEIGHT: float = Field(default=0.6)
    RETRIEVAL_KEYWORD_WEIGHT: float = Field(default=0.4)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
