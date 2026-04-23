"""
Bioinformatics utility functions for sequence analysis
"""

import logging
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction
from Bio.SeqUtils.ProtParam import ProteinAnalysis

logger = logging.getLogger(__name__)


def extract_label_from_header(header: str) -> str:
    """
    Extract label from FASTA header description.
    
    Supports multiple naming conventions:
    - Space-separated: '>seq1 Cancer_sample'
    - Pipe-separated: '>seq1|cancer'
    - Underscore: '>seq1_cancer'
    
    Auto-detects disease/normal keywords and maps them to standard labels.
    
    Args:
        header: FASTA header/description string
        
    Returns:
        str: Extracted label (e.g., 'affected', 'normal', or custom label)
    """
    # Common disease/normal keywords
    disease_keywords = ['cancer', 'tumor', 'disease', 'affected', 'diseased', 
                       'mutant', 'mutation', 'pathogenic', 'malignant', 'positive']
    normal_keywords = ['normal', 'healthy', 'control', 'wildtype', 'wild-type',
                      'benign', 'negative', 'unaffected']
    
    label = None
    
    # Try space-separated format (most common)
    parts = header.split()
    if len(parts) > 1:
        last_word = parts[-1].lower()
        
        if any(keyword in last_word for keyword in disease_keywords):
            label = 'affected'
        elif any(keyword in last_word for keyword in normal_keywords):
            label = 'normal'
        else:
            # Use last word as-is (custom label)
            label = parts[-1]
    
    # Try pipe-separated format: >seq1|cancer
    if not label and '|' in header:
        parts = header.split('|')
        if len(parts) > 1:
            potential_label = parts[-1].strip().lower()
            if any(keyword in potential_label for keyword in disease_keywords):
                label = 'affected'
            elif any(keyword in potential_label for keyword in normal_keywords):
                label = 'normal'
            else:
                label = parts[-1].strip()
    
    # Try underscore format: >seq1_cancer
    if not label and '_' in header:
        parts = header.split('_')
        potential_label = parts[-1].lower()
        if any(keyword in potential_label for keyword in disease_keywords):
            label = 'affected'
        elif any(keyword in potential_label for keyword in normal_keywords):
            label = 'normal'
        else:
            label = parts[-1]
    
    # Return label or 'unknown' if nothing found
    return label if label else 'unknown'


def detect_sequence_type(sequence: str) -> str:
    """
    Detect the type of biological sequence.
    
    Args:
        sequence: Biological sequence string
        
    Returns:
        str: Sequence type ('dna', 'rna', 'protein', 'unknown')
    """
    sequence = sequence.upper().strip()
    
    if not sequence:
        return 'unknown'
    
    # Count nucleotides and amino acids
    nucleotides = set('ATCG')
    rna_nucleotides = set('AUCG')
    amino_acids = set('ACDEFGHIKLMNPQRSTVWY')
    
    seq_chars = set(sequence)
    
    # Calculate composition ratios
    nucleotide_ratio = len(seq_chars & nucleotides) / len(seq_chars) if seq_chars else 0
    rna_ratio = len(seq_chars & rna_nucleotides) / len(seq_chars) if seq_chars else 0
    amino_ratio = len(seq_chars & amino_acids) / len(seq_chars) if seq_chars else 0
    
    # Determine sequence type based on composition
    if nucleotide_ratio > 0.9 and 'U' not in sequence:
        return 'dna'
    elif rna_ratio > 0.9 and 'U' in sequence:
        return 'rna'
    elif amino_ratio > 0.8:
        return 'protein'
    else:
        return 'unknown'


