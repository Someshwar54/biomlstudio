"""
Data processing background tasks
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List

from celery import current_task
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.dataset import Dataset
from app.services.dataset_service import DatasetService
from app.utils.bioinformatics import (
    validate_fasta_format, convert_fasta_to_csv,
    calculate_sequence_composition, detect_sequence_type
)
from app.utils.file_handlers import get_file_info, safe_file_read
from app.utils.logger import get_task_logger

logger = get_task_logger(__name__)
SessionLocal = sessionmaker(bind=engine)


@celery_app.task(bind=True, name='biomlstudio.data_processing.process_biological_data_task')
def process_biological_data_task(
    self,
    dataset_id: int,
    processing_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process biological dataset (FASTA, FASTQ, etc.).
    
    Args:
        dataset_id: Dataset ID to process
        processing_config: Processing configuration
        
    Returns:
        Dict: Processing results
    """
    task_id = self.request.id
    logger.info(f"Starting biological data processing task {task_id} for dataset {dataset_id}")
    
    try:
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")
            
            # Update processing status
            dataset.processing_status = "processing"
            db.commit()
        
        # Initialize progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Analyzing file format...'}
        )
        
        file_path = Path(dataset.file_path)
        processing_steps = []
        
        # Step 1: Validate file format
        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Validating format...'}
        )
        
        if dataset.dataset_type in ['dna', 'rna', 'protein']:
            if file_path.suffix.lower() in ['.fasta', '.fa', '.fas']:
                validation_result = validate_fasta_format(str(file_path))
                processing_steps.append(f"FASTA validation: {validation_result['status']}")
                
                if not validation_result['is_valid']:
                    raise ValueError(f"Invalid FASTA format: {validation_result['errors']}")
        
        # Step 2: Extract sequences and calculate statistics
        self.update_state(
            state='PROGRESS',
            meta={'current': 40, 'total': 100, 'status': 'Analyzing sequences...'}
        )
        
        if dataset.dataset_type in ['dna', 'rna', 'protein']:
            sequences = []
            sequence_ids = []
            
            from Bio import SeqIO
            with open(file_path, 'r') as handle:
                for record in SeqIO.parse(handle, "fasta"):
                    sequences.append(str(record.seq))
                    sequence_ids.append(record.id)
                    
                    # Limit to first 10000 for large files
                    if len(sequences) >= 10000:
                        break
            
            # Calculate composition statistics
            composition_stats = calculate_sequence_composition(
                sequences, 
                dataset.dataset_type
            )
            
            processing_steps.append(f"Analyzed {len(sequences)} sequences")
        
        # Step 3: Generate k-mer features if requested
        self.update_state(
            state='PROGRESS',
            meta={'current': 60, 'total': 100, 'status': 'Generating features...'}
        )
        
        kmer_features = None
        if processing_config.get('generate_kmers', False):
            from app.utils.bioinformatics import generate_kmer_features
            
            kmer_size = processing_config.get('kmer_size', 3)
            kmer_features = generate_kmer_features(sequences, kmer_size)
            processing_steps.append(f"Generated {kmer_size}-mer features")
        
        # Step 4: Convert to structured format if requested
        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Converting format...'}
        )
        
        output_path = None
        if processing_config.get('convert_to_csv', False):
            output_path = file_path.parent / f"{file_path.stem}_processed.csv"
            
            # Create DataFrame with sequences and features
            data = {
                'sequence_id': sequence_ids[:len(sequences)],
                'sequence': sequences,
                'length': [len(seq) for seq in sequences]
            }
            
            if kmer_features:
                # Add k-mer features as columns
                for kmer, values in kmer_features.items():
                    data[f'kmer_{kmer}'] = values
            
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            processing_steps.append(f"Converted to CSV: {output_path}")
        
        # Step 5: Update dataset record with processing results
        self.update_state(
            state='PROGRESS',
            meta={'current': 95, 'total': 100, 'status': 'Saving results...'}
        )
        
        processing_results = {
            'processing_steps': processing_steps,
            'sequence_count': len(sequences) if 'sequences' in locals() else 0,
            'composition_stats': composition_stats if 'composition_stats' in locals() else {},
            'output_path': str(output_path) if output_path else None,
            'kmer_features_generated': kmer_features is not None
        }
        
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            dataset.processing_status = "ready"
            dataset.is_validated = True
            
            # Update stats with processing results
            if dataset.stats:
                dataset.stats.update(processing_results)
            else:
                dataset.stats = processing_results
                
            db.commit()
        
        # Complete task
        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Processing completed'}
        )
        
        logger.info(f"Biological data processing completed for dataset {dataset_id}")
        
        return {
            'status': 'completed',
            'dataset_id': dataset_id,
            'results': processing_results,
            'task_id': task_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Biological data processing failed for dataset {dataset_id}: {error_msg}")
        
        # Update dataset status to error
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                dataset.processing_status = "error"
                dataset.processing_error = error_msg
                db.commit()
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'dataset_id': dataset_id}
        )
        
        raise


