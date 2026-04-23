"""
Dataset-related Pydantic schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class DatasetBase(BaseModel):
    """Base dataset schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    dataset_type: str = Field(..., pattern="^(dna|rna|protein|general)$")
    is_public: bool = False


class DatasetCreate(DatasetBase):
    """Schema for dataset creation"""
    pass


class DatasetUpdate(BaseModel):
    """Schema for dataset updates"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None


class DatasetResponse(DatasetBase):
    """Schema for dataset responses"""
    id: int
    user_id: int
    filename: str
    file_size: int
    file_extension: str
    processing_status: str
    is_validated: bool
    download_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    stats: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

    @validator('file_size')
    def format_file_size(cls, v):
        """Convert file size to human readable format"""
        return v


class DatasetListResponse(BaseModel):
    """Schema for paginated dataset list"""
    datasets: List[DatasetResponse]
    total: int
    skip: int
    limit: int


class DatasetPreview(BaseModel):
    """Schema for dataset preview data"""
    dataset_id: int
    preview_data: List[Dict[str, Any]]
    total_rows: int
    columns: Optional[List[str]] = None


class DatasetStats(BaseModel):
    """Schema for dataset statistics"""
    dataset_id: int
    total_rows: int = 0
    total_columns: int = 0
    file_size_bytes: int = 0
    sequence_count: Optional[int] = None
    avg_sequence_length: Optional[float] = None
    min_sequence_length: Optional[int] = None
    max_sequence_length: Optional[int] = None
    gc_content: Optional[float] = None
    n_content: Optional[float] = None
    column_types: Optional[Dict[str, str]] = None
    missing_values: Optional[Dict[str, int]] = None


class DatasetValidation(BaseModel):
    """Schema for dataset validation results"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    format_detected: Optional[str] = None
    sequence_type: Optional[str] = None
    encoding: Optional[str] = None


class QualityIssue(BaseModel):
    """Schema for sequence quality issue"""
    sequence_index: int
    problems: List[str]


class AmbiguousBasesInfo(BaseModel):
    """Schema for ambiguous bases information"""
    total_count: int
    sequences_affected: int
    percentage: float


class DatasetQualityAnalysis(BaseModel):
    """Schema for dataset quality analysis results"""
    total_sequences: int
    sequences_with_issues: int
    issues: List[QualityIssue] = []
    ambiguous_bases: Optional[AmbiguousBasesInfo] = None
    gaps: Optional[Dict[str, Any]] = None
    invalid_characters: Optional[Dict[str, int]] = None
    length_issues: Optional[Dict[str, int]] = None


class MissingDataAnalysis(BaseModel):
    """Schema for missing data analysis"""
    empty_sequences: int = 0
    sequences_with_all_N: int = 0
    sequences_mostly_gaps: int = 0
    missing_metadata_fields: Dict[str, Dict[str, Any]] = {}


class DatasetAnalysisResponse(BaseModel):
    """Schema for comprehensive dataset analysis response"""
    dataset_id: int
    dataset_type: str
    basic_stats: Dict[str, Any]
    quality_analysis: Optional[DatasetQualityAnalysis] = None
    missing_data: Optional[MissingDataAnalysis] = None
    recommendations: List[str] = []
    column_info: Optional[Dict[str, Any]] = None
    detailed_stats: Optional[Dict[str, Any]] = None
    correlation_analysis: Optional[Dict[str, Any]] = None
    distribution_analysis: Optional[Dict[str, Any]] = None
    outlier_analysis: Optional[Dict[str, Any]] = None


class DatasetVisualizationResponse(BaseModel):
    """Schema for dataset visualization response"""
    dataset_id: int
    plots: Dict[str, str]  # Plot name -> base64 encoded image
    plot_descriptions: Optional[Dict[str, str]] = None

