"""
Enhanced Dataset Service with advanced preprocessing and transformation capabilities
"""
#Advanced preprocessing and quality report

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from Bio import SeqIO
from Bio.SeqUtils import gc_fraction, molecular_weight
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer, KNNImputer

from app.services.dataset_service import DatasetService
from app.services.transformation_service import TransformationService
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedDatasetService(DatasetService):
    """Enhanced dataset service with advanced preprocessing capabilities"""
    
    def __init__(self):
        super().__init__()
        self.transformation_service = TransformationService()
    
    async def advanced_preprocessing(
        self,
        dataset_path: str,
        preprocessing_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply advanced preprocessing to dataset.
        
        Args:
            dataset_path: Path to the dataset file
            preprocessing_config: Configuration for preprocessing steps
            
        Returns:
            Dict containing preprocessing results and output path
        """
        try:
            # Load dataset
            df = await self._load_dataset(dataset_path)
            
            # Apply preprocessing steps in order
            for step in preprocessing_config.get("steps", []):
                step_name = step["name"]
                step_params = step.get("parameters", {})
                
                if step_name == "handle_missing_values":
                    df = await self._handle_missing_values(df, step_params)
                elif step_name == "feature_scaling":
                    df = await self._apply_feature_scaling(df, step_params)
                elif step_name == "feature_selection":
                    df = await self._apply_feature_selection(df, step_params)
                elif step_name == "dimensionality_reduction":
                    df = await self._apply_dimensionality_reduction(df, step_params)
                elif step_name == "outlier_removal":
                    df = await self._remove_outliers(df, step_params)
                elif step_name == "feature_engineering":
                    df = await self._apply_feature_engineering(df, step_params)
                elif step_name == "biological_features":
                    df = await self._extract_biological_features(df, step_params)
            
            # Save preprocessed dataset
            output_path = await self._save_preprocessed_dataset(df, dataset_path, preprocessing_config)
            
            # Generate preprocessing report
            report = await self._generate_preprocessing_report(df, preprocessing_config)
            
            return {
                "success": True,
                "output_path": output_path,
                "original_shape": (len(df), len(df.columns)),
                "processed_shape": (len(df), len(df.columns)),
                "preprocessing_report": report,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error in advanced preprocessing: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
    
    async def _load_dataset(self, dataset_path: str) -> pd.DataFrame:
        """Load dataset from various formats"""
        path = Path(dataset_path)
        
        if path.suffix.lower() == '.csv':
            return pd.read_csv(dataset_path)
        elif path.suffix.lower() == '.tsv':
            return pd.read_csv(dataset_path, sep='\t')
        elif path.suffix.lower() in ['.fasta', '.fa', '.fas']:
            # Convert FASTA to DataFrame
            return await self._fasta_to_dataframe(dataset_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    async def _fasta_to_dataframe(self, fasta_path: str) -> pd.DataFrame:
        """Convert FASTA file to DataFrame with sequence features"""
        sequences = []
        ids = []
        descriptions = []
        
        with open(fasta_path, 'r') as handle:
            for record in SeqIO.parse(handle, "fasta"):
                sequences.append(str(record.seq))
                ids.append(record.id)
                descriptions.append(record.description)
        
        df = pd.DataFrame({
            'sequence_id': ids,
            'description': descriptions,
            'sequence': sequences,
            'length': [len(seq) for seq in sequences]
        })
        
        # Add basic sequence features
        df['gc_content'] = [gc_fraction(seq) * 100 for seq in sequences]
        
        return df
    
    async def _handle_missing_values(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Handle missing values in dataset"""
        strategy = params.get("strategy", "mean")
        columns = params.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
        
        if strategy in ["mean", "median", "most_frequent", "constant"]:
            imputer = SimpleImputer(strategy=strategy)
            df[columns] = imputer.fit_transform(df[columns])
        elif strategy == "knn":
            n_neighbors = params.get("n_neighbors", 5)
            imputer = KNNImputer(n_neighbors=n_neighbors)
            df[columns] = imputer.fit_transform(df[columns])
        elif strategy == "drop":
            df = df.dropna(subset=columns)
        
        return df
    
    async def _apply_feature_scaling(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply feature scaling to numerical columns"""
        method = params.get("method", "standard")
        columns = params.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
        
        if method == "standard":
            scaler = StandardScaler()
        elif method == "minmax":
            scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unknown scaling method: {method}")
        
        df[columns] = scaler.fit_transform(df[columns])
        return df
    
    async def _apply_feature_selection(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply feature selection techniques"""
        method = params.get("method", "k_best")
        target_column = params.get("target_column")
        k = params.get("k", 10)
        
        if not target_column or target_column not in df.columns:
            return df
        
        # Prepare features and target
        X = df.drop(columns=[target_column])
        y = df[target_column]
        
        # Select numerical columns only
        numerical_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        X_numerical = X[numerical_cols]
        
        if method == "k_best":
            score_func = params.get("score_func", "f_classif")
            if score_func == "f_classif":
                selector = SelectKBest(f_classif, k=min(k, len(numerical_cols)))
            elif score_func == "mutual_info":
                selector = SelectKBest(mutual_info_classif, k=min(k, len(numerical_cols)))
            
            X_selected = selector.fit_transform(X_numerical, y)
            selected_features = [numerical_cols[i] for i in selector.get_support(indices=True)]
            
            # Keep selected features and non-numerical columns
            non_numerical_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
            df = df[selected_features + non_numerical_cols + [target_column]]
        
        return df
    
    async def _apply_dimensionality_reduction(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply dimensionality reduction techniques"""
        method = params.get("method", "pca")
        n_components = params.get("n_components", 2)
        target_column = params.get("target_column")
        
        # Prepare features
        if target_column and target_column in df.columns:
            X = df.drop(columns=[target_column])
            y = df[target_column]
        else:
            X = df
            y = None
        
        # Select numerical columns only
        numerical_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        X_numerical = X[numerical_cols]
        
        if len(numerical_cols) == 0:
            return df
        
        if method == "pca":
            reducer = PCA(n_components=min(n_components, len(numerical_cols)))
            X_reduced = reducer.fit_transform(X_numerical)
            
            # Create new DataFrame with reduced features
            reduced_columns = [f"PC{i+1}" for i in range(X_reduced.shape[1])]
            df_reduced = pd.DataFrame(X_reduced, columns=reduced_columns, index=df.index)
            
            # Add non-numerical columns and target
            non_numerical_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()
            for col in non_numerical_cols:
                df_reduced[col] = X[col]
            
            if y is not None:
                df_reduced[target_column] = y
            
            return df_reduced
        
        return df
    
    async def _remove_outliers(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Remove outliers from dataset"""
        method = params.get("method", "iqr")
        columns = params.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
        
        if method == "iqr":
            for col in columns:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        
        elif method == "zscore":
            threshold = params.get("threshold", 3)
            for col in columns:
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df = df[z_scores < threshold]
        
        return df
    
    async def _apply_feature_engineering(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply feature engineering techniques"""
        operations = params.get("operations", [])
        
        for operation in operations:
            op_type = operation.get("type")
            
            if op_type == "polynomial_features":
                degree = operation.get("degree", 2)
                columns = operation.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
                
                from sklearn.preprocessing import PolynomialFeatures
                poly = PolynomialFeatures(degree=degree, include_bias=False)
                poly_features = poly.fit_transform(df[columns])
                
                # Add polynomial features
                feature_names = poly.get_feature_names_out(columns)
                for i, name in enumerate(feature_names):
                    if name not in df.columns:  # Avoid duplicating existing features
                        df[f"poly_{name}"] = poly_features[:, i]
            
            elif op_type == "interaction_features":
                columns = operation.get("columns", [])
                if len(columns) >= 2:
                    for i in range(len(columns)):
                        for j in range(i+1, len(columns)):
                            col1, col2 = columns[i], columns[j]
                            if col1 in df.columns and col2 in df.columns:
                                df[f"{col1}_x_{col2}"] = df[col1] * df[col2]
            
            elif op_type == "log_transform":
                columns = operation.get("columns", [])
                for col in columns:
                    if col in df.columns and df[col].min() > 0:
                        df[f"log_{col}"] = np.log(df[col])
        
        return df
    
    async def _extract_biological_features(
        self,
        df: pd.DataFrame,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """Extract biological features from sequences"""
        sequence_column = params.get("sequence_column", "sequence")
        sequence_type = params.get("sequence_type", "dna")
        
        if sequence_column not in df.columns:
            return df
        
        sequences = df[sequence_column].tolist()
        
        if sequence_type in ["dna", "rna"]:
            # Nucleotide composition
            for nucleotide in ['A', 'T', 'G', 'C']:
                df[f"{nucleotide}_count"] = [seq.upper().count(nucleotide) for seq in sequences]
                df[f"{nucleotide}_freq"] = df[f"{nucleotide}_count"] / df[sequence_column].str.len()
            
            # GC content
            df["gc_content"] = [gc_fraction(seq) * 100 for seq in sequences]
            
            # Dinucleotide frequencies
            dinucleotides = ['AA', 'AT', 'AG', 'AC', 'TA', 'TT', 'TG', 'TC', 
                           'GA', 'GT', 'GG', 'GC', 'CA', 'CT', 'CG', 'CC']
            for dinuc in dinucleotides:
                df[f"{dinuc}_freq"] = [seq.upper().count(dinuc) / max(1, len(seq)-1) for seq in sequences]
        
        elif sequence_type == "protein":
            # Amino acid composition
            amino_acids = 'ACDEFGHIKLMNPQRSTVWY'
            for aa in amino_acids:
                df[f"{aa}_count"] = [seq.upper().count(aa) for seq in sequences]
                df[f"{aa}_freq"] = df[f"{aa}_count"] / df[sequence_column].str.len()
            
            # Molecular weight and isoelectric point
            molecular_weights = []
            isoelectric_points = []
            
            for seq in sequences:
                try:
                    analysis = ProteinAnalysis(seq)
                    molecular_weights.append(analysis.molecular_weight())
                    isoelectric_points.append(analysis.isoelectric_point())
                except:
                    molecular_weights.append(0)
                    isoelectric_points.append(7.0)
            
            df["molecular_weight"] = molecular_weights
            df["isoelectric_point"] = isoelectric_points
        
        return df
    
    async def _save_preprocessed_dataset(
        self,
        df: pd.DataFrame,
        original_path: str,
        config: Dict[str, Any]
    ) -> str:
        """Save preprocessed dataset to file"""
        original_path = Path(original_path)
        output_dir = original_path.parent / "preprocessed"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{original_path.stem}_preprocessed_{timestamp}.csv"
        output_path = output_dir / output_filename
        
        df.to_csv(output_path, index=False)
        return str(output_path)
    
    async def _generate_preprocessing_report(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate preprocessing report"""
        return {
            "steps_applied": [step["name"] for step in config.get("steps", [])],
            "final_shape": (len(df), len(df.columns)),
            "column_types": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "numerical_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object']).columns.tolist(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024
        }
    
    async def get_preprocessing_suggestions(
        self,
        dataset_path: str,
        task_type: str = "classification"
    ) -> Dict[str, Any]:
        """Get preprocessing suggestions based on dataset analysis"""
        try:
            df = await self._load_dataset(dataset_path)
            
            suggestions = {
                "recommended_steps": [],
                "optional_steps": [],
                "warnings": []
            }
            
            # Check for missing values
            missing_values = df.isnull().sum()
            if missing_values.sum() > 0:
                suggestions["recommended_steps"].append({
                    "name": "handle_missing_values",
                    "reason": f"Dataset has {missing_values.sum()} missing values",
                    "parameters": {"strategy": "mean"}
                })
            
            # Check for numerical columns that need scaling
            numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numerical_cols) > 1:
                # Check if scaling is needed
                ranges = df[numerical_cols].max() - df[numerical_cols].min()
                if ranges.max() / ranges.min() > 10:  # Large difference in ranges
                    suggestions["recommended_steps"].append({
                        "name": "feature_scaling",
                        "reason": "Features have very different scales",
                        "parameters": {"method": "standard"}
                    })
            
            # Check for high dimensionality
            if len(numerical_cols) > 50:
                suggestions["optional_steps"].append({
                    "name": "dimensionality_reduction",
                    "reason": "High-dimensional dataset may benefit from dimensionality reduction",
                    "parameters": {"method": "pca", "n_components": 20}
                })
            
            # Check for potential outliers
            if len(numerical_cols) > 0:
                suggestions["optional_steps"].append({
                    "name": "outlier_removal",
                    "reason": "Consider removing outliers for better model performance",
                    "parameters": {"method": "iqr"}
                })
            
            # Biological sequence suggestions
            if "sequence" in df.columns:
                suggestions["recommended_steps"].append({
                    "name": "biological_features",
                    "reason": "Extract biological features from sequences",
                    "parameters": {"sequence_column": "sequence", "sequence_type": "dna"}
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating preprocessing suggestions: {e}")
            return {"error": str(e)}
    
    async def generate_quality_report(self, dataset_path: str) -> Dict[str, Any]:
        """
        Generate a comprehensive data quality report for the dataset.
        
        Args:
            dataset_path: Path to the dataset file
            
        Returns:
            Dict containing quality metrics and analysis
        """
        try:
            # Load dataset
            df = await self._load_dataset(dataset_path)
            
            # Basic statistics
            basic_stats = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
                "file_size_mb": Path(dataset_path).stat().st_size / 1024 / 1024
            }
            
            # Missing values analysis
            missing_analysis = {}
            for col in df.columns:
                missing_count = df[col].isnull().sum()
                missing_analysis[col] = {
                    "missing_count": int(missing_count),
                    "missing_percentage": float(missing_count / len(df) * 100),
                    "data_type": str(df[col].dtype)
                }
            
            # Data type analysis
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # Numeric columns statistics
            numeric_stats = {}
            for col in numeric_columns:
                if not df[col].empty:
                    numeric_stats[col] = {
                        "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                        "median": float(df[col].median()) if not df[col].isnull().all() else None,
                        "std": float(df[col].std()) if not df[col].isnull().all() else None,
                        "min": float(df[col].min()) if not df[col].isnull().all() else None,
                        "max": float(df[col].max()) if not df[col].isnull().all() else None,
                        "unique_values": int(df[col].nunique()),
                        "outliers_count": int(len(df[(np.abs(df[col] - df[col].mean()) > 3 * df[col].std())]))
                    }
            
            # Categorical columns statistics
            categorical_stats = {}
            for col in categorical_columns:
                if not df[col].empty:
                    categorical_stats[col] = {
                        "unique_values": int(df[col].nunique()),
                        "most_frequent": str(df[col].mode().iloc[0]) if not df[col].mode().empty else None,
                        "most_frequent_count": int(df[col].value_counts().iloc[0]) if not df[col].empty else 0,
                        "least_frequent": str(df[col].value_counts().index[-1]) if len(df[col].value_counts()) > 0 else None
                    }
            
            # Duplicate analysis
            duplicate_rows = df.duplicated().sum()
            
            # Data quality score (simple heuristic)
            quality_score = 100.0
            
            # Penalize for missing values
            overall_missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            quality_score -= min(overall_missing_pct * 2, 40)  # Max 40 points deduction
            
            # Penalize for duplicates
            duplicate_pct = (duplicate_rows / len(df)) * 100
            quality_score -= min(duplicate_pct * 3, 30)  # Max 30 points deduction
            
            # Penalize for too many outliers in numeric columns
            if numeric_columns:
                total_outliers = sum([numeric_stats.get(col, {}).get('outliers_count', 0) for col in numeric_columns])
                outlier_pct = (total_outliers / len(df)) * 100
                quality_score -= min(outlier_pct, 20)  # Max 20 points deduction
            
            quality_score = max(0, quality_score)  # Ensure non-negative
            
            # Recommendations
            recommendations = []
            
            if overall_missing_pct > 10:
                recommendations.append("Consider handling missing values (>10% missing data detected)")
            
            if duplicate_rows > 0:
                recommendations.append(f"Remove {duplicate_rows} duplicate rows")
            
            if len(numeric_columns) == 0:
                recommendations.append("No numeric columns detected - consider feature engineering")
            
            if len(categorical_columns) > len(numeric_columns) * 2:
                recommendations.append("High number of categorical columns - consider encoding strategies")
            
            return {
                "basic_statistics": basic_stats,
                "missing_values_analysis": missing_analysis,
                "numeric_statistics": numeric_stats,
                "categorical_statistics": categorical_stats,
                "data_types": {
                    "numeric_columns": numeric_columns,
                    "categorical_columns": categorical_columns
                },
                "duplicate_rows": int(duplicate_rows),
                "quality_score": round(quality_score, 2),
                "recommendations": recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return {"error": str(e)}


# Initialize global instance
enhanced_dataset_service = EnhancedDatasetService()