def validate_fasta_format(file_path: str) -> Dict[str, Any]:
    """
    Validate FASTA file format.
    
    Args:
        file_path: Path to FASTA file
        
    Returns:
        Dict: Validation results
    """
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'sequence_count': 0,
        'status': 'valid'
    }
    
    try:
        with open(file_path, 'r') as handle:
            sequences = list(SeqIO.parse(handle, "fasta"))
            
            if not sequences:
                validation_result['is_valid'] = False
                validation_result['errors'].append("No valid sequences found in file")
                validation_result['status'] = 'invalid'
                return validation_result
            
            validation_result['sequence_count'] = len(sequences)
            
            # Check for common issues
            for i, record in enumerate(sequences):
                # Check for empty sequences
                if len(record.seq) == 0:
                    validation_result['warnings'].append(f"Empty sequence at record {i+1}")
                
                # Check for very short sequences
                if len(record.seq) < 10:
                    validation_result['warnings'].append(f"Very short sequence at record {i+1}")
                
                # Check for invalid characters
                seq_str = str(record.seq).upper()
                valid_chars = set('ATCGURYSWKMBDHVN-')  # Standard IUPAC codes
                invalid_chars = set(seq_str) - valid_chars
                
                if invalid_chars:
                    validation_result['warnings'].append(
                        f"Invalid characters {invalid_chars} in record {i+1}"
                    )
            
            # Set status based on warnings
            if validation_result['warnings']:
                validation_result['status'] = 'valid_with_warnings'
            
    except Exception as e:
        validation_result['is_valid'] = False
        validation_result['errors'].append(f"Error reading FASTA file: {str(e)}")
        validation_result['status'] = 'error'
    
    return validation_result


def calculate_sequence_composition(sequences: List[str], seq_type: str) -> Dict[str, Any]:
    """
    Calculate composition statistics for sequences.
    
    Args:
        sequences: List of sequence strings
        seq_type: Type of sequence ('dna', 'rna', 'protein')
        
    Returns:
        Dict: Composition statistics
    """
    if not sequences:
        return {}
    
    stats = {
        'sequence_count': len(sequences),
        'total_length': sum(len(seq) for seq in sequences),
        'avg_length': sum(len(seq) for seq in sequences) / len(sequences),
        'min_length': min(len(seq) for seq in sequences),
        'max_length': max(len(seq) for seq in sequences)
    }
    
    if seq_type in ['dna', 'rna']:
        # Nucleotide composition
        all_sequence = ''.join(sequences).upper()
        total_bases = len(all_sequence)
        
        base_counts = Counter(all_sequence)
        stats['composition'] = {
            base: count / total_bases * 100 
            for base, count in base_counts.items()
        }
        
        # GC content for sample of sequences
        gc_contents = []
        for seq in sequences[:1000]:  # Sample first 1000
            try:
                gc_content = gc_fraction(seq) * 100
                gc_contents.append(gc_content)
            except:
                continue
        
        if gc_contents:
            stats['gc_content'] = {
                'mean': np.mean(gc_contents),
                'std': np.std(gc_contents),
                'min': np.min(gc_contents),
                'max': np.max(gc_contents)
            }
    
    elif seq_type == 'protein':
        # Amino acid composition
        all_sequence = ''.join(sequences).upper()
        total_aa = len(all_sequence)
        
        aa_counts = Counter(all_sequence)
        stats['composition'] = {
            aa: count / total_aa * 100 
            for aa, count in aa_counts.items()
        }
        
        # Protein properties for sample
        molecular_weights = []
        isoelectric_points = []
        
        for seq in sequences[:100]:  # Sample first 100
            try:
                if re.match(r'^[ACDEFGHIKLMNPQRSTVWY]*$', seq.upper()):
                    analysis = ProteinAnalysis(seq)
                    molecular_weights.append(analysis.molecular_weight())
                    isoelectric_points.append(analysis.isoelectric_point())
            except:
                continue
        
        if molecular_weights:
            stats['molecular_weight'] = {
                'mean': np.mean(molecular_weights),
                'std': np.std(molecular_weights),
                'min': np.min(molecular_weights),
                'max': np.max(molecular_weights)
            }
        
        if isoelectric_points:
            stats['isoelectric_point'] = {
                'mean': np.mean(isoelectric_points),
                'std': np.std(isoelectric_points),
                'min': np.min(isoelectric_points),
                'max': np.max(isoelectric_points)
            }
    
    return stats


