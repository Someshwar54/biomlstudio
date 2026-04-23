"""
File handling utilities
"""

import hashlib
import logging
import mimetypes
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Union

import magic
import pandas as pd

logger = logging.getLogger(__name__)


def get_file_info(filename: str) -> Dict[str, Any]:
    """
    Extract information from filename.
    
    Args:
        filename: Name of the file
        
    Returns:
        Dict: File information
    """
    path = Path(filename)
    
    return {
        'name': path.name,
        'stem': path.stem,
        'extension': path.suffix.lower(),
        'parts': path.parts,
        'mime_type': mimetypes.guess_type(filename)[0],
        'is_compressed': path.suffix.lower() in ['.gz', '.zip', '.bz2', '.xz']
    }


def safe_file_read(
    file_path: Union[str, Path], 
    max_size_mb: int = 100,
    encoding: str = 'utf-8'
) -> Optional[str]:
    """
    Safely read file content with size limits.
    
    Args:
        file_path: Path to file
        max_size_mb: Maximum file size in MB
        encoding: File encoding
        
    Returns:
        str: File content or None if too large/error
    """
    try:
        file_path = Path(file_path)
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            logger.warning(f"File {file_path} too large: {file_size_mb:.2f}MB > {max_size_mb}MB")
            return None
        
        # Read file content
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
            
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None


def generate_unique_filename(
    original_filename: str, 
    user_id: int,
    prefix: str = ""
) -> str:
    """
    Generate unique filename to prevent conflicts.
    
    Args:
        original_filename: Original filename
        user_id: User ID for namespacing
        prefix: Optional prefix
        
    Returns:
        str: Unique filename
    """
    file_info = get_file_info(original_filename)
    unique_id = str(uuid.uuid4())[:8]
    
    if prefix:
        return f"{prefix}_{user_id}_{unique_id}_{file_info['stem']}{file_info['extension']}"
    else:
        return f"{user_id}_{unique_id}_{file_info['stem']}{file_info['extension']}"


def validate_file_extension(
    filename: str, 
    allowed_extensions: list
) -> bool:
    """
    Validate file extension against allowed list.
    
    Args:
        filename: Filename to check
        allowed_extensions: List of allowed extensions
        
    Returns:
        bool: True if extension is allowed
    """
    file_info = get_file_info(filename)
    extension = file_info['extension'].lstrip('.')
    
    # Normalize extensions
    allowed_normalized = [ext.lstrip('.').lower() for ext in allowed_extensions]
    
    return extension.lower() in allowed_normalized


def calculate_file_hash(
    file_path: Union[str, Path], 
    algorithm: str = 'sha256'
) -> str:
    """
    Calculate hash of file content.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (sha256, md5, sha1)
        
    Returns:
        str: File hash
    """
    file_path = Path(file_path)
    
    if algorithm == 'sha256':
        hasher = hashlib.sha256()
    elif algorithm == 'md5':
        hasher = hashlib.md5()
    elif algorithm == 'sha1':
        hasher = hashlib.sha1()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        
        return hasher.hexdigest()
        
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise


def detect_file_encoding(file_path: Union[str, Path]) -> str:
    """
    Detect file encoding.
    
    Args:
        file_path: Path to file
        
    Returns:
        str: Detected encoding
    """
    try:
        import chardet
        
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8')
            
    except ImportError:
        logger.warning("chardet not available, defaulting to utf-8")
        return 'utf-8'
    except Exception as e:
        logger.error(f"Error detecting encoding for {file_path}: {e}")
        return 'utf-8'


def get_file_mime_type(file_path: Union[str, Path]) -> str:
    """
    Get MIME type of file using python-magic.
    
    Args:
        file_path: Path to file
        
    Returns:
        str: MIME type
    """
    try:
        return magic.from_file(str(file_path), mime=True)
    except Exception as e:
        logger.warning(f"Could not detect MIME type for {file_path}: {e}")
        # Fallback to mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'


def create_temp_file(
    content: Union[str, bytes], 
    suffix: str = '.tmp',
    prefix: str = 'bioml_'
) -> Path:
    """
    Create temporary file with content.
    
    Args:
        content: File content
        suffix: File suffix
        prefix: File prefix
        
    Returns:
        Path: Path to temporary file
    """
    import tempfile
    
    # Create temporary file
    fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    temp_path = Path(temp_path)
    
    try:
        with open(fd, 'wb' if isinstance(content, bytes) else 'w') as f:
            f.write(content)
        
        return temp_path
        
    except Exception as e:
        # Clean up on error
        temp_path.unlink(missing_ok=True)
        raise


def cleanup_temp_files(temp_dir: Union[str, Path], max_age_hours: int = 24):
    """
    Clean up old temporary files.
    
    Args:
        temp_dir: Directory containing temporary files
        max_age_hours: Maximum age of files to keep
    """
    import time
    
    temp_dir = Path(temp_dir)
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    try:
        for file_path in temp_dir.glob('bioml_*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                
                if file_age > max_age_seconds:
                    file_path.unlink()
                    logger.debug(f"Cleaned up old temp file: {file_path}")
                    
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")


def read_csv_safely(
    file_path: Union[str, Path],
    max_rows: int = 100000,
    **kwargs
) -> Optional[pd.DataFrame]:
    """
    Safely read CSV file with limits.
    
    Args:
        file_path: Path to CSV file
        max_rows: Maximum number of rows to read
        **kwargs: Additional pandas read_csv arguments
        
    Returns:
        DataFrame: Loaded data or None
    """
    try:
        # Detect separator if not provided
        if 'sep' not in kwargs and 'delimiter' not in kwargs:
            with open(file_path, 'r') as f:
                first_line = f.readline()
                if '\t' in first_line:
                    kwargs['sep'] = '\t'
                else:
                    kwargs['sep'] = ','
        
        # Read with row limit
        df = pd.read_csv(
            file_path,
            nrows=max_rows,
            **kwargs
        )
        
        logger.info(f"Successfully loaded {len(df)} rows from {file_path}")
        return df
        
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        return None


def ensure_directory(directory_path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if not.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        Path: Directory path
    """
    directory_path = Path(directory_path)
    directory_path.mkdir(parents=True, exist_ok=True)
    return directory_path
