#!/usr/bin/env python3
"""
Script to fix dataset_type validation issues in the database
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import get_db
from app.models.dataset import Dataset
from sqlalchemy.orm import Session

def fix_dataset_types():
    """Fix invalid dataset_type values in the database"""
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Find datasets with invalid dataset_type
        invalid_datasets = db.query(Dataset).filter(Dataset.dataset_type == 'sequence').all()
        print(f'Found {len(invalid_datasets)} datasets with dataset_type="sequence"')
        
        # Update them to 'dna' since they're FASTA files
        for dataset in invalid_datasets:
            print(f'Updating dataset {dataset.id}: {dataset.name} from "sequence" to "dna"')
            dataset.dataset_type = 'dna'
        
        db.commit()
        print('Database updated successfully')
        db.close()
        
    except Exception as e:
        print(f'Error fixing dataset types: {e}')
        return False
    
    return True

if __name__ == "__main__":
    success = fix_dataset_types()
    if success:
        print("Dataset types fixed successfully!")
        sys.exit(0)
    else:
        print("Failed to fix dataset types!")
        sys.exit(1)