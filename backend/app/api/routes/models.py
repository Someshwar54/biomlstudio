"""
ML Model management endpoints for trained models and artifacts
"""

import logging
from datetime import datetime
from io import BytesIO
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import joblib
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.api.deps import get_current_active_user, get_db, CommonQueryParams
from app.core.exceptions import BioMLException
from app.models.ml_model import MLModel
from app.models.user import User
from app.schemas.ml_model import (
    MLModelResponse, MLModelUpdate, MLModelListResponse,
    ModelPredictionRequest, ModelPredictionResponse
)
from app.services.model_service import ModelService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=MLModelListResponse)
async def list_models(
    commons: CommonQueryParams = Depends(CommonQueryParams),
    model_type: Optional[str] = None,
    is_public: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List user's trained models with filtering and pagination.
    
    Args:
        commons: Common query parameters (pagination, sorting)
        model_type: Filter by model type
        is_public: Filter by public/private models
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        MLModelListResponse: Paginated model list
    """
    query = db.query(MLModel).filter(
        (MLModel.user_id == current_user.id) | (MLModel.is_public == True)
    )
    
    # Apply filters
    if model_type:
        query = query.filter(MLModel.model_type == model_type)
    if is_public is not None:
        query = query.filter(MLModel.is_public == is_public)
    
    # Apply sorting
    if commons.sort_order == "asc":
        query = query.order_by(asc(getattr(MLModel, commons.sort_by, MLModel.created_at)))
    else:
        query = query.order_by(desc(getattr(MLModel, commons.sort_by, MLModel.created_at)))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    models = query.offset(commons.skip).limit(commons.limit).all()
    
    return MLModelListResponse(
        models=[MLModelResponse.from_orm(model) for model in models],
        total=total,
        skip=commons.skip,
        limit=commons.limit
    )


@router.get("/{model_id}", response_model=MLModelResponse)
async def get_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get specific model details.
    
    Args:
        model_id: Model ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        MLModelResponse: Model details
    """
    model = db.query(MLModel).filter(
        MLModel.id == model_id,
        (MLModel.user_id == current_user.id) | (MLModel.is_public == True)
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    return MLModelResponse.from_orm(model)


@router.put("/{model_id}", response_model=MLModelResponse)
async def update_model(
    model_id: int,
    model_update: MLModelUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update model metadata (name, description, visibility).
    
    Args:
        model_id: Model ID
        model_update: Model update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        MLModelResponse: Updated model information
    """
    model = db.query(MLModel).filter(
        MLModel.id == model_id,
        MLModel.user_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Apply updates
    for field, value in model_update.dict(exclude_unset=True).items():
        setattr(model, field, value)
    
    model.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(model)
    
    logger.info(f"Model updated: {model.id}")
    
    return MLModelResponse.from_orm(model)


@router.get("/{model_id}/download")
async def download_model(
    model_id: int,
    format: str = "joblib",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Download trained model file.
    
    Args:
        model_id: Model ID
        format: Export format (pickle, onnx, joblib)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        StreamingResponse: Model file download
    """
    model = db.query(MLModel).filter(
        MLModel.id == model_id,
        (MLModel.user_id == current_user.id) | (MLModel.is_public == True)
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if not model.artifact_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model artifact not found"
        )
    
    # Stream from local filesystem; support joblib or pickle export
    try:
        artifact_path = Path(model.artifact_path)
        if not artifact_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model artifact file not found on disk"
            )

        filename = f"{model.name}_{model.id}.{format}"
        media_type = "application/octet-stream"

        if format not in {"joblib", "pickle"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format. Use 'joblib' or 'pickle'."
            )

        if format == "joblib":
            async def file_generator():
                async with aiofiles.open(artifact_path, 'rb') as f:
                    while True:
                        chunk = await f.read(8192)
                        if not chunk:
                            break
                        yield chunk

            return StreamingResponse(
                file_generator(),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # Convert to pickle in-memory
            model_info = joblib.load(artifact_path)
            data = pickle.dumps(model_info, protocol=pickle.HIGHEST_PROTOCOL)
            return StreamingResponse(
                BytesIO(data),
                media_type=media_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error downloading model"
        )


@router.post("/{model_id}/predict", response_model=ModelPredictionResponse)
async def predict_with_model(
    model_id: int,
    prediction_request: ModelPredictionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Make predictions using a trained model.
    
    Args:
        model_id: Model ID
        prediction_request: Input data for prediction
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ModelPredictionResponse: Prediction results
    """
    model = db.query(MLModel).filter(
        MLModel.id == model_id,
        (MLModel.user_id == current_user.id) | (MLModel.is_public == True)
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Load model and make predictions
    model_service = ModelService()
    
    try:
        predictions = await model_service.predict(
            model_id=model_id,
            input_data=prediction_request.input_data,
            return_probabilities=prediction_request.return_probabilities
        )
        
        return ModelPredictionResponse(
            model_id=model_id,
            predictions=predictions,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Prediction error for model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error making predictions"
        )


@router.get("/{model_id}/metrics")
async def get_model_metrics(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get model performance metrics and evaluation results.
    
    Args:
        model_id: Model ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Model metrics and evaluation data
    """
    model = db.query(MLModel).filter(
        MLModel.id == model_id,
        (MLModel.user_id == current_user.id) | (MLModel.is_public == True)
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if not model.metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No metrics available for this model"
        )
    
    return {
        "model_id": model_id,
        "metrics": model.metrics,
        "model_type": model.model_type,
        "timestamp": model.updated_at
    }


@router.post("/{model_id}/clone", response_model=MLModelResponse)
async def clone_model(
    model_id: int,
    clone_name: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Clone an existing model (copy model file and metadata).
    
    Args:
        model_id: Source model ID
        clone_name: Name for the cloned model
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        MLModelResponse: Cloned model information
    """
    source_model = db.query(MLModel).filter(
        MLModel.id == model_id,
        (MLModel.user_id == current_user.id) | (MLModel.is_public == True)
    ).first()
    
    if not source_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source model not found"
        )
    
    # Clone model using model service
    model_service = ModelService()
    
    try:
        cloned_model = await model_service.clone_model(
            source_model_id=model_id,
            new_name=clone_name,
            user_id=current_user.id
        )
        
        logger.info(f"Model cloned: {model_id} -> {cloned_model.id}")
        
        return MLModelResponse.from_orm(cloned_model)
        
    except Exception as e:
        logger.error(f"Error cloning model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cloning model"
        )


@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a model and its associated files.
    
    Args:
        model_id: Model ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dict: Success message
    """
    model = db.query(MLModel).filter(
        MLModel.id == model_id,
        MLModel.user_id == current_user.id
    ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Delete model artifact from local filesystem
    if model.artifact_path:
        try:
            path = Path(model.artifact_path)
            if path.exists():
                # Remove file
                path.unlink()
                # Remove parent directory if empty
                parent = path.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
        except Exception as e:
            logger.warning(f"Failed to remove model artifact for {model_id}: {e}")
    
    # Delete model record
    db.delete(model)
    db.commit()
    
    logger.info(f"Model deleted: {model_id}")
    
    return {"message": "Model deleted successfully"}
