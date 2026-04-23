"""
Dataset management endpoints for uploading, processing, and managing biological datasets
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.api.deps import (
    get_current_active_user, get_db, CommonQueryParams, 
    validate_file_upload
)
from app.core.config import settings
from app.core.exceptions import BioMLException
from app.models.dataset import Dataset
from app.models.user import User
from app.schemas.dataset import (
    DatasetResponse, DatasetUpdate, DatasetListResponse,
    DatasetPreview, DatasetStats, DatasetAnalysisResponse,
    DatasetVisualizationResponse
)
from app.services.dataset_service import DatasetService
from app.services.storage_service import StorageService
from app.services.visualization_service import VisualizationService
from app.utils.bioinformatics import (
    validate_biological_file, convert_fasta_to_csv, 
    generate_sequence_report
)
from app.utils.file_handlers import get_file_info, generate_unique_filename

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    dataset_type: str = Form("general"),
    is_public: bool = Form(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Upload a biological dataset file.
    
    Args:
        file: Uploaded file
        name: Dataset name
        description: Dataset description
        dataset_type: Type of dataset (dna, protein, rna, general)
        is_public: Whether dataset should be public
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DatasetResponse: Created dataset information
    """
    # Validate file
    file_info = get_file_info(file.filename)
    # Strip leading '.' to match settings.ALLOWED_FILE_EXTENSIONS entries
    file_ext = file_info['extension'].lstrip('.') if file_info.get('extension') else ''
    await validate_file_upload(file.size, file_ext)
    
    # Note: Biological file validation will be performed after saving the file,
    # so the validator can work with a filesystem path rather than an UploadFile
    
    try:
        # Generate unique filename
        unique_filename = generate_unique_filename(
            file.filename, 
            current_user.id
        )
        
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR) / str(current_user.id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Validate biological file format if needed (after saving so we have a path)
        if dataset_type in ['dna', 'protein', 'rna']:
            validation = validate_biological_file(str(file_path), dataset_type)
            if not validation.get('is_valid', False):
                # Remove invalid file and raise an error
                if file_path.exists():
                    file_path.unlink()
                raise BioMLException(
                    message=f"Invalid {dataset_type} file format",
                    status_code=400
                )

        # Create dataset record
        dataset_service = DatasetService()
        
        # Analyze dataset
        stats = await dataset_service.analyze_dataset(file_path, dataset_type)
        
        db_dataset = Dataset(
            user_id=current_user.id,
            name=name,
            description=description,
            dataset_type=dataset_type,
            file_path=str(file_path),
            filename=file.filename,
            file_size=file.size,
            file_extension=file_info['extension'],
            stats=stats,
            is_public=is_public,
            created_at=datetime.utcnow()
        )
        
        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset)
        
        logger.info(f"Dataset uploaded: {db_dataset.id} by user {current_user.id}")
        
        return DatasetResponse.from_orm(db_dataset)
        
    except Exception as e:
        logger.error(f"Error uploading dataset: {e}")
        # Clean up file if database save failed
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        
        raise BioMLException(
            message="Failed to upload dataset",
            status_code=500
        )