def generate_kmer_features(
    sequences: List[str], 
    k: int = 3,
    normalize: bool = True
) -> Dict[str, List[float]]:
    """
    Generate k-mer frequency features from sequences.
    
    Args:
        sequences: List of sequences
        k: K-mer size
        normalize: Whether to normalize frequencies
        
    Returns:
        Dict: K-mer features for each sequence
    """
    if not sequences:
        return {}
    
    # Get all possible k-mers from sequences
    all_kmers = set()
    kmer_counts = []
    
    for seq in sequences:
        seq = seq.upper()
        seq_kmers = defaultdict(int)
        
        # Extract k-mers from sequence
        for i in range(len(seq) - k + 1):
            kmer = seq[i:i+k]
            # Only include k-mers with valid nucleotides
            if re.match(r'^[ATCG]*$', kmer):
                seq_kmers[kmer] += 1
                all_kmers.add(kmer)
        
        kmer_counts.append(seq_kmers)
    
    # Convert to feature matrix
    all_kmers = sorted(list(all_kmers))
    features = {kmer: [] for kmer in all_kmers}
    
    for seq_kmers in kmer_counts:
        total_kmers = sum(seq_kmers.values()) if normalize else 1
        
        for kmer in all_kmers:
            count = seq_kmers.get(kmer, 0)
            frequency = count / total_kmers if total_kmers > 0 else 0
            features[kmer].append(frequency)
    
    return features


