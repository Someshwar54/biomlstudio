"""
Pydantic schemas for model builder API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class AlgorithmInfo(BaseModel):
    """Information about an ML algorithm"""
    name: str
    type: str = Field(..., description="Algorithm type (classification, regression, clustering)")
    category: str = Field(..., description="Algorithm category (ensemble, linear, etc.)")
    description: str
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list)
    complexity: str = Field(..., description="Complexity level (low, medium, high)")


class PreprocessingStep(BaseModel):
    """Configuration for a preprocessing step"""
    name: str = Field(..., description="Name of the preprocessing step")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class ModelConfigRequest(BaseModel):
    """Request model for model configuration"""
    algorithm: str = Field(..., description="Algorithm name")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    preprocessing: List[PreprocessingStep] = Field(default_factory=list)
    task_type: str = Field(..., description="Task type (classification, regression, clustering)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "algorithm": "random_forest_classifier",
                "hyperparameters": {
                    "n_estimators": 100,
                    "max_depth": 10,
                    "random_state": 42
                },
                "preprocessing": [
                    {
                        "name": "standard_scaler",
                        "parameters": {},
                        "enabled": True
                    }
                ],
                "task_type": "classification"
            }
        }


class ModelConfigResponse(BaseModel):
    """Response model for model configuration"""
    config: Dict[str, Any]
    validation: Dict[str, Any]
    timestamp: datetime


class ModelSuggestionRequest(BaseModel):
    """Request for algorithm suggestions"""
    task_type: str = Field(..., description="ML task type")
    dataset_id: Optional[int] = None
    dataset_characteristics: Optional[Dict[str, Any]] = None
    max_suggestions: int = Field(default=5, ge=1, le=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "classification",
                "dataset_id": 123,
                "max_suggestions": 5
            }
        }


class AlgorithmSuggestion(BaseModel):
    """Individual algorithm suggestion"""
    algorithm: str
    score: float = Field(..., description="Suggestion score")
    info: AlgorithmInfo
    reasons: List[str] = Field(default_factory=list)


class ModelSuggestionResponse(BaseModel):
    """Response for algorithm suggestions"""
    suggestions: List[AlgorithmSuggestion]
    dataset_info: Dict[str, Any]
    task_type: str


class ModelValidationResponse(BaseModel):
    """Response for model configuration validation"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class TrainingParameters(BaseModel):
    """Training parameters configuration"""
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    random_state: int = Field(default=42)
    cross_validation: bool = True
    cv_folds: int = Field(default=5, ge=3, le=10)
    scale_features: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_size": 0.2,
                "random_state": 42,
                "cross_validation": True,
                "cv_folds": 5,
                "scale_features": True
            }
        }


class HyperparameterOptimizationRequest(BaseModel):
    """Request for hyperparameter optimization"""
    dataset_id: int
    model_config: ModelConfigRequest
    method: str = Field(default="grid_search", pattern="^(grid_search|random_search)$")
    cv_folds: int = Field(default=5, ge=3, le=10)
    n_iterations: int = Field(default=50, ge=10, le=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": 123,
                "model_config": {
                    "algorithm": "random_forest_classifier",
                    "hyperparameters": {},
                    "preprocessing": [],
                    "task_type": "classification"
                },
                "method": "grid_search",
                "cv_folds": 5,
                "n_iterations": 50
            }
        }


class ModelTrainingRequest(BaseModel):
    """Request for model training"""
    dataset_id: int
    model_config: ModelConfigRequest
    model_name: Optional[str] = None
    description: Optional[str] = None
    training_params: Optional[TrainingParameters] = None
    auto_optimize: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": 123,
                "model_config": {
                    "algorithm": "random_forest_classifier",
                    "hyperparameters": {
                        "n_estimators": 100,
                        "max_depth": 10
                    },
                    "preprocessing": [
                        {
                            "name": "standard_scaler",
                            "parameters": {},
                            "enabled": True
                        }
                    ],
                    "task_type": "classification"
                },
                "model_name": "My RF Classifier",
                "description": "Random Forest model for biological classification",
                "auto_optimize": True
            }
        }


