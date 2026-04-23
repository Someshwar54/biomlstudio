"""
Job-related Pydantic schemas
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job type enumeration"""
    TRAINING = "TRAINING"
    PREPROCESSING = "PREPROCESSING"
    EVALUATION = "EVALUATION"
    PREDICTION = "PREDICTION"
    DATA_ANALYSIS = "DATA_ANALYSIS"
    ML_WORKFLOW = "ML_WORKFLOW"


class JobBase(BaseModel):
    """Base job schema"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    job_type: JobType
    config: Dict[str, Any]


class JobCreate(JobBase):
    """Schema for job creation"""
    name: str = Field(..., min_length=1, max_length=255)  # Required for creation
    dataset_id: Optional[int] = None
    priority: int = Field(5, ge=1, le=10)
    scheduled_at: Optional[datetime] = None


class JobUpdate(BaseModel):
    """Schema for job updates"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[int] = Field(None, ge=1, le=10)
    scheduled_at: Optional[datetime] = None


class JobResponse(JobBase):
    """Schema for job responses"""
    id: int
    user_id: int
    status: JobStatus
    progress_percent: float = 0.0
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime
    updated_at: Optional[datetime] = None
    dataset_id: Optional[int] = None
    model_id: Optional[int] = None
    parent_job_id: Optional[int] = None

    class Config:
        from_attributes = True
        protected_namespaces = ()

    @field_validator('duration_seconds')
    def format_duration(cls, v):
        """Format duration for display"""
        if v is None:
            return None
        if v < 60:
            return f"{v:.1f} seconds"
        elif v < 3600:
            return f"{v/60:.1f} minutes"
        else:
            return f"{v/3600:.1f} hours"


class JobListResponse(BaseModel):
    """Schema for paginated job list"""
    jobs: List[JobResponse]
    total: int
    skip: int
    limit: int


class JobMetrics(BaseModel):
    """Schema for job metrics and results"""
    job_id: int
    metrics: Dict[str, Any]
    artifacts: Optional[List[str]] = None
    model_performance: Optional[Dict[str, float]] = None
    training_history: Optional[List[Dict[str, float]]] = None
    feature_importance: Optional[Dict[str, float]] = None
    confusion_matrix: Optional[List[List[int]]] = None
    roc_curve: Optional[Dict[str, List[float]]] = None
    
    class Config:
        protected_namespaces = ()


class JobLog(BaseModel):
    """Schema for job execution logs"""
    job_id: int
    logs: List[str]
    timestamp: datetime
    log_level: str = "INFO"


class JobProgress(BaseModel):
    """Schema for job progress updates"""
    job_id: int
    progress_percent: float = Field(..., ge=0, le=100)
    current_step: str
    estimated_time_remaining: Optional[int] = None  # seconds
    message: Optional[str] = None
