"""
Tests for validation utilities
"""

import pytest
from app.utils.validators import (
    validate_email, validate_password_strength,
    validate_dataset_config, validate_model_config,
    validate_file_upload
)


class TestValidators:
    """Test validation utility functions"""
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails"""
        valid_emails = [
            "user@example.com",
            "test.user+tag@domain.co.uk",
            "simple@test.org"
        ]
        
        for email in valid_emails:
            result = validate_email(email)
            assert result["is_valid"] is True
            assert result["normalized_email"] == email.lower()
            assert len(result["errors"]) == 0
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails"""
        invalid_emails = [
            "invalid.email@",
            "@domain.com",
            "plain.text",
            "user@",
            ""
        ]
        
        for email in invalid_emails:
            result = validate_email(email)
            assert result["is_valid"] is False
            assert len(result["errors"]) > 0
    
    def test_validate_password_strength_strong(self):
        """Test password validation with strong passwords"""
        strong_passwords = [
            "StrongP@ssword123",
            "MySecure!Password456",
            "Complex&Password789"
        ]
        
        for password in strong_passwords:
            result = validate_password_strength(password)
            assert result["is_valid"] is True
            assert result["score"] >= 4
            assert result["strength"] in ["Good", "Strong", "Very Strong"]
    
    def test_validate_password_strength_weak(self):
        """Test password validation with weak passwords"""
        weak_passwords = [
            "weak",
            "password",
            "123456",
            "qwerty",
            "abc123"
        ]
        
        for password in weak_passwords:
            result = validate_password_strength(password)
            assert result["is_valid"] is False
            assert result["score"] <= 2
            assert len(result["errors"]) > 0
    
    def test_validate_dataset_config_valid(self):
        """Test dataset config validation with valid configs"""
        valid_configs = [
            {
                "dataset_type": "dna",
                "name": "Test Dataset",
                "description": "A test dataset"
            },
            {
                "dataset_type": "protein",
                "name": "Protein Data",
                "max_file_size": 100
            }
        ]
        
        for config in valid_configs:
            result = validate_dataset_config(config)
            assert result["is_valid"] is True
            assert len(result["errors"]) == 0
    
    def test_validate_dataset_config_missing_required(self):
        """Test dataset config validation with missing required fields"""
        invalid_configs = [
            {},  # Missing everything
            {"dataset_type": "dna"},  # Missing name
            {"name": "Test"},  # Missing dataset_type
        ]
        
        for config in invalid_configs:
            result = validate_dataset_config(config)
            assert result["is_valid"] is False
            assert len(result["errors"]) > 0
    
    def test_validate_dataset_config_invalid_type(self):
        """Test dataset config validation with invalid type"""
        config = {
            "dataset_type": "invalid_type",
            "name": "Test Dataset"
        }
        
        result = validate_dataset_config(config)
        
        assert result["is_valid"] is False
        assert any("Invalid dataset type" in error for error in result["errors"])
    
    def test_validate_model_config_valid(self):
        """Test model config validation with valid configs"""
        valid_configs = [
            {
                "model_type": "classification",
                "algorithm": "random_forest",
                "hyperparameters": {
                    "n_estimators": 100,
                    "max_depth": 10
                },
                "test_size": 0.2,
                "cv_folds": 5
            },
            {
                "model_type": "regression",
                "algorithm": "linear_regression"
            }
        ]
        
        for config in valid_configs:
            result = validate_model_config(config)
            assert result["is_valid"] is True
            assert len(result["errors"]) == 0
    
    def test_validate_model_config_invalid(self):
        """Test model config validation with invalid configs"""
        invalid_configs = [
            {"model_type": "invalid_type", "algorithm": "random_forest"},
            {"model_type": "classification", "algorithm": "unknown_algorithm"},
            {"model_type": "classification", "algorithm": "random_forest", "test_size": 1.5},
            {"model_type": "classification", "algorithm": "random_forest", "cv_folds": 1}
        ]
        
        for config in invalid_configs:
            result = validate_model_config(config)
            assert result["is_valid"] is False
            assert len(result["errors"]) > 0
    
    def test_validate_file_upload_valid(self):
        """Test file upload validation with valid parameters"""
        result = validate_file_upload(
            filename="test.fasta",
            file_size=1024 * 1024,  # 1MB
            allowed_extensions=["fasta", "csv", "txt"],
            max_size_mb=10
        )
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_file_upload_invalid_extension(self):
        """Test file upload validation with invalid extension"""
        result = validate_file_upload(
            filename="test.exe",
            file_size=1024,
            allowed_extensions=["fasta", "csv", "txt"],
            max_size_mb=10
        )
        
        assert result["is_valid"] is False
        assert any("not allowed" in error for error in result["errors"])
    
    def test_validate_file_upload_too_large(self):
        """Test file upload validation with file too large"""
        result = validate_file_upload(
            filename="test.fasta",
            file_size=20 * 1024 * 1024,  # 20MB
            allowed_extensions=["fasta"],
            max_size_mb=10
        )
        
        assert result["is_valid"] is False
        assert any("exceeds maximum" in error for error in result["errors"])
    
    def test_validate_file_upload_empty_file(self):
        """Test file upload validation with empty file"""
        result = validate_file_upload(
            filename="test.fasta",
            file_size=0,
            allowed_extensions=["fasta"],
            max_size_mb=10
        )
        
        assert result["is_valid"] is False
        assert any("empty" in error for error in result["errors"])
