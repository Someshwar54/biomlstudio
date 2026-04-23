"""
Training service with live monitoring, metrics tracking, and model evaluation
"""

import logging
import time
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime

from sklearn.model_selection import cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix, classification_report,
    mean_squared_error, mean_absolute_error, r2_score,
    log_loss
)

from app.services.automl_service import automl_service
from app.services.visualization_service import VisualizationService

logger = logging.getLogger(__name__)


class TrainingMonitor:
    """Monitor and log training progress in real-time"""
    
    def __init__(self):
        self.logs = []
        self.metrics_history = {
            'train_scores': [],
            'val_scores': [],
            'timestamps': [],
            'epochs': []
        }
        self.start_time = None
    
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.log("Training started", "INFO")
    
    def log(self, message: str, level: str = "INFO"):
        """Add log entry"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'elapsed_time': time.time() - self.start_time if self.start_time else 0
        }
        self.logs.append(log_entry)
        logger.info(f"[{level}] {message}")
    
    def record_metric(self, epoch: int, train_score: float, val_score: Optional[float] = None):
        """Record training metrics"""
        self.metrics_history['epochs'].append(epoch)
        self.metrics_history['train_scores'].append(train_score)
        if val_score is not None:
            self.metrics_history['val_scores'].append(val_score)
        self.metrics_history['timestamps'].append(time.time())
    
    def get_logs(self) -> List[Dict]:
        """Get all logs"""
        return self.logs
    
    def get_metrics(self) -> Dict:
        """Get metrics history"""
        return self.metrics_history


class TrainingService:
    """
    Comprehensive training service with monitoring and evaluation.
    Supports multiple models, hyperparameter tuning, and real-time logging.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.viz_service = VisualizationService()
        self.monitor = None
    
    async def train_with_monitoring(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        task_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Train model with full monitoring and evaluation.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            task_config: Task configuration
            
        Returns:
            Dict: Training results with metrics and model
        """
        self.monitor = TrainingMonitor()
        self.monitor.start()
        
        results = {
            'success': False,
            'models_trained': [],
            'best_model': None,
            'metrics': {},
            'logs': [],
            'training_time': 0
        }
        
        try:
            # Determine task type
            task_type = task_config.get('task_type', 'general_classification')
            is_regression = 'regression' in task_type
            
            self.monitor.log(f"Task type: {task_type}")
            self.monitor.log(f"Training samples: {len(X_train)}, Features: {X_train.shape[1]}")
            
            # Get data characteristics
            n_classes = len(np.unique(y_train)) if not is_regression else None
            data_chars = {
                'n_samples': len(X_train),
                'n_features': X_train.shape[1],
                'n_classes': n_classes,
                'task_type': task_type
            }
            
            # Select models using AutoML
            self.monitor.log("Selecting optimal models...")
            model_configs = automl_service.select_models(
                task_type=task_type,
                data_characteristics=data_chars,
                n_models=task_config.get('n_models', 3)
            )
            
            self.monitor.log(f"Selected {len(model_configs)} models: {[m['name'] for m in model_configs]}")
            
            # Train each model
            trained_models = []
            for i, model_config in enumerate(model_configs, 1):
                self.monitor.log(f"Training model {i}/{len(model_configs)}: {model_config['name']}")
                
                model_results = await self._train_single_model(
                    model_config=model_config,
                    X_train=X_train,
                    y_train=y_train,
                    X_val=X_val,
                    y_val=y_val,
                    is_regression=is_regression,
                    optimize_hyperparams=task_config.get('optimize_hyperparams', False),
                    feature_names=task_config.get('feature_names', [])
                )
                
                if model_results['success']:
                    trained_models.append(model_results)
                    self.monitor.log(
                        f"{model_config['name']} - Score: {model_results['metrics']['primary_score']:.4f}",
                        "SUCCESS"
                    )
            
            # Select best model
            if trained_models:
                best_model_result = max(
                    trained_models,
                    key=lambda x: x['metrics']['primary_score']
                )
                
                self.monitor.log(
                    f"Best model: {best_model_result['model_name']} "
                    f"(Score: {best_model_result['metrics']['primary_score']:.4f})",
                    "SUCCESS"
                )
                
                # Generate comprehensive evaluation
                evaluation = await self._comprehensive_evaluation(
                    model=best_model_result['model'],
                    X_train=X_train,
                    y_train=y_train,
                    X_val=X_val,
                    y_val=y_val,
                    is_regression=is_regression,
                    feature_names=task_config.get('feature_names', [])
                )
                
                results.update({
                    'success': True,
                    'models_trained': trained_models,
                    'best_model': best_model_result,
                    'evaluation': evaluation,
                    'metrics': evaluation['metrics'],
                    'visualizations': evaluation['visualizations'],
                    'feature_importance': evaluation.get('feature_importance', {}),
                    'training_time': time.time() - self.monitor.start_time
                })
            else:
                self.monitor.log("No models were successfully trained", "ERROR")
            
        except Exception as e:
            self.monitor.log(f"Training error: {str(e)}", "ERROR")
            self.logger.error(f"Training error: {e}", exc_info=True)
        
        finally:
            results['logs'] = self.monitor.get_logs()
            results['metrics_history'] = self.monitor.get_metrics()
        
        return results
    
    async def _train_single_model(
        self,
        model_config: Dict[str, Any],
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray],
        y_val: Optional[np.ndarray],
        is_regression: bool,
        optimize_hyperparams: bool = False,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Train a single model"""
        result = {
            'success': False,
            'model_name': model_config['name'],
            'model_type': model_config['model_type']
        }
        
        try:
            start_time = time.time()
            
            # Get model instance
            model = automl_service.get_model_instance(model_config, is_regression)
            
            # Hyperparameter optimization
            if optimize_hyperparams:
                self.monitor.log(f"  Optimizing hyperparameters...")
                param_grid = automl_service.get_hyperparameter_grid(model_config['model_type'])
                
                if param_grid:
                    model = await self._optimize_hyperparameters(
                        model, X_train, y_train, param_grid, is_regression
                    )
            
            # Train model
            self.monitor.log(f"  Fitting {model_config['name']}...")
            
            # Check if model supports validation monitoring (XGBoost)
            if hasattr(model, 'fit') and 'XGB' in str(type(model)):
                if X_val is not None and y_val is not None:
                    eval_set = [(X_train, y_train), (X_val, y_val)]
                    model.fit(
                        X_train, y_train,
                        eval_set=eval_set,
                        verbose=False
                    )
                else:
                    model.fit(X_train, y_train)
            else:
                model.fit(X_train, y_train)
            
            training_time = time.time() - start_time
            self.monitor.log(f"  Training completed in {training_time:.2f}s")
            
            # Evaluate
            train_score = model.score(X_train, y_train)
            val_score = model.score(X_val, y_val) if X_val is not None else None
            
            # Calculate detailed metrics
            y_train_pred = model.predict(X_train)
            
            if is_regression:
                primary_metric = r2_score(y_train, y_train_pred)
            else:
                primary_metric = accuracy_score(y_train, y_train_pred)
            
            result.update({
                'success': True,
                'model': model,
                'training_time': training_time,
                'metrics': {
                    'train_score': train_score,
                    'val_score': val_score,
                    'primary_score': val_score if val_score is not None else train_score
                }
            })
            
        except Exception as e:
            self.monitor.log(f"  Error training {model_config['name']}: {str(e)}", "ERROR")
            self.logger.error(f"Model training error: {e}")
        
        return result
    
    async def _optimize_hyperparameters(
        self,
        model,
        X_train: np.ndarray,
        y_train: np.ndarray,
        param_grid: Dict,
        is_regression: bool
    ):
        """Optimize model hyperparameters"""
        try:
            scoring = 'r2' if is_regression else 'accuracy'
            
            # Use RandomizedSearchCV for faster optimization
            search = RandomizedSearchCV(
                model,
                param_distributions=param_grid,
                n_iter=10,
                cv=3,
                scoring=scoring,
                n_jobs=-1,
                random_state=42,
                verbose=0
            )
            
            search.fit(X_train, y_train)
            self.monitor.log(f"  Best params: {search.best_params_}")
            
            return search.best_estimator_
            
        except Exception as e:
            self.monitor.log(f"  Hyperparameter optimization failed: {str(e)}", "WARNING")
            return model
    
    async def _comprehensive_evaluation(
        self,
        model,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray],
        y_val: Optional[np.ndarray],
        is_regression: bool,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive model evaluation"""
        self.monitor.log("Generating comprehensive evaluation...")
        
        evaluation = {
            'metrics': {},
            'visualizations': {},
            'predictions': {}
        }
        
        try:
            # Predictions
            y_train_pred = model.predict(X_train)
            y_val_pred = model.predict(X_val) if X_val is not None else None
            
            if is_regression:
                # Regression metrics
                train_metrics = {
                    'mse': mean_squared_error(y_train, y_train_pred),
                    'rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
                    'mae': mean_absolute_error(y_train, y_train_pred),
                    'r2': r2_score(y_train, y_train_pred)
                }
                
                if y_val_pred is not None:
                    val_metrics = {
                        'mse': mean_squared_error(y_val, y_val_pred),
                        'rmse': np.sqrt(mean_squared_error(y_val, y_val_pred)),
                        'mae': mean_absolute_error(y_val, y_val_pred),
                        'r2': r2_score(y_val, y_val_pred)
                    }
                    evaluation['metrics']['validation'] = val_metrics
                
                evaluation['metrics']['training'] = train_metrics
                
                # Regression visualizations
                if y_val is not None:
                    viz_plots = self.viz_service.generate_regression_plots(
                        y_true=y_val,
                        y_pred=y_val_pred
                    )
                    evaluation['visualizations'] = viz_plots
                
            else:
                # Classification metrics
                y_train_proba = model.predict_proba(X_train) if hasattr(model, 'predict_proba') else None
                y_val_proba = model.predict_proba(X_val) if (X_val is not None and hasattr(model, 'predict_proba')) else None
                
                n_classes = len(np.unique(y_train))
                
                train_metrics = {
                    'accuracy': accuracy_score(y_train, y_train_pred),
                    'precision': precision_score(y_train, y_train_pred, average='weighted', zero_division=0),
                    'recall': recall_score(y_train, y_train_pred, average='weighted', zero_division=0),
                    'f1_score': f1_score(y_train, y_train_pred, average='weighted', zero_division=0)
                }
                
                if n_classes == 2 and y_train_proba is not None:
                    train_metrics['roc_auc'] = roc_auc_score(y_train, y_train_proba[:, 1])
                
                evaluation['metrics']['training'] = train_metrics
                
                if y_val_pred is not None:
                    val_metrics = {
                        'accuracy': accuracy_score(y_val, y_val_pred),
                        'precision': precision_score(y_val, y_val_pred, average='weighted', zero_division=0),
                        'recall': recall_score(y_val, y_val_pred, average='weighted', zero_division=0),
                        'f1_score': f1_score(y_val, y_val_pred, average='weighted', zero_division=0)
                    }
                    
                    if n_classes == 2 and y_val_proba is not None:
                        val_metrics['roc_auc'] = roc_auc_score(y_val, y_val_proba[:, 1])
                    
                    evaluation['metrics']['validation'] = val_metrics
                
                # Classification visualizations
                if y_val is not None:
                    # Get feature importance if available
                    feature_importance = None
                    
                    # Handle different types of models
                    if hasattr(model, 'feature_importances_'):
                        # Tree-based models (Random Forest, XGBoost, etc.)
                        importances = model.feature_importances_
                    elif hasattr(model, 'coef_'):
                        # Linear models (Logistic Regression, SVM, etc.)
                        if len(model.coef_.shape) > 1 and model.coef_.shape[0] > 1:
                            # Multi-class: use mean of absolute coefficients
                            importances = np.mean(np.abs(model.coef_), axis=0)
                        else:
                            # Binary classification: use absolute coefficients
                            importances = np.abs(model.coef_[0])
                    else:
                        importances = None
                    
                    if importances is not None:
                        # Use provided feature names or generate generic ones
                        if feature_names and len(feature_names) == len(importances):
                            feature_name_list = feature_names
                        elif hasattr(X_train, 'columns'):
                            feature_name_list = list(X_train.columns)
                        else:
                            feature_name_list = [f'feature_{i}' for i in range(len(importances))]
                        
                        feature_importance = {
                            feature_name_list[i]: float(imp)
                            for i, imp in enumerate(importances)
                        }
                    
                    viz_plots = self.viz_service.generate_classification_plots(
                        y_true=y_val,
                        y_pred=y_val_pred,
                        y_proba=y_val_proba,
                        feature_importance=feature_importance
                    )
                    evaluation['visualizations'] = viz_plots
                    
                    # Add feature importance to evaluation results
                    evaluation['feature_importance'] = feature_importance
            
            # Store predictions for analysis
            evaluation['predictions'] = {
                'train_true': y_train.tolist() if len(y_train) < 1000 else y_train[:1000].tolist(),
                'train_pred': y_train_pred.tolist() if len(y_train_pred) < 1000 else y_train_pred[:1000].tolist(),
            }
            
            if y_val_pred is not None:
                evaluation['predictions'].update({
                    'val_true': y_val.tolist() if len(y_val) < 1000 else y_val[:1000].tolist(),
                    'val_pred': y_val_pred.tolist() if len(y_val_pred) < 1000 else y_val_pred[:1000].tolist(),
                })
            
            self.monitor.log("Evaluation completed successfully")
            
        except Exception as e:
            self.monitor.log(f"Evaluation error: {str(e)}", "ERROR")
            self.logger.error(f"Evaluation error: {e}")
        
        return evaluation
    
    async def save_model_artifacts(
        self,
        model,
        results: Dict[str, Any],
        save_dir: Path,
        model_name: str = "model"
    ) -> Dict[str, str]:
        """
        Save model and all artifacts.
        
        Returns:
            Dict: Paths to saved artifacts
        """
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        artifacts = {}
        
        try:
            # Save model
            model_path = save_dir / f"{model_name}.joblib"
            joblib.dump(model, model_path)
            artifacts['model'] = str(model_path)
            self.monitor.log(f"Model saved to {model_path}")
            
            # Save metrics
            metrics_path = save_dir / f"{model_name}_metrics.json"
            with open(metrics_path, 'w') as f:
                # Convert numpy types to native Python types for JSON serialization
                metrics_json = json.loads(
                    json.dumps(results.get('metrics', {}), default=lambda x: float(x) if isinstance(x, np.floating) else int(x) if isinstance(x, np.integer) else str(x))
                )
                json.dump(metrics_json, f, indent=2)
            artifacts['metrics'] = str(metrics_path)
            
            # Save training logs
            logs_path = save_dir / f"{model_name}_logs.json"
            with open(logs_path, 'w') as f:
                json.dump(results.get('logs', []), f, indent=2)
            artifacts['logs'] = str(logs_path)
            
            # Save visualizations
            if 'visualizations' in results:
                for plot_name, plot_data in results['visualizations'].items():
                    plot_path = save_dir / f"{model_name}_{plot_name}.png"
                    # plot_data is base64, could save it
                    artifacts[f'plot_{plot_name}'] = str(plot_path)
            
            self.monitor.log(f"All artifacts saved to {save_dir}")
            
        except Exception as e:
            self.monitor.log(f"Error saving artifacts: {str(e)}", "ERROR")
            self.logger.error(f"Artifact save error: {e}")
        
        return artifacts


# Global instance
training_service = TrainingService()
