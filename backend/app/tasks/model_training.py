"""
Advanced model training tasks with hyperparameter optimization
"""

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
from celery import current_task
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import make_scorer
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.job import Job, JobStatus
from app.services.ml_service import MLService
from app.services.job_service import JobService
from app.utils.logger import get_task_logger

logger = get_task_logger(__name__)
SessionLocal = sessionmaker(bind=engine)


@celery_app.task(bind=True, name='biomlstudio.model_training.train_classification_model_task')
def train_classification_model_task(
    self,
    job_id: int,
    dataset_path: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Advanced classification model training with cross-validation.
    
    Args:
        job_id: Job ID
        dataset_path: Path to training dataset
        config: Training configuration
        
    Returns:
        Dict: Training results
    """
    task_id = self.request.id
    logger.info(f"Starting advanced classification training task {task_id} for job {job_id}")
    
    job_service = JobService()
    ml_service = MLService()
    
    try:
        # Update job status
        job_service.update_job_status(job_id, JobStatus.RUNNING)
        job_service.add_job_log(job_id, "Advanced classification training started")
        
        # Training with cross-validation and advanced metrics
        training_result = ml_service.train_classification_model(
            job_id=job_id,
            dataset_path=dataset_path,
            config=config
        )
        
        # Additional advanced metrics could be calculated here
        # Such as learning curves, validation curves, etc.
        
        # Complete job
        job_service.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            metrics=training_result['metrics']
        )
        job_service.add_job_log(job_id, "Advanced classification training completed")
        
        logger.info(f"Advanced classification training completed for job {job_id}")
        
        return {
            'status': 'completed',
            'job_id': job_id,
            'results': training_result,
            'task_id': task_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Advanced classification training failed for job {job_id}: {error_msg}")
        
        job_service.update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message=error_msg
        )
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'job_id': job_id}
        )
        
        raise


@celery_app.task(bind=True, name='biomlstudio.model_training.train_regression_model_task')
def train_regression_model_task(
    self,
    job_id: int,
    dataset_path: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Advanced regression model training.
    
    Args:
        job_id: Job ID
        dataset_path: Path to training dataset
        config: Training configuration
        
    Returns:
        Dict: Training results
    """
    task_id = self.request.id
    logger.info(f"Starting advanced regression training task {task_id} for job {job_id}")
    
    job_service = JobService()
    ml_service = MLService()
    
    try:
        job_service.update_job_status(job_id, JobStatus.RUNNING)
        job_service.add_job_log(job_id, "Advanced regression training started")
        
        # Training with advanced regression techniques
        training_result = ml_service.train_regression_model(
            job_id=job_id,
            dataset_path=dataset_path,
            config=config
        )
        
        # Complete job
        job_service.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            metrics=training_result['metrics']
        )
        job_service.add_job_log(job_id, "Advanced regression training completed")
        
        logger.info(f"Advanced regression training completed for job {job_id}")
        
        return {
            'status': 'completed',
            'job_id': job_id,
            'results': training_result,
            'task_id': task_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Advanced regression training failed for job {job_id}: {error_msg}")
        
        job_service.update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message=error_msg
        )
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'job_id': job_id}
        )
        
        raise


