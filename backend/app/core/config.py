"""
Configuration management using Pydantic Settings
"""

import secrets
import os
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "BioMLStudio"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = secrets.token_urlsafe(32)
    API_VERSION: str = "v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./bioml.db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "filesystem://"
    CELERY_RESULT_BACKEND: str = "db+sqlite:///./celery_results.db"
    
    # Storage Configuration
    STORAGE_TYPE: str = "local"  # 'local' or 's3' or 'minio'
    LOCAL_STORAGE_PATH: str = "storage"
    
    # MinIO/S3 Storage (disabled by default)
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None
    MINIO_BUCKET_NAME: Optional[str] = None
    MINIO_SECURE: bool = False
    
    # AWS S3 (alternative)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_DEFAULT_REGION: str = "us-east-1"
    AWS_S3_BUCKET: Optional[str] = None
    
    def __init__(self, **values):
        super().__init__(**values)
        # Ensure local storage directory exists
        if self.STORAGE_TYPE == 'local':
            os.makedirs(self.LOCAL_STORAGE_PATH, exist_ok=True)
    
    # Security
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    
    # CORS
    CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_FILE_EXTENSIONS: List[str] = [
        "csv", "txt", "fasta", "fa", "fastq", "fq", 
        "json", "xlsx", "tsv", "gbk", "gff"
    ]
    UPLOAD_CHUNK_SIZE: int = 8192
    UPLOAD_DIR: str = "uploads"
    
    # ML Settings
    MODEL_STORAGE_PATH: str = "models"
    MODELS_DIR: str = "models"
    MAX_TRAINING_TIME_SECONDS: int = 7200  # 2 hours
    DEFAULT_TEST_SIZE: float = 0.2
    MAX_FEATURES: int = 10000
    N_JOBS: int = -1
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    SENTRY_DSN: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    FROM_EMAIL: EmailStr = "noreply@biomlstudio.com"
    
    # Bioinformatics specific
    MAX_SEQUENCE_LENGTH: int = 50000
    SUPPORTED_SEQUENCE_TYPES: List[str] = ["dna", "rna", "protein"]
    DEFAULT_KMER_SIZE: int = 3
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        if not v:
            return v
        # Normalize legacy 'postgres://' scheme to a valid SQLAlchemy URL
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+psycopg2://", 1)
        allowed_prefixes = (
            "postgresql://",
            "postgresql+psycopg2://",
            "postgresql+psycopg://",
            "sqlite:///",
        )
        if not v.startswith(allowed_prefixes):
            raise ValueError(
                "Database URL must start with postgresql://, postgresql+psycopg2://, postgresql+psycopg:// or sqlite:///"
            )
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
