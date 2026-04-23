"""
Pydantic schemas for dataset preprocessing API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class PreprocessingStep(BaseModel):
    """Configuration for a single preprocessing step"""
    name: str = Field(..., description="Name of the preprocessing step")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "handle_missing_values",
                "parameters": {
                    "strategy": "mean",
                    "columns": ["feature1", "feature2"]
                },
                "enabled": True
            }
        }


class PreprocessingConfigRequest(BaseModel):
    """Request for dataset preprocessing configuration"""
    steps: List[PreprocessingStep] = Field(..., description="List of preprocessing steps")
    output_name: Optional[str] = None
    save_intermediate: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "steps": [
                    {
                        "name": "handle_missing_values",
                        "parameters": {"strategy": "mean"},
                        "enabled": True
                    },
                    {
                        "name": "feature_scaling",
                        "parameters": {"method": "standard"},
                        "enabled": True
                    }
                ],
                "output_name": "preprocessed_dataset",
                "save_intermediate": False
            }
        }


class PreprocessingResponse(BaseModel):
    """Response for preprocessing operations"""
    job_id: int
    status: str
    message: str
    estimated_time_minutes: int


class PreprocessingSuggestion(BaseModel):
    """Individual preprocessing suggestion"""
    name: str
    reason: str
    parameters: Dict[str, Any]
    priority: str = Field(default="medium", description="Priority level (low, medium, high)")


class PreprocessingSuggestionResponse(BaseModel):
    """Response for preprocessing suggestions"""
    dataset_id: int
    task_type: str
    suggestions: Dict[str, List[PreprocessingSuggestion]]
    timestamp: datetime


class BiologicalFeatureExtractionRequest(BaseModel):
    """Request for biological feature extraction"""
    sequence_column: str = Field(default="sequence", description="Column containing sequences")
    sequence_type: str = Field(..., description="Type of sequence (dna, rna, protein)")
    extract_composition: bool = True
    extract_physicochemical: bool = True
    extract_kmers: bool = False
    kmer_size: int = Field(default=3, ge=2, le=6)
    
    class Config:
        json_schema_extra = {
            "example": {
                "sequence_column": "sequence",
                "sequence_type": "dna",
                "extract_composition": True,
                "extract_physicochemical": True,
                "extract_kmers": True,
                "kmer_size": 3
            }
        }


class DataQualityMetrics(BaseModel):
    """Data quality metrics"""
    completeness_score: float = Field(..., ge=0, le=1)
    consistency_score: float = Field(..., ge=0, le=1)
    validity_score: float = Field(..., ge=0, le=1)
    uniqueness_score: float = Field(..., ge=0, le=1)
    overall_score: float = Field(..., ge=0, le=1)


class DataQualityIssue(BaseModel):
    """Individual data quality issue"""
    type: str = Field(..., description="Type of issue")
    severity: str = Field(..., description="Severity level (low, medium, high)")
    description: str
    affected_columns: List[str] = Field(default_factory=list)
    suggested_fix: Optional[str] = None


class DataQualityReport(BaseModel):
    """Comprehensive data quality report"""
    dataset_id: int
    metrics: DataQualityMetrics
    issues: List[DataQualityIssue]
    statistics: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime


class FeatureEngineeringOperation(BaseModel):
    """Feature engineering operation configuration"""
    type: str = Field(..., description="Type of operation")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    target_columns: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "polynomial_features",
                "parameters": {"degree": 2},
                "target_columns": ["feature1", "feature2"]
            }
        }


class DataTransformationRequest(BaseModel):
    """Request for data transformation"""
    transformations: List[FeatureEngineeringOperation]
    target_column: Optional[str] = None
    validation_split: float = Field(default=0.2, ge=0.1, le=0.5)
    
    class Config:
        json_schema_extra = {
            "example": {
                "transformations": [
                    {
                        "type": "polynomial_features",
                        "parameters": {"degree": 2},
                        "target_columns": ["feature1", "feature2"]
                    },
                    {
                        "type": "log_transform",
                        "parameters": {},
                        "target_columns": ["feature3"]
                    }
                ],
                "target_column": "target",
                "validation_split": 0.2
            }
        }


class OutlierDetectionConfig(BaseModel):
    """Configuration for outlier detection"""
    method: str = Field(..., description="Outlier detection method")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    columns: List[str] = Field(default_factory=list)
    action: str = Field(default="remove", description="Action to take (remove, flag, transform)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "method": "iqr",
                "parameters": {"multiplier": 1.5},
                "columns": ["feature1", "feature2"],
                "action": "remove"
            }
        }


class FeatureSelectionConfig(BaseModel):
    """Configuration for feature selection"""
    method: str = Field(..., description="Feature selection method")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    target_column: str
    n_features: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "method": "k_best",
                "parameters": {"score_func": "f_classif"},
                "target_column": "target",
                "n_features": 10
            }
        }


class DimensionalityReductionConfig(BaseModel):
    """Configuration for dimensionality reduction"""
    method: str = Field(..., description="Dimensionality reduction method")
    n_components: int = Field(..., ge=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "method": "pca",
                "n_components": 10,
                "parameters": {"random_state": 42}
            }
        }


class DataValidationRule(BaseModel):
    """Data validation rule"""
    column: str
    rule_type: str = Field(..., description="Type of validation rule")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    error_message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "column": "age",
                "rule_type": "range",
                "parameters": {"min": 0, "max": 120},
                "error_message": "Age must be between 0 and 120"
            }
        }


class DataValidationRequest(BaseModel):
    """Request for data validation"""
    rules: List[DataValidationRule]
    stop_on_error: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "rules": [
                    {
                        "column": "age",
                        "rule_type": "range",
                        "parameters": {"min": 0, "max": 120},
                        "error_message": "Age must be between 0 and 120"
                    }
                ],
                "stop_on_error": False
            }
        }


class DataValidationResult(BaseModel):
    """Result of data validation"""
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    
    
class SequenceAnalysisConfig(BaseModel):
    """Configuration for sequence analysis"""
    sequence_column: str = Field(default="sequence")
    sequence_type: str = Field(..., description="dna, rna, or protein")
    analyses: List[str] = Field(..., description="List of analyses to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "sequence_column": "sequence",
                "sequence_type": "dna",
                "analyses": ["composition", "gc_content", "motifs", "orfs"],
                "parameters": {
                    "min_orf_length": 100,
                    "genetic_code": 1
                }
            }
        }


class SequenceAnalysisResult(BaseModel):
    """Result of sequence analysis"""
    analysis_type: str
    results: Dict[str, Any]
    statistics: Dict[str, Any]
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)


class BatchProcessingRequest(BaseModel):
    """Request for batch processing multiple datasets"""
    dataset_ids: List[int] = Field(..., min_items=1, max_items=50)
    preprocessing_config: PreprocessingConfigRequest
    merge_results: bool = False
    output_format: str = Field(default="csv", description="Output format for results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dataset_ids": [1, 2, 3],
                "preprocessing_config": {
                    "steps": [
                        {
                            "name": "handle_missing_values",
                            "parameters": {"strategy": "mean"},
                            "enabled": True
                        }
                    ]
                },
                "merge_results": False,
                "output_format": "csv"
            }
        }


class BatchProcessingResponse(BaseModel):
    """Response for batch processing"""
    job_id: int
    status: str
    message: str
    dataset_count: int
    estimated_time_minutes: int