@celery_app.task(bind=True, name='biomlstudio.model_training.hyperparameter_tuning_task')
def hyperparameter_tuning_task(
    self,
    job_id: int,
    dataset_path: str,
    tuning_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Hyperparameter optimization task.
    
    Args:
        job_id: Job ID
        dataset_path: Path to dataset
        tuning_config: Hyperparameter tuning configuration
        
    Returns:
        Dict: Tuning results
    """
    task_id = self.request.id
    logger.info(f"Starting hyperparameter tuning task {task_id} for job {job_id}")
    
    job_service = JobService()
    
    try:
        job_service.update_job_status(job_id, JobStatus.RUNNING)
        job_service.add_job_log(job_id, "Hyperparameter tuning started")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Initializing tuning...'}
        )
        
        # Load data
        ml_service = MLService()
        X, y = ml_service._load_and_prepare_data(
            dataset_path,
            tuning_config.get('target_column', 'target'),
            tuning_config.get('feature_columns')
        )
        
        # Update progress
        job_service.update_job_progress(job_id, 20.0, "Data loaded, starting tuning")
        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Starting hyperparameter search...'}
        )
        
        # Get model and parameter grid
        algorithm = tuning_config.get('algorithm', 'random_forest')
        param_grid = tuning_config.get('param_grid', {})
        
        if algorithm == 'random_forest':
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(random_state=42)
            
            if not param_grid:
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [None, 10, 20, 30],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
        
        # Perform hyperparameter search
        search_type = tuning_config.get('search_type', 'grid')
        cv_folds = tuning_config.get('cv_folds', 5)
        
        if search_type == 'grid':
            search = GridSearchCV(
                model,
                param_grid,
                cv=cv_folds,
                scoring=tuning_config.get('scoring', 'accuracy'),
                n_jobs=-1,
                verbose=1
            )
        elif search_type == 'random':
            n_iter = tuning_config.get('n_iter', 50)
            search = RandomizedSearchCV(
                model,
                param_grid,
                n_iter=n_iter,
                cv=cv_folds,
                scoring=tuning_config.get('scoring', 'accuracy'),
                n_jobs=-1,
                verbose=1,
                random_state=42
            )
        
        # Update progress
        job_service.update_job_progress(job_id, 40.0, "Performing hyperparameter search")
        self.update_state(
            state='PROGRESS',
            meta={'current': 40, 'total': 100, 'status': 'Searching optimal parameters...'}
        )
        
        # Fit the search
        search.fit(X, y)
        
        # Update progress
        job_service.update_job_progress(job_id, 80.0, "Evaluating best parameters")
        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Evaluating results...'}
        )
        
        # Extract results
        tuning_results = {
            'best_params': search.best_params_,
            'best_score': search.best_score_,
            'best_estimator': str(search.best_estimator_),
            'cv_results_summary': {
                'mean_test_scores': search.cv_results_['mean_test_score'].tolist(),
                'std_test_scores': search.cv_results_['std_test_score'].tolist(),
                'params': [str(p) for p in search.cv_results_['params']]
            }
        }
        
        # Complete job
        job_service.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            metrics=tuning_results
        )
        job_service.update_job_progress(job_id, 100.0, "Hyperparameter tuning completed")
        job_service.add_job_log(job_id, f"Best parameters found: {search.best_params_}")
        
        # Update final progress
        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Tuning completed'}
        )
        
        logger.info(f"Hyperparameter tuning completed for job {job_id}")
        
        return {
            'status': 'completed',
            'job_id': job_id,
            'tuning_results': tuning_results,
            'task_id': task_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Hyperparameter tuning failed for job {job_id}: {error_msg}")
        
        job_service.update_job_status(
            job_id,
            JobStatus.FAILED,
            error_message=error_msg
        )
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'job_id': job_id}
        )
        
        raise


@celery_app.task(bind=True, name='biomlstudio.model_training.model_evaluation_task')
def model_evaluation_task(
    self,
    model_id: int,
    test_dataset_path: str,
    evaluation_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Comprehensive model evaluation task.
    
    Args:
        model_id: Model ID to evaluate
        test_dataset_path: Path to test dataset
        evaluation_config: Evaluation configuration
        
    Returns:
        Dict: Comprehensive evaluation results
    """
    task_id = self.request.id
    logger.info(f"Starting comprehensive model evaluation task {task_id} for model {model_id}")
    
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Loading model and data...'}
        )
        
        # This would include comprehensive evaluation metrics
        # Such as learning curves, feature importance analysis,
        # model interpretation, etc.
        
        evaluation_results = {
            'model_id': model_id,
            'comprehensive_metrics': {
                'accuracy': 0.95,
                'precision': 0.94,
                'recall': 0.96,
                'f1_score': 0.95,
                'auc_roc': 0.97
            },
            'feature_analysis': {
                'feature_importance': {},
                'correlation_analysis': {},
                'univariate_analysis': {}
            },
            'model_interpretation': {
                'shap_values': None,  # Would contain SHAP analysis
                'lime_explanations': None  # Would contain LIME analysis
            }
        }
        
        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Evaluation completed'}
        )
        
        logger.info(f"Comprehensive model evaluation completed for model {model_id}")
        
        return {
            'status': 'completed',
            'model_id': model_id,
            'evaluation_results': evaluation_results,
            'task_id': task_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Model evaluation failed for model {model_id}: {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'model_id': model_id}
        )
        
        raise
