"""
SHAP (SHapley Additive exPlanations) Schemas
Pydantic models for SHAP explanation requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SHAPExplanationRequest(BaseModel):
    """Request schema for generating SHAP explanations"""
    model_id: Optional[int] = Field(None, description="Model ID from database")
    model_path: Optional[str] = Field(None, description="Direct path to model file")
    dataset_id: Optional[int] = Field(None, description="Dataset ID for explanation")
    sample_indices: Optional[List[int]] = Field(None, description="Specific sample indices to explain")
    max_display: int = Field(10, ge=5, le=50, description="Maximum features to display")
    sample_size: int = Field(100, ge=10, le=1000, description="Background dataset size")
    
    class Config:
        protected_namespaces = ()


class FeatureContribution(BaseModel):
    """Single feature's contribution to a prediction"""
    feature: str
    value: float
    shap_value: float
    contribution: str  # 'positive' or 'negative'


class SinglePredictionExplanation(BaseModel):
    """SHAP explanation for a single prediction"""
    prediction: float
    probability: Optional[List[float]] = None
    contributions: List[FeatureContribution]
    base_value: Optional[float] = None


class PredictionExplanationRequest(BaseModel):
    """Request schema for explaining a single prediction"""
    model_id: Optional[int] = None
    model_path: Optional[str] = None
    input_data: Dict[str, Any] = Field(..., description="Feature values for prediction")
    dataset_id: Optional[int] = Field(None, description="Dataset for background comparison")
    
    class Config:
        protected_namespaces = ()


class TopFeature(BaseModel):
    """Top feature information from SHAP analysis"""
    feature: str
    importance: float
    mean_shap: float
    std_shap: float


class SHAPSummary(BaseModel):
    """Summary statistics from SHAP analysis"""
    feature_importance: Dict[str, float]
    top_features: List[TopFeature]
    total_features: int


class SHAPPlots(BaseModel):
    """SHAP visualization plots as base64 images"""
    summary_plot: Optional[str] = Field(None, description="SHAP summary plot (beeswarm)")
    bar_plot: Optional[str] = Field(None, description="Mean absolute SHAP values bar plot")
    waterfall_plot: Optional[str] = Field(None, description="Waterfall plot for single prediction")
    force_plot: Optional[str] = Field(None, description="Force plot for single prediction")


class SHAPExplanationResponse(BaseModel):
    """Response schema for SHAP explanations"""
    success: bool
    shap_values: Optional[List[List[float]]] = Field(None, description="SHAP values matrix")
    feature_names: Optional[List[str]] = None
    plots: Optional[SHAPPlots] = None
    summary: Optional[SHAPSummary] = None
    explainer_type: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        protected_namespaces = ()


class PredictionExplanationResponse(BaseModel):
    """Response schema for single prediction explanation"""
    success: bool
    explanation: Optional[SinglePredictionExplanation] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        protected_namespaces = ()


class JobSHAPRequest(BaseModel):
    """Request to generate SHAP explanations for a completed job"""
    job_id: int = Field(..., description="Job ID with trained model")
    max_display: int = Field(10, ge=5, le=50)
    sample_size: int = Field(100, ge=10, le=1000)
    
    class Config:
        protected_namespaces = ()


class ModelComparisonSHAPRequest(BaseModel):
    """Request to compare SHAP explanations across models"""
    model_ids: List[int] = Field(..., min_items=2, max_items=5)
    dataset_id: int
    max_display: int = Field(10, ge=5, le=30)
    
    class Config:
        protected_namespaces = ()
