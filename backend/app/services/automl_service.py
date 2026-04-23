"""
AutoML service for intelligent model selection and configuration
Automatically selects best models based on task type and data characteristics
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.svm import SVC, SVR
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
import xgboost as xgb

logger = logging.getLogger(__name__)


class AutoMLService:
    """
    Intelligent AutoML service for bioinformatics tasks.
    Selects optimal algorithms based on task type and dataset characteristics.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define task-specific model recommendations
        self.task_models = {
            'protein_classification': [
                'random_forest', 'xgboost', 'svm', 'gradient_boosting'
            ],
            'dna_classification': [
                'random_forest', 'xgboost', 'gradient_boosting', 'logistic_regression'
            ],
            'rna_classification': [
                'random_forest', 'xgboost', 'gradient_boosting'
            ],
            'protein_function_prediction': [
                'random_forest', 'xgboost', 'neural_network', 'svm'
            ],
            'gene_expression': [
                'random_forest', 'xgboost', 'ridge_regression', 'gradient_boosting'
            ],
            'general_classification': [
                'random_forest', 'xgboost', 'logistic_regression', 'gradient_boosting', 'svm'
            ],
            'general_regression': [
                'random_forest', 'xgboost', 'ridge_regression', 'gradient_boosting', 'svr'
            ]
        }
    
    def select_models(
        self,
        task_type: str,
        data_characteristics: Dict[str, Any],
        n_models: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Select best models for the given task and data.
        
        Args:
            task_type: Type of ML task (e.g., 'protein_classification')
            data_characteristics: Dict with data info (n_samples, n_features, etc.)
            n_models: Number of models to recommend
            
        Returns:
            List of model configurations
        """
        self.logger.info(f"Selecting models for task: {task_type}")
        
        # Get recommended models for this task
        recommended_models = self.task_models.get(
            task_type,
            self.task_models['general_classification']
        )
        
        # Analyze data characteristics to refine selection
        n_samples = data_characteristics.get('n_samples', 0)
        n_features = data_characteristics.get('n_features', 0)
        n_classes = data_characteristics.get('n_classes', 2)
        
        # Filter and rank models based on data characteristics
        ranked_models = self._rank_models(
            recommended_models,
            n_samples,
            n_features,
            n_classes,
            task_type
        )
        
        # Return top n_models with configurations
        selected_models = []
        for model_name in ranked_models[:n_models]:
            config = self._get_model_config(model_name, data_characteristics)
            selected_models.append(config)
        
        return selected_models
    
    def _rank_models(
        self,
        models: List[str],
        n_samples: int,
        n_features: int,
        n_classes: int,
        task_type: str
    ) -> List[str]:
        """Rank models based on data characteristics"""
        scores = {}
        
        for model_name in models:
            score = 100  # Base score
            
            # Adjust based on sample size
            if n_samples < 1000:
                if model_name in ['logistic_regression', 'naive_bayes', 'knn']:
                    score += 20
                elif model_name in ['xgboost', 'neural_network']:
                    score -= 20
            elif n_samples > 10000:
                if model_name in ['xgboost', 'gradient_boosting', 'neural_network']:
                    score += 20
                elif model_name in ['knn']:
                    score -= 30
            
            # Adjust based on feature count
            if n_features > 100:
                if model_name in ['random_forest', 'xgboost', 'gradient_boosting']:
                    score += 15
                elif model_name in ['logistic_regression', 'naive_bayes']:
                    score -= 10
            
            # Adjust based on number of classes
            if n_classes > 10:
                if model_name in ['random_forest', 'xgboost']:
                    score += 10
                elif model_name in ['svm']:
                    score -= 15
            
            # Bioinformatics task preferences
            if 'protein' in task_type or 'dna' in task_type:
                if model_name in ['random_forest', 'xgboost']:
                    score += 25
            
            scores[model_name] = score
        
        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [name for name, score in ranked]
    
    def _get_model_config(
        self,
        model_name: str,
        data_characteristics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get model configuration with hyperparameters"""
        n_samples = data_characteristics.get('n_samples', 0)
        n_features = data_characteristics.get('n_features', 0)
        n_classes = data_characteristics.get('n_classes', 2)
        is_regression = 'regression' in data_characteristics.get('task_type', '')
        
        configs = {
            'random_forest': {
                'name': 'Random Forest',
                'model_type': 'random_forest',
                'algorithm': 'ensemble',
                'params': {
                    'n_estimators': 100 if n_samples < 10000 else 200,
                    'max_depth': None if n_samples > 1000 else 20,
                    'min_samples_split': 2,
                    'min_samples_leaf': 1,
                    'max_features': 'sqrt' if not is_regression else 'auto',
                    'random_state': 42,
                    'n_jobs': -1
                },
                'description': 'Robust ensemble method, works well for biological data',
                'pros': ['Handles high dimensions', 'Feature importance', 'No scaling needed'],
                'cons': ['Can overfit on noisy data', 'Slower prediction']
            },
            'xgboost': {
                'name': 'XGBoost',
                'model_type': 'xgboost',
                'algorithm': 'gradient_boosting',
                'params': {
                    'n_estimators': 100,
                    'max_depth': 6 if n_samples > 1000 else 4,
                    'learning_rate': 0.1,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'objective': 'multi:softprob' if n_classes > 2 else 'binary:logistic',
                    'random_state': 42,
                    'n_jobs': -1,
                    'eval_metric': 'mlogloss' if n_classes > 2 else 'logloss'
                },
                'description': 'State-of-the-art gradient boosting, excellent for structured data',
                'pros': ['High accuracy', 'Fast training', 'Handles missing values'],
                'cons': ['Requires tuning', 'Can overfit']
            },
            'gradient_boosting': {
                'name': 'Gradient Boosting',
                'model_type': 'gradient_boosting',
                'algorithm': 'gradient_boosting',
                'params': {
                    'n_estimators': 100,
                    'learning_rate': 0.1,
                    'max_depth': 3,
                    'subsample': 0.8,
                    'random_state': 42
                },
                'description': 'Powerful ensemble method with sequential learning',
                'pros': ['High accuracy', 'Feature importance', 'Flexible'],
                'cons': ['Slower training', 'Sensitive to overfitting']
            },
            'svm': {
                'name': 'Support Vector Machine',
                'model_type': 'svm',
                'algorithm': 'support_vector',
                'params': {
                    'C': 1.0,
                    'kernel': 'rbf',
                    'gamma': 'scale',
                    'probability': True,
                    'random_state': 42
                },
                'description': 'Effective for high-dimensional spaces',
                'pros': ['Works well with limited samples', 'Effective in high dimensions'],
                'cons': ['Slow with large datasets', 'Requires scaling']
            },
            'logistic_regression': {
                'name': 'Logistic Regression',
                'model_type': 'logistic_regression',
                'algorithm': 'linear',
                'params': {
                    'C': 1.0,
                    'max_iter': 1000,
                    'random_state': 42,
                    'n_jobs': -1
                },
                'description': 'Simple and interpretable linear model',
                'pros': ['Fast', 'Interpretable', 'Probabilistic output'],
                'cons': ['Linear decision boundary', 'May underfit complex data']
            },
            'ridge_regression': {
                'name': 'Ridge Regression',
                'model_type': 'ridge_regression',
                'algorithm': 'linear',
                'params': {
                    'alpha': 1.0,
                    'random_state': 42
                },
                'description': 'Linear regression with L2 regularization',
                'pros': ['Handles multicollinearity', 'Fast', 'Stable'],
                'cons': ['Linear assumptions', 'May underfit']
            },
            'knn': {
                'name': 'K-Nearest Neighbors',
                'model_type': 'knn',
                'algorithm': 'instance_based',
                'params': {
                    'n_neighbors': min(5, n_samples // 10) if n_samples > 50 else 3,
                    'weights': 'distance',
                    'n_jobs': -1
                },
                'description': 'Instance-based learning algorithm',
                'pros': ['Simple', 'No training phase', 'Non-parametric'],
                'cons': ['Slow prediction', 'Memory intensive', 'Sensitive to scaling']
            },
            'naive_bayes': {
                'name': 'Gaussian Naive Bayes',
                'model_type': 'naive_bayes',
                'algorithm': 'probabilistic',
                'params': {},
                'description': 'Fast probabilistic classifier',
                'pros': ['Very fast', 'Works with small datasets', 'Probabilistic'],
                'cons': ['Independence assumption', 'May underfit']
            },
            'decision_tree': {
                'name': 'Decision Tree',
                'model_type': 'decision_tree',
                'algorithm': 'tree',
                'params': {
                    'max_depth': 10 if n_samples < 1000 else None,
                    'min_samples_split': 2,
                    'min_samples_leaf': 1,
                    'random_state': 42
                },
                'description': 'Simple tree-based model',
                'pros': ['Interpretable', 'No scaling needed', 'Handles non-linear'],
                'cons': ['Prone to overfitting', 'Unstable']
            },
            'svr': {
                'name': 'Support Vector Regression',
                'model_type': 'svr',
                'algorithm': 'support_vector',
                'params': {
                    'C': 1.0,
                    'kernel': 'rbf',
                    'gamma': 'scale'
                },
                'description': 'SVM for regression tasks',
                'pros': ['Works in high dimensions', 'Robust to outliers'],
                'cons': ['Slow with large datasets', 'Requires scaling']
            }
        }
        
        return configs.get(model_name, configs['random_forest'])
    
    def get_model_instance(
        self,
        model_config: Dict[str, Any],
        is_regression: bool = False
    ):
        """
        Get actual sklearn/xgboost model instance.
        
        Args:
            model_config: Model configuration dict
            is_regression: Whether this is a regression task
            
        Returns:
            Initialized model instance
        """
        model_type = model_config['model_type']
        params = model_config['params']
        
        try:
            if model_type == 'random_forest':
                if is_regression:
                    return RandomForestRegressor(**params)
                return RandomForestClassifier(**params)
            
            elif model_type == 'xgboost':
                if is_regression:
                    params['objective'] = 'reg:squarederror'
                    params['eval_metric'] = 'rmse'
                    return xgb.XGBRegressor(**params)
                return xgb.XGBClassifier(**params)
            
            elif model_type == 'gradient_boosting':
                if is_regression:
                    return GradientBoostingRegressor(**params)
                return GradientBoostingClassifier(**params)
            
            elif model_type == 'svm':
                if is_regression:
                    return SVR(**{k: v for k, v in params.items() if k != 'probability'})
                return SVC(**params)
            
            elif model_type == 'logistic_regression':
                return LogisticRegression(**params)
            
            elif model_type == 'ridge_regression':
                return Ridge(**params)
            
            elif model_type == 'knn':
                if is_regression:
                    return KNeighborsRegressor(**params)
                return KNeighborsClassifier(**params)
            
            elif model_type == 'naive_bayes':
                return GaussianNB(**params)
            
            elif model_type == 'decision_tree':
                if is_regression:
                    return DecisionTreeRegressor(**params)
                return DecisionTreeClassifier(**params)
            
            elif model_type == 'svr':
                return SVR(**params)
            
            else:
                self.logger.warning(f"Unknown model type: {model_type}, defaulting to Random Forest")
                if is_regression:
                    return RandomForestRegressor(random_state=42)
                return RandomForestClassifier(random_state=42)
                
        except Exception as e:
            self.logger.error(f"Error creating model instance: {e}")
            if is_regression:
                return RandomForestRegressor(random_state=42)
            return RandomForestClassifier(random_state=42)
    
    def suggest_task_type(
        self,
        dataset_type: str,
        has_labels: bool,
        n_classes: Optional[int] = None
    ) -> str:
        """
        Suggest task type based on dataset characteristics.
        
        Args:
            dataset_type: Type of dataset (dna, protein, rna, general)
            has_labels: Whether dataset has labels
            n_classes: Number of classes if classification
            
        Returns:
            Suggested task type
        """
        if not has_labels:
            return 'clustering'
        
        if dataset_type == 'protein':
            return 'protein_classification'
        elif dataset_type == 'dna':
            return 'dna_classification'
        elif dataset_type == 'rna':
            return 'rna_classification'
        elif n_classes and n_classes > 1:
            return 'general_classification'
        else:
            return 'general_regression'
    
    def get_hyperparameter_grid(self, model_type: str) -> Dict[str, List]:
        """Get hyperparameter search grid for optimization"""
        grids = {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            },
            'xgboost': {
                'n_estimators': [50, 100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.3],
                'subsample': [0.7, 0.8, 0.9],
                'colsample_bytree': [0.7, 0.8, 0.9]
            },
            'svm': {
                'C': [0.1, 1, 10, 100],
                'kernel': ['rbf', 'linear'],
                'gamma': ['scale', 'auto', 0.1, 0.01]
            },
            'logistic_regression': {
                'C': [0.01, 0.1, 1, 10, 100],
                'penalty': ['l2'],
                'solver': ['lbfgs', 'liblinear']
            }
        }
        
        return grids.get(model_type, {})


# Global instance
automl_service = AutoMLService()
