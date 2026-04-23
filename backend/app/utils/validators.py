"""
Validation utility functions
"""

import re
from typing import Any, Dict, List

from email_validator import validate_email as email_validate, EmailNotValidError


def validate_email(email: str) -> Dict[str, Any]:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        Dict: Validation result
    """
    try:
        valid = email_validate(email)
        return {
            'is_valid': True,
            'normalized_email': valid.email,
            'errors': []
        }
    except EmailNotValidError as e:
        return {
            'is_valid': False,
            'normalized_email': None,
            'errors': [str(e)]
        }


def validate_password_strength(password: str, min_length: int = 8) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        
    Returns:
        Dict: Validation result with strength score
    """
    errors = []
    score = 0
    
    # Length check
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")
    else:
        score += 1
        if len(password) >= 12:
            score += 1
    
    # Character type checks
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    else:
        score += 1
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    else:
        score += 1
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    else:
        score += 1
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        errors.append("Password must contain at least one special character")
    else:
        score += 1
    
    # Common patterns check
    if re.search(r'(.)\1{2,}', password):
        errors.append("Password should not contain repeated characters")
        score -= 1
    
    # Dictionary words (simplified check)
    common_words = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in common_words:
        errors.append("Password is too common")
        score -= 2
    
    # Calculate strength
    strength_labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong']
    strength_index = min(max(score, 0), len(strength_labels) - 1)
    
    return {
        'is_valid': len(errors) == 0,
        'score': score,
        'strength': strength_labels[strength_index],
        'errors': errors
    }


def validate_dataset_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate dataset configuration.
    
    Args:
        config: Dataset configuration
        
    Returns:
        Dict: Validation result
    """
    errors = []
    warnings = []
    
    required_fields = ['dataset_type', 'name']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate dataset type
    valid_types = ['dna', 'rna', 'protein', 'general']
    if 'dataset_type' in config and config['dataset_type'] not in valid_types:
        errors.append(f"Invalid dataset type. Must be one of: {', '.join(valid_types)}")
    
    # Validate name
    if 'name' in config:
        if len(config['name']) < 1:
            errors.append("Dataset name cannot be empty")
        if len(config['name']) > 255:
            errors.append("Dataset name too long (max 255 characters)")
    
    # Validate optional fields
    if 'description' in config and len(config['description']) > 1000:
        warnings.append("Description is very long (>1000 characters)")
    
    if 'max_file_size' in config:
        if not isinstance(config['max_file_size'], int) or config['max_file_size'] <= 0:
            errors.append("max_file_size must be a positive integer")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def validate_model_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate machine learning model configuration.
    
    Args:
        config: Model configuration
        
    Returns:
        Dict: Validation result
    """
    errors = []
    warnings = []
    
    required_fields = ['model_type', 'algorithm']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Validate model type
    valid_types = ['classification', 'regression', 'clustering']
    if 'model_type' in config and config['model_type'] not in valid_types:
        errors.append(f"Invalid model type. Must be one of: {', '.join(valid_types)}")
    
    # Validate algorithm
    valid_algorithms = [
        'random_forest', 'logistic_regression', 'svm', 
        'linear_regression', 'xgboost', 'neural_network'
    ]
    if 'algorithm' in config and config['algorithm'] not in valid_algorithms:
        errors.append(f"Invalid algorithm. Must be one of: {', '.join(valid_algorithms)}")
    
    # Validate hyperparameters
    if 'hyperparameters' in config:
        if not isinstance(config['hyperparameters'], dict):
            errors.append("Hyperparameters must be a dictionary")
        else:
            # Algorithm-specific validation
            algorithm = config.get('algorithm')
            hyperparams = config['hyperparameters']
            
            if algorithm == 'random_forest':
                if 'n_estimators' in hyperparams:
                    if not isinstance(hyperparams['n_estimators'], int) or hyperparams['n_estimators'] <= 0:
                        errors.append("n_estimators must be a positive integer")
                
                if 'max_depth' in hyperparams:
                    if hyperparams['max_depth'] is not None and (
                        not isinstance(hyperparams['max_depth'], int) or hyperparams['max_depth'] <= 0
                    ):
                        errors.append("max_depth must be a positive integer or None")
    
    # Validate training parameters
    if 'test_size' in config:
        test_size = config['test_size']
        if not isinstance(test_size, (int, float)) or test_size <= 0 or test_size >= 1:
            errors.append("test_size must be a float between 0 and 1")
    
    if 'cv_folds' in config:
        if not isinstance(config['cv_folds'], int) or config['cv_folds'] < 2:
            errors.append("cv_folds must be an integer >= 2")
    
    # Validate target column
    if 'target_column' in config:
        if not isinstance(config['target_column'], str) or len(config['target_column']) == 0:
            errors.append("target_column must be a non-empty string")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def validate_file_upload(
    filename: str, 
    file_size: int,
    allowed_extensions: List[str],
    max_size_mb: int = 100
) -> Dict[str, Any]:
    """
    Validate file upload parameters.
    
    Args:
        filename: Name of uploaded file
        file_size: Size of file in bytes
        allowed_extensions: List of allowed file extensions
        max_size_mb: Maximum file size in MB
        
    Returns:
        Dict: Validation result
    """
    errors = []
    
    # Validate filename
    if not filename or len(filename.strip()) == 0:
        errors.append("Filename cannot be empty")
    
    # Validate file extension
    if filename:
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        if extension not in [ext.lower() for ext in allowed_extensions]:
            errors.append(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
    
    # Validate file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        errors.append(f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)")
    
    if file_size <= 0:
        errors.append("File appears to be empty")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple JSON schema validation.
    
    Args:
        data: Data to validate
        schema: Schema definition
        
    Returns:
        Dict: Validation result
    """
    try:
        import jsonschema
        
        jsonschema.validate(instance=data, schema=schema)
        return {
            'is_valid': True,
            'errors': []
        }
    except ImportError:
        return {
            'is_valid': True,
            'errors': ['jsonschema package not available for validation']
        }
    except jsonschema.exceptions.ValidationError as e:
        return {
            'is_valid': False,
            'errors': [str(e)]
        }