def convert_fasta_to_csv(
    fasta_path: str, 
    csv_path: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convert FASTA file to CSV format.
    
    Args:
        fasta_path: Input FASTA file path
        csv_path: Output CSV file path
        config: Conversion configuration
        
    Returns:
        Dict: Conversion results
    """
    try:
        sequences_data = []
        
        with open(fasta_path, 'r') as handle:
            for i, record in enumerate(SeqIO.parse(handle, "fasta")):
                seq_data = {
                    'sequence_id': record.id,
                    'sequence': str(record.seq),
                    'length': len(record.seq)
                }
                
                # Extract label from description using dedicated function
                label = extract_label_from_header(record.description)
                seq_data['label'] = label
                
                # Add sequence type detection
                seq_type = detect_sequence_type(str(record.seq))
                seq_data['sequence_type'] = seq_type
                
                # Add composition features if requested
                if config.get('add_composition', False):
                    if seq_type in ['dna', 'rna']:
                        seq_str = str(record.seq).upper()
                        total_len = len(seq_str)
                        
                        seq_data.update({
                            'gc_content': gc_fraction(seq_str) * 100,
                            'a_content': seq_str.count('A') / total_len * 100,
                            't_content': seq_str.count('T') / total_len * 100,
                            'c_content': seq_str.count('C') / total_len * 100,
                            'g_content': seq_str.count('G') / total_len * 100,
                            'n_content': seq_str.count('N') / total_len * 100
                        })
                
                # Add k-mer features if requested
                if config.get('add_kmers', False):
                    kmer_size = config.get('kmer_size', 3)
                    kmers = generate_kmer_features([str(record.seq)], kmer_size)
                    
                    for kmer, freqs in kmers.items():
                        seq_data[f'kmer_{kmer}'] = freqs[0] if freqs else 0
                
                sequences_data.append(seq_data)
                
                # Limit for large files
                if config.get('max_sequences') and i >= config['max_sequences']:
                    break
        
        # Create DataFrame and save
        df = pd.DataFrame(sequences_data)
        
        # Reorder columns: label first, then numeric features, drop metadata
        if 'label' in df.columns:
            other_cols = [col for col in df.columns if col not in ['sequence_id', 'sequence', 'sequence_type', 'label']]
            df = df[['label'] + other_cols]
        
        df.to_csv(csv_path, index=False)
        
        return {
            'success': True,
            'sequences_converted': len(sequences_data),
            'output_path': csv_path,
            'columns': list(df.columns)
        }
        
    except Exception as e:
        logger.error(f"Error converting FASTA to CSV: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def validate_biological_file(file_path: str, expected_type: str) -> Dict[str, Any]:
    """
    Validate biological file format and content.
    
    Args:
        file_path: Path to file
        expected_type: Expected sequence type
        
    Returns:
        Dict: Validation results
    """
    file_path = Path(file_path)
    
    validation = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'detected_format': None,
        'detected_type': None
    }
    
    try:
        # Detect file format
        if file_path.suffix.lower() in ['.fasta', '.fa', '.fas']:
            validation['detected_format'] = 'fasta'
            
            # Validate FASTA format
            fasta_validation = validate_fasta_format(str(file_path))
            validation['is_valid'] = fasta_validation['is_valid']
            validation['errors'].extend(fasta_validation['errors'])
            validation['warnings'].extend(fasta_validation['warnings'])
            
            # Check sequence type if file is valid
            if validation['is_valid'] and fasta_validation['sequence_count'] > 0:
                with open(file_path, 'r') as handle:
                    first_record = next(SeqIO.parse(handle, "fasta"))
                    validation['detected_type'] = detect_sequence_type(str(first_record.seq))
                    
                    # Check if detected type matches expected
                    if validation['detected_type'] != expected_type:
                        validation['warnings'].append(
                            f"Detected sequence type '{validation['detected_type']}' "
                            f"doesn't match expected type '{expected_type}'"
                        )
        
        elif file_path.suffix.lower() in ['.fastq', '.fq']:
            validation['detected_format'] = 'fastq'
            # FASTQ validation would be implemented here
            
        elif file_path.suffix.lower() in ['.csv', '.tsv']:
            validation['detected_format'] = 'tabular'
            # CSV/TSV validation would be implemented here
            
        else:
            validation['is_valid'] = False
            validation['errors'].append(f"Unsupported file format: {file_path.suffix}")
    
    except Exception as e:
        validation['is_valid'] = False
        validation['errors'].append(f"Error validating file: {str(e)}")
    
    return validation


def analyze_sequence_quality(sequences: List[str], seq_type: str = 'dna') -> Dict[str, Any]:
    """
    Analyze sequence quality metrics including ambiguous bases, gaps, and anomalies.
    
    Args:
        sequences: List of sequence strings
        seq_type: Sequence type ('dna', 'rna', 'protein')
        
    Returns:
        Dict: Quality analysis results
    """
    if not sequences:
        return {'error': 'No sequences provided'}
    
    quality_metrics = {
        'total_sequences': len(sequences),
        'sequences_with_issues': 0,
        'issues': []
    }
    
    if seq_type in ['dna', 'rna']:
        # DNA/RNA specific quality checks
        ambiguous_bases = set('NRYSWKMBDHV')
        valid_bases = set('ATCG' if seq_type == 'dna' else 'AUCG')
        
        total_ambiguous = 0
        total_gaps = 0
        total_invalid = 0
        sequences_with_ambiguous = 0
        sequences_with_gaps = 0
        sequences_too_short = 0
        
        for i, seq in enumerate(sequences):
            seq_upper = seq.upper()
            seq_issues = []
            
            # Count ambiguous bases
            ambiguous_count = sum(1 for base in seq_upper if base in ambiguous_bases)
            if ambiguous_count > 0:
                total_ambiguous += ambiguous_count
                sequences_with_ambiguous += 1
                seq_issues.append(f"Contains {ambiguous_count} ambiguous bases")
            
            # Count gaps
            gap_count = seq_upper.count('-')
            if gap_count > 0:
                total_gaps += gap_count
                sequences_with_gaps += 1
                seq_issues.append(f"Contains {gap_count} gaps")
            
            # Check for invalid characters
            invalid_chars = set(seq_upper) - valid_bases - ambiguous_bases - {'-'}
            if invalid_chars:
                total_invalid += len([c for c in seq_upper if c in invalid_chars])
                seq_issues.append(f"Contains invalid characters: {invalid_chars}")
            
            # Check sequence length
            if len(seq) < 50:
                sequences_too_short += 1
                seq_issues.append(f"Very short sequence ({len(seq)} bp)")
            
            if seq_issues:
                quality_metrics['sequences_with_issues'] += 1
                if i < 10:  # Report first 10 problematic sequences
                    quality_metrics['issues'].append({
                        'sequence_index': i,
                        'problems': seq_issues
                    })
        
        quality_metrics.update({
            'ambiguous_bases': {
                'total_count': total_ambiguous,
                'sequences_affected': sequences_with_ambiguous,
                'percentage': (sequences_with_ambiguous / len(sequences)) * 100
            },
            'gaps': {
                'total_count': total_gaps,
                'sequences_affected': sequences_with_gaps,
                'percentage': (sequences_with_gaps / len(sequences)) * 100
            },
            'invalid_characters': {
                'total_count': total_invalid
            },
            'length_issues': {
                'too_short': sequences_too_short
            }
        })
    
    elif seq_type == 'protein':
        # Protein specific quality checks
        valid_aa = set('ACDEFGHIKLMNPQRSTVWY')
        ambiguous_aa = set('XBZJ')
        
        sequences_with_unusual = 0
        total_unusual = 0
        
        for i, seq in enumerate(sequences):
            seq_upper = seq.upper()
            seq_issues = []
            
            # Check for unusual amino acids
            unusual_count = sum(1 for aa in seq_upper if aa in ambiguous_aa)
            if unusual_count > 0:
                total_unusual += unusual_count
                sequences_with_unusual += 1
                seq_issues.append(f"Contains {unusual_count} ambiguous amino acids")
            
            # Check for gaps
            if '-' in seq_upper:
                seq_issues.append("Contains gaps")
            
            if seq_issues and i < 10:
                quality_metrics['issues'].append({
                    'sequence_index': i,
                    'problems': seq_issues
                })
        
        quality_metrics.update({
            'unusual_amino_acids': {
                'total_count': total_unusual,
                'sequences_affected': sequences_with_unusual
            }
        })
    
    return quality_metrics


def detect_missing_data(sequences: List[str], metadata: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Detect missing or incomplete data in sequence dataset.
    
    Args:
        sequences: List of sequence strings
        metadata: Optional metadata associated with sequences
        
    Returns:
        Dict: Missing data analysis
    """
    missing_data = {
        'empty_sequences': 0,
        'sequences_with_all_N': 0,
        'sequences_mostly_gaps': 0,
        'missing_metadata_fields': {}
    }
    
    for i, seq in enumerate(sequences):
        # Check for empty sequences
        if not seq or len(seq) == 0:
            missing_data['empty_sequences'] += 1
            continue
        
        seq_upper = seq.upper()
        
        # Check for sequences that are all N (unknown bases)
        if seq_upper.replace('N', '').replace('-', '') == '':
            missing_data['sequences_with_all_N'] += 1
        
        # Check for sequences mostly composed of gaps
        if seq_upper.count('-') / len(seq_upper) > 0.5:
            missing_data['sequences_mostly_gaps'] += 1
    
    # Check metadata completeness if provided
    if metadata:
        # Identify all possible fields
        all_fields = set()
        for record in metadata:
            all_fields.update(record.keys())
        
        # Count missing values per field
        for field in all_fields:
            missing_count = sum(1 for record in metadata if field not in record or not record[field])
            if missing_count > 0:
                missing_data['missing_metadata_fields'][field] = {
                    'count': missing_count,
                    'percentage': (missing_count / len(metadata)) * 100
                }
    
    return missing_data


def generate_sequence_report(file_path: str, dataset_type: str) -> Dict[str, Any]:
    """
    Generate comprehensive sequence analysis report.
    
    Args:
        file_path: Path to sequence file
        dataset_type: Type of dataset ('dna', 'rna', 'protein')
        
    Returns:
        Dict: Comprehensive analysis report
    """
    report = {
        'file_info': {
            'path': file_path,
            'type': dataset_type
        }
    }
    
    try:
        file_path = Path(file_path)
        
        # Load sequences based on file type
        sequences = []
        if file_path.suffix.lower() in ['.fasta', '.fa', '.fas']:
            with open(file_path, 'r') as handle:
                for record in SeqIO.parse(handle, "fasta"):
                    sequences.append(str(record.seq))
        
        if not sequences:
            return {'error': 'No sequences found in file'}
        
        # Basic statistics
        report['basic_stats'] = calculate_sequence_composition(sequences, dataset_type)
        
        # Quality analysis
        report['quality_analysis'] = analyze_sequence_quality(sequences, dataset_type)
        
        # Missing data detection
        report['missing_data'] = detect_missing_data(sequences)
        
        # Summary recommendations
        recommendations = []
        
        if report['missing_data']['empty_sequences'] > 0:
            recommendations.append(f"Remove {report['missing_data']['empty_sequences']} empty sequences")
        
        if report['missing_data']['sequences_with_all_N'] > 0:
            recommendations.append(f"Review {report['missing_data']['sequences_with_all_N']} sequences with all N bases")
        
        if report['quality_analysis']['sequences_with_issues'] > len(sequences) * 0.1:
            recommendations.append("More than 10% of sequences have quality issues - consider data cleaning")
        
        report['recommendations'] = recommendations
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating sequence report: {e}")
        return {'error': str(e)}
