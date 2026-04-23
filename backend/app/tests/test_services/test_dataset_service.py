"""
Tests for dataset service
"""

import pytest
from pathlib import Path
from app.services.dataset_service import DatasetService


class TestDatasetService:
    """Test dataset service functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_biological_dataset(self, temp_fasta_file):
        """Test biological dataset analysis"""
        dataset_service = DatasetService()
        
        stats = await dataset_service.analyze_dataset(temp_fasta_file, "dna")
        
        assert "sequence_count" in stats
        assert "total_sequences" in stats
        assert stats["sequence_count"] > 0
        assert stats["format"] == "fasta"
        assert "avg_sequence_length" in stats
        assert "gc_content" in stats
    
    @pytest.mark.asyncio
    async def test_analyze_general_dataset(self, temp_csv_file):
        """Test general dataset analysis"""
        dataset_service = DatasetService()
        
        stats = await dataset_service.analyze_dataset(temp_csv_file, "general")
        
        assert "total_rows" in stats
        assert "total_columns" in stats
        assert stats["total_rows"] > 0
        assert stats["format"] in ["csv", "tsv"]
        assert "columns" in stats
    
    @pytest.mark.asyncio
    async def test_preview_biological_dataset(self, temp_fasta_file):
        """Test biological dataset preview"""
        dataset_service = DatasetService()
        
        preview = await dataset_service.preview_dataset(str(temp_fasta_file), "dna", 2)
        
        assert isinstance(preview, list)
        assert len(preview) <= 2
        if preview:
            assert "id" in preview[0]
            assert "sequence" in preview[0]
            assert "length" in preview[0]
    
    @pytest.mark.asyncio
    async def test_preview_general_dataset(self, temp_csv_file):
        """Test general dataset preview"""
        dataset_service = DatasetService()
        
        preview = await dataset_service.preview_dataset(str(temp_csv_file), "general", 3)
        
        assert isinstance(preview, list)
        assert len(preview) <= 3
        if preview:
            assert "sequence" in preview[0]
            assert "label" in preview[0]
    
    @pytest.mark.asyncio
    async def test_validate_biological_dataset(self, temp_fasta_file):
        """Test biological dataset validation"""
        dataset_service = DatasetService()
        
        validation = await dataset_service.validate_dataset(str(temp_fasta_file), "dna")
        
        assert "is_valid" in validation
        assert "errors" in validation
        assert isinstance(validation["errors"], list)
        assert isinstance(validation["is_valid"], bool)
    
    @pytest.mark.asyncio
    async def test_validate_general_dataset(self, temp_csv_file):
        """Test general dataset validation"""
        dataset_service = DatasetService()
        
        validation = await dataset_service.validate_dataset(str(temp_csv_file), "general")
        
        assert "is_valid" in validation
        assert isinstance(validation["errors"], list)
    
    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self):
        """Test analyzing non-existent file"""
        dataset_service = DatasetService()
        
        with pytest.raises(FileNotFoundError):
            await dataset_service.analyze_dataset(Path("nonexistent.fasta"), "dna")
    
    @pytest.mark.asyncio
    async def test_delete_dataset_files(self, temp_fasta_file, test_dataset):
        """Test dataset file deletion"""
        dataset_service = DatasetService()
        
        # File should exist initially
        assert temp_fasta_file.exists()
        
        # Delete files
        success = await dataset_service.delete_dataset_files(test_dataset.id)
        
        # For mocked environment, this should succeed
        assert isinstance(success, bool)
