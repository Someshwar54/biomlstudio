"""
Background task modules for BioMLStudio

Contains Celery tasks for ML training, data processing, and other
long-running operations that should be executed asynchronously.
"""

from .ml_tasks import (
    start_training_task, start_preprocessing_task, 
    evaluate_model_task, predict_batch_task
)
from .data_processing import (
    process_biological_data_task, validate_dataset_task,
    generate_dataset_stats_task, convert_file_format_task
)
from .model_training import (
    train_classification_model_task, train_regression_model_task,
    hyperparameter_tuning_task, model_evaluation_task
)

__all__ = [
    # ML tasks
    "start_training_task", "start_preprocessing_task", 
    "evaluate_model_task", "predict_batch_task",
    # Data processing tasks
    "process_biological_data_task", "validate_dataset_task",
    "generate_dataset_stats_task", "convert_file_format_task",
    # Model training tasks
    "train_classification_model_task", "train_regression_model_task",
    "hyperparameter_tuning_task", "model_evaluation_task",
]
