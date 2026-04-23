"""
Visualization service for generating ML analysis plots and charts
"""

import io
import base64
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sklearn.metrics import confusion_matrix, roc_curve, auc
from sklearn.inspection import permutation_importance

logger = logging.getLogger(__name__)


class VisualizationService:
    """Service for generating ML analysis visualizations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Set matplotlib to non-interactive backend
        plt.switch_backend('Agg')
        
        # Set style
        plt.style.use('default')
        sns.set_palette("husl")
    
    def generate_classification_plots(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
        feature_importance: Optional[Dict[str, float]] = None,
        class_names: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Generate classification analysis plots.
        
        This creates the visualizations mentioned in your specification:
        - Confusion matrix
        - Feature importance (if available)
        - ROC curve (for binary classification)
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Prediction probabilities (optional)
            feature_importance: Feature importance scores (optional)
            class_names: Class names for labeling (optional)
            
        Returns:
            Dict: Base64-encoded plot images
        """
        plots = {}
        
        try:
            # 1. Confusion Matrix
            plots['confusion_matrix'] = self._create_confusion_matrix(
                y_true, y_pred, class_names
            )
            
            # 2. Feature Importance (if available)
            if feature_importance:
                plots['feature_importance'] = self._create_feature_importance_plot(
                    feature_importance
                )
            
            # 3. ROC Curve (for binary classification)
            if y_proba is not None and len(np.unique(y_true)) == 2:
                plots['roc_curve'] = self._create_roc_curve(
                    y_true, y_proba[:, 1] if y_proba.ndim > 1 else y_proba
                )
            
            return plots
            
        except Exception as e:
            self.logger.error(f"Error generating classification plots: {e}")
            return {}
    
    def generate_regression_plots(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        feature_importance: Optional[Dict[str, float]] = None
    ) -> Dict[str, str]:
        """
        Generate regression analysis plots.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            feature_importance: Feature importance scores (optional)
            
        Returns:
            Dict: Base64-encoded plot images
        """
        plots = {}
        
        try:
            # 1. Actual vs Predicted scatter plot
            plots['actual_vs_predicted'] = self._create_regression_scatter(
                y_true, y_pred
            )
            
            # 2. Residuals plot
            plots['residuals'] = self._create_residuals_plot(y_true, y_pred)
            
            # 3. Feature Importance (if available)
            if feature_importance:
                plots['feature_importance'] = self._create_feature_importance_plot(
                    feature_importance
                )
            
            return plots
            
        except Exception as e:
            self.logger.error(f"Error generating regression plots: {e}")
            return {}
    
    def create_model_comparison_plot(
        self,
        model_results: Dict[str, Dict[str, Any]],
        primary_metric: str
    ) -> str:
        """
        Create a comparison plot showing model performance.
        
        Args:
            model_results: Results from multiple models
            primary_metric: Primary metric to compare (e.g., 'accuracy', 'r2')
            
        Returns:
            Base64-encoded plot image
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            models = list(model_results.keys())
            scores = [
                model_results[model]['metrics'].get(primary_metric, 0)
                for model in models
            ]
            
            bars = ax.bar(models, scores, color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12'][:len(models)])
            
            # Add value labels on bars
            for bar, score in zip(bars, scores):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{score:.3f}', ha='center', va='bottom')
            
            ax.set_title(f'Model Comparison - {primary_metric.title()}', fontsize=14, fontweight='bold')
            ax.set_ylabel(primary_metric.title(), fontsize=12)
            ax.set_xlabel('Model', fontsize=12)
            ax.set_ylim(0, max(scores) * 1.1)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            return self._plot_to_base64(fig)
            
        except Exception as e:
            self.logger.error(f"Error creating model comparison plot: {e}")
            return ""
    
    def _create_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_names: Optional[List[str]] = None
    ) -> str:
        """Create confusion matrix heatmap"""
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        cm = confusion_matrix(y_true, y_pred)
        
        # Create heatmap
        sns.heatmap(
            cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=class_names or range(len(cm)),
            yticklabels=class_names or range(len(cm)),
            ax=ax
        )
        
        ax.set_title('Confusion Matrix', fontsize=14, fontweight='bold')
        ax.set_xlabel('Predicted Label', fontsize=12)
        ax.set_ylabel('True Label', fontsize=12)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _create_feature_importance_plot(
        self,
        feature_importance: Dict[str, float],
        max_features: int = 15
    ) -> str:
        """Create feature importance bar plot"""
        
        # Sort features by importance
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:max_features]
        
        features, importances = zip(*sorted_features)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create horizontal bar plot
        bars = ax.barh(range(len(features)), importances)
        ax.set_yticks(range(len(features)))
        ax.set_yticklabels(features)
        ax.set_xlabel('Importance', fontsize=12)
        ax.set_title('Feature Importance', fontsize=14, fontweight='bold')
        
        # Add value labels
        for i, (bar, importance) in enumerate(zip(bars, importances)):
            ax.text(importance + 0.001, bar.get_y() + bar.get_height()/2,
                   f'{importance:.3f}', ha='left', va='center')
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _create_roc_curve(self, y_true: np.ndarray, y_score: np.ndarray) -> str:
        """Create ROC curve plot"""
        
        fpr, tpr, _ = roc_curve(y_true, y_score)
        roc_auc = auc(fpr, tpr)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        ax.plot(fpr, tpr, color='darkorange', lw=2,
                label=f'ROC curve (AUC = {roc_auc:.3f})')
        ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', alpha=0.5)
        
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate', fontsize=12)
        ax.set_ylabel('True Positive Rate', fontsize=12)
        ax.set_title('ROC Curve', fontsize=14, fontweight='bold')
        ax.legend(loc="lower right")
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _create_regression_scatter(self, y_true: np.ndarray, y_pred: np.ndarray) -> str:
        """Create actual vs predicted scatter plot"""
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        ax.scatter(y_true, y_pred, alpha=0.6, color='#3498db')
        
        # Add diagonal line (perfect prediction)
        min_val = min(min(y_true), min(y_pred))
        max_val = max(max(y_true), max(y_pred))
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, alpha=0.8)
        
        ax.set_xlabel('Actual Values', fontsize=12)
        ax.set_ylabel('Predicted Values', fontsize=12)
        ax.set_title('Actual vs Predicted Values', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _create_residuals_plot(self, y_true: np.ndarray, y_pred: np.ndarray) -> str:
        """Create residuals plot"""
        
        residuals = y_true - y_pred
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        ax.scatter(y_pred, residuals, alpha=0.6, color='#e74c3c')
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.8)
        
        ax.set_xlabel('Predicted Values', fontsize=12)
        ax.set_ylabel('Residuals', fontsize=12)
        ax.set_title('Residuals Plot', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _plot_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        
        # Convert to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        plt.close(fig)  # Free memory
        buffer.close()
        
        return image_base64
    
    def generate_dataset_visualizations(
        self,
        df: pd.DataFrame,
        dataset_type: str = 'general',
        sequence_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate visualizations for dataset analysis.
        
        Args:
            df: Dataset as DataFrame
            dataset_type: Type of dataset ('dna', 'rna', 'protein', 'general')
            sequence_stats: Optional sequence-specific statistics
            
        Returns:
            Dict: Base64-encoded plot images
        """
        plots = {}
        
        try:
            # 1. Missing data heatmap
            if df.isnull().sum().sum() > 0:
                plots['missing_data_heatmap'] = self._create_missing_data_heatmap(df)
            
            # 2. Data distribution plots for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                plots['distribution_plots'] = self._create_distribution_plots(df, numeric_cols[:6])
            
            # 3. Correlation heatmap for numeric data
            if len(numeric_cols) > 1:
                plots['correlation_heatmap'] = self._create_correlation_heatmap(df[numeric_cols])
            
            # 4. Sequence-specific visualizations
            if dataset_type in ['dna', 'rna'] and sequence_stats:
                if 'gc_content' in sequence_stats:
                    plots['gc_content_distribution'] = self._create_gc_distribution(sequence_stats)
                
                if 'nucleotide_composition' in sequence_stats or 'composition' in sequence_stats:
                    plots['nucleotide_composition'] = self._create_composition_plot(
                        sequence_stats.get('nucleotide_composition') or sequence_stats.get('composition')
                    )
            
            # 5. Sequence length distribution
            if 'length' in df.columns:
                plots['length_distribution'] = self._create_length_distribution(df['length'])
            
            return plots
            
        except Exception as e:
            self.logger.error(f"Error generating dataset visualizations: {e}")
            return {}
    
    def _create_missing_data_heatmap(self, df: pd.DataFrame) -> str:
        """Create heatmap showing missing data patterns"""
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Calculate missing data percentage for each column
        missing_data = df.isnull()
        
        # Only show columns with missing data
        cols_with_missing = [col for col in df.columns if missing_data[col].sum() > 0]
        
        if not cols_with_missing:
            return ""
        
        # Sample rows if too many
        sample_size = min(100, len(df))
        if len(df) > sample_size:
            missing_sample = missing_data[cols_with_missing].sample(sample_size)
        else:
            missing_sample = missing_data[cols_with_missing]
        
        sns.heatmap(missing_sample.T, cmap='RdYlGn_r', cbar=True, 
                    yticklabels=cols_with_missing, ax=ax)
        ax.set_title('Missing Data Pattern', fontsize=14, fontweight='bold')
        ax.set_xlabel('Sample Index', fontsize=12)
        ax.set_ylabel('Features', fontsize=12)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _create_distribution_plots(self, df: pd.DataFrame, columns: List[str]) -> str:
        """Create distribution plots for numeric columns"""
        
        n_cols = min(3, len(columns))
        n_rows = (len(columns) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
        
        if n_rows == 1 and n_cols == 1:
            axes = np.array([axes])
        axes = axes.flatten() if n_rows > 1 or n_cols > 1 else axes
        
        for idx, col in enumerate(columns):
            ax = axes[idx] if len(columns) > 1 else axes[0]
            
            # Remove NaN values
            data = df[col].dropna()
            
            if len(data) > 0:
                ax.hist(data, bins=30, color='#3498db', alpha=0.7, edgecolor='black')
                ax.set_title(f'Distribution of {col}', fontsize=11, fontweight='bold')
                ax.set_xlabel(col, fontsize=10)
                ax.set_ylabel('Frequency', fontsize=10)
                ax.grid(axis='y', alpha=0.3)
        
        # Hide empty subplots
        for idx in range(len(columns), len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _create_correlation_heatmap(self, df: pd.DataFrame) -> str:
        """Create correlation heatmap for numeric features"""
        
        # Calculate correlation matrix
        corr = df.corr()
        
        fig, ax = plt.subplots(figsize=(12, 10))
        
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', 
                    center=0, square=True, linewidths=1, ax=ax,
                    cbar_kws={"shrink": 0.8})
        
        ax.set_title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _create_gc_distribution(self, stats: Dict[str, Any]) -> str:
        """Create GC content distribution plot"""
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if isinstance(stats.get('gc_content'), dict):
            gc_data = stats['gc_content']
            mean_gc = gc_data.get('mean', 0)
            std_gc = gc_data.get('std', 0)
            
            # Create a simulated distribution for visualization
            x = np.linspace(0, 100, 100)
            y = np.exp(-0.5 * ((x - mean_gc) / std_gc) ** 2) if std_gc > 0 else np.zeros_like(x)
            
            ax.plot(x, y, linewidth=2, color='#2ecc71')
            ax.fill_between(x, y, alpha=0.3, color='#2ecc71')
            ax.axvline(mean_gc, color='red', linestyle='--', linewidth=2, 
                      label=f'Mean: {mean_gc:.2f}%')
            
        else:
            # Single value
            gc_val = stats.get('avg_gc_content', 0) * 100
            ax.axvline(gc_val, color='#2ecc71', linewidth=3, 
                      label=f'GC Content: {gc_val:.2f}%')
        
        ax.set_xlabel('GC Content (%)', fontsize=12)
        ax.set_ylabel('Density', fontsize=12)
        ax.set_title('GC Content Distribution', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _create_composition_plot(self, composition: Dict[str, float]) -> str:
        """Create nucleotide/amino acid composition plot"""
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Sort by frequency
        sorted_comp = sorted(composition.items(), key=lambda x: x[1], reverse=True)
        bases, counts = zip(*sorted_comp) if sorted_comp else ([], [])
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(bases)))
        bars = ax.bar(bases, counts, color=colors, edgecolor='black', linewidth=1.5)
        
        ax.set_xlabel('Base/Amino Acid', fontsize=12)
        ax.set_ylabel('Count / Percentage', fontsize=12)
        ax.set_title('Sequence Composition', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _create_length_distribution(self, lengths: pd.Series) -> str:
        """Create sequence length distribution plot"""
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        lengths_clean = lengths.dropna()
        
        ax.hist(lengths_clean, bins=30, color='#9b59b6', alpha=0.7, edgecolor='black')
        ax.axvline(lengths_clean.mean(), color='red', linestyle='--', linewidth=2,
                  label=f'Mean: {lengths_clean.mean():.0f}')
        ax.axvline(lengths_clean.median(), color='orange', linestyle='--', linewidth=2,
                  label=f'Median: {lengths_clean.median():.0f}')
        
        ax.set_xlabel('Sequence Length (bp/aa)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Sequence Length Distribution', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)


# Global instance
visualization_service = VisualizationService()