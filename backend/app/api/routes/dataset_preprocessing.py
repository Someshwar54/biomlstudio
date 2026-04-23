"""
Dataset preprocessing endpoints for advanced data transformation
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.exceptions import BioMLException
from app.models.dataset import Dataset
from app.models.job import JobType
from app.models.user import User
from app.schemas.dataset_preprocessing import (
    PreprocessingConfigRequest, PreprocessingResponse,
    PreprocessingSuggestionResponse, BiologicalFeatureExtractionRequest,
    DataQualityReport, DataTransformationRequest
)
from app.services.enhanced_dataset_service import enhanced_dataset_service
from app.services.job_service import JobService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{dataset_id}/preprocess", response_model=PreprocessingResponse)
async def preprocess_dataset(
    dataset_id: int,
    config: PreprocessingConfigRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Apply advanced preprocessing to a dataset.
    
    Args:
        dataset_id: Dataset ID to preprocess
        config: Preprocessing configuration
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Preprocessing job information
    """
    try:
        # Validate dataset access
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Create preprocessing job
        job_service = JobService()
        job = await job_service.create_job(
            db=db,
            user_id=current_user.id,
            job_type=JobType.PREPROCESSING,
            name=f"Preprocess {dataset.name}",
            description=f"Advanced preprocessing for dataset {dataset.name}",
            config={
                "dataset_id": dataset_id,
                "dataset_path": dataset.file_path,
                "preprocessing_config": config.dict()
            }
        )
        
        # Start background preprocessing task
        background_tasks.add_task(
            start_preprocessing_task,
            job_id=job.id,
            dataset_path=dataset.file_path,
            config=config.dict()
        )
        
        return PreprocessingResponse(
            job_id=job.id,
            status="started",
            message="Dataset preprocessing started",
            estimated_time_minutes=5
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting preprocessing: {e}")
        raise BioMLException(
            message="Failed to start dataset preprocessing",
            status_code=500
        )


@router.get("/{dataset_id}/preprocessing-suggestions", response_model=PreprocessingSuggestionResponse)
async def get_preprocessing_suggestions(
    dataset_id: int,
    task_type: str = "classification",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get preprocessing suggestions for a dataset.
    
    Args:
        dataset_id: Dataset ID
        task_type: ML task type (classification, regression, clustering)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Preprocessing suggestions
    """
    try:
        # Validate dataset access
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Get preprocessing suggestions
        suggestions = await enhanced_dataset_service.get_preprocessing_suggestions(
            dataset.file_path,
            task_type
        )
        
        return PreprocessingSuggestionResponse(
            dataset_id=dataset_id,
            task_type=task_type,
            suggestions=suggestions,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preprocessing suggestions: {e}")
        raise BioMLException(
            message="Failed to get preprocessing suggestions",
            status_code=500
        )


@router.post("/{dataset_id}/extract-biological-features", response_model=PreprocessingResponse)
async def extract_biological_features(
    dataset_id: int,
    request: BiologicalFeatureExtractionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Extract biological features from sequence data.
    
    Args:
        dataset_id: Dataset ID
        request: Feature extraction configuration
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Feature extraction job information
    """
    try:
        # Validate dataset access
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == current_user.id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Validate that dataset contains biological sequences
        if dataset.dataset_type not in ['dna', 'rna', 'protein']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset must contain biological sequences"
            )
        
        # Create feature extraction configuration
        config = {
            "steps": [{
                "name": "biological_features",
                "parameters": {
                    "sequence_column": request.sequence_column,
                    "sequence_type": request.sequence_type,
                    "extract_composition": request.extract_composition,
                    "extract_physicochemical": request.extract_physicochemical,
                    "kmer_size": request.kmer_size,
                    "extract_kmers": request.extract_kmers
                }
            }]
        }
        
        # Create job
        job_service = JobService()
        job = await job_service.create_job(
            db=db,
            user_id=current_user.id,
            job_type=JobType.DATA_ANALYSIS,
            name=f"Extract features from {dataset.name}",
            description=f"Biological feature extraction for {dataset.name}",
            config={
                "dataset_id": dataset_id,
                "dataset_path": dataset.file_path,
                "preprocessing_config": config
            }
        )
        
        # Start background task
        background_tasks.add_task(
            start_preprocessing_task,
            job_id=job.id,
            dataset_path=dataset.file_path,
            config=config
        )
        
        return PreprocessingResponse(
            job_id=job.id,
            status="started",
            message="Biological feature extraction started",
            estimated_time_minutes=3
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting feature extraction: {e}")
        raise BioMLException(
            message="Failed to start biological feature extraction",
            status_code=500
        )


@router.get("/{dataset_id}/quality-report", response_model=DataQualityReport)
async def get_data_quality_report(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate data quality report for a dataset.
    
    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Data quality report
    """
    try:
        # Validate dataset access
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            (Dataset.user_id == current_user.id) | (Dataset.is_public == True)
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Generate quality report
        report = await enhanced_dataset_service.generate_quality_report(
            dataset.file_path
        )
        
        return DataQualityReport(
            dataset_id=dataset_id,
            **report,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quality report: {e}")
        raise BioMLException(
            message="Failed to generate data quality report",
            status_code=500
        )


@router.post("/{dataset_id}/transform", response_model=PreprocessingResponse)
async def transform_dataset(
    dataset_id: int,
    request: DataTransformationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Apply data transformations to a dataset.
    
    Args:
        dataset_id: Dataset ID
        request: Transformation configuration
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Transformation job information
    """
    try:
        # Validate dataset access
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == current_user.id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Create transformation job
        job_service = JobService()
        job = await job_service.create_job(
            db=db,
            user_id=current_user.id,
            job_type=JobType.DATA_ANALYSIS,
            name=f"Transform {dataset.name}",
            description=f"Data transformation for {dataset.name}",
            config={
                "dataset_id": dataset_id,
                "dataset_path": dataset.file_path,
                "transformation_config": request.dict()
            }
        )
        
        # Start background transformation task
        background_tasks.add_task(
            start_transformation_task,
            job_id=job.id,
            dataset_path=dataset.file_path,
            config=request.dict()
        )
        
        return PreprocessingResponse(
            job_id=job.id,
            status="started",
            message="Dataset transformation started",
            estimated_time_minutes=5
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting transformation: {e}")
        raise BioMLException(
            message="Failed to start dataset transformation",
            status_code=500
        )


# Background task functions
async def start_preprocessing_task(job_id: int, dataset_path: str, config: Dict[str, Any]):
    """Background task for dataset preprocessing"""
    from app.core.database import get_db_context
    from app.models.job import Job, JobStatus
    
    with get_db_context() as db:
        try:
            # Update job status
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                return
            
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            db.commit()
            
            # Run preprocessing
            result = await enhanced_dataset_service.advanced_preprocessing(
                dataset_path, config
            )
            
            if result["success"]:
                # Create new dataset record for preprocessed data
                original_dataset = db.query(Dataset).filter(
                    Dataset.id == job.config["dataset_id"]
                ).first()
                
                if original_dataset:
                    preprocessed_dataset = Dataset(
                        user_id=original_dataset.user_id,
                        name=f"{original_dataset.name} (Preprocessed)",
                        description=f"Preprocessed version of {original_dataset.name}",
                        dataset_type=original_dataset.dataset_type,
                        file_path=result["output_path"],
                        filename=Path(result["output_path"]).name,
                        file_size=Path(result["output_path"]).stat().st_size,
                        file_extension=".csv",
                        stats=result["preprocessing_report"],
                        is_public=False,
                        created_at=datetime.utcnow()
                    )
                    
                    db.add(preprocessed_dataset)
                    db.commit()
                    
                    result["preprocessed_dataset_id"] = preprocessed_dataset.id
                
                # Update job with success
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.result = result
                db.commit()
            else:
                # Update job with failure
                job.status = JobStatus.FAILED
                job.error_message = result.get("error", "Unknown error")
                job.completed_at = datetime.utcnow()
                db.commit()
                
        except Exception as e:
            logger.error(f"Preprocessing task failed for job {job_id}: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()


async def start_transformation_task(job_id: int, dataset_path: str, config: Dict[str, Any]):
    """Background task for dataset transformation"""
    # Similar implementation to preprocessing task
    # This would handle specific transformation operations
    pass
