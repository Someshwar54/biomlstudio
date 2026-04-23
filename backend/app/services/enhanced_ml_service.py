"""
Enhanced ML Service with advanced model building and training capabilities
"""

import logging
import joblib
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from app.services.ml_service import MLService
from app.services.model_builder_service import model_builder_service
from app.services.shap_service import shap_service
from app.core.database import get_db_context
from app.models.ml_model import MLModel, ModelType, ModelFramework
from app.models.job import Job, JobStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedMLService(MLService):
    """Enhanced ML service with model builder integration"""
    
    def __init__(self):
        super().__init__()
        self.model_builder = model_builder_service
    
    async def train_model_with_pipeline(
        self,
        job_id: int,
        dataset_path: str,
        model_config: Dict[str, Any],
        training_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Train a model using the configured pipeline from model builder.
        
        Args:
            job_id: Associated job ID
            dataset_path: Path to training dataset
            model_config: Model configuration from model builder
            training_params: Training parameters
            
        Returns:
            Dict: Training results and metrics
        """
        try:
            # Load and prepare data
            df = self._load_dataset(dataset_path)
            
            # Extract target column
            target_column = training_params.get('target_column', 'target')
            if target_column not in df.columns:
                # Try to infer target column (last column)
                target_column = df.columns[-1]
            
            # Prepare features and target
            feature_columns = training_params.get('feature_columns')
            if feature_columns:
                X = df[feature_columns]
            else:
                X = df.drop(columns=[target_column])
            
            y = df[target_column]
            
            # Handle categorical target
            label_encoder = None
            if not pd.api.types.is_numeric_dtype(y):
                label_encoder = LabelEncoder()
                y = label_encoder.fit_transform(y)
            
            # Split data
            test_size = training_params.get('test_size', 0.2)
            random_state = training_params.get('random_state', 42)
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state,
                stratify=y if model_config['task_type'] == 'classification' else None
            )
            
            # Build pipeline from configuration
            pipeline = self.model_builder.build_model_pipeline(model_config)
            
            # Auto-optimize hyperparameters if requested
            if training_params.get('auto_optimize', False):
                pipeline, optimization_results = self.model_builder.optimize_hyperparameters(
                    pipeline=pipeline,
                    X=X_train,
                    y=y_train,
                    method=training_params.get('optimization_method', 'grid_search'),
                    cv=training_params.get('cv_folds', 5)
                )
            else:
                optimization_results = None
            
            # Train the model
            pipeline.fit(X_train, y_train)
            
            # Make predictions
            y_pred = pipeline.predict(X_test)
            
            # Calculate metrics based on task type
            if model_config['task_type'] == 'classification':
                metrics = self._calculate_enhanced_classification_metrics(
                    y_test, y_pred, pipeline, X_test, label_encoder
                )
            elif model_config['task_type'] == 'regression':
                metrics = self._calculate_enhanced_regression_metrics(y_test, y_pred)
            else:
                metrics = {}
            
            # Cross-validation
            if training_params.get('cross_validation', True):
                cv_folds = training_params.get('cv_folds', 5)
                cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv_folds)
                metrics['cv_scores'] = {
                    'mean': cv_scores.mean(),
                    'std': cv_scores.std(),
                    'scores': cv_scores.tolist()
                }
            
            # Feature importance
            feature_importance = self._extract_feature_importance(
                pipeline, X.columns.tolist()
            )
            
            # Save model
            model_artifacts = {
                'pipeline': pipeline,
                'label_encoder': label_encoder,
                'feature_names': X.columns.tolist(),
                'model_config': model_config,
                'training_params': training_params,
                'optimization_results': optimization_results
            }
            
            model_path = self._save_enhanced_model(job_id, model_artifacts)
            
            # Generate SHAP explanations if requested
            shap_results = None
            if training_params.get('generate_shap', True):
                try:
                    logger.info("Generating SHAP explanations...")
                    shap_results = shap_service.generate_shap_explanations(
                        model_path=str(model_path),
                        X_data=X_test,
                        feature_names=feature_names,
                        max_display=15,
                        sample_size=min(100, len(X_test))
                    )
                except Exception as e:
                    logger.warning(f"Could not generate SHAP explanations: {e}")
            
            # Create model record in database
            model_record = await self._create_model_record(
                job_id=job_id,
                model_config=model_config,
                metrics=metrics,
                model_path=str(model_path),
                feature_importance=feature_importance
            )
            
            return {
                'success': True,
                'model_id': model_record.id,
                'model_path': str(model_path),
                'metrics': metrics,
                'feature_importance': feature_importance,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'algorithm': model_config['algorithm'],
                'optimization_results': optimization_results,
                'shap_explanations': shap_results
            }
            
        except Exception as e:
            logger.error(f"Error training model with pipeline: {e}")
            raise
    
    def _load_dataset(self, dataset_path: str) -> pd.DataFrame:
        """Load dataset from file"""
        path = Path(dataset_path)
        
        if path.suffix.lower() == '.csv':
            return pd.read_csv(dataset_path)
        elif path.suffix.lower() == '.tsv':
            return pd.read_csv(dataset_path, sep='\t')
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    def _calculate_enhanced_classification_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        pipeline: Pipeline,
        X_test: pd.DataFrame,
        label_encoder: Optional[LabelEncoder] = None
    ) -> Dict[str, Any]:
        """Calculate enhanced classification metrics"""
        
        # Basic metrics
        metrics = self._calculate_classification_metrics(y_true, y_pred)
        
        # Add probability predictions if available
        if hasattr(pipeline, 'predict_proba'):
            y_proba = pipeline.predict_proba(X_test)
            
            # ROC AUC for binary classification
            if len(np.unique(y_true)) == 2:
                metrics['roc_auc'] = roc_auc_score(y_true, y_proba[:, 1])
            
            # Prediction confidence
            max_proba = np.max(y_proba, axis=1)
            metrics['prediction_confidence'] = {
                'mean': float(np.mean(max_proba)),
                'std': float(np.std(max_proba)),
                'min': float(np.min(max_proba)),
                'max': float(np.max(max_proba))
            }
        
        # Class distribution
        unique, counts = np.unique(y_true, return_counts=True)
        metrics['class_distribution'] = dict(zip(unique.tolist(), counts.tolist()))
        
        # Prediction distribution
        unique_pred, counts_pred = np.unique(y_pred, return_counts=True)
        metrics['prediction_distribution'] = dict(zip(unique_pred.tolist(), counts_pred.tolist()))
        
        return metrics
    
    def _calculate_enhanced_regression_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, Any]:
        """Calculate enhanced regression metrics"""
        
        # Basic metrics
        metrics = self._calculate_regression_metrics(y_true, y_pred)
        
        # Additional regression metrics
        residuals = y_true - y_pred
        metrics['residual_stats'] = {
            'mean': float(np.mean(residuals)),
            'std': float(np.std(residuals)),
            'min': float(np.min(residuals)),
            'max': float(np.max(residuals))
        }
        
        # Prediction range
        metrics['prediction_range'] = {
            'min': float(np.min(y_pred)),
            'max': float(np.max(y_pred)),
            'mean': float(np.mean(y_pred)),
            'std': float(np.std(y_pred))
        }
        
        return metrics
    
    def _extract_feature_importance(
        self,
        pipeline: Pipeline,
        feature_names: List[str]
    ) -> Optional[Dict[str, float]]:
        """Extract feature importance from trained pipeline"""
        
        # Get the model step from pipeline
        model = pipeline.named_steps.get('model')
        
        if hasattr(model, 'feature_importances_'):
            # Tree-based models
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            # Linear models
            if len(model.coef_.shape) == 1:
                importances = np.abs(model.coef_)
            else:
                importances = np.mean(np.abs(model.coef_), axis=0)
        else:
            return None
        
        # Handle feature transformation in pipeline
        if 'standard_scaler' in pipeline.named_steps or 'minmax_scaler' in pipeline.named_steps:
            # Feature names remain the same after scaling
            pass
        
        if len(importances) != len(feature_names):
            # Handle case where feature dimensions changed
            feature_names = [f'feature_{i}' for i in range(len(importances))]
        
        return dict(zip(feature_names, importances.tolist()))
    
    def _save_enhanced_model(
        self,
        job_id: int,
        model_artifacts: Dict[str, Any]
    ) -> Path:
        """Save enhanced model artifacts"""
        
        model_dir = self.model_storage_path / f"job_{job_id}"
        model_dir.mkdir(exist_ok=True)
        
        # Save main model file
        model_path = model_dir / "model.joblib"
        joblib.dump(model_artifacts, model_path)
        
        # Save configuration as JSON for easy access
        config_path = model_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump({
                'model_config': model_artifacts['model_config'],
                'training_params': model_artifacts['training_params'],
                'feature_names': model_artifacts['feature_names']
            }, f, indent=2)
        
        logger.info(f"Enhanced model saved to {model_path}")
        return model_path
    
    async def _create_model_record(
        self,
        job_id: int,
        model_config: Dict[str, Any],
        metrics: Dict[str, Any],
        model_path: str,
        feature_importance: Optional[Dict[str, float]]
    ) -> MLModel:
        """Create model record in database"""
        
        with get_db_context() as db:
            # Get job information
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Determine model type
            task_type = model_config['task_type']
            if task_type == 'classification':
                model_type = ModelType.CLASSIFICATION
            elif task_type == 'regression':
                model_type = ModelType.REGRESSION
            elif task_type == 'clustering':
                model_type = ModelType.CLUSTERING
            else:
                model_type = ModelType.OTHER
            
            # Create model record
            model_record = MLModel(
                user_id=job.user_id,
                name=f"{model_config['algorithm']} - {job.name}",
                description=f"Model trained with {model_config['algorithm']} algorithm",
                model_type=model_type,
                framework=ModelFramework.SCIKIT_LEARN,
                algorithm=model_config['algorithm'],
                hyperparameters=model_config.get('hyperparameters', {}),
                metrics=metrics,
                feature_importance=feature_importance,
                artifact_path=model_path,
                job_id=job_id,
                is_public=False,
                created_at=datetime.utcnow()
            )
            
            db.add(model_record)
            db.commit()
            db.refresh(model_record)
            
            return model_record
    
    async def compare_models(
        self,
        model_ids: List[int],
        evaluation_dataset_path: str,
        metrics_to_compare: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple models on the same dataset.
        
        Args:
            model_ids: List of model IDs to compare
            evaluation_dataset_path: Path to evaluation dataset
            metrics_to_compare: List of metrics to compare
            
        Returns:
            Model comparison results
        """
        try:
            # Load evaluation dataset
            df = self._load_dataset(evaluation_dataset_path)
            
            comparison_results = {
                'models': [],
                'best_model': None,
                'comparison_summary': {},
                'timestamp': datetime.utcnow()
            }
            
            for model_id in model_ids:
                # Load model
                model_info = self._load_model(model_id)
                if not model_info:
                    continue
                
                pipeline = model_info['pipeline']
                feature_names = model_info.get('feature_names', [])
                
                # Prepare data (assuming last column is target)
                target_col = df.columns[-1]
                if feature_names:
                    X = df[feature_names]
                else:
                    X = df.drop(columns=[target_col])
                y = df[target_col]
                
                # Handle categorical target
                label_encoder = model_info.get('label_encoder')
                if label_encoder:
                    y = label_encoder.transform(y)
                
                # Make predictions
                y_pred = pipeline.predict(X)
                
                # Calculate metrics
                task_type = model_info['model_config']['task_type']
                if task_type == 'classification':
                    metrics = self._calculate_enhanced_classification_metrics(
                        y, y_pred, pipeline, X, label_encoder
                    )
                else:
                    metrics = self._calculate_enhanced_regression_metrics(y, y_pred)
                
                comparison_results['models'].append({
                    'model_id': model_id,
                    'algorithm': model_info['model_config']['algorithm'],
                    'metrics': metrics
                })
            
            # Determine best model based on primary metric
            if comparison_results['models']:
                primary_metric = metrics_to_compare[0] if metrics_to_compare else 'accuracy'
                best_model = max(
                    comparison_results['models'],
                    key=lambda x: x['metrics'].get(primary_metric, 0)
                )
                comparison_results['best_model'] = best_model['model_id']
                
                # Create comparison summary
                for metric in metrics_to_compare:
                    comparison_results['comparison_summary'][metric] = {
                        model['model_id']: model['metrics'].get(metric, 0)
                        for model in comparison_results['models']
                    }
            
            return comparison_results
            
        except Exception as e:
            logger.error(f"Error comparing models: {e}")
            raise
    
    async def auto_ml_pipeline(
        self,
        dataset_path: str,
        target_column: str,
        task_type: str,
        time_budget_minutes: int = 30,
        max_models: int = 10
    ) -> Dict[str, Any]:
        """
        Automated ML pipeline that tries multiple algorithms and configurations.
        
        Args:
            dataset_path: Path to dataset
            target_column: Target column name
            task_type: ML task type
            time_budget_minutes: Time budget for AutoML
            max_models: Maximum number of models to try
            
        Returns:
            AutoML results with best model
        """
        try:
            # Load dataset
            df = self._load_dataset(dataset_path)
            
            # Get dataset characteristics
            dataset_info = {
                'n_samples': len(df),
                'n_features': len(df.columns) - 1,
                'file_size_mb': Path(dataset_path).stat().st_size / (1024 * 1024)
            }
            
            # Get algorithm suggestions
            suggestions = self.model_builder.suggest_algorithms(
                dataset_info=dataset_info,
                task_type=task_type,
                max_suggestions=max_models
            )
            
            results = {
                'tried_models': [],
                'best_model': None,
                'best_score': -np.inf if task_type == 'regression' else 0,
                'time_taken_minutes': 0,
                'dataset_info': dataset_info
            }
            
            start_time = datetime.now()
            
            for suggestion in suggestions:
                # Check time budget
                elapsed_time = (datetime.now() - start_time).total_seconds() / 60
                if elapsed_time >= time_budget_minutes:
                    break
                
                algorithm = suggestion['algorithm']
                
                try:
                    # Create basic model configuration
                    model_config = {
                        'algorithm': algorithm,
                        'task_type': task_type,
                        'hyperparameters': {},
                        'preprocessing': [
                            {
                                'name': 'standard_scaler',
                                'parameters': {},
                                'enabled': True
                            }
                        ]
                    }
                    
                    # Quick training and evaluation
                    X = df.drop(columns=[target_column])
                    y = df[target_column]
                    
                    # Handle categorical target
                    if not pd.api.types.is_numeric_dtype(y):
                        le = LabelEncoder()
                        y = le.fit_transform(y)
                    
                    # Split data
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42
                    )
                    
                    # Build and train pipeline
                    pipeline = self.model_builder.build_model_pipeline(model_config)
                    pipeline.fit(X_train, y_train)
                    
                    # Evaluate
                    y_pred = pipeline.predict(X_test)
                    
                    if task_type == 'classification':
                        from sklearn.metrics import accuracy_score
                        score = accuracy_score(y_test, y_pred)
                    else:
                        from sklearn.metrics import r2_score
                        score = r2_score(y_test, y_pred)
                    
                    model_result = {
                        'algorithm': algorithm,
                        'score': score,
                        'config': model_config,
                        'training_time_seconds': 0  # Would track actual time
                    }
                    
                    results['tried_models'].append(model_result)
                    
                    # Update best model
                    if (task_type == 'classification' and score > results['best_score']) or \
                       (task_type == 'regression' and score > results['best_score']):
                        results['best_score'] = score
                        results['best_model'] = model_result
                
                except Exception as e:
                    logger.warning(f"Failed to train {algorithm}: {e}")
                    continue
            
            results['time_taken_minutes'] = (datetime.now() - start_time).total_seconds() / 60
            
            return results
            
        except Exception as e:
            logger.error(f"Error in AutoML pipeline: {e}")
            raise


# Initialize global instance
enhanced_ml_service = EnhancedMLService()
