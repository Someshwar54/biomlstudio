"""
Model service: wraps MLService for predictions, cloning, and simple export helpers.
"""

import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_context
from app.models.ml_model import MLModel, ModelType, ModelFramework
from app.services.ml_service import MLService

logger = logging.getLogger(__name__)


class ModelService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ml = MLService()

    # Prediction wrapper to match existing API usage
    async def predict(
        self,
        model_id: int,
        input_data: List[Dict[str, Any]],
        return_probabilities: bool = False,
    ) -> Dict[str, Any]:
        # Underlying is synchronous; safe to call directly
        return self.ml.predict_with_model(
            model_id=model_id,
            input_data=input_data,
            return_probabilities=return_probabilities,
        )

    # Clone model: duplicate artifact and create a new MLModel row
    async def clone_model(
        self,
        source_model_id: int,
        new_name: str,
        user_id: int,
    ) -> MLModel:
        with get_db_context() as db:
            src: Optional[MLModel] = (
                db.query(MLModel).filter(MLModel.id == source_model_id).first()
            )
            if not src or not src.artifact_path:
                raise ValueError("Source model not found or has no artifact")

            src_path = Path(src.artifact_path)
            if not src_path.exists():
                raise ValueError("Source model artifact file not found")

            # Create destination directory
            dest_dir = Path(settings.MODEL_STORAGE_PATH) / f"clone_{source_model_id}_{int(datetime.utcnow().timestamp())}"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / src_path.name

            shutil.copy2(src_path, dest_path)

            cloned = MLModel(
                user_id=user_id,
                name=new_name,
                description=src.description,
                model_type=src.model_type,
                framework=src.framework,
                algorithm=src.algorithm,
                artifact_path=str(dest_path),
                hyperparameters=src.hyperparameters,
                metrics=src.metrics,
                feature_importance=src.feature_importance,
                training_samples_count=src.training_samples_count,
                validation_samples_count=src.validation_samples_count,
                is_public=False,
                created_at=datetime.utcnow(),
            )
            db.add(cloned)
            db.commit()
            db.refresh(cloned)
            return cloned
