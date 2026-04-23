"""
ML Job management endpoints for training, preprocessing, and evaluation tasks
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.api.deps import get_current_active_user, get_db, CommonQueryParams
from app.core.exceptions import BioMLException
from app.models.job import Job
from app.models.user import User
from app.schemas.job import (
    JobCreate, JobResponse, JobUpdate, JobStatus, 
    JobMetrics, JobListResponse
)
from app.services.job_service import JobService
from app.tasks.ml_tasks import start_training_task, start_preprocessing_task

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Create a new ML job (training, preprocessing, etc.).
    
    Args:
        job_data: Job creation data
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JobResponse: Created job information
    """
    try:
        # Create job record
        db_job = Job(
            user_id=current_user.id,
            job_type=job_data.job_type,
            name=job_data.name,
            description=job_data.description,
            config=job_data.config,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        # Start Celery task based on job type (dispatch via Celery so task_id is set)
        if job_data.job_type == "training":
            # Dispatch to Celery worker
            start_training_task.delay(job_id=db_job.id, config=job_data.config)
        elif job_data.job_type == "preprocessing":
            start_preprocessing_task.delay(job_id=db_job.id, config=job_data.config)
        else:
            raise BioMLException(
                message=f"Unsupported job type: {job_data.job_type}",
                status_code=400
            )
        
        # Update status to queued
        db_job.status = JobStatus.QUEUED
        db_job.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Job created: {db_job.id} by user {current_user.id}")
        
        return JobResponse.from_orm(db_job)
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        db.rollback()
        raise BioMLException(
            message="Failed to create job",
            status_code=500
        )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    commons: CommonQueryParams = Depends(CommonQueryParams),
    job_type: Optional[str] = None,
    status: Optional[JobStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List user's jobs with filtering and pagination.
    
    Args:
        commons: Common query parameters (pagination, sorting)
        job_type: Filter by job type
        status: Filter by job status
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JobListResponse: Paginated job list
    """
    query = db.query(Job).filter(Job.user_id == current_user.id)
    
    # Apply filters
    if job_type:
        query = query.filter(Job.job_type == job_type)
    if status:
        query = query.filter(Job.status == status)
    
    # Apply sorting
    if commons.sort_order == "asc":
        query = query.order_by(asc(getattr(Job, commons.sort_by, Job.created_at)))
    else:
        query = query.order_by(desc(getattr(Job, commons.sort_by, Job.created_at)))
    
    # Apply pagination first for better performance
    jobs = query.offset(commons.skip).limit(commons.limit).all()
    
    # Get total count (this is expensive, so we do it after pagination)
    total = query.count()
    
    return JobListResponse(
        jobs=[JobResponse.from_orm(job) for job in jobs],
        total=total,
        skip=commons.skip,
        limit=commons.limit
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific job details.
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JobResponse: Job details
        
    Raises:
        HTTPException: If job not found or access denied
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return JobResponse.from_orm(job)


@router.get("/{job_id}/results")
async def get_job_results(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed job results including metrics, plots, and model comparisons.
    
    This endpoint provides the comprehensive results that match your specification:
    - Model metrics (accuracy, precision, recall, F1, AUC, etc.)
    - Feature importance rankings
    - Visualizations (confusion matrix, ROC curves, model comparison)
    - Best model recommendation
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Detailed job results with visualizations
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    # Return the job results which should contain:
    # - metrics: accuracy, precision, recall, F1, AUC, etc.
    # - plots: base64-encoded visualizations
    # - feature_importance: ranked features
    # - comparison: model comparison if multiple models trained
    return {
        "job_id": job.id,
        "job_name": job.name,
        "job_type": job.job_type,
        "status": job.status,
        "results": {
            "metrics": job.metrics or {},
            "feature_importance": (job.artifacts or {}).get('feature_importance', {}),
            "confusion_matrix": (job.artifacts or {}).get('confusion_matrix', []),
            "sequence_stats": (job.artifacts or {}).get('sequence_stats')
        },
        "created_at": job.created_at,
        "completed_at": job.updated_at
    }


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update job information (name, description, etc.).
    
    Args:
        job_id: Job ID
        job_update: Job update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JobResponse: Updated job information
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Only allow updates for certain statuses
    if job.status in [JobStatus.RUNNING, JobStatus.COMPLETED]:
        allowed_fields = ["name", "description"]
        update_data = job_update.dict(exclude_unset=True)
        
        for field in update_data:
            if field not in allowed_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot update {field} for job with status {job.status}"
                )
    
    # Apply updates
    for field, value in job_update.dict(exclude_unset=True).items():
        setattr(job, field, value)
    
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    
    logger.info(f"Job updated: {job.id}")
    
    return JobResponse.from_orm(job)


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Cancel a running or queued job.
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Success message
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status not in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    # Update job status
    job.status = JobStatus.CANCELLED
    job.updated_at = datetime.utcnow()
    job.error_message = "Cancelled by user"
    
    db.commit()
    
    logger.info(f"Job cancelled: {job.id}")
    
    return {"message": "Job cancelled successfully"}


@router.get("/{job_id}/metrics", response_model=JobMetrics)
async def get_job_metrics(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get job training metrics and performance data.
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        JobMetrics: Job metrics data
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if not job.metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No metrics available for this job"
        )
    
    return JobMetrics(**job.metrics)


@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get job execution logs.
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Job logs
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get logs from job service
    job_service = JobService()
    logs = await job_service.get_job_logs(job_id)
    
    return {
        "job_id": job_id,
        "logs": logs,
        "timestamp": datetime.utcnow()
    }


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a job and its associated data.
    
    Args:
        job_id: Job ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Success message
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Don't allow deletion of running jobs
    if job.status == JobStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running job. Cancel it first."
        )
    
    # Delete job and associated files
    job_service = JobService()
    await job_service.cleanup_job_data(job_id)
    
    db.delete(job)
    db.commit()
    
    logger.info(f"Job deleted: {job_id}")
    
    return {"message": "Job deleted successfully"}
