"""
Enhanced Model Builder Service for drag-and-drop model configuration
"""

import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    AdaBoostClassifier, AdaBoostRegressor
)
from sklearn.linear_model import (
    LogisticRegression, LinearRegression, Ridge, Lasso,
    ElasticNet, SGDClassifier, SGDRegressor
)
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


class ModelBuilderService:
    """Service for building ML models through drag-and-drop configuration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.available_algorithms = self._initialize_algorithms()
        self.available_preprocessors = self._initialize_preprocessors()
        self.hyperparameter_grids = self._initialize_hyperparameter_grids()
    
    def _initialize_algorithms(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available ML algorithms with metadata"""
        return {
            # Classification Algorithms
            "random_forest_classifier": {
                "class": RandomForestClassifier,
                "type": "classification",
                "category": "ensemble",
                "description": "Random Forest Classifier - Ensemble of decision trees",
                "pros": ["Handles overfitting well", "Feature importance", "Works with missing values"],
                "cons": ["Can be slow on large datasets", "Less interpretable"],
                "use_cases": ["General classification", "Feature selection", "Biological classification"],
                "complexity": "medium"
            },
            "logistic_regression": {
                "class": LogisticRegression,
                "type": "classification",
                "category": "linear",
                "description": "Logistic Regression - Linear classification algorithm",
                "pros": ["Fast", "Interpretable", "Probabilistic output"],
                "cons": ["Assumes linear relationship", "Sensitive to outliers"],
                "use_cases": ["Binary classification", "Baseline model", "Linear separable data"],
                "complexity": "low"
            },
            "svm_classifier": {
                "class": SVC,
                "type": "classification",
                "category": "kernel",
                "description": "Support Vector Machine - Kernel-based classification",
                "pros": ["Effective in high dimensions", "Memory efficient", "Versatile kernels"],
                "cons": ["Slow on large datasets", "Sensitive to scaling"],
                "use_cases": ["High-dimensional data", "Text classification", "Image classification"],
                "complexity": "high"
            },
            "gradient_boosting_classifier": {
                "class": GradientBoostingClassifier,
                "type": "classification",
                "category": "ensemble",
                "description": "Gradient Boosting - Sequential ensemble method",
                "pros": ["High accuracy", "Handles mixed data types", "Feature importance"],
                "cons": ["Prone to overfitting", "Computationally expensive"],
                "use_cases": ["Structured data", "Competitions", "High accuracy needs"],
                "complexity": "high"
            },
            "knn_classifier": {
                "class": KNeighborsClassifier,
                "type": "classification",
                "category": "instance_based",
                "description": "K-Nearest Neighbors - Instance-based learning",
                "pros": ["Simple", "No assumptions about data", "Works well locally"],
                "cons": ["Computationally expensive", "Sensitive to irrelevant features"],
                "use_cases": ["Small datasets", "Non-linear patterns", "Recommendation systems"],
                "complexity": "low"
            },
            "naive_bayes": {
                "class": GaussianNB,
                "type": "classification",
                "category": "probabilistic",
                "description": "Naive Bayes - Probabilistic classifier",
                "pros": ["Fast", "Works with small datasets", "Handles multiple classes"],
                "cons": ["Strong independence assumption", "Can be outperformed"],
                "use_cases": ["Text classification", "Medical diagnosis", "Spam filtering"],
                "complexity": "low"
            },
            "decision_tree_classifier": {
                "class": DecisionTreeClassifier,
                "type": "classification",
                "category": "tree",
                "description": "Decision Tree - Tree-based classification",
                "pros": ["Highly interpretable", "No data preprocessing needed", "Handles mixed data"],
                "cons": ["Prone to overfitting", "Unstable"],
                "use_cases": ["Rule extraction", "Medical diagnosis", "Interpretable models"],
                "complexity": "medium"
            },
            "mlp_classifier": {
                "class": MLPClassifier,
                "type": "classification",
                "category": "neural_network",
                "description": "Multi-layer Perceptron - Neural network classifier",
                "pros": ["Can learn complex patterns", "Flexible architecture", "Universal approximator"],
                "cons": ["Requires large datasets", "Many hyperparameters", "Black box"],
                "use_cases": ["Complex patterns", "Large datasets", "Non-linear relationships"],
                "complexity": "high"
            },
            
            # Regression Algorithms
            "random_forest_regressor": {
                "class": RandomForestRegressor,
                "type": "regression",
                "category": "ensemble",
                "description": "Random Forest Regressor - Ensemble of decision trees",
                "pros": ["Handles overfitting well", "Feature importance", "Works with missing values"],
                "cons": ["Can be slow on large datasets", "Less interpretable"],
                "use_cases": ["General regression", "Feature selection", "Biological predictions"],
                "complexity": "medium"
            },
            "linear_regression": {
                "class": LinearRegression,
                "type": "regression",
                "category": "linear",
                "description": "Linear Regression - Simple linear relationship modeling",
                "pros": ["Fast", "Interpretable", "No hyperparameters"],
                "cons": ["Assumes linear relationship", "Sensitive to outliers"],
                "use_cases": ["Linear relationships", "Baseline model", "Simple predictions"],
                "complexity": "low"
            },
            "ridge_regression": {
                "class": Ridge,
                "type": "regression",
                "category": "linear",
                "description": "Ridge Regression - Linear regression with L2 regularization",
                "pros": ["Handles multicollinearity", "Prevents overfitting", "Stable"],
                "cons": ["Doesn't perform feature selection", "Assumes linear relationship"],
                "use_cases": ["High-dimensional data", "Multicollinearity", "Regularization needed"],
                "complexity": "low"
            },
            "lasso_regression": {
                "class": Lasso,
                "type": "regression",
                "category": "linear",
                "description": "Lasso Regression - Linear regression with L1 regularization",
                "pros": ["Feature selection", "Prevents overfitting", "Sparse solutions"],
                "cons": ["Can be unstable", "Assumes linear relationship"],
                "use_cases": ["Feature selection", "High-dimensional data", "Sparse models"],
                "complexity": "low"
            },
            "svm_regressor": {
                "class": SVR,
                "type": "regression",
                "category": "kernel",
                "description": "Support Vector Regression - Kernel-based regression",
                "pros": ["Effective in high dimensions", "Memory efficient", "Robust to outliers"],
                "cons": ["Slow on large datasets", "Sensitive to scaling"],
                "use_cases": ["High-dimensional data", "Non-linear relationships", "Robust predictions"],
                "complexity": "high"
            },
            "gradient_boosting_regressor": {
                "class": GradientBoostingRegressor,
                "type": "regression",
                "category": "ensemble",
                "description": "Gradient Boosting Regressor - Sequential ensemble method",
                "pros": ["High accuracy", "Handles mixed data types", "Feature importance"],
                "cons": ["Prone to overfitting", "Computationally expensive"],
                "use_cases": ["Structured data", "High accuracy needs", "Complex patterns"],
                "complexity": "high"
            },
            
            # Clustering Algorithms
            "kmeans": {
                "class": KMeans,
                "type": "clustering",
                "category": "centroid",
                "description": "K-Means - Centroid-based clustering",
                "pros": ["Fast", "Simple", "Works well with spherical clusters"],
                "cons": ["Need to specify k", "Sensitive to initialization", "Assumes spherical clusters"],
                "use_cases": ["Customer segmentation", "Gene clustering", "Data exploration"],
                "complexity": "low"
            },
            "dbscan": {
                "class": DBSCAN,
                "type": "clustering",
                "category": "density",
                "description": "DBSCAN - Density-based clustering",
                "pros": ["Finds arbitrary shapes", "Handles noise", "No need to specify clusters"],
                "cons": ["Sensitive to parameters", "Struggles with varying densities"],
                "use_cases": ["Anomaly detection", "Irregular clusters", "Noise handling"],
                "complexity": "medium"
            }
        }
    
    def _initialize_preprocessors(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available preprocessing steps"""
        return {
            "standard_scaler": {
                "class": StandardScaler,
                "description": "Standardize features by removing mean and scaling to unit variance",
                "use_cases": ["Most algorithms", "When features have different scales"],
                "parameters": {}
            },
            "minmax_scaler": {
                "class": MinMaxScaler,
                "description": "Scale features to a given range (default 0-1)",
                "use_cases": ["Neural networks", "When you need bounded values"],
                "parameters": {"feature_range": (0, 1)}
            },
            "robust_scaler": {
                "class": RobustScaler,
                "description": "Scale features using statistics robust to outliers",
                "use_cases": ["When data contains outliers", "Robust preprocessing"],
                "parameters": {}
            }
        }
    
    def _initialize_hyperparameter_grids(self) -> Dict[str, Dict[str, List]]:
        """Initialize hyperparameter grids for automatic tuning"""
        return {
            "random_forest_classifier": {
                "n_estimators": [50, 100, 200],
                "max_depth": [None, 10, 20, 30],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4]
            },
            "random_forest_regressor": {
                "n_estimators": [50, 100, 200],
                "max_depth": [None, 10, 20, 30],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4]
            },
            "logistic_regression": {
                "C": [0.1, 1.0, 10.0],
                "penalty": ["l1", "l2"],
                "solver": ["liblinear", "saga"]
            },
            "svm_classifier": {
                "C": [0.1, 1, 10],
                "kernel": ["linear", "rbf", "poly"],
                "gamma": ["scale", "auto"]
            },
            "gradient_boosting_classifier": {
                "n_estimators": [50, 100, 200],
                "learning_rate": [0.01, 0.1, 0.2],
                "max_depth": [3, 5, 7]
            },
            "knn_classifier": {
                "n_neighbors": [3, 5, 7, 9],
                "weights": ["uniform", "distance"],
                "metric": ["euclidean", "manhattan"]
            },
            "ridge_regression": {
                "alpha": [0.1, 1.0, 10.0, 100.0]
            },
            "lasso_regression": {
                "alpha": [0.1, 1.0, 10.0, 100.0]
            },
            "kmeans": {
                "n_clusters": [2, 3, 4, 5, 6, 7, 8],
                "init": ["k-means++", "random"],
                "n_init": [10, 20]
            }
        }
    
    def get_available_algorithms(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """Get list of available algorithms, optionally filtered by task type"""
        if task_type:
            return {
                name: info for name, info in self.available_algorithms.items()
                if info["type"] == task_type
            }
        return self.available_algorithms
    
    def get_algorithm_info(self, algorithm_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific algorithm"""
        if algorithm_name not in self.available_algorithms:
            raise ValueError(f"Algorithm '{algorithm_name}' not found")
        return self.available_algorithms[algorithm_name]
    
    def build_model_pipeline(self, config: Dict[str, Any]) -> Pipeline:
        """
        Build a scikit-learn pipeline from configuration.
        
        Args:
            config: Model configuration dictionary
            
        Returns:
            Configured scikit-learn Pipeline
        """
        steps = []
        
        # Add preprocessing steps
        if "preprocessing" in config:
            for prep_step in config["preprocessing"]:
                prep_name = prep_step["name"]
                prep_params = prep_step.get("parameters", {})
                
                if prep_name in self.available_preprocessors:
                    prep_class = self.available_preprocessors[prep_name]["class"]
                    preprocessor = prep_class(**prep_params)
                    steps.append((prep_name, preprocessor))
        
        # Add model step
        algorithm_name = config["algorithm"]
        algorithm_params = config.get("hyperparameters", {})
        
        if algorithm_name not in self.available_algorithms:
            raise ValueError(f"Algorithm '{algorithm_name}' not supported")
        
        model_class = self.available_algorithms[algorithm_name]["class"]
        model = model_class(**algorithm_params)
        steps.append(("model", model))
        
        return Pipeline(steps)
    
    def suggest_algorithms(self, 
                          dataset_info: Dict[str, Any], 
                          task_type: str,
                          max_suggestions: int = 5) -> List[Dict[str, Any]]:
        """
        Suggest suitable algorithms based on dataset characteristics.
        
        Args:
            dataset_info: Information about the dataset
            task_type: Type of ML task (classification, regression, clustering)
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of suggested algorithms with scores
        """
        suggestions = []
        
        # Get dataset characteristics
        n_samples = dataset_info.get("n_samples", 0)
        n_features = dataset_info.get("n_features", 0)
        dataset_size = dataset_info.get("file_size_mb", 0)
        
        # Filter algorithms by task type
        candidate_algorithms = {
            name: info for name, info in self.available_algorithms.items()
            if info["type"] == task_type
        }
        
        for name, info in candidate_algorithms.items():
            score = 0
            reasons = []
            
            # Score based on dataset size
            if dataset_size < 10:  # Small dataset
                if info["complexity"] in ["low", "medium"]:
                    score += 2
                    reasons.append("Good for small datasets")
            elif dataset_size > 100:  # Large dataset
                if name in ["logistic_regression", "linear_regression", "sgd_classifier"]:
                    score += 2
                    reasons.append("Efficient for large datasets")
            
            # Score based on number of features
            if n_features > 1000:  # High-dimensional
                if info["category"] in ["linear", "kernel"]:
                    score += 1
                    reasons.append("Handles high-dimensional data well")
            
            # Score based on interpretability needs (assume medium importance)
            if info["complexity"] == "low":
                score += 1
                reasons.append("Interpretable model")
            
            # Default scoring
            if info["complexity"] == "medium":
                score += 1
            
            suggestions.append({
                "algorithm": name,
                "score": score,
                "info": info,
                "reasons": reasons
            })
        
        # Sort by score and return top suggestions
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions[:max_suggestions]
    
    def optimize_hyperparameters(self,
                                pipeline: Pipeline,
                                X: np.ndarray,
                                y: np.ndarray,
                                method: str = "grid_search",
                                cv: int = 5,
                                n_iter: int = 50) -> Tuple[Pipeline, Dict[str, Any]]:
        """
        Optimize hyperparameters for the model pipeline.
        
        Args:
            pipeline: Scikit-learn pipeline
            X: Feature matrix
            y: Target vector
            method: Optimization method ('grid_search' or 'random_search')
            cv: Number of cross-validation folds
            n_iter: Number of iterations for random search
            
        Returns:
            Tuple of (optimized_pipeline, optimization_results)
        """
        # Get the algorithm name from the pipeline
        model_step = pipeline.named_steps["model"]
        algorithm_name = None
        
        for name, info in self.available_algorithms.items():
            if isinstance(model_step, info["class"]):
                algorithm_name = name
                break
        
        if not algorithm_name or algorithm_name not in self.hyperparameter_grids:
            return pipeline, {"message": "No hyperparameter grid available"}
        
        # Create parameter grid for pipeline
        param_grid = {}
        for param, values in self.hyperparameter_grids[algorithm_name].items():
            param_grid[f"model__{param}"] = values
        
        # Perform hyperparameter optimization
        if method == "grid_search":
            search = GridSearchCV(
                pipeline, param_grid, cv=cv, scoring="accuracy", n_jobs=-1
            )
        else:  # random_search
            search = RandomizedSearchCV(
                pipeline, param_grid, cv=cv, n_iter=n_iter, 
                scoring="accuracy", n_jobs=-1
            )
        
        search.fit(X, y)
        
        optimization_results = {
            "best_score": search.best_score_,
            "best_params": search.best_params_,
            "cv_results": {
                "mean_test_score": search.cv_results_["mean_test_score"].tolist(),
                "std_test_score": search.cv_results_["std_test_score"].tolist(),
                "params": search.cv_results_["params"]
            }
        }
        
        return search.best_estimator_, optimization_results
    
    def validate_model_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate model configuration and return validation results.
        
        Args:
            config: Model configuration dictionary
            
        Returns:
            Validation results with errors and warnings
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Check required fields
        if "algorithm" not in config:
            validation_result["errors"].append("Algorithm not specified")
            validation_result["is_valid"] = False
        
        # Validate algorithm
        algorithm = config.get("algorithm")
        if algorithm and algorithm not in self.available_algorithms:
            validation_result["errors"].append(f"Unknown algorithm: {algorithm}")
            validation_result["is_valid"] = False
        
        # Validate hyperparameters
        if algorithm and "hyperparameters" in config:
            algo_info = self.available_algorithms[algorithm]
            model_class = algo_info["class"]
            
            try:
                # Try to instantiate the model with given parameters
                model_class(**config["hyperparameters"])
            except Exception as e:
                validation_result["errors"].append(f"Invalid hyperparameters: {str(e)}")
                validation_result["is_valid"] = False
        
        # Validate preprocessing steps
        if "preprocessing" in config:
            for step in config["preprocessing"]:
                if "name" not in step:
                    validation_result["errors"].append("Preprocessing step missing name")
                    validation_result["is_valid"] = False
                elif step["name"] not in self.available_preprocessors:
                    validation_result["errors"].append(f"Unknown preprocessor: {step['name']}")
                    validation_result["is_valid"] = False
        
        # Add suggestions
        if algorithm:
            algo_info = self.available_algorithms[algorithm]
            if algo_info["complexity"] == "high":
                validation_result["suggestions"].append(
                    "Consider using cross-validation for hyperparameter tuning"
                )
            if algo_info["category"] == "kernel":
                validation_result["suggestions"].append(
                    "Consider adding feature scaling for better performance"
                )
        
        return validation_result
    
    def export_model_config(self, config: Dict[str, Any], format: str = "json") -> str:
        """Export model configuration to specified format"""
        if format == "json":
            return json.dumps(config, indent=2)
        elif format == "yaml":
            import yaml
            return yaml.dump(config, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_model_config(self, config_str: str, format: str = "json") -> Dict[str, Any]:
        """Import model configuration from specified format"""
        if format == "json":
            return json.loads(config_str)
        elif format == "yaml":
            import yaml
            return yaml.safe_load(config_str)
        else:
            raise ValueError(f"Unsupported import format: {format}")


# Initialize global instance
model_builder_service = ModelBuilderService()
