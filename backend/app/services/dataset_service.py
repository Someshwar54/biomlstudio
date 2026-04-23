"""
Dataset service for managing biological datasets
"""
#Datasets: Upload, analyze, preview, validate

import hashlib
import logging
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional

from Bio import SeqIO
from Bio.SeqUtils import gc_fraction

from app.core.config import settings
from app.core.database import get_db_context
from app.models.dataset import Dataset
from app.utils.bioinformatics import (
    detect_sequence_type, validate_fasta_format, 
    calculate_sequence_composition
)

logger = logging.getLogger(__name__)


class DatasetService:
    """Service for dataset management and analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_dataset(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """
        Analyze dataset and generate statistics.
        
        Args:
            file_path: Path to dataset file
            dataset_type: Type of dataset (dna, protein, rna, general)
            
        Returns:
            Dict: Dataset statistics
        """
        try:
            stats = {}
            file_extension = file_path.suffix.lower()
            
            # First check file extension to determine analysis method
            is_biological_extension = file_extension in ['.fasta', '.fa', '.fas', '.fastq', '.fq']
            is_general_extension = file_extension in ['.csv', '.tsv']
            
            if is_biological_extension:
                # If file is FASTA/FASTQ, analyze as biological data regardless of dataset_type
                stats = await self._analyze_biological_dataset(file_path, dataset_type)
            elif is_general_extension and dataset_type == 'general':
                # Only analyze as general dataset if explicitly marked as 'general' type
                stats = await self._analyze_general_dataset(file_path)
            elif dataset_type in ['dna', 'rna', 'protein']:
                # Fall back to biological analysis if dataset_type is specified
                stats = await self._analyze_biological_dataset(file_path, dataset_type)
            else:
                # Default to general analysis
                stats = await self._analyze_general_dataset(file_path)
            
            # Add file hash for integrity checking
            stats['file_hash'] = self._calculate_file_hash(file_path)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing dataset {file_path}: {e}")
            return {"error": str(e)}
    
    async def _analyze_biological_dataset(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """Analyze biological sequence dataset"""
        file_extension = file_path.suffix.lower()
        
        if file_extension in ['.fasta', '.fa', '.fas']:
            return await self._analyze_fasta_file(file_path, dataset_type)
        elif file_extension in ['.fastq', '.fq']:
            return await self._analyze_fastq_file(file_path, dataset_type)
        elif file_extension in ['.csv', '.tsv']:
            return await self._analyze_sequence_csv(file_path, dataset_type)
        else:
            raise ValueError(f"Unsupported biological file format: {file_extension}")
    
    async def _analyze_fasta_file(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """Analyze FASTA format file"""
        sequences = []
        sequence_lengths = []
        
        try:
            with open(file_path, 'r') as handle:
                for record in SeqIO.parse(handle, "fasta"):
                    sequences.append(str(record.seq))
                    sequence_lengths.append(len(record.seq))
            
            if not sequences:
                raise ValueError("No valid sequences found in FASTA file")
            
            # Calculate sequence statistics
            stats = {
                "format": "fasta",
                "sequence_count": len(sequences),
                "total_sequences": len(sequences),
                "total_rows": len(sequences),  # For UI consistency
                "min_sequence_length": min(sequence_lengths),
                "max_sequence_length": max(sequence_lengths),
                "avg_sequence_length": sum(sequence_lengths) / len(sequence_lengths),
                "total_bases": sum(sequence_lengths)
            }
            
            # Add sequence-type specific stats
            if dataset_type in ['dna', 'rna']:
                gc_contents = [gc_fraction(seq) for seq in sequences[:100]]  # Sample first 100
                stats.update({
                    "avg_gc_content": sum(gc_contents) / len(gc_contents),
                    "min_gc_content": min(gc_contents),
                    "max_gc_content": max(gc_contents)
                })
                
                # Count nucleotides in sample
                sample_seq = ''.join(sequences[:10])  # First 10 sequences
                nucleotide_counts = {
                    'A': sample_seq.upper().count('A'),
                    'T': sample_seq.upper().count('T'),
                    'G': sample_seq.upper().count('G'),
                    'C': sample_seq.upper().count('C'),
                    'N': sample_seq.upper().count('N')
                }
                stats["nucleotide_composition"] = nucleotide_counts
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing FASTA file: {e}")
            raise
    
    async def _analyze_fastq_file(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """Analyze FASTQ format file"""
        sequences = []
        sequence_lengths = []
        quality_scores = []
        
        try:
            with open(file_path, 'r') as handle:
                for record in SeqIO.parse(handle, "fastq"):
                    sequences.append(str(record.seq))
                    sequence_lengths.append(len(record.seq))
                    if hasattr(record, 'letter_annotations') and 'phred_quality' in record.letter_annotations:
                        quality_scores.append(sum(record.letter_annotations['phred_quality']) / len(record.seq))
            
            if not sequences:
                raise ValueError("No valid sequences found in FASTQ file")
            
            stats = {
                "format": "fastq",
                "sequence_count": len(sequences),
                "total_sequences": len(sequences),
                "total_rows": len(sequences),  # For UI consistency
                "min_sequence_length": min(sequence_lengths),
                "max_sequence_length": max(sequence_lengths),
                "avg_sequence_length": sum(sequence_lengths) / len(sequence_lengths),
                "total_bases": sum(sequence_lengths)
            }
            
            if quality_scores:
                stats.update({
                    "avg_quality_score": sum(quality_scores) / len(quality_scores),
                    "min_quality_score": min(quality_scores),
                    "max_quality_score": max(quality_scores)
                })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing FASTQ file: {e}")
            raise
    
    async def _analyze_sequence_csv(
        self, 
        file_path: Path, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """Analyze CSV file containing biological sequences"""
        try:
            # Detect delimiter
            with open(file_path, 'r') as f:
                first_line = f.readline()
                delimiter = '\t' if '\t' in first_line else ','
            
            df = pd.read_csv(file_path, delimiter=delimiter)
            
            stats = {
                "format": "csv" if delimiter == ',' else "tsv",
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns),
                "sequence_count": len(df),
                "total_sequences": len(df)
            }
            
            # Check if there's a sequence column
            sequence_cols = [col for col in df.columns if 'seq' in col.lower()]
            if sequence_cols:
                sequences = df[sequence_cols[0]].astype(str)
                sequence_lengths = sequences.str.len()
                stats.update({
                    "min_sequence_length": int(sequence_lengths.min()),
                    "max_sequence_length": int(sequence_lengths.max()),
                    "avg_sequence_length": float(sequence_lengths.mean())
                })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing sequence CSV: {e}")
            raise
    
    async def _analyze_general_dataset(self, file_path: Path) -> Dict[str, Any]:
        """Analyze general CSV/TSV dataset"""
        try:
            # Detect delimiter
            with open(file_path, 'r') as f:
                first_line = f.readline()
                delimiter = '\t' if '\t' in first_line else ','
            
            # Read dataset
            df = pd.read_csv(file_path, delimiter=delimiter, nrows=10000)  # Sample first 10k rows
            
            stats = {
                "format": "csv" if delimiter == ',' else "tsv",
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns),
                "column_types": df.dtypes.astype(str).to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024
            }
            
            # Add sample data for preview
            stats["sample_data"] = df.head(5).to_dict('records')
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing general dataset: {e}")
            raise
    
    async def preview_dataset(
        self, 
        file_path: str, 
        dataset_type: str, 
        rows: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate preview data for dataset.
        
        Args:
            file_path: Path to dataset file
            dataset_type: Type of dataset
            rows: Number of rows to preview
            
        Returns:
            List: Preview data records
        """
        from app.core.config import settings
        
        file_path = Path(file_path)
        
        # If path is relative, make it absolute relative to the backend directory
        if not file_path.is_absolute():
            # Get the backend directory (where the app is running)
            backend_dir = Path(__file__).parent.parent.parent
            file_path = backend_dir / file_path
        
        self.logger.info(f"Preview called: file={file_path.name}, dataset_type={dataset_type}, suffix={file_path.suffix}, absolute_path={file_path}")
        
        # Check if file exists, if not try to find it in uploads directory
        if not file_path.exists():
            self.logger.warning(f"File not found at {file_path}, searching in uploads directory...")
            backend_dir = Path(__file__).parent.parent.parent
            
            # Try to find the file by name in uploads directory
            uploads_dir = backend_dir / "uploads"
            if uploads_dir.exists():
                for user_dir in uploads_dir.iterdir():
                    if user_dir.is_dir():
                        potential_file = user_dir / file_path.name
                        if potential_file.exists():
                            file_path = potential_file
                            self.logger.info(f"Found file at alternative location: {file_path}")
                            break
            
            # If still not found, return empty result
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return []
        
        try:
            if dataset_type in ['dna', 'rna', 'protein']:
                return await self._preview_biological_dataset(file_path, rows)
            else:
                return await self._preview_general_dataset(file_path, rows)
                
        except Exception as e:
            self.logger.error(f"Error previewing dataset: {e}")
            return []
    
    async def _preview_biological_dataset(
        self, 
        file_path: Path, 
        rows: int
    ) -> List[Dict[str, Any]]:
        """Preview biological sequence dataset"""
        preview_data = []
        
        self.logger.info(f"Biological preview: file={file_path.name}, suffix={file_path.suffix}")
        
        if file_path.suffix.lower() in ['.fasta', '.fa', '.fas']:
            # Convert FASTA to CSV for preview
            from app.utils.bioinformatics import convert_fasta_to_csv
            import tempfile
            import pandas as pd
            import os
            
            temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w')
            temp_csv_path = temp_csv.name
            temp_csv.close()
            
            try:
                conversion_config = {
                    'add_composition': True,
                    'add_kmers': True,
                    'kmer_size': 3,
                    'max_sequences': 100
                }
                
                self.logger.info(f"Converting FASTA to CSV: {file_path} -> {temp_csv_path}")
                result = convert_fasta_to_csv(str(file_path), temp_csv_path, conversion_config)
                
                if result['success']:
                    self.logger.info(f"Conversion successful: {result['sequences_converted']} sequences, columns: {result.get('columns', [])}")
                    df = pd.read_csv(temp_csv_path)
                    self.logger.info(f"DataFrame loaded: shape={df.shape}, columns={list(df.columns)}")
                    
                    # Keep sequence_id and sequence_type for potential target columns
                    # Only drop the actual sequence data to save space
                    df = df.drop(columns=['sequence'], errors='ignore')
                    self.logger.info(f"After dropping sequence: columns={list(df.columns)}")
                    
                    # For biological data, add a sample class column if not present
                    if 'class' not in df.columns and 'label' not in df.columns and 'target' not in df.columns:
                        # Extract potential class from sequence_id (common pattern)
                        if 'sequence_id' in df.columns:
                            df['class'] = df['sequence_id'].str.extract(r'([a-zA-Z_]+)', expand=False).fillna('unknown')
                    
                    # Replace NaN with None for JSON serialization
                    df = df.fillna(0)  # Fill NaN with 0 for numeric k-mer counts
                    preview_data = df.head(rows).to_dict('records')
                    self.logger.info(f"Preview data created: {len(preview_data)} rows")
                else:
                    self.logger.error(f"FASTA conversion failed: {result.get('error')}")
                    preview_data = []
            except Exception as e:
                self.logger.error(f"Error converting FASTA for preview: {e}", exc_info=True)
                preview_data = []
            finally:
                # Clean up temp file
                if os.path.exists(temp_csv_path):
                    os.unlink(temp_csv_path)
        
        return preview_data
    
    async def _preview_general_dataset(
        self, 
        file_path: Path, 
        rows: int
    ) -> List[Dict[str, Any]]:
        """Preview general CSV/TSV dataset"""
        try:
            # Detect delimiter
            with open(file_path, 'r') as f:
                first_line = f.readline()
                delimiter = '\t' if '\t' in first_line else ','
            
            df = pd.read_csv(file_path, delimiter=delimiter, nrows=rows)
            # Replace NaN with None for JSON serialization
            df = df.fillna(0)  # or use None: df.where(pd.notnull(df), None)
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Error previewing general dataset: {e}")
            return []
    
    async def validate_dataset(
        self, 
        file_path: str, 
        dataset_type: str
    ) -> Dict[str, Any]:
        """
        Validate dataset format and content.
        
        Args:
            file_path: Path to dataset file
            dataset_type: Expected dataset type
            
        Returns:
            Dict: Validation results
        """
        file_path = Path(file_path)
        
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "format_detected": None,
            "sequence_type": None
        }
        
        try:
            if dataset_type in ['dna', 'rna', 'protein']:
                return await self._validate_biological_dataset(file_path, dataset_type)
            else:
                return await self._validate_general_dataset(file_path)
                
        except Exception as e:
            validation_results["is_valid"] = False
            validation_results["errors"].append(str(e))
            return validation_results
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    async def get_dataset_by_id(self, dataset_id: int) -> Optional[Dataset]:
        """Get dataset by ID"""
        with get_db_context() as db:
            return db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    async def delete_dataset_files(self, dataset_id: int) -> bool:
        """Delete dataset files from storage"""
        dataset = await self.get_dataset_by_id(dataset_id)
        
        if not dataset:
            return False
        
        try:
            file_path = Path(dataset.file_path)
            if file_path.exists():
                file_path.unlink()
            
            self.logger.info(f"Dataset files deleted for dataset {dataset_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting dataset files: {e}")
            return False
