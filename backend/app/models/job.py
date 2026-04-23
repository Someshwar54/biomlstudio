"""
Job model for managing ML training and processing tasks
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Dict, Any

from sqlalchemy import (
    Column, DateTime, Enum as SQLEnum, ForeignKey, 
    Integer, String, Text, JSON, Float
)
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .dataset import Dataset
    from .ml_model import MLModel


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


class Job(Base):
    """Job model for ML and data processing tasks"""
    
    __tablename__ = "jobs"
    
    # Basic job information
    name = Column(String(255), nullable=True)
    description = Column(Text)
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    
    # Job configuration
    config = Column(JSON, nullable=False)  # Job-specific configuration
    parameters = Column(JSON)  # Model hyperparameters, preprocessing settings, etc.
    
    # Execution tracking
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Progress tracking
    progress_percent = Column(Float, default=0.0)
    progress = Column(Float, default=0.0)  # Simplified progress for workflow
    current_step = Column(String(100))
    total_steps = Column(Integer)
    
    # Results and metrics
    result = Column(JSON)  # Workflow results including artifacts, metrics, etc.
    metrics = Column(JSON)  # Training metrics, evaluation results, etc.
    artifacts = Column(JSON)  # Paths to generated files, models, etc.
    logs = Column(Text)  # Execution logs
    
    # Error handling
    error_message = Column(Text)
    error_traceback = Column(Text)
    
    # Resource usage
    cpu_usage_percent = Column(Float)
    memory_usage_mb = Column(Float)
    gpu_usage_percent = Column(Float)
    
    # Priority and scheduling
    priority = Column(Integer, default=5)  # 1-10, higher = more priority
    scheduled_at = Column(DateTime)
    
    # Retry mechanism
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="jobs")
    
    dataset_id = Column(Integer, ForeignKey("datasets.id"), index=True)
    dataset = relationship("Dataset", back_populates="jobs")
    
    model_id = Column(Integer, ForeignKey("ml_models.id"), index=True)
    model = relationship("MLModel", back_populates="training_jobs")
    
    # Parent-child job relationships for pipelines
    parent_job_id = Column(Integer, ForeignKey("jobs.id"), index=True)
    
    def __repr__(self) -> str:
        return f"<Job(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running"""
        return self.status in [JobStatus.QUEUED, JobStatus.RUNNING]
    
    @property
    def is_finished(self) -> bool:
        """Check if job is finished (completed, failed, or cancelled)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    @property
    def is_successful(self) -> bool:
        """Check if job completed successfully"""
        return self.status == JobStatus.COMPLETED
    
    def start_job(self) -> None:
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.current_step = "Initializing"
    
    def complete_job(self, metrics: Dict[str, Any] = None) -> None:
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percent = 100.0
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = duration.total_seconds()
        
        if metrics:
            self.metrics = metrics
    
    def fail_job(self, error_message: str, traceback: str = None) -> None:
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_traceback = traceback
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = duration.total_seconds()
    
    def cancel_job(self) -> None:
        """Mark job as cancelled"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = duration.total_seconds()
    
    def update_progress(self, percent: float, current_step: str = None) -> None:
        """Update job progress"""
        self.progress_percent = min(100.0, max(0.0, percent))
        if current_step:
            self.current_step = current_step
    
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return (
            self.status == JobStatus.FAILED and 
            self.retry_count < self.max_retries
        )
    
    def get_runtime_summary(self) -> Dict[str, Any]:
        """Get job runtime summary"""
        summary = {
            "status": self.status,
            "progress_percent": self.progress_percent,
            "current_step": self.current_step,
        }
        
        if self.started_at:
            if self.completed_at:
                summary["duration_seconds"] = self.duration_seconds
            else:
                # Calculate current runtime
                current_duration = datetime.utcnow() - self.started_at
                summary["current_runtime_seconds"] = current_duration.total_seconds()
        
        if self.metrics:
            summary["metrics"] = self.metrics
            
        if self.error_message:
            summary["error"] = self.error_message
        
        return summary


# Define the self-referential relationship after the class is defined
Job.parent_job = relationship(
    "Job",
    remote_side=[Job.id],
    backref="child_jobs",
    foreign_keys=[Job.parent_job_id]
)
