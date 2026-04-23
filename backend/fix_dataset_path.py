#!/usr/bin/env python3
"""
Fix dataset file paths in database
"""
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.models.dataset import Dataset

def fix_dataset_paths():
    """Fix dataset file paths to point to existing files"""
    db = SessionLocal()
    try:
        # Get datasets with missing files
        datasets = db.query(Dataset).all()
        
        for dataset in datasets:
            print(f"Dataset {dataset.id}: {dataset.name}")
            print(f"  Current path: {dataset.file_path}")
            print(f"  Dataset type: {dataset.dataset_type}")
            
            # Check if file exists
            file_path = Path(dataset.file_path)
            if not file_path.is_absolute():
                # Make absolute path
                backend_dir = Path(__file__).parent
                full_path = backend_dir / file_path
            else:
                full_path = file_path
                
            if not full_path.exists():
                print(f"  ❌ File does not exist: {full_path}")
                
                # For dataset ID 123, update to existing file
                if dataset.id == 123:
                    new_path = "uploads/2/2_0cad4a6b_seq_001_affected.fasta"
                    print(f"  🔧 Updating to: {new_path}")
                    dataset.file_path = new_path
                    db.commit()
                    print(f"  ✅ Updated successfully")
            else:
                print(f"  ✅ File exists: {full_path}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_dataset_paths()