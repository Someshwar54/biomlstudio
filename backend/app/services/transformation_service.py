"""
Data transformation service for handling dataset preprocessing and feature engineering.
"""
import itertools
import logging
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder

logger = logging.getLogger(__name__)

class TransformationService:
    """Service for data transformation and feature engineering"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract_metadata(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from dataset.
        
        Args:
            file_path: Path to the dataset file
            dataset_type: Type of dataset (dna, rna, protein, general)
            
        Returns:
            Dict containing extracted metadata
        """
        metadata = {
            "basic_info": await self._extract_basic_info(file_path, dataset_type),
            "sequence_stats": await self._extract_sequence_stats(file_path, dataset_type),
            "quality_metrics": await self._extract_quality_metrics(file_path, dataset_type)
        }
        
        if dataset_type in ['dna', 'rna', 'protein']:
            metadata["biological_features"] = await self._extract_biological_features(
                file_path, dataset_type
            )
        
        return metadata
    
    async def _extract_basic_info(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """Extract basic file and sequence information"""
        file_size = file_path.stat().st_size
        file_extension = file_path.suffix.lower()
        
        basic_info = {
            "file_name": file_path.name,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "file_extension": file_extension,
            "dataset_type": dataset_type
        }
        
        return basic_info
    
    async def _extract_sequence_stats(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """Extract sequence-level statistics"""
        stats = {
            "total_sequences": 0,
            "sequence_lengths": [],
            "gc_content": []
        }
        
        try:
            if file_path.suffix.lower() in ['.fasta', '.fa', '.fas']:
                with open(file_path, 'r') as handle:
                    sequences = list(SeqIO.parse(handle, "fasta"))
                    stats["total_sequences"] = len(sequences)
                    
                    if sequences:
                        seq_lengths = [len(seq) for seq in sequences]
                        stats["sequence_lengths"] = {
                            "min": min(seq_lengths),
                            "max": max(seq_lengths),
                            "mean": sum(seq_lengths) / len(seq_lengths),
                            "median": sorted(seq_lengths)[len(seq_lengths)//2]
                        }
                        
                        if dataset_type in ['dna', 'rna']:
                            gc_contents = [gc_fraction(str(seq.seq)) * 100 for seq in sequences[:1000]]
                            stats["gc_content"] = {
                                "min": min(gc_contents),
                                "max": max(gc_contents),
                                "mean": sum(gc_contents) / len(gc_contents)
                            }
        
        except Exception as e:
            self.logger.error(f"Error extracting sequence stats: {e}")
            
        return stats
    
    async def _extract_quality_metrics(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """Extract quality metrics for the dataset"""
        # Placeholder for quality metrics
        return {
            "quality_score": 0.95,
            "completeness": 0.98,
            "contamination": 0.01
        }
    
    async def _extract_biological_features(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """Extract biological features specific to the sequence type"""
        features = {}
        
        if dataset_type in ['dna', 'rna']:
            features.update(await self._extract_nucleotide_features(file_path))
        elif dataset_type == 'protein':
            features.update(await self._extract_protein_features(file_path))
            
        return features
    
    async def _extract_nucleotide_features(self, file_path: Path) -> Dict[str, Any]:
        """Extract nucleotide-specific features"""
        features = {
            "nucleotide_composition": {},
            "gc_skew": 0.0,
            "at_skew": 0.0
        }
        
        try:
            with open(file_path, 'r') as handle:
                sequences = [str(record.seq) for record in SeqIO.parse(handle, "fasta")]
                if sequences:
                    # Calculate nucleotide composition
                    seq_str = ''.join(sequences[:10])  # Sample first 10 sequences
                    total = max(1, len(seq_str))
                    features["nucleotide_composition"] = {
                        'A': seq_str.upper().count('A') / total,
                        'T': seq_str.upper().count('T') / total,
                        'G': seq_str.upper().count('G') / total,
                        'C': seq_str.upper().count('C') / total,
                        'N': seq_str.upper().count('N') / total
                    }
                    
                    # Calculate GC and AT skew
                    g = seq_str.upper().count('G')
                    c = seq_str.upper().count('C')
                    a = seq_str.upper().count('A')
                    t = seq_str.upper().count('T')
                    
                    features["gc_skew"] = (g - c) / max(1, g + c)
                    features["at_skew"] = (a - t) / max(1, a + t)
                    
        except Exception as e:
            self.logger.error(f"Error extracting nucleotide features: {e}")
            
        return features
    
    async def _extract_protein_features(self, file_path: Path) -> Dict[str, Any]:
        """Extract protein-specific features"""
        features = {
            "amino_acid_composition": {},
            "molecular_weight": 0.0,
            "isoelectric_point": 0.0
        }
        
        try:
            with open(file_path, 'r') as handle:
                sequences = [str(record.seq) for record in SeqIO.parse(handle, "fasta")]
                if sequences:
                    # Calculate amino acid composition
                    seq_str = ''.join(sequences[:10])  # Sample first 10 sequences
                    total = max(1, len(seq_str))
                    aa_counts = {}
                    for aa in set(seq_str.upper()):
                        aa_counts[aa] = seq_str.upper().count(aa) / total
                    features["amino_acid_composition"] = aa_counts
                    
        except Exception as e:
            self.logger.error(f"Error extracting protein features: {e}")
            
        return features
    
    # Data Transformation Methods
    async def normalize_sequences(
        self,
        sequences: List[str],
        method: str = 'minmax',
        target_length: Optional[int] = None
    ) -> List[str]:
        """
        Normalize sequence lengths and values.
        
        Args:
            sequences: List of sequence strings
            method: Normalization method ('minmax', 'zscore', 'length')
            target_length: Target length for sequence padding/truncation
            
        Returns:
            List of normalized sequences
        """
        if not sequences:
            return []
            
        if method == 'length' and target_length:
            return self._normalize_sequence_length(sequences, target_length)
        else:
            # Convert sequences to numerical representation first
            encoded_seqs = await self.encode_sequences(sequences, 'onehot')
            
            if method == 'minmax':
                scaler = MinMaxScaler()
                normalized = scaler.fit_transform(encoded_seqs)
            elif method == 'zscore':
                scaler = StandardScaler()
                normalized = scaler.fit_transform(encoded_seqs)
            else:
                raise ValueError(f"Unsupported normalization method: {method}")
                
            return normalized.tolist()
    
    def _normalize_sequence_length(
        self,
        sequences: List[str],
        target_length: int
    ) -> List[str]:
        """Normalize all sequences to the same length by padding or truncating"""
        normalized = []
        for seq in sequences:
            if len(seq) < target_length:
                # Pad with 'N' for nucleotides or 'X' for proteins
                pad_char = 'N' if all(c in 'ACGTUN' for c in seq.upper()) else 'X'
                normalized.append(seq + pad_char * (target_length - len(seq)))
            else:
                normalized.append(seq[:target_length])
        return normalized
    
    async def encode_sequences(
        self,
        sequences: List[str],
        encoding: str = 'onehot',
        **kwargs
    ) -> np.ndarray:
        """
        Encode biological sequences into numerical representations.
        
        Args:
            sequences: List of sequence strings
            encoding: Encoding method ('onehot', 'integer', 'kmer')
            **kwargs: Additional encoding parameters
            
        Returns:
            Numpy array of encoded sequences
        """
        if encoding == 'onehot':
            return self._onehot_encode(sequences, **kwargs)
        elif encoding == 'integer':
            return self._integer_encode(sequences, **kwargs)
        elif encoding == 'kmer':
            return await self._kmer_encode(sequences, **kwargs)
        else:
            raise ValueError(f"Unsupported encoding method: {encoding}")
    
    def _onehot_encode(
        self,
        sequences: List[str],
        alphabet: str = 'ACGT'
    ) -> np.ndarray:
        """One-hot encode sequences"""
        char_to_int = {char: i for i, char in enumerate(alphabet)}
        onehot_encoded = np.zeros((len(sequences), len(max(sequences, key=len)), len(alphabet)))
        
        for i, seq in enumerate(sequences):
            for j, char in enumerate(seq):
                if char in char_to_int:
                    onehot_encoded[i, j, char_to_int[char]] = 1
                    
        return onehot_encoded
    
    def _integer_encode(
        self,
        sequences: List[str],
        alphabet: str = 'ACGT'
    ) -> np.ndarray:
        """Integer encode sequences"""
        char_to_int = {char: i+1 for i, char in enumerate(alphabet)}  # 0 for padding
        max_length = max(len(seq) for seq in sequences)
        encoded = np.zeros((len(sequences), max_length))
        
        for i, seq in enumerate(sequences):
            encoded[i, :len(seq)] = [char_to_int.get(char, 0) for char in seq]
            
        return encoded
    
    async def _kmer_encode(
        self,
        sequences: List[str],
        k: int = 3,
        normalize: bool = True
    ) -> np.ndarray:
        """K-mer frequency encoding"""
        from collections import defaultdict
        
        # Generate all possible k-mers
        alphabet = set(''.join(sequences))
        kmers = [''.join(p) for p in itertools.product(alphabet, repeat=k)]
        kmer_index = {kmer: i for i, kmer in enumerate(kmers)}
        
        # Count k-mers for each sequence
        kmer_counts = np.zeros((len(sequences), len(kmers)))
        
        for i, seq in enumerate(sequences):
            counts = defaultdict(int)
            for j in range(len(seq) - k + 1):
                kmer = seq[j:j+k]
                counts[kmer] += 1
            
            # Normalize by sequence length
            total = max(1, len(seq) - k + 1) if normalize else 1
            for kmer, count in counts.items():
                if kmer in kmer_index:
                    kmer_counts[i, kmer_index[kmer]] = count / total
                    
        return kmer_counts


