"""
ML Model model for managing trained machine learning models
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Dict, Any, List

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    String, Text, JSON, Float, Enum as SQLEnum
)
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .job import Job


class ModelType(str, Enum):
    """Model type enumeration"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    SEQUENCE_ANALYSIS = "sequence_analysis"
    STRUCTURE_PREDICTION = "structure_prediction"
    CUSTOM = "custom"


class ModelFramework(str, Enum):
    """ML framework enumeration"""
    SCIKIT_LEARN = "scikit_learn"
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    BIOPYTHON = "biopython"
    CUSTOM = "custom"


class MLModel(Base):
    """ML Model for trained machine learning models"""
    
    __tablename__ = "ml_models"
    
    # Basic model information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    model_type = Column(SQLEnum(ModelType), nullable=False, index=True)
    framework = Column(SQLEnum(ModelFramework), nullable=False)
    
    # Model version and lineage
    version = Column(String(50), default="1.0.0")
    parent_model_id = Column(Integer, ForeignKey("ml_models.id"), index=True)
    parent_model = relationship(
        "MLModel", 
        remote_side="MLModel.id",  # Use string to avoid circular imports
        backref="derived_models",
        foreign_keys=[parent_model_id]
    )
    
    # Model artifacts
    artifact_path = Column(String(500))  # Path to serialized model file
    model_size_bytes = Column(Integer)
    model_hash = Column(String(64))  # SHA-256 hash for integrity
    
    # Model configuration
    algorithm = Column(String(100))  # Random Forest, SVM, Neural Network, etc.
    hyperparameters = Column(JSON)  # Model hyperparameters
    feature_names = Column(JSON)  # List of feature names
    target_names = Column(JSON)  # List of target/class names
    preprocessing_steps = Column(JSON)  # Preprocessing pipeline configuration
    
    # Training information
    training_dataset_info = Column(JSON)  # Info about training data
    training_duration_seconds = Column(Float)
    training_samples_count = Column(Integer)
    validation_samples_count = Column(Integer)
    
    # Performance metrics
    metrics = Column(JSON)  # Model performance metrics
    cross_validation_scores = Column(JSON)  # CV scores if available
    feature_importance = Column(JSON)  # Feature importance scores
    
    # Model status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    is_deployed = Column(Boolean, default=False)
    
    # Usage tracking
    prediction_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # Model metadata
    tags = Column(JSON)  # List of tags for categorization
    license = Column(String(100))  # Model license
    citation = Column(Text)  # How to cite this model
    
    # Deployment information
    deployment_url = Column(String(500))
    api_endpoint = Column(String(500))
    deployment_config = Column(JSON)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="models")
    
    training_jobs = relationship(
        "Job",
        back_populates="model",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<MLModel(id={self.id}, name='{self.name}', type='{self.model_type}')>"
    
    @property
    def size_human_readable(self) -> str:
        """Human readable model size"""
        if not self.model_size_bytes:
            return "Unknown"
            
        size = self.model_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get model performance summary"""
        if not self.metrics:
            return {}
        
        summary = {
            "model_type": self.model_type,
            "algorithm": self.algorithm,
            "training_samples": self.training_samples_count,
        }
        
        # Add type-specific metrics
        if self.model_type == ModelType.CLASSIFICATION:
            summary.update({
                "accuracy": self.metrics.get("accuracy"),
                "precision": self.metrics.get("precision"),
                "recall": self.metrics.get("recall"),
                "f1_score": self.metrics.get("f1_score"),
                "auc_roc": self.metrics.get("auc_roc"),
            })
        elif self.model_type == ModelType.REGRESSION:
            summary.update({
                "r2_score": self.metrics.get("r2_score"),
                "mse": self.metrics.get("mse"),
                "mae": self.metrics.get("mae"),
                "rmse": self.metrics.get("rmse"),
            })
        
        return summary
    
    def increment_prediction_count(self) -> None:
        """Increment prediction counter"""
        self.prediction_count += 1
        self.last_used = datetime.utcnow()
    
    def increment_download_count(self) -> None:
        """Increment download counter"""
        self.download_count += 1
        self.last_used = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """Add tag to model"""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove tag from model"""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)
    
    def get_training_job(self) -> "Job":
        """Get the primary training job for this model"""
        return self.training_jobs.filter_by(job_type="training").first()
    
    def is_ready_for_deployment(self) -> bool:
        """Check if model is ready for deployment"""
        return (
            self.artifact_path is not None and
            self.metrics is not None and
            self.is_active
        )
