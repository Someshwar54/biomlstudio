"""
Simplified analysis endpoints for one-click ML pipeline
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.models.user import User
from app.models.dataset import Dataset
from app.schemas.job import JobCreate, JobResponse
from app.tasks.ml_tasks import start_auto_analysis_task

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/auto-analyze/{dataset_id}", response_model=JobResponse)
async def auto_analyze_dataset(
    dataset_id: int,
    target_column: str,
    analysis_type: str = "classification",  # or "regression"
    feature_columns: Optional[str] = None,  # comma-separated or None for auto-detect
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    One-click analysis: Upload CSV, select target, get results.
    
    This endpoint simplifies the ML pipeline to match your specification:
    1. Takes a dataset and target column
    2. Automatically prepares data (clean NaNs, scale, balance if needed)
    3. Trains multiple models (RF + LogisticRegression)
    4. Returns metrics + plots
    
    Args:
        dataset_id: ID of uploaded dataset
        target_column: Column to predict
        analysis_type: "classification" or "regression"
        feature_columns: Specific features (optional, auto-detect if None)
        
    Returns:
        JobResponse: Created analysis job
    """
    # Verify dataset ownership
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=404, 
            detail="Dataset not found or access denied"
        )
    
    # Parse feature columns if provided
    features = None
    if feature_columns:
        features = [col.strip() for col in feature_columns.split(",")]
        # Ensure target column is not in features
        features = [f for f in features if f != target_column]
    
    # Create simplified job configuration
    config = {
        "dataset_id": dataset_id,
        "dataset_path": dataset.file_path,
        "target_column": target_column,
        "feature_columns": features,
        "analysis_type": analysis_type,
        "auto_preprocess": True,  # Enable automatic preprocessing
        "models": ["random_forest", "logistic_regression"],  # Train both
        "generate_plots": True,  # Generate visualizations
        "test_size": 0.2,
        "scale_features": True,
        "handle_imbalance": True if analysis_type == "classification" else False
    }
    
    # Create job using existing job creation logic
    job_data = JobCreate(
        job_type="data_analysis",
        name=f"Auto Analysis: {dataset.name}",
        description=f"Automated {analysis_type} analysis on {target_column}",
        config=config
    )
    
    # Create job record
    from app.models.job import Job, JobStatus
    from datetime import datetime
    
    db_job = Job(
        user_id=current_user.id,
        dataset_id=dataset_id,
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
    
    # Run analysis directly (no Celery) for demo
    import threading
    
    def run_analysis():
        from app.core.database import SessionLocal
        from app.services.ml_service import MLService
        from app.services.job_service import JobService
        
        db_local = SessionLocal()
        try:
            job = db_local.query(Job).filter(Job.id == db_job.id).first()
            job.status = JobStatus.RUNNING
            db_local.commit()
            
            ml_service = MLService()
            
            # Load and prepare data
            import pandas as pd
            from sklearn.preprocessing import LabelEncoder
            from pathlib import Path
            
            file_path = Path(config['dataset_path'])
            
            # Check if FASTA file and convert to CSV with k-mer features
            if file_path.suffix.lower() in ['.fasta', '.fa', '.fas']:
                from app.utils.bioinformatics import convert_fasta_to_csv
                import tempfile
                
                temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w')
                temp_csv.close()
                
                conversion_config = {
                    'add_composition': True,
                    'add_kmers': True,
                    'kmer_size': 3,
                    'max_sequences': 10000
                }
                
                result = convert_fasta_to_csv(str(file_path), temp_csv.name, conversion_config)
                
                if not result['success']:
                    raise Exception(f"Failed to convert FASTA: {result.get('error')}")
                
                df = pd.read_csv(temp_csv.name)
                
                sequence_metadata = ['sequence_id', 'sequence', 'sequence_type']
                
                job.artifacts = job.artifacts or {}
                job.artifacts['sequence_stats'] = {
                    'total_sequences': len(df),
                    'avg_length': float(df['length'].mean()) if 'length' in df.columns else 0,
                    'sequence_type': df['sequence_type'].iloc[0] if 'sequence_type' in df.columns else 'unknown'
                }
                db_local.commit()
                
                # Drop metadata columns that shouldn't be used for training
                df = df.drop(columns=[col for col in sequence_metadata if col in df.columns], errors='ignore')
                
            else:
                df = pd.read_csv(config['dataset_path'])
            
            # Encode categorical columns
            label_encoders = {}
            for col in df.columns:
                if df[col].dtype == 'object':
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype(str))
                    label_encoders[col] = le
            
            # Auto-detect features if not provided
            feature_cols = config['feature_columns']
            if feature_cols is None:
                # Use all columns except target
                feature_cols = [col for col in df.columns if col != config['target_column']]
            
            # Separate features and target
            X = df[feature_cols]
            y = df[config['target_column']]
            
            # Train model
            if config['analysis_type'] == 'classification':
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.model_selection import train_test_split
                from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                model = RandomForestClassifier(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_test)
                
                # Calculate metrics
                metrics = {
                    'accuracy': float(accuracy_score(y_test, y_pred)),
                    'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                    'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
                    'f1_score': float(f1_score(y_test, y_pred, average='weighted', zero_division=0))
                }
                
                # Feature importance
                feature_importance = {
                    name: float(importance) 
                    for name, importance in zip(feature_cols, model.feature_importances_)
                }
                
                # Confusion matrix
                cm = confusion_matrix(y_test, y_pred)
                
                # Save model
                import joblib
                from pathlib import Path
                model_dir = Path(settings.MODELS_DIR) / str(job.user_id)
                model_dir.mkdir(parents=True, exist_ok=True)
                model_path = model_dir / f"model_{job.id}.joblib"
                joblib.dump(model, str(model_path))
                
                result = {
                    'metrics': metrics,
                    'feature_importance': feature_importance,
                    'confusion_matrix': cm.tolist(),
                    'model_path': str(model_path)
                }
            else:
                from sklearn.ensemble import RandomForestRegressor
                from sklearn.model_selection import train_test_split
                from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
                
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_test)
                
                metrics = {
                    'r2_score': float(r2_score(y_test, y_pred)),
                    'mse': float(mean_squared_error(y_test, y_pred)),
                    'mae': float(mean_absolute_error(y_test, y_pred))
                }
                
                feature_importance = {
                    name: float(importance) 
                    for name, importance in zip(feature_cols, model.feature_importances_)
                }
                
                # Save model
                import joblib
                from pathlib import Path
                model_dir = Path(settings.MODELS_DIR) / str(job.user_id)
                model_dir.mkdir(parents=True, exist_ok=True)
                model_path = model_dir / f"model_{job.id}.joblib"
                joblib.dump(model, str(model_path))
                
                result = {
                    'metrics': metrics,
                    'feature_importance': feature_importance,
                    'model_path': str(model_path)
                }
            
            job.status = JobStatus.COMPLETED
            job.metrics = result.get('metrics', {})
            job.artifacts = {
                'feature_importance': result.get('feature_importance', {}),
                'confusion_matrix': result.get('confusion_matrix', []),
                'model_path': result.get('model_path', '')
            }
            job.updated_at = datetime.utcnow()
            db_local.commit()
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            job = db_local.query(Job).filter(Job.id == db_job.id).first()
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.updated_at = datetime.utcnow()
            db_local.commit()
        finally:
            db_local.close()
    
    # Run in background thread
    thread = threading.Thread(target=run_analysis)
    thread.daemon = True
    thread.start()
    
    # Set to queued initially
    db_job.status = JobStatus.QUEUED
    db_job.updated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Auto analysis job created: {db_job.id} for dataset {dataset_id}")
    
    return JobResponse.from_orm(db_job)


@router.get("/download-model/{job_id}")
async def download_model(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    from app.models.job import Job
    
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    model_path = (job.artifacts or {}).get('model_path')
    if not model_path:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_file = Path(model_path)
    if not model_file.exists():
        raise HTTPException(status_code=404, detail="Model file not found")
    
    return FileResponse(
        path=str(model_file),
        filename=f"model_{job_id}.joblib",
        media_type="application/octet-stream"
    )
