"""
Dataset model for managing uploaded biological datasets
"""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Any

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, 
    String, Text, JSON, BigInteger
)
from sqlalchemy.orm import relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .job import Job


class Dataset(Base):
    """Dataset model for biological data files"""
    
    __tablename__ = "datasets"
    
    # Basic dataset information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    dataset_type = Column(String(50), nullable=False, index=True)  # dna, protein, rna, general
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes
    file_extension = Column(String(10), nullable=False)
    file_hash = Column(String(64))  # SHA-256 hash for integrity
    
    # Dataset metadata
    stats = Column(JSON)  # Dataset statistics (rows, columns, sequence counts, etc.)
    schema_info = Column(JSON)  # Column types, sequence formats, etc.
    sample_data = Column(JSON)  # Preview data for quick display
    
    # Access control
    is_public = Column(Boolean, default=False, nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    
    # Processing status
    processing_status = Column(String(20), default="uploaded")  # uploaded, processing, ready, error
    processing_error = Column(Text)
    
    # Usage tracking
    download_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="datasets")
    
    jobs = relationship(
        "Job", 
        back_populates="dataset",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name='{self.name}', type='{self.dataset_type}')>"
    
    @property
    def size_human_readable(self) -> str:
        """Human readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    @property
    def is_biological_data(self) -> bool:
        """Check if dataset contains biological sequences"""
        return self.dataset_type in ['dna', 'rna', 'protein']
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.stats:
            return {}
        
        summary = {
            "total_records": self.stats.get("total_rows", 0),
            "file_size": self.size_human_readable,
            "dataset_type": self.dataset_type,
            "columns": self.stats.get("columns", []),
        }
        
        # Add biological-specific stats
        if self.is_biological_data:
            summary.update({
                "sequence_count": self.stats.get("sequence_count", 0),
                "avg_sequence_length": self.stats.get("avg_sequence_length", 0),
                "min_sequence_length": self.stats.get("min_sequence_length", 0),
                "max_sequence_length": self.stats.get("max_sequence_length", 0),
            })
        
        return summary
    
    def increment_download_count(self) -> None:
        """Increment download counter"""
        self.download_count += 1
        self.last_accessed = datetime.utcnow()
    
    def mark_as_accessed(self) -> None:
        """Update last accessed timestamp"""
        self.last_accessed = datetime.utcnow()
