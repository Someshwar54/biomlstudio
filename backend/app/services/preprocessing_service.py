"""
Comprehensive preprocessing service for bioinformatics data
Handles sequence encoding, feature engineering, and data preparation
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
import itertools

from Bio import SeqIO
from Bio.SeqUtils import gc_fraction, molecular_weight
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder, RobustScaler
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif

logger = logging.getLogger(__name__)


class PreprocessingService:
    """
    Comprehensive preprocessing service for biological data.
    Supports multiple encoding methods and automatic feature engineering.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.label_encoders = {}
        self.scalers = {}
    
    async def preprocess_dataset(
        self,
        file_path: str,
        dataset_type: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete preprocessing pipeline for biological datasets.
        
        Args:
            file_path: Path to dataset file
            dataset_type: Type of dataset ('dna', 'rna', 'protein', 'general')
            config: Preprocessing configuration
            
        Returns:
            Dict: Preprocessing results with train/val/test splits
        """
        self.logger.info(f"Starting preprocessing for {dataset_type} dataset")
        
        results = {
            'success': False,
            'preprocessing_steps': [],
            'warnings': [],
            'errors': []
        }
        
        try:
            # Step 1: Load and clean data
            df, step_info = await self._load_and_clean_data(file_path, dataset_type)
            results['preprocessing_steps'].append(step_info)
            
            if df is None or df.empty:
                results['errors'].append("Failed to load dataset")
                return results
            
            # Step 2: Handle missing values
            df, step_info = await self._handle_missing_values(df, config.get('missing_value_strategy', 'drop'))
            results['preprocessing_steps'].append(step_info)
            
            # Step 3: Feature engineering based on dataset type
            if dataset_type in ['dna', 'rna', 'protein']:
                df, step_info = await self._engineer_sequence_features(df, dataset_type, config)
                results['preprocessing_steps'].append(step_info)
            else:
                df, step_info = await self._engineer_general_features(df, config)
                results['preprocessing_steps'].append(step_info)
            
            # Step 4: Encode sequences if needed
            if 'sequence' in df.columns:
                df, step_info = await self._encode_sequences(
                    df,
                    encoding_method=config.get('encoding_method', 'kmer'),
                    **config.get('encoding_params', {})
                )
                results['preprocessing_steps'].append(step_info)
            
            # Step 5: Normalize/scale features
            df, step_info = await self._normalize_features(df, config.get('scaling_method', 'standard'))
            results['preprocessing_steps'].append(step_info)
            
            # Step 6: Split into train/val/test
            splits, step_info = await self._create_data_splits(
                df,
                target_column=config.get('target_column', 'label'),
                test_size=config.get('test_size', 0.2),
                val_size=config.get('val_size', 0.1),
                stratify=config.get('stratify', True)
            )
            results['preprocessing_steps'].append(step_info)
            
            results.update({
                'success': True,
                'train_data': splits['train'],
                'val_data': splits['val'],
                'test_data': splits['test'],
                'feature_names': splits['feature_names'],
                'encoders': {
                    'label_encoders': self.label_encoders,
                    'scalers': self.scalers
                },
                'original_shape': df.shape,
                'final_shape': splits['train']['X'].shape
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Preprocessing error: {e}")
            results['errors'].append(str(e))
            return results
    
    async def _load_and_clean_data(
        self,
        file_path: str,
        dataset_type: str
    ) -> Tuple[Optional[pd.DataFrame], Dict]:
        """Load data and perform initial cleaning"""
        step_info = {
            'step': 'Load and Clean Data',
            'actions': [],
            'stats': {}
        }
        
        try:
            file_path = Path(file_path)
            
            if dataset_type in ['dna', 'rna', 'protein']:
                # Load biological sequences
                if file_path.suffix.lower() in ['.fasta', '.fa', '.fas']:
                    from app.utils.bioinformatics import extract_label_from_header
                    
                    sequences_data = []
                    with open(file_path, 'r') as handle:
                        for record in SeqIO.parse(handle, "fasta"):
                            seq_str = str(record.seq).upper()
                            # Remove invalid characters
                            if dataset_type == 'dna':
                                seq_str = ''.join(c for c in seq_str if c in 'ATCG')
                            elif dataset_type == 'rna':
                                seq_str = ''.join(c for c in seq_str if c in 'AUCG')
                            elif dataset_type == 'protein':
                                seq_str = ''.join(c for c in seq_str if c in 'ACDEFGHIKLMNPQRSTVWY')
                            
                            if len(seq_str) > 0:
                                # Extract label from FASTA header
                                label = extract_label_from_header(record.description)
                                
                                sequences_data.append({
                                    'id': record.id,
                                    'sequence': seq_str,
                                    'length': len(seq_str),
                                    'label': label
                                })
                    
                    df = pd.DataFrame(sequences_data)
                    step_info['actions'].append(f"Loaded {len(df)} sequences from FASTA")
                    step_info['actions'].append("Removed invalid characters")
                    step_info['actions'].append(f"Extracted labels from headers")
                    
                    # Log label distribution
                    if 'label' in df.columns:
                        label_counts = df['label'].value_counts()
                        step_info['actions'].append(f"Label distribution: {label_counts.to_dict()}")
                    
                elif file_path.suffix.lower() in ['.csv', '.tsv']:
                    delimiter = '\t' if file_path.suffix == '.tsv' else ','
                    df = pd.read_csv(file_path, delimiter=delimiter)
                    step_info['actions'].append(f"Loaded {len(df)} rows from CSV/TSV")
            else:
                # Load general dataset
                delimiter = '\t' if file_path.suffix == '.tsv' else ','
                df = pd.read_csv(file_path, delimiter=delimiter)
                step_info['actions'].append(f"Loaded {len(df)} rows")
            
            # Remove duplicates
            initial_rows = len(df)
            df = df.drop_duplicates()
            removed = initial_rows - len(df)
            if removed > 0:
                step_info['actions'].append(f"Removed {removed} duplicate rows")
            
            step_info['stats'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns)
            }
            
            return df, step_info
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            step_info['actions'].append(f"Error: {str(e)}")
            return None, step_info
    
    async def _handle_missing_values(
        self,
        df: pd.DataFrame,
        strategy: str = 'drop'
    ) -> Tuple[pd.DataFrame, Dict]:
        """Handle missing values in the dataset"""
        step_info = {
            'step': 'Handle Missing Values',
            'actions': [],
            'stats': {}
        }
        
        initial_rows = len(df)
        missing_before = df.isnull().sum().sum()
        
        step_info['stats']['missing_before'] = int(missing_before)
        
        if missing_before == 0:
            step_info['actions'].append("No missing values found")
            return df, step_info
        
        if strategy == 'drop':
            df = df.dropna()
            step_info['actions'].append(f"Dropped rows with missing values")
        elif strategy == 'mean':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
            step_info['actions'].append("Filled missing values with column means")
        elif strategy == 'median':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
            step_info['actions'].append("Filled missing values with column medians")
        elif strategy == 'forward_fill':
            df = df.fillna(method='ffill')
            step_info['actions'].append("Forward filled missing values")
        
        rows_removed = initial_rows - len(df)
        if rows_removed > 0:
            step_info['actions'].append(f"Removed {rows_removed} rows ({rows_removed/initial_rows*100:.1f}%)")
        
        step_info['stats']['missing_after'] = int(df.isnull().sum().sum())
        
        return df, step_info
    
    async def _engineer_sequence_features(
        self,
        df: pd.DataFrame,
        dataset_type: str,
        config: Dict
    ) -> Tuple[pd.DataFrame, Dict]:
        """Engineer features from biological sequences"""
        step_info = {
            'step': 'Feature Engineering (Biological)',
            'actions': [],
            'stats': {}
        }
        
        if 'sequence' not in df.columns:
            step_info['actions'].append("No sequence column found")
            return df, step_info
        
        features_added = []
        
        # Length features
        if 'length' not in df.columns:
            df['length'] = df['sequence'].str.len()
            features_added.append('length')
        
        if dataset_type in ['dna', 'rna']:
            # GC content
            df['gc_content'] = df['sequence'].apply(
                lambda seq: (seq.count('G') + seq.count('C')) / len(seq) if len(seq) > 0 else 0
            )
            features_added.append('gc_content')
            
            # Individual nucleotide content
            for nucleotide in ['A', 'T', 'G', 'C']:
                col_name = f'{nucleotide.lower()}_content'
                df[col_name] = df['sequence'].apply(
                    lambda seq: seq.count(nucleotide) / len(seq) if len(seq) > 0 else 0
                )
                features_added.append(col_name)
            
            # AT/GC ratio
            df['at_gc_ratio'] = df.apply(
                lambda row: (row.get('a_content', 0) + row.get('t_content', 0)) / 
                           (row.get('g_content', 0) + row.get('c_content', 0) + 0.001),
                axis=1
            )
            features_added.append('at_gc_ratio')
        
        elif dataset_type == 'protein':
            # Amino acid composition
            amino_acids = 'ACDEFGHIKLMNPQRSTVWY'
            for aa in amino_acids:
                col_name = f'aa_{aa.lower()}_freq'
                df[col_name] = df['sequence'].apply(
                    lambda seq: seq.count(aa) / len(seq) if len(seq) > 0 else 0
                )
                features_added.append(col_name)
            
            # Molecular weight (approximate)
            aa_weights = {
                'A': 89, 'C': 121, 'D': 133, 'E': 147, 'F': 165,
                'G': 75, 'H': 155, 'I': 131, 'K': 146, 'L': 131,
                'M': 149, 'N': 132, 'P': 115, 'Q': 146, 'R': 174,
                'S': 105, 'T': 119, 'V': 117, 'W': 204, 'Y': 181
            }
            df['molecular_weight'] = df['sequence'].apply(
                lambda seq: sum(aa_weights.get(aa, 0) for aa in seq)
            )
            features_added.append('molecular_weight')
        
        step_info['actions'].append(f"Added {len(features_added)} engineered features")
        step_info['stats']['features_added'] = features_added
        
        return df, step_info
    
    async def _engineer_general_features(
        self,
        df: pd.DataFrame,
        config: Dict
    ) -> Tuple[pd.DataFrame, Dict]:
        """Engineer features for general datasets"""
        step_info = {
            'step': 'Feature Engineering (General)',
            'actions': [],
            'stats': {}
        }
        
        features_added = []
        
        # Polynomial features for numeric columns (if enabled)
        if config.get('polynomial_features', False):
            from sklearn.preprocessing import PolynomialFeatures
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) > 0 and len(numeric_cols) <= 10:  # Limit to avoid explosion
                poly = PolynomialFeatures(degree=2, include_bias=False)
                poly_features = poly.fit_transform(df[numeric_cols])
                poly_feature_names = poly.get_feature_names_out(numeric_cols)
                
                # Add only interaction terms
                for i, name in enumerate(poly_feature_names):
                    if '^2' in name or ' ' in name:  # Squared or interaction term
                        df[name] = poly_features[:, i]
                        features_added.append(name)
                
                step_info['actions'].append(f"Added {len(features_added)} polynomial features")
        
        step_info['stats']['features_added'] = len(features_added)
        
        return df, step_info
    
    async def _encode_sequences(
        self,
        df: pd.DataFrame,
        encoding_method: str = 'kmer',
        **kwargs
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Encode sequences using various methods.
        Supports: one-hot, kmer, integer encoding
        """
        step_info = {
            'step': f'Sequence Encoding ({encoding_method})',
            'actions': [],
            'stats': {}
        }
        
        if 'sequence' not in df.columns:
            return df, step_info
        
        sequences = df['sequence'].tolist()
        
        if encoding_method == 'onehot':
            encoded_features = self._onehot_encode_sequences(sequences, **kwargs)
            step_info['actions'].append("Applied one-hot encoding")
        elif encoding_method == 'kmer':
            encoded_features = self._kmer_encode_sequences(sequences, **kwargs)
            step_info['actions'].append(f"Applied k-mer encoding (k={kwargs.get('k', 3)})")
        elif encoding_method == 'integer':
            encoded_features = self._integer_encode_sequences(sequences, **kwargs)
            step_info['actions'].append("Applied integer encoding")
        else:
            step_info['actions'].append(f"Unknown encoding method: {encoding_method}")
            return df, step_info
        
        # Add encoded features to dataframe
        for i in range(encoded_features.shape[1]):
            df[f'encoded_feature_{i}'] = encoded_features[:, i]
        
        step_info['stats'] = {
            'encoding_dimensions': encoded_features.shape[1],
            'encoding_method': encoding_method
        }
        
        return df, step_info
    
    def _kmer_encode_sequences(
        self,
        sequences: List[str],
        k: int = 3,
        normalize: bool = True
    ) -> np.ndarray:
        """K-mer frequency encoding"""
        # Get alphabet from sequences
        alphabet = set(''.join(sequences))
        
        # Generate all possible k-mers (limit to prevent explosion)
        if len(alphabet) ** k > 10000:
            k = 2  # Reduce k if too many combinations
        
        kmers = [''.join(p) for p in itertools.product(sorted(alphabet), repeat=k)]
        kmer_index = {kmer: i for i, kmer in enumerate(kmers)}
        
        # Count k-mers
        kmer_matrix = np.zeros((len(sequences), len(kmers)))
        
        for i, seq in enumerate(sequences):
            counts = defaultdict(int)
            for j in range(len(seq) - k + 1):
                kmer = seq[j:j+k]
                if kmer in kmer_index:
                    counts[kmer] += 1
            
            # Normalize by sequence length
            total = max(1, len(seq) - k + 1) if normalize else 1
            for kmer, count in counts.items():
                kmer_matrix[i, kmer_index[kmer]] = count / total
        
        return kmer_matrix
    
    def _onehot_encode_sequences(
        self,
        sequences: List[str],
        max_length: Optional[int] = None
    ) -> np.ndarray:
        """One-hot encoding for sequences"""
        alphabet = sorted(set(''.join(sequences)))
        char_to_int = {char: i for i, char in enumerate(alphabet)}
        
        if max_length is None:
            max_length = max(len(seq) for seq in sequences)
        
        # Flatten one-hot to 2D matrix
        encoded = np.zeros((len(sequences), max_length * len(alphabet)))
        
        for i, seq in enumerate(sequences):
            for j, char in enumerate(seq[:max_length]):
                if char in char_to_int:
                    pos = j * len(alphabet) + char_to_int[char]
                    encoded[i, pos] = 1
        
        return encoded
    
    def _integer_encode_sequences(
        self,
        sequences: List[str],
        max_length: Optional[int] = None
    ) -> np.ndarray:
        """Integer encoding for sequences"""
        alphabet = sorted(set(''.join(sequences)))
        char_to_int = {char: i+1 for i, char in enumerate(alphabet)}
        
        if max_length is None:
            max_length = max(len(seq) for seq in sequences)
        
        encoded = np.zeros((len(sequences), max_length))
        
        for i, seq in enumerate(sequences):
            for j, char in enumerate(seq[:max_length]):
                encoded[i, j] = char_to_int.get(char, 0)
        
        return encoded
    
    async def _normalize_features(
        self,
        df: pd.DataFrame,
        method: str = 'standard'
    ) -> Tuple[pd.DataFrame, Dict]:
        """Normalize/scale numeric features"""
        step_info = {
            'step': f'Feature Normalization ({method})',
            'actions': [],
            'stats': {}
        }
        
        # Get numeric columns (exclude label/target columns)
        exclude_cols = ['label', 'target', 'id', 'sequence']
        numeric_cols = [
            col for col in df.select_dtypes(include=[np.number]).columns
            if col not in exclude_cols
        ]
        
        if len(numeric_cols) == 0:
            step_info['actions'].append("No numeric features to normalize")
            return df, step_info
        
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        elif method == 'robust':
            scaler = RobustScaler()
        else:
            step_info['actions'].append(f"Unknown scaling method: {method}")
            return df, step_info
        
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        self.scalers[method] = scaler
        
        step_info['actions'].append(f"Normalized {len(numeric_cols)} features using {method} scaling")
        step_info['stats']['normalized_features'] = len(numeric_cols)
        
        return df, step_info
    
    async def _create_data_splits(
        self,
        df: pd.DataFrame,
        target_column: str = 'label',
        test_size: float = 0.2,
        val_size: float = 0.1,
        stratify: bool = True
    ) -> Tuple[Dict, Dict]:
        """Split data into train/validation/test sets"""
        step_info = {
            'step': 'Data Splitting',
            'actions': [],
            'stats': {},
            'warnings': []
        }
        
        # Separate features and target
        if target_column not in df.columns:
            # Try to find target column
            possible_targets = ['label', 'target', 'class', 'y']
            target_column = next((col for col in possible_targets if col in df.columns), df.columns[-1])
        
        exclude_cols = [target_column, 'id', 'sequence']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        X = df[feature_cols].values
        y = df[target_column].values
        
        # Encode target if not numeric
        if not np.issubdtype(y.dtype, np.number):
            le = LabelEncoder()
            y = le.fit_transform(y)
            self.label_encoders[target_column] = le
            step_info['actions'].append(f"Encoded target variable ({len(le.classes_)} classes)")
        
        # Check class distribution
        unique_classes, class_counts = np.unique(y, return_counts=True)
        min_class_count = np.min(class_counts)
        
        # Validate minimum samples per class for stratified split
        min_samples_needed = 2  # Minimum for stratified split
        if min_class_count < min_samples_needed:
            step_info['warnings'].append(
                f"Class with only {min_class_count} sample(s) detected. "
                f"Need at least {min_samples_needed} samples per class for stratified split. "
                f"Using simple random split instead."
            )
            stratify = False
        
        # Adjust split sizes for very small datasets
        total_samples = len(y)
        if total_samples < 20:
            step_info['warnings'].append(
                f"Very small dataset ({total_samples} samples). "
                f"Results may not be reliable. Recommend at least 50 samples."
            )
            # Use larger train set for tiny datasets
            test_size = min(0.2, max(0.1, 2 / total_samples))
            val_size = min(0.1, max(0.05, 1 / total_samples))
        
        # First split: train+val vs test
        stratify_param = y if stratify and len(unique_classes) > 1 and min_class_count >= 2 else None
        
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=stratify_param
        )
        
        # Second split: train vs val
        # Check if we can still stratify after first split
        if stratify_param is not None:
            unique_temp, counts_temp = np.unique(y_temp, return_counts=True)
            if np.min(counts_temp) < 2:
                stratify_param = None
                step_info['warnings'].append(
                    "Insufficient samples for stratified validation split. Using random split."
                )
        
        val_ratio = val_size / (1 - test_size)
        stratify_param_val = y_temp if stratify_param is not None else None
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_ratio, random_state=42, stratify=stratify_param_val
        )
        
        splits = {
            'train': {'X': X_train, 'y': y_train},
            'val': {'X': X_val, 'y': y_val},
            'test': {'X': X_test, 'y': y_test},
            'feature_names': feature_cols
        }
        
        step_info['actions'].append(f"Split data: {len(X_train)} train, {len(X_val)} val, {len(X_test)} test")
        step_info['stats'] = {
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'test_samples': len(X_test),
            'n_features': X_train.shape[1],
            'n_classes': len(np.unique(y))
        }
        
        return splits, step_info


# Global instance
preprocessing_service = PreprocessingService()
