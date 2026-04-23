"""
Pydantic schemas for request/response validation and serialization
"""

from .auth import Token, TokenData, UserCreate, UserResponse, PasswordChange
from .dataset import (
    DatasetCreate, DatasetResponse, DatasetUpdate, DatasetListResponse,
    DatasetPreview, DatasetStats
)
from .job import (
    JobCreate, JobResponse, JobUpdate, JobListResponse,
    JobMetrics, JobStatus, JobType
)
from .ml_model import (
    MLModelResponse, MLModelUpdate, MLModelListResponse,
    ModelPredictionRequest, ModelPredictionResponse
)
from .user import UserUpdate

__all__ = [
    # Auth schemas
    "Token", "TokenData", "UserCreate", "UserResponse", "PasswordChange",
    # Dataset schemas
    "DatasetCreate", "DatasetResponse", "DatasetUpdate", "DatasetListResponse",
    "DatasetPreview", "DatasetStats",
    # Job schemas
    "JobCreate", "JobResponse", "JobUpdate", "JobListResponse",
    "JobMetrics", "JobStatus", "JobType",
    # ML Model schemas
    "MLModelResponse", "MLModelUpdate", "MLModelListResponse",
    "ModelPredictionRequest", "ModelPredictionResponse",
    # User schemas
    "UserUpdate",
]
