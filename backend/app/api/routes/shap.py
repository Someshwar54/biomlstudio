"""
SHAP Explanation Routes
API endpoints for generating and retrieving SHAP explanations
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any
import logging

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.job import Job
from app.models.ml_model import MLModel
from app.models.dataset import Dataset
from app.schemas.shap import (
    SHAPExplanationRequest,
    SHAPExplanationResponse,
    PredictionExplanationRequest,
    PredictionExplanationResponse,
    JobSHAPRequest
)
from app.services.shap_service import shap_service
from app.core.config import settings
import pandas as pd
import numpy as np
from pathlib import Path

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/explain/model/{model_id}", response_model=SHAPExplanationResponse)
async def explain_model(
    model_id: int,
    request: SHAPExplanationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate SHAP explanations for a trained model.
    
    This endpoint creates interpretable explanations showing which features
    contribute most to the model's predictions.
    """
    try:
        # Get model from database
        model = db.query(MLModel).filter(
            MLModel.id == model_id,
            MLModel.user_id == current_user.id
        ).first()
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        if not model.model_path or not Path(model.model_path).exists():
            raise HTTPException(status_code=404, detail="Model file not found")
        
        # Load test data or dataset
        if request.dataset_id:
            dataset = db.query(Dataset).filter(
                Dataset.id == request.dataset_id,
                Dataset.user_id == current_user.id
            ).first()
            
            if not dataset:
                raise HTTPException(status_code=404, detail="Dataset not found")
            
            df = pd.read_csv(dataset.file_path)
            
            # Get feature columns (exclude target if present)
            feature_cols = [col for col in df.columns if col not in ['target', 'label']]
            X_data = df[feature_cols].values
            feature_names = feature_cols
        else:
            # Use model's training data info if available
            raise HTTPException(
                status_code=400,
                detail="dataset_id is required to generate explanations"
            )
        
        # Limit samples if specified
        if request.sample_indices:
            X_data = X_data[request.sample_indices]
        elif len(X_data) > request.sample_size:
            # Random sample for performance
            indices = np.random.choice(len(X_data), request.sample_size, replace=False)
            X_data = X_data[indices]
        
        # Generate SHAP explanations
        result = shap_service.generate_shap_explanations(
            model_path=model.model_path,
            X_data=X_data,
            feature_names=feature_names,
            max_display=request.max_display,
            sample_size=request.sample_size
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'SHAP generation failed'))
        
        return SHAPExplanationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SHAP explanations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain/prediction", response_model=PredictionExplanationResponse)
async def explain_prediction(
    request: PredictionExplanationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Explain a single prediction using SHAP values.
    
    This shows which features contributed most to a specific prediction.
    """
    try:
        # Get model
        if request.model_id:
            model = db.query(MLModel).filter(
                MLModel.id == request.model_id,
                MLModel.user_id == current_user.id
            ).first()
            
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            model_path = model.model_path
            feature_names = model.feature_names
        elif request.model_path:
            model_path = request.model_path
            feature_names = None
        else:
            raise HTTPException(status_code=400, detail="model_id or model_path required")
        
        if not Path(model_path).exists():
            raise HTTPException(status_code=404, detail="Model file not found")
        
        # Convert input data to array
        if feature_names:
            single_input = np.array([request.input_data.get(f, 0) for f in feature_names])
        else:
            single_input = np.array(list(request.input_data.values()))
        
        # Get background data if dataset specified
        background_data = None
        if request.dataset_id:
            dataset = db.query(Dataset).filter(
                Dataset.id == request.dataset_id,
                Dataset.user_id == current_user.id
            ).first()
            
            if dataset:
                df = pd.read_csv(dataset.file_path)
                feature_cols = [col for col in df.columns if col not in ['target', 'label']]
                background_data = df[feature_cols].values[:100]  # Use first 100 samples
        
        # Generate explanation
        result = shap_service.explain_prediction(
            model_path=model_path,
            single_input=single_input,
            feature_names=feature_names,
            background_data=background_data
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Explanation failed'))
        
        return PredictionExplanationResponse(
            success=True,
            explanation=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain/job/{job_id}", response_model=SHAPExplanationResponse)
async def explain_job_model(
    job_id: int,
    request: JobSHAPRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate SHAP explanations for a model trained in a specific job.
    
    This is useful for analyzing completed training jobs.
    """
    try:
        # Get job
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get model from job
        if not job.model_id:
            raise HTTPException(status_code=404, detail="Job has no associated model")
        
        model = db.query(MLModel).filter(MLModel.id == job.model_id).first()
        if not model or not Path(model.model_path).exists():
            raise HTTPException(status_code=404, detail="Model file not found")
        
        # Get dataset
        if not job.dataset_id:
            raise HTTPException(status_code=404, detail="Job has no associated dataset")
        
        dataset = db.query(Dataset).filter(Dataset.id == job.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Load dataset
        df = pd.read_csv(dataset.file_path)
        feature_cols = [col for col in df.columns if col not in ['target', 'label']]
        X_data = df[feature_cols].values
        
        # Limit samples for performance
        if len(X_data) > request.sample_size:
            indices = np.random.choice(len(X_data), request.sample_size, replace=False)
            X_data = X_data[indices]
        
        # Generate SHAP explanations
        result = shap_service.generate_shap_explanations(
            model_path=model.model_path,
            X_data=X_data,
            feature_names=feature_cols,
            max_display=request.max_display,
            sample_size=request.sample_size
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'SHAP generation failed'))
        
        return SHAPExplanationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SHAP explanations for job: {e}")
        raise HTTPException(status_code=500, detail=str(e))