@celery_app.task(bind=True, name='biomlstudio.data_processing.validate_dataset_task')
def validate_dataset_task(
    self,
    dataset_id: int,
    validation_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate dataset format and content.
    
    Args:
        dataset_id: Dataset ID to validate
        validation_config: Validation configuration
        
    Returns:
        Dict: Validation results
    """
    task_id = self.request.id
    logger.info(f"Starting dataset validation task {task_id} for dataset {dataset_id}")
    
    dataset_service = DatasetService()
    
    try:
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting validation...'}
        )
        
        # Perform validation
        validation_results = dataset_service.validate_dataset(
            dataset.file_path,
            dataset.dataset_type
        )
        
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Validation completed'}
        )
        
        # Update dataset validation status
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            dataset.is_validated = validation_results['is_valid']
            if not validation_results['is_valid']:
                dataset.processing_error = '; '.join(validation_results['errors'])
            db.commit()
        
        logger.info(f"Dataset validation completed for dataset {dataset_id}")
        
        return {
            'status': 'completed',
            'dataset_id': dataset_id,
            'validation_results': validation_results,
            'task_id': task_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Dataset validation failed for dataset {dataset_id}: {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'dataset_id': dataset_id}
        )
        
        raise


@celery_app.task(bind=True, name='biomlstudio.data_processing.generate_dataset_stats_task')
def generate_dataset_stats_task(
    self,
    dataset_id: int
) -> Dict[str, Any]:
    """
    Generate comprehensive statistics for dataset.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        Dict: Generated statistics
    """
    task_id = self.request.id
    logger.info(f"Starting stats generation task {task_id} for dataset {dataset_id}")
    
    dataset_service = DatasetService()
    
    try:
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")
        
        # Generate comprehensive statistics
        stats = dataset_service.analyze_dataset(
            Path(dataset.file_path),
            dataset.dataset_type
        )
        
        # Update dataset with new stats
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            dataset.stats = stats
            db.commit()
        
        logger.info(f"Stats generation completed for dataset {dataset_id}")
        
        return {
            'status': 'completed',
            'dataset_id': dataset_id,
            'stats': stats,
            'task_id': task_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Stats generation failed for dataset {dataset_id}: {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'dataset_id': dataset_id}
        )
        
        raise


@celery_app.task(bind=True, name='biomlstudio.data_processing.convert_file_format_task')
def convert_file_format_task(
    self,
    dataset_id: int,
    target_format: str,
    conversion_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convert dataset to different format.
    
    Args:
        dataset_id: Dataset ID to convert
        target_format: Target format (csv, json, etc.)
        conversion_config: Conversion configuration
        
    Returns:
        Dict: Conversion results
    """
    task_id = self.request.id
    logger.info(f"Starting format conversion task {task_id} for dataset {dataset_id}")
    
    try:
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")
        
        source_path = Path(dataset.file_path)
        target_path = source_path.parent / f"{source_path.stem}_converted.{target_format}"
        
        # Perform format conversion based on source and target formats
        if dataset.dataset_type in ['dna', 'rna', 'protein'] and target_format == 'csv':
            # Convert biological sequences to CSV
            conversion_result = convert_fasta_to_csv(
                str(source_path),
                str(target_path),
                conversion_config
            )
        else:
            raise ValueError(f"Conversion from {source_path.suffix} to {target_format} not supported")
        
        logger.info(f"Format conversion completed for dataset {dataset_id}")
        
        return {
            'status': 'completed',
            'dataset_id': dataset_id,
            'source_path': str(source_path),
            'target_path': str(target_path),
            'conversion_result': conversion_result,
            'task_id': task_id
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Format conversion failed for dataset {dataset_id}: {error_msg}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'dataset_id': dataset_id}
        )
        
        raise
