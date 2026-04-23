"""
ML Model-related Pydantic schemas
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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


class MLModelBase(BaseModel):
    """Base ML model schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    model_type: ModelType
    framework: ModelFramework
    is_public: bool = False
    tags: Optional[List[str]] = None
    
    class Config:
        protected_namespaces = ()


class MLModelUpdate(BaseModel):
    """Schema for model updates"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


class MLModelResponse(MLModelBase):
    """Schema for model responses"""
    id: int
    user_id: int
    version: str = "1.0.0"
    algorithm: Optional[str] = None
    artifact_path: Optional[str] = None
    model_size_bytes: Optional[int] = None
    training_duration_seconds: Optional[float] = None
    training_samples_count: Optional[int] = None
    validation_samples_count: Optional[int] = None
    is_active: bool = True
    is_deployed: bool = False
    prediction_count: int = 0
    download_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    metrics: Optional[Dict[str, Any]] = None
    hyperparameters: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        protected_namespaces = ()


class MLModelListResponse(BaseModel):
    """Schema for paginated model list"""
    models: List[MLModelResponse]
    total: int
    skip: int
    limit: int


class ModelPredictionRequest(BaseModel):
    """Schema for model prediction requests"""
    input_data: List[Dict[str, Any]] = Field(..., min_items=1)
    return_probabilities: bool = False
    return_feature_importance: bool = False


class ModelPredictionResponse(BaseModel):
    """Schema for model prediction responses"""
    model_id: int
    predictions: List[Any]
    probabilities: Optional[List[List[float]]] = None
    feature_importance: Optional[Dict[str, float]] = None
    prediction_time_ms: Optional[float] = None
    timestamp: datetime
    
    class Config:
        protected_namespaces = ()


class ModelMetrics(BaseModel):
    """Schema for model performance metrics"""
    model_id: int
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    auc_roc: Optional[float] = None
    r2_score: Optional[float] = None
    mse: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    confusion_matrix: Optional[List[List[int]]] = None
    classification_report: Optional[Dict[str, Any]] = None
    cross_validation_scores: Optional[List[float]] = None
    
    class Config:
        protected_namespaces = ()


class ModelDeployment(BaseModel):
    """Schema for model deployment configuration"""
    model_id: int
    deployment_name: str
    endpoint_url: str
    is_active: bool = True
    scaling_config: Optional[Dict[str, Any]] = None
    environment_config: Optional[Dict[str, Any]] = None
    
    class Config:
        protected_namespaces = ()
