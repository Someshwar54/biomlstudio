"""
Comprehensive ML workflow endpoints
Handles end-to-end training pipeline with monitoring
"""

import logging
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, get_user_from_token_query
from app.models.user import User
from app.models.dataset import Dataset
from app.models.job import Job, JobStatus, JobType
from app.services.preprocessing_service import preprocessing_service
from app.services.automl_service import automl_service
from app.services.training_service import training_service
from app.services.export_service import export_service
from app.services.shap_service import shap_service
from app.core.config import settings
from pydantic import BaseModel
import numpy as np

logger = logging.getLogger(__name__)
router = APIRouter()


class WorkflowConfig(BaseModel):
    """Configuration for ML workflow"""
    dataset_id: int
    task_type: str = "general_classification"  # protein_classification, dna_classification, gene_expression, etc.
    target_column: str = "label"
    encoding_method: str = "kmer"  # kmer, onehot, integer
    kmer_size: int = 3
    test_size: float = 0.2
    val_size: float = 0.1
    optimize_hyperparams: bool = False
    n_models: int = 3
    generate_report: bool = True


class WorkflowStartResponse(BaseModel):
    """Response for workflow start"""
    job_id: int
    status: str
    message: str


@router.post("/start", response_model=WorkflowStartResponse)
async def start_ml_workflow(
    config: WorkflowConfig,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Start complete ML workflow: preprocessing → model selection → training → evaluation → export.
    
    This is the main endpoint that orchestrates the entire BioMLStudio pipeline:
    1. Loads and preprocesses data (cleaning, encoding, feature engineering)
    2. Automatically selects best models based on task type
    3. Trains multiple models with hyperparameter optimization
    4. Generates comprehensive metrics and visualizations
    5. Creates PDF report with all results
    6. Exports trained model and artifacts
    
    Args:
        config: Workflow configuration
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        db: Database session
        
    Returns:
        WorkflowStartResponse: Job information
    """
    # Verify dataset exists and user has access
    dataset = db.query(Dataset).filter(
        Dataset.id == config.dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Create job
    job = Job(
        user_id=current_user.id,
        dataset_id=dataset.id,
        job_type=JobType.ML_WORKFLOW,
        status=JobStatus.PENDING,
        config=config.dict()
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start workflow in background
    background_tasks.add_task(
        execute_ml_workflow,
        job_id=job.id,
        dataset_path=dataset.file_path,
        dataset_type=dataset.dataset_type,
        config=config.dict()
    )
    
    logger.info(f"ML workflow started: Job {job.id} for user {current_user.id}")
    
    return WorkflowStartResponse(
        job_id=job.id,
        status="started",
        message=f"ML workflow started. Processing dataset: {dataset.name}"
    )


async def execute_ml_workflow(
    job_id: int,
    dataset_path: str,
    dataset_type: str,
    config: Dict[str, Any]
):
    """
    Execute complete ML workflow (runs in background).
    
    This function handles the entire pipeline:
    - Data preprocessing and encoding
    - AutoML model selection
    - Training with monitoring
    - Evaluation and visualization
    - Model and report export
    """
    from app.core.database import get_db_context
    
    with get_db_context() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            db.commit()
            
            logger.info(f"Starting ML workflow for job {job_id}")
            
            # Step 1: Preprocessing
            logger.info("Step 1: Preprocessing data...")
            job.progress = 10
            db.commit()
            
            preprocessing_config = {
                'encoding_method': config.get('encoding_method', 'kmer'),
                'encoding_params': {'k': config.get('kmer_size', 3)},
                'missing_value_strategy': 'drop',
                'scaling_method': 'standard',
                'test_size': config.get('test_size', 0.2),
                'val_size': config.get('val_size', 0.1),
                'target_column': config.get('target_column', 'label'),
                'stratify': True
            }
            
            preprocessing_results = await preprocessing_service.preprocess_dataset(
                file_path=dataset_path,
                dataset_type=dataset_type,
                config=preprocessing_config
            )
            
            if not preprocessing_results['success']:
                raise Exception(f"Preprocessing failed: {preprocessing_results.get('errors')}")
            
            logger.info("Preprocessing completed successfully")
            job.progress = 30
            db.commit()
            
            # Step 2: Training with AutoML
            logger.info("Step 2: Training models...")
            job.progress = 40
            db.commit()
            
            task_config = {
                'task_type': config.get('task_type', 'general_classification'),
                'optimize_hyperparams': config.get('optimize_hyperparams', False),
                'n_models': config.get('n_models', 3),
                'feature_names': preprocessing_results.get('feature_names', [])
            }
            
            training_results = await training_service.train_with_monitoring(
                X_train=preprocessing_results['train_data']['X'],
                y_train=preprocessing_results['train_data']['y'],
                X_val=preprocessing_results['val_data']['X'],
                y_val=preprocessing_results['val_data']['y'],
                task_config=task_config
            )
            
            if not training_results['success']:
                raise Exception("Training failed")
            
            logger.info("Training completed successfully")
            job.progress = 70
            db.commit()
            
            # Create output directory
            output_dir = Path(settings.MODELS_DIR) / f"job_{job_id}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 3: Generate SHAP explanations
            logger.info("Step 3: Generating SHAP explanations...")
            shap_results = None
            try:
                # Get the best model path
                best_model = training_results['best_model']['model']
                
                # Save model temporarily for SHAP analysis
                import joblib
                temp_model_path = output_dir / "temp_model.joblib"
                
                # Get feature names from preprocessing results
                feature_names = preprocessing_results.get('feature_names', 
                                [f'feature_{i}' for i in range(preprocessing_results['final_shape'][1])])
                
                joblib.dump({
                    'model': best_model,
                    'feature_names': feature_names
                }, temp_model_path)
                
                # Generate SHAP explanations on test data
                X_test = preprocessing_results['test_data']['X']
                shap_results = shap_service.generate_shap_explanations(
                    model_path=str(temp_model_path),
                    X_data=X_test[:100] if len(X_test) > 100 else X_test,  # Limit samples for performance
                    feature_names=feature_names,
                    max_display=15,
                    sample_size=min(100, len(X_test))
                )
                
                logger.info("SHAP explanations generated successfully")
            except Exception as e:
                logger.warning(f"Could not generate SHAP explanations: {e}")
            
            job.progress = 80
            db.commit()
            
            # Step 4: Save model and generate reports
            logger.info("Step 4: Saving model and generating reports...")
            
            # Create output directory
            output_dir = Path(settings.MODELS_DIR) / f"job_{job_id}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save model artifacts
            best_model = training_results['best_model']['model']
            artifacts = await training_service.save_model_artifacts(
                model=best_model,
                results=training_results,
                save_dir=output_dir,
                model_name=f"model_job_{job_id}"
            )
            
            # Generate PDF report if requested
            if config.get('generate_report', True):
                dataset = db.query(Dataset).filter(Dataset.id == job.dataset_id).first()
                dataset_info = {
                    'name': dataset.name,
                    'dataset_type': dataset.dataset_type,
                    'total_samples': preprocessing_results['original_shape'][0],
                    'n_features': preprocessing_results['final_shape'][1],
                    'file_size_mb': dataset.file_size / (1024 * 1024)
                }
                
                report_path = str(output_dir / f"report_job_{job_id}.pdf")
                
                # Combine all results for report
                report_data = {
                    **training_results,
                    'preprocessing_steps': preprocessing_results['preprocessing_steps']
                }
                
                await export_service.generate_pdf_report(
                    results=report_data,
                    dataset_info=dataset_info,
                    output_path=report_path
                )
                
                artifacts['report'] = report_path
                logger.info(f"PDF report generated: {report_path}")
            
            # Update job with results
            job.status = JobStatus.COMPLETED
            job.progress = 100
            
            # Flatten metrics for frontend (use validation metrics, fallback to training)
            evaluation_metrics = training_results.get('metrics', {})
            flattened_metrics = evaluation_metrics.get('validation', evaluation_metrics.get('training', {}))
            
            # Prepare models_trained data for frontend (exclude model objects)
            models_comparison = []
            for model_result in training_results.get('models_trained', []):
                models_comparison.append({
                    'model_name': model_result['model_name'],
                    'model_type': model_result['model_type'],
                    'training_time': model_result['training_time'],
                    'metrics': model_result['metrics'],
                    'is_best': model_result['model_name'] == training_results['best_model']['model_name']
                })
            
            # Extract feature importance from training results
            feature_importance = {}
            evaluation_data = training_results.get('evaluation', {})
            visualizations = evaluation_data.get('visualizations', {})
            
            # Try to get feature importance from different sources
            if 'feature_importance' in training_results:
                feature_importance = training_results['feature_importance']
            elif 'best_model' in training_results and hasattr(training_results['best_model'].get('model'), 'feature_importances_'):
                # Extract from best model if available
                model = training_results['best_model']['model']
                feature_names = preprocessing_results.get('feature_names', 
                                [f'feature_{i}' for i in range(len(model.feature_importances_))])
                feature_importance = {
                    feature_names[i]: imp 
                    for i, imp in enumerate(model.feature_importances_)
                }
            
            job.result = {
                'success': True,
                'best_model': training_results['best_model']['model_name'],
                'metrics': flattened_metrics,
                'full_metrics': training_results['metrics'],  # Keep nested structure for advanced use
                'models_trained': models_comparison,  # All trained models comparison
                'artifacts': artifacts,
                'training_time': training_results['training_time'],
                'visualizations': training_results.get('visualizations', {}),
                'feature_importance': feature_importance,  # Add feature importance here
                'shap_explanations': shap_results if shap_results and shap_results.get('success') else None
            }
            db.commit()
            
            logger.info(f"ML workflow completed successfully for job {job_id}")
            
        except Exception as e:
            logger.error(f"ML workflow error for job {job_id}: {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            db.commit()


@router.get("/{job_id}/status")
async def get_workflow_status(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get workflow job status and progress"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return {
        'job_id': job.id,
        'status': job.status.value,
        'progress': job.progress,
        'result': job.result,
        'error_message': job.error_message,
        'created_at': job.created_at,
        'updated_at': job.updated_at
    }


@router.get("/{job_id}/results")
async def get_workflow_results(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get complete workflow results including metrics and visualizations"""
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
            detail=f"Job not completed yet. Current status: {job.status.value}"
        )
    
    return {
        'job_id': job.id,
        'dataset_id': job.dataset_id,
        'results': job.result,
        'config': job.config
    }


@router.get("/{job_id}/download/model")
async def download_model(
    job_id: int,
    current_user: User = Depends(get_user_from_token_query),
    db: Session = Depends(get_db)
):
    """Download trained model file"""
    from fastapi.responses import FileResponse
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not available"
        )
    
    model_path = job.result.get('artifacts', {}).get('model')
    if not model_path or not Path(model_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model file not found"
        )
    
    return FileResponse(
        path=model_path,
        media_type='application/octet-stream',
        filename=f"model_job_{job_id}.joblib"
    )


@router.get("/{job_id}/download/report")
async def download_report(
    job_id: int,
    current_user: User = Depends(get_user_from_token_query),
    db: Session = Depends(get_db)
):
    """Download PDF report"""
    from fastapi.responses import FileResponse
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not available"
        )
    
    report_path = job.result.get('artifacts', {}).get('report')
    if not report_path or not Path(report_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found"
        )
    
    return FileResponse(
        path=report_path,
        media_type='application/pdf',
        filename=f"report_job_{job_id}.pdf"
    )
