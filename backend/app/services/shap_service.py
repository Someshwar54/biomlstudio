"""
SHAP (SHapley Additive exPlanations) Service
Provides model interpretation and explainability using SHAP values.
"""
import shap
import numpy as np
import pandas as pd
import joblib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import matplotlib.pyplot as plt
import io
import base64

logger = logging.getLogger(__name__)


class SHAPService:
    """Service for generating SHAP explanations for ML models"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Use non-interactive backend for matplotlib
        plt.switch_backend('Agg')
    
    def generate_shap_explanations(
        self,
        model_path: str,
        X_data: np.ndarray,
        feature_names: Optional[List[str]] = None,
        max_display: int = 10,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """
        Generate SHAP explanations for a trained model.
        
        Args:
            model_path: Path to the saved model
            X_data: Input data for explanation
            feature_names: Names of features
            max_display: Maximum features to display in visualizations
            sample_size: Number of samples for background dataset
            
        Returns:
            Dict containing SHAP values, plots, and summary statistics
        """
        try:
            # Load model artifacts
            model_artifacts = joblib.load(model_path)
            model = model_artifacts['model']
            
            # Prepare data
            if isinstance(X_data, pd.DataFrame):
                feature_names = feature_names or X_data.columns.tolist()
                X_array = X_data.values
            else:
                X_array = X_data
                feature_names = feature_names or [f'feature_{i}' for i in range(X_array.shape[1])]
            
            # Limit data size for performance
            if len(X_array) > sample_size:
                # Use kmeans to select representative samples
                from sklearn.cluster import KMeans
                kmeans = KMeans(n_clusters=min(sample_size, len(X_array)), random_state=42)
                kmeans.fit(X_array)
                X_background = kmeans.cluster_centers_
            else:
                X_background = X_array
            
            # Choose appropriate explainer based on model type
            explainer, shap_values = self._get_explainer_and_values(
                model, X_array, X_background
            )
            
            # Generate visualizations
            plots = self._generate_shap_plots(
                shap_values, X_array, feature_names, max_display, explainer
            )
            
            # Calculate summary statistics
            summary_stats = self._calculate_shap_summary(
                shap_values, feature_names
            )
            
            return {
                'success': True,
                'shap_values': shap_values.tolist() if isinstance(shap_values, np.ndarray) else shap_values,
                'feature_names': feature_names,
                'plots': plots,
                'summary': summary_stats,
                'explainer_type': type(explainer).__name__
            }
            
        except Exception as e:
            self.logger.error(f"Error generating SHAP explanations: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_explainer_and_values(
        self,
        model: Any,
        X_data: np.ndarray,
        X_background: np.ndarray
    ) -> Tuple[Any, np.ndarray]:
        """
        Get appropriate SHAP explainer and calculate values based on model type.
        """
        model_type = type(model).__name__
        
        try:
            # Tree-based models (most efficient)
            if hasattr(model, 'tree_') or 'Forest' in model_type or 'XGB' in model_type or 'GBM' in model_type:
                self.logger.info("Using TreeExplainer for tree-based model")
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_data)
                
                # Handle multi-class case
                if isinstance(shap_values, list):
                    # Use the first class for visualization
                    shap_values = shap_values[0]
                
            # Linear models
            elif hasattr(model, 'coef_'):
                self.logger.info("Using LinearExplainer for linear model")
                explainer = shap.LinearExplainer(model, X_background)
                shap_values = explainer.shap_values(X_data)
                
            # Neural networks and other models
            else:
                self.logger.info("Using KernelExplainer (may be slow)")
                # Use a subset for kernel explainer to improve speed
                background_subset = shap.sample(X_background, min(100, len(X_background)))
                explainer = shap.KernelExplainer(model.predict, background_subset)
                shap_values = explainer.shap_values(X_data[:min(50, len(X_data))])
            
            return explainer, shap_values
            
        except Exception as e:
            self.logger.warning(f"Error with specific explainer, falling back to KernelExplainer: {e}")
            # Fallback to kernel explainer
            background_subset = shap.sample(X_background, min(50, len(X_background)))
            explainer = shap.KernelExplainer(model.predict, background_subset)
            shap_values = explainer.shap_values(X_data[:min(30, len(X_data))])
            return explainer, shap_values
    
    def _generate_shap_plots(
        self,
        shap_values: np.ndarray,
        X_data: np.ndarray,
        feature_names: List[str],
        max_display: int,
        explainer: Any
    ) -> Dict[str, str]:
        """
        Generate SHAP visualization plots.
        """
        plots = {}
        
        try:
            # 1. Summary Plot (Feature Importance)
            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values, X_data, 
                feature_names=feature_names,
                max_display=max_display,
                show=False
            )
            plots['summary_plot'] = self._fig_to_base64()
            plt.close()
            
            # 2. Bar Plot (Mean absolute SHAP values)
            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values, X_data,
                feature_names=feature_names,
                plot_type='bar',
                max_display=max_display,
                show=False
            )
            plots['bar_plot'] = self._fig_to_base64()
            plt.close()
            
            # 3. Waterfall plot for first prediction
            if hasattr(explainer, 'expected_value'):
                try:
                    plt.figure(figsize=(10, 8))
                    expected_value = explainer.expected_value
                    if isinstance(expected_value, np.ndarray):
                        expected_value = expected_value[0]
                    
                    shap_exp = shap.Explanation(
                        values=shap_values[0],
                        base_values=expected_value,
                        data=X_data[0],
                        feature_names=feature_names
                    )
                    shap.waterfall_plot(shap_exp, show=False)
                    plots['waterfall_plot'] = self._fig_to_base64()
                    plt.close()
                except Exception as e:
                    self.logger.warning(f"Could not generate waterfall plot: {e}")
            
            # 4. Force plot for first prediction (as matplotlib)
            try:
                plt.figure(figsize=(20, 3))
                expected_value = explainer.expected_value
                if isinstance(expected_value, np.ndarray):
                    expected_value = expected_value[0]
                
                shap.force_plot(
                    expected_value,
                    shap_values[0],
                    X_data[0],
                    feature_names=feature_names,
                    matplotlib=True,
                    show=False
                )
                plots['force_plot'] = self._fig_to_base64()
                plt.close()
            except Exception as e:
                self.logger.warning(f"Could not generate force plot: {e}")
            
        except Exception as e:
            self.logger.error(f"Error generating SHAP plots: {e}")
        
        return plots
    
    def _calculate_shap_summary(
        self,
        shap_values: np.ndarray,
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics from SHAP values.
        """
        # Mean absolute SHAP values (feature importance)
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        # Sort features by importance
        sorted_indices = np.argsort(mean_abs_shap)[::-1]
        
        feature_importance = {
            feature_names[i]: float(mean_abs_shap[i])
            for i in sorted_indices
        }
        
        # Top features
        top_features = [
            {
                'feature': feature_names[i],
                'importance': float(mean_abs_shap[i]),
                'mean_shap': float(shap_values[:, i].mean()),
                'std_shap': float(shap_values[:, i].std())
            }
            for i in sorted_indices[:10]
        ]
        
        return {
            'feature_importance': feature_importance,
            'top_features': top_features,
            'total_features': len(feature_names)
        }
    
    def explain_prediction(
        self,
        model_path: str,
        single_input: np.ndarray,
        feature_names: Optional[List[str]] = None,
        background_data: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Explain a single prediction using SHAP.
        
        Args:
            model_path: Path to the saved model
            single_input: Single sample to explain (1D or 2D array)
            feature_names: Names of features
            background_data: Background dataset for comparison
            
        Returns:
            Dict containing SHAP explanation for the prediction
        """
        try:
            # Load model
            model_artifacts = joblib.load(model_path)
            model = model_artifacts['model']
            
            # Reshape if needed
            if single_input.ndim == 1:
                single_input = single_input.reshape(1, -1)
            
            # Get feature names
            if feature_names is None:
                feature_names = model_artifacts.get('feature_names', 
                    [f'feature_{i}' for i in range(single_input.shape[1])])
            
            # Use background data or create from input
            if background_data is None:
                background_data = single_input
            
            # Get explainer and values
            explainer, shap_values = self._get_explainer_and_values(
                model, single_input, background_data
            )
            
            # Get prediction
            prediction = model.predict(single_input)[0]
            
            # Get probability if available
            probability = None
            if hasattr(model, 'predict_proba'):
                probability = model.predict_proba(single_input)[0].tolist()
            
            # Create feature contributions
            contributions = [
                {
                    'feature': feature_names[i],
                    'value': float(single_input[0, i]),
                    'shap_value': float(shap_values[0, i]),
                    'contribution': 'positive' if shap_values[0, i] > 0 else 'negative'
                }
                for i in range(len(feature_names))
            ]
            
            # Sort by absolute SHAP value
            contributions.sort(key=lambda x: abs(x['shap_value']), reverse=True)
            
            return {
                'success': True,
                'prediction': float(prediction),
                'probability': probability,
                'contributions': contributions,
                'base_value': float(explainer.expected_value) if hasattr(explainer, 'expected_value') else None
            }
            
        except Exception as e:
            self.logger.error(f"Error explaining prediction: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _fig_to_base64(self) -> str:
        """Convert current matplotlib figure to base64 string."""
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return f"data:image/png;base64,{img_base64}"


# Global instance
shap_service = SHAPService()
