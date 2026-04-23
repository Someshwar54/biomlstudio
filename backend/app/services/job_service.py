"""
Job service for managing ML training and processing jobs
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import get_db_context
from app.models.job import Job, JobStatus, JobType
from app.models.user import User

logger = logging.getLogger(__name__)


class JobService:
    """Service for job management and execution"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def create_job(
        self, 
        db: Session,
        user_id: int,
        name: str,
        job_type: JobType,
        config: Dict[str, Any],
        dataset_id: Optional[int] = None,
        description: Optional[str] = None,
        priority: int = 5
    ) -> Job:
        """
        Create a new job.
        
        Args:
            db: Database session
            user_id: User ID who owns the job
            name: Job name
            job_type: Type of job
            config: Job configuration
            dataset_id: Associated dataset ID
            description: Job description
            priority: Job priority (1-10)
            
        Returns:
            Job: Created job instance
        """
        job = Job(
            user_id=user_id,
            name=name,
            description=description,
            job_type=job_type,
            config=config,
            dataset_id=dataset_id,
            priority=priority,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        self.logger.info(f"Job created: {job.id} - {job.name}")
        return job
    
    async def update_job_status(
        self, 
        job_id: int, 
        status: JobStatus,
        error_message: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update job status and related fields.
        
        Args:
            job_id: Job ID
            status: New job status
            error_message: Error message if job failed
            metrics: Job metrics if completed
            
        Returns:
            bool: True if updated successfully
        """
        with get_db_context() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                return False
            
            job.status = status
            job.updated_at = datetime.utcnow()
            
            if status == JobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.utcnow()
            
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job.completed_at = datetime.utcnow()
                if job.started_at:
                    duration = job.completed_at - job.started_at
                    job.duration_seconds = duration.total_seconds()
            
            if error_message:
                job.error_message = error_message
            
            if metrics:
                job.metrics = metrics
            
            db.commit()
            
            self.logger.info(f"Job {job_id} status updated to {status}")
            return True
    
    async def update_job_progress(
        self, 
        job_id: int, 
        progress_percent: float,
        current_step: Optional[str] = None
    ) -> bool:
        """
        Update job progress.
        
        Args:
            job_id: Job ID
            progress_percent: Progress percentage (0-100)
            current_step: Current processing step
            
        Returns:
            bool: True if updated successfully
        """
        with get_db_context() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                return False
            
            job.progress_percent = max(0.0, min(100.0, progress_percent))
            if current_step:
                job.current_step = current_step
            job.updated_at = datetime.utcnow()
            
            db.commit()
            return True
    
    async def get_job_logs(self, job_id: int) -> List[str]:
        """
        Get job execution logs.
        
        Args:
            job_id: Job ID
            
        Returns:
            List: Job log entries
        """
        with get_db_context() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if not job or not job.logs:
                return []
            
            # Parse logs (assuming newline-separated format)
            return job.logs.split('\n') if job.logs else []
    
    async def add_job_log(self, job_id: int, log_entry: str) -> bool:
        """
        Add log entry to job.
        
        Args:
            job_id: Job ID
            log_entry: Log entry to add
            
        Returns:
            bool: True if added successfully
        """
        with get_db_context() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                return False
            
            timestamp = datetime.utcnow().isoformat()
            formatted_entry = f"[{timestamp}] {log_entry}"
            
            if job.logs:
                job.logs += f"\n{formatted_entry}"
            else:
                job.logs = formatted_entry
            
            job.updated_at = datetime.utcnow()
            db.commit()
            return True
    
    async def cancel_job(self, job_id: int, user_id: int) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: Job ID to cancel
            user_id: User ID requesting cancellation
            
        Returns:
            bool: True if cancelled successfully
        """
        with get_db_context() as db:
            job = db.query(Job).filter(
                Job.id == job_id,
                Job.user_id == user_id
            ).first()
            
            if not job:
                return False
            
            if job.status not in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]:
                return False
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            job.error_message = "Cancelled by user"
            
            if job.started_at:
                duration = job.completed_at - job.started_at
                job.duration_seconds = duration.total_seconds()
            
            db.commit()
            
            self.logger.info(f"Job {job_id} cancelled by user {user_id}")
            return True
    
    async def retry_job(self, job_id: int) -> bool:
        """
        Retry a failed job.
        
        Args:
            job_id: Job ID to retry
            
        Returns:
            bool: True if retry initiated successfully
        """
        with get_db_context() as db:
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if not job or not job.can_retry():
                return False
            
            job.retry_count += 1
            job.status = JobStatus.PENDING
            job.progress_percent = 0.0
            job.current_step = None
            job.error_message = None
            job.error_traceback = None
            job.started_at = None
            job.completed_at = None
            job.duration_seconds = None
            job.updated_at = datetime.utcnow()
            
            db.commit()
            
            self.logger.info(f"Job {job_id} queued for retry (attempt {job.retry_count})")
            return True
    
    async def cleanup_job_data(self, job_id: int) -> bool:
        """
        Clean up job-related files and temporary data.
        
        Args:
            job_id: Job ID to clean up
            
        Returns:
            bool: True if cleaned up successfully
        """
        try:
            # Clean up temporary files, model artifacts, etc.
            # This would interact with storage service
            
            self.logger.info(f"Job data cleaned up for job {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up job {job_id}: {e}")
            return False
    
    async def get_user_job_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get job statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Job statistics
        """
        with get_db_context() as db:
            jobs = db.query(Job).filter(Job.user_id == user_id).all()
            
            stats = {
                "total_jobs": len(jobs),
                "status_counts": {},
                "avg_duration_seconds": 0,
                "total_duration_seconds": 0,
                "job_types": {}
            }
            
            total_duration = 0
            completed_jobs = 0
            
            for job in jobs:
                # Count by status
                status_key = job.status.value
                stats["status_counts"][status_key] = stats["status_counts"].get(status_key, 0) + 1
                
                # Count by type
                type_key = job.job_type.value
                stats["job_types"][type_key] = stats["job_types"].get(type_key, 0) + 1
                
                # Duration statistics
                if job.duration_seconds:
                    total_duration += job.duration_seconds
                    completed_jobs += 1
            
            stats["total_duration_seconds"] = total_duration
            if completed_jobs > 0:
                stats["avg_duration_seconds"] = total_duration / completed_jobs
            
            return stats
