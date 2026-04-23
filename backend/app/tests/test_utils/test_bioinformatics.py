"""
Tests for bioinformatics utilities
"""

import pytest
from app.utils.bioinformatics import (
    detect_sequence_type, validate_fasta_format,
    calculate_sequence_composition, generate_kmer_features
)


class TestBioinformaticsUtils:
    """Test bioinformatics utility functions"""
    
    def test_detect_sequence_type_dna(self):
        """Test DNA sequence type detection"""
        dna_sequences = [
            "ATCGATCGATCG",
            "AAATTTCCCGGG",
            "ATCGATCGNNNN"
        ]
        
        for seq in dna_sequences:
            result = detect_sequence_type(seq)
            assert result == "dna"
    
    def test_detect_sequence_type_rna(self):
        """Test RNA sequence type detection"""
        rna_sequences = [
            "AUCGAUCGAUCG",
            "AAAUUUCCCGGG",
            "AUCGAUCGUNNN"
        ]
        
        for seq in rna_sequences:
            result = detect_sequence_type(seq)
            assert result == "rna"
    
    def test_detect_sequence_type_protein(self):
        """Test protein sequence type detection"""
        protein_sequences = [
            "MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG",
            "ACDEFGHIKLMNPQRSTVWY",
            "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHF"
        ]
        
        for seq in protein_sequences:
            result = detect_sequence_type(seq)
            assert result == "protein"
    
    def test_detect_sequence_type_unknown(self):
        """Test unknown sequence type detection"""
        unknown_sequences = [
            "123456789",
            "!@#$%^&*()",
            "",
            "XYZXYZXYZ"
        ]
        
        for seq in unknown_sequences:
            result = detect_sequence_type(seq)
            assert result == "unknown"
    
    def test_validate_fasta_format_valid(self, temp_fasta_file):
        """Test FASTA format validation with valid file"""
        result = validate_fasta_format(str(temp_fasta_file))
        
        assert result["is_valid"] is True
        assert result["sequence_count"] > 0
        assert result["status"] in ["valid", "valid_with_warnings"]
        assert len(result["errors"]) == 0
    
    def test_validate_fasta_format_invalid(self, tmp_path):
        """Test FASTA format validation with invalid file"""
        invalid_fasta = tmp_path / "invalid.fasta"
        invalid_fasta.write_text("This is not a FASTA file\nNo headers here")
        
        result = validate_fasta_format(str(invalid_fasta))
        
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert result["sequence_count"] == 0
    
    def test_calculate_sequence_composition_dna(self):
        """Test sequence composition calculation for DNA"""
        sequences = [
            "ATCGATCGATCG",
            "AAATTTCCCGGG",
            "TTTTAAAACCCC"
        ]
        
        result = calculate_sequence_composition(sequences, "dna")
        
        assert "sequence_count" in result
        assert "total_length" in result
        assert "avg_length" in result
        assert "composition" in result
        assert "gc_content" in result
        assert result["sequence_count"] == len(sequences)
    
    def test_calculate_sequence_composition_protein(self):
        """Test sequence composition calculation for protein"""
        sequences = [
            "ACDEFGHIKLMNPQRSTVWY",
            "MVLSPADKTNVKAAWGKVGA",
            "MKTVRQERLKSIVRILERSE"
        ]
        
        result = calculate_sequence_composition(sequences, "protein")
        
        assert "sequence_count" in result
        assert "composition" in result
        assert "molecular_weight" in result or "isoelectric_point" in result
        assert result["sequence_count"] == len(sequences)
    
    def test_calculate_sequence_composition_empty(self):
        """Test sequence composition calculation with empty list"""
        result = calculate_sequence_composition([], "dna")
        
        assert result == {}
    
    def test_generate_kmer_features(self):
        """Test k-mer feature generation"""
        sequences = [
            "ATCGATCG",
            "GCTAGCTA",
            "TTTTAAAA"
        ]
        
        result = generate_kmer_features(sequences, k=3, normalize=True)
        
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # Check that all sequences have features
        for kmer, frequencies in result.items():
            assert len(frequencies) == len(sequences)
            assert all(0 <= freq <= 1 for freq in frequencies)  # Normalized
    
    def test_generate_kmer_features_different_k(self):
        """Test k-mer feature generation with different k values"""
        sequences = ["ATCGATCGATCG"]
        
        for k in [2, 3, 4]:
            result = generate_kmer_features(sequences, k=k)
            assert isinstance(result, dict)
            # Check that k-mer length is correct
            if result:
                sample_kmer = next(iter(result.keys()))
                assert len(sample_kmer) == k
    
    def test_generate_kmer_features_empty(self):
        """Test k-mer feature generation with empty sequences"""
        result = generate_kmer_features([], k=3)
        
        assert result == {}
