"""
ML service for machine learning operations and model management
"""
#Models: Train/evaluate/predict and download artifacts

import joblib
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, r2_score, classification_report,
    confusion_matrix, roc_auc_score, roc_curve
)
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.utils.class_weight import compute_class_weight

from app.core.config import settings
from app.core.database import get_db_context
from app.models.ml_model import MLModel, ModelType, ModelFramework
from app.models.job import Job
from app.services.visualization_service import visualization_service

logger = logging.getLogger(__name__)


class MLService:
    """Service for machine learning operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_storage_path = Path(settings.MODEL_STORAGE_PATH)
        self.model_storage_path.mkdir(exist_ok=True)
    
    def train_classification_model(
        self, 
        job_id: int,
        dataset_path: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Train a classification model.
        
        Args:
            job_id: Associated job ID
            dataset_path: Path to training dataset
            config: Training configuration
            
        Returns:
            Dict: Training results and metrics
        """
        try:
            # Load and prepare data
            X, y = self._load_and_prepare_data(
                dataset_path, 
                config.get('target_column', 'target'),
                config.get('feature_columns')
            )
            
            # Split data
            test_size = config.get('test_size', 0.2)
            random_state = config.get('random_state', 42)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
            
            # Scale features if requested
            scaler = None
            if config.get('scale_features', True):
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
                X_test = scaler.transform(X_test)
            
            # Initialize model with class imbalance handling
            algorithm = config.get('algorithm', 'random_forest')
            hyperparams = config.get('hyperparameters', {})
            hyperparams['handle_imbalance'] = config.get('handle_imbalance', False)
            model = self._get_classification_model(algorithm, hyperparams)
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
            
            # Calculate metrics
            metrics = self._calculate_classification_metrics(y_test, y_pred, y_proba)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            metrics['cv_accuracy_mean'] = cv_scores.mean()
            metrics['cv_accuracy_std'] = cv_scores.std()
            
            # Feature importance
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_names = config.get('feature_names', [f'feature_{i}' for i in range(X.shape[1])])
                feature_importance = dict(zip(feature_names, model.feature_importances_))
            
            # Generate plots if requested
            plots = {}
            if config.get('generate_plots', False):
                plots = visualization_service.generate_classification_plots(
                    y_test, y_pred, y_proba, feature_importance
                )
            
            # Save model
            model_path = self._save_model(job_id, {
                'model': model,
                'scaler': scaler,
                'feature_names': config.get('feature_names'),
                'target_names': list(np.unique(y)),
                'config': config
            })
            
            return {
                'model_path': str(model_path),
                'metrics': metrics,
                'feature_importance': feature_importance,
                'plots': plots,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'algorithm': algorithm
            }
            
        except Exception as e:
            self.logger.error(f"Error training classification model: {e}")
            raise
    
    def train_regression_model(
        self, 
        job_id: int,
        dataset_path: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Train a regression model.
        
        Args:
            job_id: Associated job ID
            dataset_path: Path to training dataset
            config: Training configuration
            
        Returns:
            Dict: Training results and metrics
        """
        try:
            # Load and prepare data (with auto-cleaning)
            X, y = self._load_and_prepare_data(
                dataset_path, 
                config.get('target_column', 'target'),
                config.get('feature_columns'),
                auto_clean=config.get('auto_preprocess', True)
            )
            
            # Split data
            test_size = config.get('test_size', 0.2)
            random_state = config.get('random_state', 42)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            
            # Scale features if requested
            scaler = None
            if config.get('scale_features', True):
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
                X_test = scaler.transform(X_test)
            
            # Initialize model
            algorithm = config.get('algorithm', 'random_forest')
            model = self._get_regression_model(algorithm, config.get('hyperparameters', {}))
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            metrics = self._calculate_regression_metrics(y_test, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='r2')
            metrics['cv_r2_mean'] = cv_scores.mean()
            metrics['cv_r2_std'] = cv_scores.std()
            
            # Feature importance
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_names = config.get('feature_names', [f'feature_{i}' for i in range(X.shape[1])])
                feature_importance = dict(zip(feature_names, model.feature_importances_))
            
            # Generate plots if requested
            plots = {}
            if config.get('generate_plots', False):
                plots = visualization_service.generate_regression_plots(
                    y_test, y_pred, feature_importance
                )
            
            # Save model
            model_path = self._save_model(job_id, {
                'model': model,
                'scaler': scaler,
                'feature_names': config.get('feature_names'),
                'config': config
            })
            
            return {
                'model_path': str(model_path),
                'plots': plots,
                'metrics': metrics,
                'feature_importance': feature_importance,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'algorithm': algorithm
            }
            
        except Exception as e:
            self.logger.error(f"Error training regression model: {e}")
            raise
    
    def predict_with_model(
        self,
        model_id: int,
        input_data: List[Dict[str, Any]],
        return_probabilities: bool = False
    ) -> Dict[str, Any]:
        """
        Make predictions with a trained model.
        
        Args:
            model_id: Model ID
            input_data: Input data for prediction
            return_probabilities: Whether to return prediction probabilities
            
        Returns:
            Dict: Prediction results
        """
        try:
            # Load model
            model_info = self._load_model(model_id)
            
            if not model_info:
                raise ValueError(f"Model {model_id} not found")
            
            model = model_info['model']
            scaler = model_info.get('scaler')
            feature_names = model_info.get('feature_names')
            
            # Prepare input data
            df = pd.DataFrame(input_data)
            
            if feature_names:
                # Ensure all required features are present
                missing_features = set(feature_names) - set(df.columns)
                if missing_features:
                    raise ValueError(f"Missing features: {missing_features}")
                
                X = df[feature_names].values
            else:
                X = df.values
            
            # Scale features if scaler was used during training
            if scaler:
                X = scaler.transform(X)
            
            # Make predictions
            predictions = model.predict(X)
            
            results = {
                'predictions': predictions.tolist(),
                'model_id': model_id,
                'input_count': len(input_data)
            }
            
            # Add probabilities for classification models
            if return_probabilities and hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X)
                results['probabilities'] = probabilities.tolist()
            
            # Update model usage count
            self._update_model_usage(model_id)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error making predictions with model {model_id}: {e}")
            raise
    
    def _load_and_prepare_data(
        self,
        dataset_path: str,
        target_column: str,
        feature_columns: Optional[List[str]] = None,
        auto_clean: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load and prepare dataset for training with automatic data cleaning.
        
        This implements the data preparation steps from your specification:
        - Load CSV data
        - Remove NaNs 
        - Handle categorical variables
        - Basic data validation
        """
        
        # Load dataset
        if dataset_path.endswith('.csv'):
            df = pd.read_csv(dataset_path)
        elif dataset_path.endswith('.tsv'):
            df = pd.read_csv(dataset_path, sep='\t')
        else:
            raise ValueError(f"Unsupported file format: {dataset_path}")
        
        # Validate target column exists
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset")
        
        # Automatic data cleaning if requested
        if auto_clean:
            # Remove rows with missing target values
            df = df.dropna(subset=[target_column])
            
            # For features, either drop or fill missing values
            if feature_columns:
                feature_cols = feature_columns
            else:
                feature_cols = [col for col in df.columns if col != target_column]
            
            # Drop rows where too many features are missing (>50%)
            df = df.dropna(subset=feature_cols, thresh=len(feature_cols) * 0.5)
            
            # Fill remaining missing values with median (numeric) or mode (categorical)
            for col in feature_cols:
                if df[col].dtype in ['object', 'category']:
                    # Categorical: fill with mode
                    mode_val = df[col].mode()
                    if len(mode_val) > 0:
                        df[col] = df[col].fillna(mode_val[0])
                else:
                    # Numeric: fill with median
                    df[col] = df[col].fillna(df[col].median())
        
        # Prepare features and target
        if feature_columns:
            X = df[feature_columns]
        else:
            # Use all columns except target
            feature_cols = [col for col in df.columns if col != target_column]
            X = df[feature_cols]
        
        y = df[target_column]
        
        # Handle categorical features - simple label encoding for now
        for col in X.select_dtypes(include=['object', 'category']).columns:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
        
        # Convert to numpy arrays
        X = X.values
        y = y.values
        
        # Handle categorical target for classification
        if not np.issubdtype(y.dtype, np.number):
            le = LabelEncoder()
            y = le.fit_transform(y)
        
        self.logger.info(f"Data prepared: {X.shape[0]} samples, {X.shape[1]} features")
        
        return X, y
    
    def _get_classification_model(self, algorithm: str, hyperparameters: Dict[str, Any]):
        """Get classification model instance with class imbalance handling"""
        
        # Handle class imbalance by setting class weights
        class_weight = None
        if hyperparameters.get('handle_imbalance', False):
            class_weight = 'balanced'
        
        if algorithm == 'random_forest':
            return RandomForestClassifier(
                n_estimators=hyperparameters.get('n_estimators', 100),
                max_depth=hyperparameters.get('max_depth'),
                min_samples_split=hyperparameters.get('min_samples_split', 2),
                min_samples_leaf=hyperparameters.get('min_samples_leaf', 1),
                class_weight=class_weight,
                random_state=hyperparameters.get('random_state', 42)
            )
        elif algorithm == 'logistic_regression':
            return LogisticRegression(
                C=hyperparameters.get('C', 1.0),
                max_iter=hyperparameters.get('max_iter', 1000),
                class_weight=class_weight,
                random_state=hyperparameters.get('random_state', 42)
            )
        else:
            raise ValueError(f"Unsupported classification algorithm: {algorithm}")
    
    def _get_regression_model(self, algorithm: str, hyperparameters: Dict[str, Any]):
        """Get regression model instance"""
        
        if algorithm == 'random_forest':
            return RandomForestRegressor(
                n_estimators=hyperparameters.get('n_estimators', 100),
                max_depth=hyperparameters.get('max_depth'),
                min_samples_split=hyperparameters.get('min_samples_split', 2),
                min_samples_leaf=hyperparameters.get('min_samples_leaf', 1),
                random_state=hyperparameters.get('random_state', 42)
            )
        elif algorithm == 'linear_regression':
            return LinearRegression()
        else:
            raise ValueError(f"Unsupported regression algorithm: {algorithm}")
    
    def _calculate_classification_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Calculate classification metrics"""
        
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted'),
            'recall': recall_score(y_true, y_pred, average='weighted'),
            'f1_score': f1_score(y_true, y_pred, average='weighted'),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
            'classification_report': classification_report(y_true, y_pred, output_dict=True)
        }
        
        # Add AUC for binary classification
        if len(np.unique(y_true)) == 2 and y_proba is not None:
            metrics['auc_roc'] = roc_auc_score(y_true, y_proba[:, 1])
            
            # ROC curve data
            fpr, tpr, thresholds = roc_curve(y_true, y_proba[:, 1])
            metrics['roc_curve'] = {
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist(),
                'thresholds': thresholds.tolist()
            }
        
        return metrics
    
    def _calculate_regression_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, Any]:
        """Calculate regression metrics"""
        
        return {
            'r2_score': r2_score(y_true, y_pred),
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': np.mean(np.abs(y_true - y_pred))
        }
    
    def _save_model(self, job_id: int, model_info: Dict[str, Any]) -> Path:
        """Save trained model to disk"""
        
        model_dir = self.model_storage_path / f"job_{job_id}"
        model_dir.mkdir(exist_ok=True)
        
        model_path = model_dir / "model.joblib"
        
        # Save using joblib for sklearn models
        joblib.dump(model_info, model_path)
        
        self.logger.info(f"Model saved to {model_path}")
        return model_path
    
    def _load_model(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Load trained model from disk"""
        
        with get_db_context() as db:
            model_record = db.query(MLModel).filter(MLModel.id == model_id).first()
            
            if not model_record or not model_record.artifact_path:
                return None
            
            try:
                model_info = joblib.load(model_record.artifact_path)
                return model_info
            except Exception as e:
                self.logger.error(f"Error loading model {model_id}: {e}")
                return None
    
    def _update_model_usage(self, model_id: int) -> None:
        """Update model usage statistics"""
        
        with get_db_context() as db:
            model = db.query(MLModel).filter(MLModel.id == model_id).first()
            
            if model:
                model.increment_prediction_count()
                db.commit()

    def evaluate_model(
        self,
        model_id: int,
        test_dataset_path: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a trained model on a test dataset and return metrics."""
        try:
            model_info = self._load_model(model_id)
            if not model_info:
                raise ValueError(f"Model {model_id} not found")

            model = model_info['model']
            scaler = model_info.get('scaler')
            feature_names = model_info.get('feature_names')

            target_column = config.get('target_column', 'target')
            feature_columns = config.get('feature_columns') or feature_names

            X, y = self._load_and_prepare_data(
                test_dataset_path,
                target_column,
                feature_columns
            )

            if scaler:
                X = scaler.transform(X)

            y_pred = model.predict(X)
            y_proba = model.predict_proba(X) if hasattr(model, 'predict_proba') else None

            # Determine task type by y dtype or config
            task_type = config.get('model_type')
            if task_type is None:
                # Heuristic: if y has few unique values -> classification
                task_type = 'classification' if len(np.unique(y)) <= 20 else 'regression'

            if task_type == 'classification':
                metrics = self._calculate_classification_metrics(y, y_pred, y_proba)
            else:
                metrics = self._calculate_regression_metrics(y, y_pred)

            return {
                'model_id': model_id,
                'metrics': metrics,
                'samples': len(y),
            }
        except Exception as e:
            logger.error(f"Error evaluating model {model_id}: {e}")
            raise