@router.get("/", response_model=DatasetListResponse)
async def list_datasets(
    commons: CommonQueryParams = Depends(CommonQueryParams),
    dataset_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List user's datasets with filtering and pagination.
    
    Args:
        commons: Common query parameters
        dataset_type: Filter by dataset type
        is_public: Filter by public/private datasets
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DatasetListResponse: Paginated dataset list
    """
    query = db.query(Dataset).filter(
        (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
    )
    
    # Apply filters
    if dataset_type:
        query = query.filter(Dataset.dataset_type == dataset_type)
    if is_public is not None:
        query = query.filter(Dataset.is_public == is_public)
    
    # Apply sorting
    if commons.sort_order == "asc":
        query = query.order_by(asc(getattr(Dataset, commons.sort_by, Dataset.created_at)))
    else:
        query = query.order_by(desc(getattr(Dataset, commons.sort_by, Dataset.created_at)))
    
    # Apply pagination first for better performance
    datasets = query.offset(commons.skip).limit(commons.limit).all()
    
    # Get total count (this is expensive, so we do it after pagination)
    total = query.count()
    
    return DatasetListResponse(
        datasets=[DatasetResponse.from_orm(dataset) for dataset in datasets],
        total=total,
        skip=commons.skip,
        limit=commons.limit
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific dataset details.
    
    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DatasetResponse: Dataset details
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    return DatasetResponse.from_orm(dataset)


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
async def preview_dataset(
    dataset_id: int,
    rows: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Preview dataset content (first few rows/sequences).
    
    Args:
        dataset_id: Dataset ID
        rows: Number of rows/sequences to preview
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DatasetPreview: Dataset preview data
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    dataset_service = DatasetService()
    preview_data = await dataset_service.preview_dataset(
        dataset.file_path,
        dataset.dataset_type,
        rows=rows
    )
    
    # Extract columns from preview data
    columns = list(preview_data[0].keys()) if preview_data else []
    
    logger.info(f"Preview for dataset {dataset_id}: {len(preview_data)} rows, columns: {columns}")
    
    return DatasetPreview(
        dataset_id=dataset_id,
        preview_data=preview_data,
        total_rows=dataset.stats.get('total_rows', 0) if dataset.stats else 0,
        columns=columns
    )


@router.get("/{dataset_id}/stats", response_model=DatasetStats)
async def get_dataset_stats(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed dataset statistics.
    
    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DatasetStats: Dataset statistics
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    return DatasetStats(
        dataset_id=dataset_id,
        **dataset.stats if dataset.stats else {}
    )


@router.get("/{dataset_id}/download")
async def download_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Download dataset file.
    
    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        StreamingResponse: Dataset file download
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    file_path = Path(dataset.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file not found"
        )
    
    async def file_generator():
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(settings.UPLOAD_CHUNK_SIZE):
                yield chunk
    
    return StreamingResponse(
        file_generator(),
        media_type='application/octet-stream',
        headers={
            "Content-Disposition": f"attachment; filename={dataset.filename}"
        }
    )


@router.post("/convert/fasta-to-csv")
async def convert_fasta_endpoint(
    file: UploadFile = File(...),
    add_composition: bool = Form(False),
    add_kmers: bool = Form(False),
    kmer_size: int = Form(3),
    max_sequences: int = Form(0),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Convert a FASTA file into CSV with optional features (composition and k-mers).

    Returns a JSON object with the output path and columns.
    """
    try:
        # Save uploaded FASTA to a temp user folder
        upload_dir = Path(settings.UPLOAD_DIR) / str(current_user.id) / "conversions"
        upload_dir.mkdir(parents=True, exist_ok=True)
        fasta_path = upload_dir / (Path(file.filename).stem + ".fasta")

        async with aiofiles.open(fasta_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Prepare output path
        csv_path = upload_dir / (Path(file.filename).stem + ".csv")

        config = {
            'add_composition': add_composition,
            'add_kmers': add_kmers,
            'kmer_size': kmer_size,
            'max_sequences': max_sequences if max_sequences > 0 else None,
        }

        result = convert_fasta_to_csv(str(fasta_path), str(csv_path), config)
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Conversion failed'))

        return {
            'message': 'Conversion successful',
            'output_path': result['output_path'],
            'sequences_converted': result['sequences_converted'],
            'columns': result['columns'],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting FASTA to CSV: {e}")
        raise HTTPException(status_code=500, detail="Internal error during conversion")


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: int,
    dataset_update: DatasetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update dataset metadata.
    
    Args:
        dataset_id: Dataset ID
        dataset_update: Dataset update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DatasetResponse: Updated dataset information
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Apply updates
    for field, value in dataset_update.dict(exclude_unset=True).items():
        setattr(dataset, field, value)
    
    dataset.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(dataset)
    
    logger.info(f"Dataset updated: {dataset.id}")
    
    return DatasetResponse.from_orm(dataset)


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete dataset and its file.
    
    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Success message
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Delete file
    file_path = Path(dataset.file_path)
    if file_path.exists():
        file_path.unlink()
    
    # Delete dataset record
    db.delete(dataset)
    db.commit()
    
    logger.info(f"Dataset deleted: {dataset_id}")
    
    return {"message": "Dataset deleted successfully"}


@router.post("/{dataset_id}/validate")
async def validate_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate dataset format and content.
    
    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Validation results
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    dataset_service = DatasetService()
    validation_results = await dataset_service.validate_dataset(
        dataset.file_path,
        dataset.dataset_type
    )
    
    return {
        "dataset_id": dataset_id,
        "validation_results": validation_results,
        "timestamp": datetime.utcnow()
    }


@router.get("/{dataset_id}/analyze", response_model=DatasetAnalysisResponse)
async def analyze_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Perform comprehensive analysis on a dataset.
    
    Provides detailed insights including:
    - Missing data detection
    - DNA/RNA sequence quality metrics
    - Data completeness analysis
    - Statistical summaries
    - Recommendations for data cleaning
    
    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DatasetAnalysisResponse: Comprehensive analysis results
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    try:
        file_path = Path(dataset.file_path)
        
        # Perform comprehensive analysis based on dataset type
        if dataset.dataset_type in ['dna', 'rna', 'protein']:
            # Biological sequence analysis
            report = generate_sequence_report(str(file_path), dataset.dataset_type)
            
            # Convert FASTA to CSV for additional analysis
            import tempfile
            from app.utils.bioinformatics import convert_fasta_to_csv
            
            # Create temporary CSV for enhanced analysis
            temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w')
            temp_csv.close()
            
            try:
                conversion_config = {
                    'add_composition': True,
                    'add_kmers': True,
                    'kmer_size': 3,
                    'max_sequences': 10000
                }
                
                conversion_result = convert_fasta_to_csv(str(file_path), temp_csv.name, conversion_config)
                
                if conversion_result.get('success'):
                    # Load converted CSV for enhanced analysis
                    df = pd.read_csv(temp_csv.name)
                    
                    # Remove sequence metadata columns for numerical analysis
                    metadata_cols = ['sequence_id', 'sequence', 'sequence_type']
                    numeric_df = df.drop(columns=[col for col in metadata_cols if col in df.columns], errors='ignore')
                    
                    # Enhanced analysis on numeric features
                    detailed_stats = {}
                    correlation_analysis = {}
                    distribution_analysis = {}
                    outlier_analysis = {}
                    
                    numeric_cols = numeric_df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        try:
                            from scipy import stats
                            has_scipy = True
                        except ImportError:
                            has_scipy = False
                            logger.warning("scipy not available, skipping advanced distribution analysis")
                        
                        # Helper function to handle NaN values
                        def safe_float(value):
                            if pd.isna(value) or np.isinf(value):
                                return None
                            return float(value)
                        
                        # Detailed statistics
                        for col in numeric_cols:
                            col_data = numeric_df[col].dropna()
                            if len(col_data) > 0:
                                detailed_stats[col] = {
                                    'mean': safe_float(col_data.mean()),
                                    'std': safe_float(col_data.std()),
                                    'min': safe_float(col_data.min()),
                                    'max': safe_float(col_data.max()),
                                    '25%': safe_float(col_data.quantile(0.25)),
                                    '50%': safe_float(col_data.quantile(0.5)),
                                    '75%': safe_float(col_data.quantile(0.75))
                                }
                                
                                # Distribution analysis
                                if len(col_data) > 10 and has_scipy:
                                    try:
                                        skewness = safe_float(stats.skew(col_data))
                                        kurtosis_val = safe_float(stats.kurtosis(col_data))
                                        
                                        if skewness is not None and kurtosis_val is not None:
                                            dist_type = "Normal"
                                            if abs(skewness) > 1:
                                                dist_type = "Right-skewed" if skewness > 0 else "Left-skewed"
                                            elif abs(kurtosis_val) > 3:
                                                dist_type = "Heavy-tailed" if kurtosis_val > 0 else "Light-tailed"
                                            
                                            distribution_analysis[col] = {
                                                'skewness': skewness,
                                                'kurtosis': kurtosis_val,
                                                'distribution_type': dist_type
                                            }
                                    except:
                                        pass
                                
                                # Outlier analysis
                                if len(col_data) > 10:
                                    Q1 = col_data.quantile(0.25)
                                    Q3 = col_data.quantile(0.75)
                                    IQR = Q3 - Q1
                                    lower_bound = Q1 - 1.5 * IQR
                                    upper_bound = Q3 + 1.5 * IQR
                                    
                                    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                                    outlier_analysis[col] = {
                                        'count': len(outliers),
                                        'percentage': safe_float((len(outliers) / len(col_data)) * 100),
                                        'method': 'IQR',
                                        'values': [safe_float(x) for x in outliers.tolist()[:10] if safe_float(x) is not None]
                                    }
                        
                        # Correlation analysis for sequence features
                        if len(numeric_cols) > 1:
                            try:
                                corr_matrix = numeric_df[numeric_cols].corr()
                                
                                # Find high correlations
                                high_correlations = []
                                feature_relationships = {}
                                
                                for i, col1 in enumerate(numeric_cols):
                                    relationships = {
                                        'strongest_positive': None,
                                        'strongest_negative': None,
                                        'average_correlation': 0
                                    }
                                    
                                    correlations = []
                                    for j, col2 in enumerate(numeric_cols):
                                        if i != j:
                                            corr_val = corr_matrix.loc[col1, col2]
                                            if not pd.isna(corr_val):
                                                correlations.append(abs(corr_val))
                                                
                                                if abs(corr_val) > 0.7:
                                                    high_correlations.append({
                                                        'feature1': col1,
                                                        'feature2': col2,
                                                        'correlation': safe_float(corr_val)
                                                    })
                                                
                                                if corr_val > 0 and (relationships['strongest_positive'] is None or 
                                                                   corr_val > relationships['strongest_positive']['correlation']):
                                                    relationships['strongest_positive'] = {
                                                        'feature': col2,
                                                        'correlation': safe_float(corr_val)
                                                    }
                                                elif corr_val < 0 and (relationships['strongest_negative'] is None or 
                                                                     corr_val < relationships['strongest_negative']['correlation']):
                                                    relationships['strongest_negative'] = {
                                                        'feature': col2,
                                                        'correlation': safe_float(corr_val)
                                                    }
                                    
                                    if correlations:
                                        avg_corr = safe_float(np.mean(correlations))
                                        if avg_corr is not None:
                                            relationships['average_correlation'] = avg_corr
                                    feature_relationships[col1] = relationships
                                
                                # Remove duplicate high correlations
                                seen_pairs = set()
                                unique_high_correlations = []
                                for item in high_correlations:
                                    pair = tuple(sorted([item['feature1'], item['feature2']]))
                                    if pair not in seen_pairs:
                                        seen_pairs.add(pair)
                                        unique_high_correlations.append(item)
                                
                                correlation_analysis = {
                                    'high_correlations': unique_high_correlations,
                                    'matrix_summary': {
                                        'high_correlations': len(unique_high_correlations),
                                        'moderate_correlations': len([c for c in high_correlations if 0.3 < abs(c['correlation']) < 0.7]),
                                        'low_correlations': len([c for c in high_correlations if abs(c['correlation']) < 0.3])
                                    },
                                    'feature_relationships': feature_relationships
                                }
                            except Exception as e:
                                logger.warning(f"Correlation analysis failed for biological data: {e}")
                
                # Clean up temp file
                Path(temp_csv.name).unlink(missing_ok=True)
                
            except Exception as e:
                logger.warning(f"Enhanced analysis failed for biological data: {e}")
                # Clean up temp file
                Path(temp_csv.name).unlink(missing_ok=True)
            
            return DatasetAnalysisResponse(
                dataset_id=dataset_id,
                dataset_type=dataset.dataset_type,
                basic_stats=report.get('basic_stats', {}),
                quality_analysis=report.get('quality_analysis'),
                missing_data=report.get('missing_data'),
                recommendations=report.get('recommendations', []),
                detailed_stats=detailed_stats if 'detailed_stats' in locals() else None,
                correlation_analysis=correlation_analysis if 'correlation_analysis' in locals() else None,
                distribution_analysis=distribution_analysis if 'distribution_analysis' in locals() else None,
                outlier_analysis=outlier_analysis if 'outlier_analysis' in locals() else None
            )
        else:
            # General dataset analysis
            try:
                from scipy import stats
                has_scipy = True
            except ImportError:
                has_scipy = False
                logger.warning("scipy not available, skipping advanced distribution analysis")
            
            # Detect delimiter
            with open(file_path, 'r') as f:
                first_line = f.readline()
                delimiter = '\t' if '\t' in first_line else ','
            
            df = pd.read_csv(file_path, delimiter=delimiter, nrows=10000)
            
            # Calculate basic statistics
            basic_stats = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': list(df.columns),
                'column_types': df.dtypes.astype(str).to_dict(),
                'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
                'categorical_columns': df.select_dtypes(include=['object']).columns.tolist()
            }
            
            # Missing data analysis
            missing_info = {}
            non_null_counts = {}
            unique_counts = {}
            data_types = {}
            
            for col in df.columns:
                null_count = df[col].isnull().sum()
                non_null_counts[col] = int(len(df) - null_count)
                unique_counts[col] = int(df[col].nunique())
                data_types[col] = str(df[col].dtype)
                
                if null_count > 0:
                    missing_info[col] = {
                        'count': int(null_count),
                        'percentage': float((null_count / len(df)) * 100)
                    }
            
            # Column information
            column_info = {
                'missing_values': missing_info,
                'non_null_counts': non_null_counts,
                'unique_counts': unique_counts,
                'data_types': data_types
            }
            
            # Detailed statistical analysis
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            detailed_stats = {}
            distribution_analysis = {}
            
            if len(numeric_cols) > 0:
                # Helper function to handle NaN values
                def safe_float(value):
                    if pd.isna(value) or np.isinf(value):
                        return None
                    return float(value)
                
                desc_stats = df[numeric_cols].describe()
                for col in numeric_cols:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        detailed_stats[col] = {
                            'mean': safe_float(col_data.mean()),
                            'std': safe_float(col_data.std()),
                            'min': safe_float(col_data.min()),
                            'max': safe_float(col_data.max()),
                            '25%': safe_float(col_data.quantile(0.25)),
                            '50%': safe_float(col_data.quantile(0.5)),
                            '75%': safe_float(col_data.quantile(0.75))
                        }
                        
                        # Distribution analysis
                        if len(col_data) > 10 and has_scipy:
                            try:
                                skewness = safe_float(stats.skew(col_data))
                                kurtosis_val = safe_float(stats.kurtosis(col_data))
                                
                                if skewness is not None and kurtosis_val is not None:
                                    # Simple distribution type detection
                                    dist_type = "Normal"
                                    if abs(skewness) > 1:
                                        dist_type = "Right-skewed" if skewness > 0 else "Left-skewed"
                                    elif abs(kurtosis_val) > 3:
                                        dist_type = "Heavy-tailed" if kurtosis_val > 0 else "Light-tailed"
                                    
                                    distribution_analysis[col] = {
                                        'skewness': skewness,
                                        'kurtosis': kurtosis_val,
                                        'distribution_type': dist_type
                                    }
                            except:
                                pass
            
            # Outlier analysis using IQR method
            outlier_analysis = {}
            for col in numeric_cols:
                col_data = df[col].dropna()
                if len(col_data) > 10:
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                    outlier_analysis[col] = {
                        'count': len(outliers),
                        'percentage': safe_float((len(outliers) / len(col_data)) * 100),
                        'method': 'IQR',
                        'values': [safe_float(x) for x in outliers.tolist()[:10] if safe_float(x) is not None]
                    }
            
            # Correlation analysis
            correlation_analysis = {}
            if len(numeric_cols) > 1:
                try:
                    corr_matrix = df[numeric_cols].corr()
                    
                    # Find high correlations
                    high_correlations = []
                    feature_relationships = {}
                    
                    for i, col1 in enumerate(numeric_cols):
                        relationships = {
                            'strongest_positive': None,
                            'strongest_negative': None,
                            'average_correlation': 0
                        }
                        
                        correlations = []
                        for j, col2 in enumerate(numeric_cols):
                            if i != j:
                                corr_val = corr_matrix.loc[col1, col2]
                                if not pd.isna(corr_val):
                                    correlations.append(abs(corr_val))
                                    
                                    # Check for high correlation
                                    if abs(corr_val) > 0.7:
                                        high_correlations.append({
                                            'feature1': col1,
                                            'feature2': col2,
                                            'correlation': safe_float(corr_val)
                                        })
                                    
                                    # Track strongest relationships
                                    if corr_val > 0 and (relationships['strongest_positive'] is None or 
                                                       corr_val > relationships['strongest_positive']['correlation']):
                                        relationships['strongest_positive'] = {
                                            'feature': col2,
                                            'correlation': safe_float(corr_val)
                                        }
                                    elif corr_val < 0 and (relationships['strongest_negative'] is None or 
                                                         corr_val < relationships['strongest_negative']['correlation']):
                                        relationships['strongest_negative'] = {
                                            'feature': col2,
                                            'correlation': safe_float(corr_val)
                                        }
                        
                        if correlations:
                            avg_corr = safe_float(np.mean(correlations))
                            if avg_corr is not None:
                                relationships['average_correlation'] = avg_corr
                        feature_relationships[col1] = relationships
                    
                    # Remove duplicate high correlations
                    seen_pairs = set()
                    unique_high_correlations = []
                    for item in high_correlations:
                        pair = tuple(sorted([item['feature1'], item['feature2']]))
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            unique_high_correlations.append(item)
                    
                    # Matrix summary
                    matrix_summary = {
                        'high_correlations': len(unique_high_correlations),
                        'moderate_correlations': len([c for c in high_correlations if 0.3 < abs(c['correlation']) < 0.7]),
                        'low_correlations': len([c for c in high_correlations if abs(c['correlation']) < 0.3])
                    }
                    
                    correlation_analysis = {
                        'high_correlations': unique_high_correlations,
                        'matrix_summary': matrix_summary,
                        'feature_relationships': feature_relationships
                    }
                except Exception as e:
                    logger.warning(f"Correlation analysis failed: {e}")
            
            # Enhanced recommendations
            recommendations = []
            if missing_info:
                total_missing_pct = sum(info['percentage'] for info in missing_info.values()) / len(missing_info)
                if total_missing_pct > 20:
                    recommendations.append("High percentage of missing data detected - consider imputation or removal")
                elif total_missing_pct > 5:
                    recommendations.append("Some missing data present - review data collection process")
                else:
                    recommendations.append("Missing data is minimal and manageable")
            
            if len(df.columns) > 100:
                recommendations.append("High dimensionality detected - consider feature selection or dimensionality reduction")
            elif len(df.columns) > 50:
                recommendations.append("Moderate number of features - feature selection may improve model performance")
            
            if len(numeric_cols) == 0:
                recommendations.append("No numeric columns detected - consider feature encoding for categorical variables")
            
            # Check for outliers
            outlier_cols = [col for col, analysis in outlier_analysis.items() if analysis.get('percentage') and analysis['percentage'] > 5]
            if outlier_cols:
                recommendations.append(f"Significant outliers detected in {len(outlier_cols)} columns - consider outlier treatment")
            
            # Dataset size recommendations
            if len(df) < 1000:
                recommendations.append("Small dataset size - consider data augmentation or collecting more samples")
            elif len(df) > 100000:
                recommendations.append("Large dataset - consider sampling for faster prototyping")
            
            return DatasetAnalysisResponse(
                dataset_id=dataset_id,
                dataset_type=dataset.dataset_type,
                basic_stats=basic_stats,
                column_info=column_info,
                detailed_stats=detailed_stats,
                correlation_analysis=correlation_analysis,
                distribution_analysis=distribution_analysis,
                outlier_analysis=outlier_analysis,
                recommendations=recommendations
            )
            
    except Exception as e:
        logger.error(f"Error analyzing dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze dataset: {str(e)}"
        )


@router.get("/{dataset_id}/visualize", response_model=DatasetVisualizationResponse)
async def visualize_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate visualizations for dataset analysis.
    
    Creates various plots including:
    - Distribution charts
    - Missing data heatmaps
    - Correlation matrices
    - GC content distribution (for DNA/RNA)
    - Sequence quality plots
    
    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DatasetVisualizationResponse: Visualization plots as base64 images
    """
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    try:
        file_path = Path(dataset.file_path)
        viz_service = VisualizationService()
        
        # Load data as DataFrame for visualization
        if dataset.dataset_type in ['dna', 'rna', 'protein']:
            # For biological data, create a DataFrame from sequences
            from Bio import SeqIO
            import pandas as pd
            
            sequences_data = []
            with open(file_path, 'r') as handle:
                for record in SeqIO.parse(handle, "fasta"):
                    sequences_data.append({
                        'id': record.id,
                        'length': len(record.seq),
                        'sequence': str(record.seq)[:100]  # Truncate for display
                    })
            
            df = pd.DataFrame(sequences_data)
            
            # Generate visualizations with sequence stats
            plots = viz_service.generate_dataset_visualizations(
                df=df,
                dataset_type=dataset.dataset_type,
                sequence_stats=dataset.stats
            )
        else:
            # General dataset
            import pandas as pd
            
            with open(file_path, 'r') as f:
                first_line = f.readline()
                delimiter = '\t' if '\t' in first_line else ','
            
            df = pd.read_csv(file_path, delimiter=delimiter, nrows=5000)
            
            plots = viz_service.generate_dataset_visualizations(
                df=df,
                dataset_type=dataset.dataset_type
            )
        
        # Add plot descriptions
        plot_descriptions = {
            'missing_data_heatmap': 'Heatmap showing missing data patterns across features',
            'distribution_plots': 'Distribution of numeric features',
            'correlation_heatmap': 'Correlation matrix between numeric features',
            'gc_content_distribution': 'GC content distribution across sequences',
            'nucleotide_composition': 'Nucleotide composition analysis',
            'length_distribution': 'Sequence length distribution'
        }
        
        return DatasetVisualizationResponse(
            dataset_id=dataset_id,
            plots=plots,
            plot_descriptions={k: v for k, v in plot_descriptions.items() if k in plots}
        )
        
    except Exception as e:
        logger.error(f"Error generating visualizations for dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate visualizations: {str(e)}"
        )

