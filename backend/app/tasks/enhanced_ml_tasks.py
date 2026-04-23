"""
Enhanced ML background tasks for model training and optimization
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.core.database import get_db_context
from app.models.job import Job, JobStatus
from app.models.dataset import Dataset
from app.services.enhanced_ml_service import enhanced_ml_service

logger = logging.getLogger(__name__)


async def start_model_training_task(job_id: int, config: Dict[str, Any]):
    """
    Background task for enhanced model training with pipeline configuration.
    
    Args:
        job_id: Job ID for tracking
        config: Training configuration including model config and parameters
    """
    with get_db_context() as db:
        try:
            # Update job status
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Starting enhanced model training for job {job_id}")
            
            # Get dataset
            dataset_id = config["dataset_id"]
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                raise Exception(f"Dataset {dataset_id} not found")
            
            # Extract configuration
            model_config = config["model_config"]
            training_params = config.get("training_params", {})
            
            # Add dataset path to training params
            training_params["dataset_path"] = dataset.file_path
            
            # Train model using enhanced ML service
            result = await enhanced_ml_service.train_model_with_pipeline(
                job_id=job_id,
                dataset_path=dataset.file_path,
                model_config=model_config,
                training_params=training_params
            )
            
            if result["success"]:
                # Update job with success
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.result = result
                job.metrics = result.get("metrics", {})
                
                logger.info(f"Model training completed successfully for job {job_id}")
            else:
                # Update job with failure
                job.status = JobStatus.FAILED
                job.error_message = result.get("error", "Training failed")
                job.completed_at = datetime.utcnow()
                
                logger.error(f"Model training failed for job {job_id}: {result.get('error')}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Model training task failed for job {job_id}: {e}")
            
            # Update job with failure
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()


async def start_hyperparameter_optimization_task(job_id: int, config: Dict[str, Any]):
    """
    Background task for hyperparameter optimization.
    
    Args:
        job_id: Job ID for tracking
        config: Optimization configuration
    """
    with get_db_context() as db:
        try:
            # Update job status
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Starting hyperparameter optimization for job {job_id}")
            
            # Get dataset
            dataset_id = config["dataset_id"]
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                raise Exception(f"Dataset {dataset_id} not found")
            
            # Load dataset
            import pandas as pd
            if dataset.file_path.endswith('.csv'):
                df = pd.read_csv(dataset.file_path)
            else:
                raise Exception("Unsupported file format for optimization")
            
            # Prepare data (assuming last column is target)
            X = df.iloc[:, :-1].values
            y = df.iloc[:, -1].values
            
            # Build pipeline
            model_config = config["model_config"]
            pipeline = enhanced_ml_service.model_builder.build_model_pipeline(model_config)
            
            # Optimize hyperparameters
            optimized_pipeline, optimization_results = enhanced_ml_service.model_builder.optimize_hyperparameters(
                pipeline=pipeline,
                X=X,
                y=y,
                method=config.get("optimization_method", "grid_search"),
                cv=config.get("cv_folds", 5),
                n_iter=config.get("n_iterations", 50)
            )
            
            # Update job with results
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.metrics = optimization_results
            job.result = {
                "optimized_config": model_config,
                "best_parameters": optimization_results.get("best_params", {}),
                "best_score": optimization_results.get("best_score", 0),
                "optimization_method": config.get("optimization_method", "grid_search")
            }
            
            db.commit()
            
            logger.info(f"Hyperparameter optimization completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Hyperparameter optimization failed for job {job_id}: {e}")
            
            # Update job with failure
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()


async def start_automl_task(job_id: int, config: Dict[str, Any]):
    """
    Background task for AutoML pipeline.
    
    Args:
        job_id: Job ID for tracking
        config: AutoML configuration
    """
    with get_db_context() as db:
        try:
            # Update job status
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Starting AutoML pipeline for job {job_id}")
            
            # Get dataset
            dataset_id = config["dataset_id"]
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                raise Exception(f"Dataset {dataset_id} not found")
            
            # Run AutoML pipeline
            result = await enhanced_ml_service.auto_ml_pipeline(
                dataset_path=dataset.file_path,
                target_column=config["target_column"],
                task_type=config["task_type"],
                time_budget_minutes=config.get("time_budget_minutes", 30),
                max_models=config.get("max_models", 10)
            )
            
            # Update job with results
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            job.metrics = {
                "best_score": result.get("best_score", 0),
                "models_tried": len(result.get("tried_models", [])),
                "time_taken_minutes": result.get("time_taken_minutes", 0)
            }
            
            db.commit()
            
            logger.info(f"AutoML pipeline completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"AutoML pipeline failed for job {job_id}: {e}")
            
            # Update job with failure
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()


async def start_model_comparison_task(job_id: int, config: Dict[str, Any]):
    """
    Background task for model comparison.
    
    Args:
        job_id: Job ID for tracking
        config: Comparison configuration
    """
    with get_db_context() as db:
        try:
            # Update job status
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Starting model comparison for job {job_id}")
            
            # Get evaluation dataset
            dataset_id = config["evaluation_dataset_id"]
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                raise Exception(f"Evaluation dataset {dataset_id} not found")
            
            # Compare models
            result = await enhanced_ml_service.compare_models(
                model_ids=config["model_ids"],
                evaluation_dataset_path=dataset.file_path,
                metrics_to_compare=config.get("metrics_to_compare", ["accuracy"])
            )
            
            # Update job with results
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            job.metrics = {
                "models_compared": len(config["model_ids"]),
                "best_model_id": result.get("best_model")
            }
            
            db.commit()
            
            logger.info(f"Model comparison completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Model comparison failed for job {job_id}: {e}")
            
            # Update job with failure
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()


async def start_batch_preprocessing_task(job_id: int, config: Dict[str, Any]):
    """
    Background task for batch preprocessing multiple datasets.
    
    Args:
        job_id: Job ID for tracking
        config: Batch preprocessing configuration
    """
    with get_db_context() as db:
        try:
            # Update job status
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Starting batch preprocessing for job {job_id}")
            
            dataset_ids = config["dataset_ids"]
            preprocessing_config = config["preprocessing_config"]
            
            results = {
                "processed_datasets": [],
                "failed_datasets": [],
                "total_datasets": len(dataset_ids)
            }
            
            for dataset_id in dataset_ids:
                try:
                    # Get dataset
                    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
                    if not dataset:
                        results["failed_datasets"].append({
                            "dataset_id": dataset_id,
                            "error": "Dataset not found"
                        })
                        continue
                    
                    # Process dataset
                    from app.services.enhanced_dataset_service import enhanced_dataset_service
                    result = await enhanced_dataset_service.advanced_preprocessing(
                        dataset.file_path,
                        preprocessing_config
                    )
                    
                    if result["success"]:
                        results["processed_datasets"].append({
                            "dataset_id": dataset_id,
                            "output_path": result["output_path"],
                            "original_shape": result["original_shape"],
                            "processed_shape": result["processed_shape"]
                        })
                    else:
                        results["failed_datasets"].append({
                            "dataset_id": dataset_id,
                            "error": result.get("error", "Unknown error")
                        })
                        
                except Exception as e:
                    results["failed_datasets"].append({
                        "dataset_id": dataset_id,
                        "error": str(e)
                    })
            
            # Update job with results
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = results
            job.metrics = {
                "total_datasets": results["total_datasets"],
                "successful_datasets": len(results["processed_datasets"]),
                "failed_datasets": len(results["failed_datasets"])
            }
            
            db.commit()
            
            logger.info(f"Batch preprocessing completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Batch preprocessing failed for job {job_id}: {e}")
            
            # Update job with failure
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