class ModelTrainingResponse(BaseModel):
    """Response for model training"""
    job_id: int
    status: str
    message: str
    model_config: ModelConfigRequest
    estimated_time_minutes: int
    
    class Config:
        protected_namespaces = ()


class DatasetCharacteristics(BaseModel):
    """Dataset characteristics for algorithm suggestions"""
    n_samples: int = Field(..., description="Number of samples/rows")
    n_features: int = Field(..., description="Number of features/columns")
    file_size_mb: float = Field(..., description="File size in MB")
    dataset_type: str = Field(..., description="Type of dataset")
    has_missing_values: bool = False
    is_balanced: Optional[bool] = None
    feature_types: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "n_samples": 1000,
                "n_features": 20,
                "file_size_mb": 5.2,
                "dataset_type": "dna",
                "has_missing_values": False,
                "is_balanced": True,
                "feature_types": ["numerical", "categorical"]
            }
        }


class ModelPipelineStep(BaseModel):
    """Individual step in model pipeline"""
    step_type: str = Field(..., description="Type of step (preprocessor, model)")
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None


class ModelPipelineConfig(BaseModel):
    """Complete model pipeline configuration"""
    steps: List[ModelPipelineStep]
    task_type: str
    created_at: datetime
    created_by: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "steps": [
                    {
                        "step_type": "preprocessor",
                        "name": "standard_scaler",
                        "parameters": {},
                        "description": "Standardize features"
                    },
                    {
                        "step_type": "model",
                        "name": "random_forest_classifier",
                        "parameters": {
                            "n_estimators": 100,
                            "max_depth": 10
                        },
                        "description": "Random Forest Classifier"
                    }
                ],
                "task_type": "classification",
                "created_at": "2024-01-01T00:00:00Z",
                "created_by": "user123"
            }
        }


class ModelPerformanceMetrics(BaseModel):
    """Model performance metrics"""
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    r2_score: Optional[float] = None
    mse: Optional[float] = None
    rmse: Optional[float] = None
    cross_val_score: Optional[float] = None
    cross_val_std: Optional[float] = None


class ModelEvaluationResult(BaseModel):
    """Model evaluation results"""
    model_id: int
    metrics: ModelPerformanceMetrics
    confusion_matrix: Optional[List[List[int]]] = None
    feature_importance: Optional[Dict[str, float]] = None
    roc_curve: Optional[Dict[str, List[float]]] = None
    evaluation_dataset: str
    timestamp: datetime
    
    class Config:
        protected_namespaces = ()


class ModelComparisonRequest(BaseModel):
    """Request for model comparison"""
    model_ids: List[int] = Field(..., min_items=2, max_items=10)
    evaluation_dataset_id: int
    metrics_to_compare: List[str] = Field(default=["accuracy", "f1_score"])
    
    class Config:
        protected_namespaces = ()


class ModelComparisonResponse(BaseModel):
    """Response for model comparison"""
    models: List[ModelEvaluationResult]
    best_model_id: int
    comparison_summary: Dict[str, Any]
    timestamp: datetime
    
    class Config:
        protected_namespaces = ()


class AutoMLRequest(BaseModel):
    """Request for automated ML pipeline"""
    dataset_id: int
    task_type: str
    target_column: str
    feature_columns: Optional[List[str]] = None
    time_budget_minutes: int = Field(default=30, ge=5, le=180)
    optimization_metric: str = Field(default="accuracy")
    max_models: int = Field(default=10, ge=3, le=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": 123,
                "task_type": "classification",
                "target_column": "species",
                "feature_columns": ["feature1", "feature2", "feature3"],
                "time_budget_minutes": 30,
                "optimization_metric": "accuracy",
                "max_models": 10
            }
        }


class AutoMLResponse(BaseModel):
    """Response for automated ML"""
    job_id: int
    status: str
    message: str
    estimated_completion: datetime
    models_to_try: List[str]
