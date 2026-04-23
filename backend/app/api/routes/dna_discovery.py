"""
API routes for DNA Discovery and Advanced Bioinformatics Analysis
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from pathlib import Path
import pandas as pd
import logging

from app.api.deps import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.dataset import Dataset
from app.services.dna_discovery_service import dna_discovery_service
from app.services.dna_ml_models import (
    create_dna_model, ComprehensiveDNAAnalyzer,
    DNAFeatureExtractor, GeneClassifier, PathogenDetector,
    DrugTargetPredictor, BiomarkerDiscoverer
)
from app.utils.bioinformatics import detect_sequence_type, validate_fasta_format
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(tags=["DNA Discovery"])


@router.get("/")
async def dna_discovery_root():
    """Root endpoint for DNA Discovery service"""
    return {
        "message": "DNA Discovery Service is running",
        "version": "1.0.0",
        "endpoints": [
            "/analyze-comprehensive",
            "/discover-genes", 
            "/identify-mutations",
            "/detect-pathogens",
            "/find-drug-targets",
            "/identify-motifs",
            "/generate-biomarkers",
            "/train-ml-model",
            "/upload-fasta",
            "/ensemble-analysis"
        ]
    }

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint without authentication"""
    return {"status": "working", "message": "DNA Discovery routes are loaded"}


# Pydantic models for request/response
class DNAAnalysisRequest(BaseModel):
    sequences: List[str] = Field(..., description="List of DNA sequences to analyze")
    sequence_ids: Optional[List[str]] = Field(None, description="Optional sequence identifiers")
    analysis_config: Optional[Dict[str, Any]] = Field(None, description="Analysis configuration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sequences": [
                    "ATGCGTACGTAGCTAGCTAGCTAG",
                    "GCTAGCTAGCTAGCTAGCTAGCTA"
                ],
                "sequence_ids": ["seq1", "seq2"],
                "analysis_config": {
                    "gene_discovery": True,
                    "mutation_analysis": True,
                    "drug_targets": True,
                    "pathogen_detection": True,
                    "motif_analysis": True,
                    "biomarker_generation": True,
                    "evolutionary_analysis": True
                }
            }
        }


class GeneDiscoveryRequest(BaseModel):
    sequences: List[str]
    min_orf_length: int = Field(default=300, description="Minimum ORF length for gene prediction")


class MutationAnalysisRequest(BaseModel):
    sequences: List[str]
    reference_sequence: Optional[str] = Field(None, description="Reference sequence for comparison")


class PathogenDetectionRequest(BaseModel):
    sequences: List[str]
    detection_sensitivity: float = Field(default=0.8, description="Detection sensitivity threshold")


class DrugTargetRequest(BaseModel):
    sequences: List[str]
    target_types: List[str] = Field(default=["enzyme", "receptor", "channel"], 
                                  description="Types of drug targets to identify")


class BiomarkerRequest(BaseModel):
    sequences: List[str]
    labels: Optional[List[str]] = Field(None, description="Labels for supervised biomarker discovery")
    biomarker_types: List[str] = Field(default=["cancer", "infection", "genetic"], 
                                     description="Types of biomarkers to discover")


class MLModelTrainingRequest(BaseModel):
    model_type: str = Field(..., description="Type of model to train")
    sequences: List[str]
    labels: List[str]
    training_config: Optional[Dict[str, Any]] = Field(None, description="Training configuration")


class SequenceUploadResponse(BaseModel):
    message: str
    sequence_count: int
    sequences_processed: List[Dict[str, Any]]
    analysis_id: str


class DNAAnalysisResponse(BaseModel):
    analysis_id: str
    summary: Dict[str, Any]
    gene_discovery: Optional[Dict[str, Any]] = None
    mutation_analysis: Optional[Dict[str, Any]] = None
    drug_targets: Optional[Dict[str, Any]] = None
    pathogen_detection: Optional[Dict[str, Any]] = None
    motif_analysis: Optional[Dict[str, Any]] = None
    biomarker_generation: Optional[Dict[str, Any]] = None
    evolutionary_analysis: Optional[Dict[str, Any]] = None


@router.post("/analyze-comprehensive", response_model=DNAAnalysisResponse)
async def analyze_dna_comprehensive(
    request: DNAAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Perform comprehensive DNA sequence analysis including:
    - Gene discovery and ORF analysis
    - Disease mutation identification
    - Drug target prediction
    - Pathogen detection
    - Functional motif analysis
    - Biomarker generation
    - Evolutionary analysis
    """
    try:
        logger.info(f"Starting comprehensive DNA analysis for user {current_user.id}")
        
        # Validate sequences
        if not request.sequences:
            raise HTTPException(status_code=400, detail="No sequences provided")
        
        for i, seq in enumerate(request.sequences):
            seq_type = detect_sequence_type(seq)
            if seq_type not in ['dna', 'rna']:
                logger.warning(f"Sequence {i} detected as {seq_type}, converting for DNA analysis")
        
        # Perform comprehensive analysis
        results = dna_discovery_service.comprehensive_sequence_analysis(
            sequences=request.sequences,
            sequence_ids=request.sequence_ids,
            analysis_config=request.analysis_config or {}
        )
        
        # Log results summary for debugging
        logger.info(f"🔍 Results keys: {list(results.keys())}")
        if 'gene_discovery' in results:
            gene_count = len(results['gene_discovery'].get('potential_genes', []))
            logger.info(f"📊 Total genes discovered: {gene_count}")
        if 'pathogen_detection' in results:
            resistance_count = len(results['pathogen_detection'].get('resistance_genes', []))
            logger.info(f"🦠 Total resistance genes: {resistance_count}")
        
        # Format response
        response_data = DNAAnalysisResponse(
            analysis_id=f"dna_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
            summary=results.get('summary', {}),
            gene_discovery=results.get('gene_discovery'),
            mutation_analysis=results.get('mutation_analysis'),
            drug_targets=results.get('drug_targets'),
            pathogen_detection=results.get('pathogen_detection'),
            motif_analysis=results.get('motif_analysis'),
            biomarker_generation=results.get('biomarker_generation'),
            evolutionary_analysis=results.get('evolutionary_analysis')
        )
        
        logger.info(f"DNA analysis completed for user {current_user.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in comprehensive DNA analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/discover-genes")
async def discover_genes(
    request: GeneDiscoveryRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Discover new genes by identifying Open Reading Frames (ORFs)
    and predicting their coding potential
    """
    try:
        logger.info(f"Starting gene discovery for {len(request.sequences)} sequences")
        
        results = dna_discovery_service.discover_new_genes(
            sequences=request.sequences,
            min_length=request.min_orf_length
        )
        
        return {
            "analysis_type": "gene_discovery",
            "input_sequences": len(request.sequences),
            "results": results,
            "biological_insights": {
                "potential_new_genes": len(results.get('potential_genes', [])),
                "coding_potential_distribution": [
                    gene.get('coding_potential', 0) 
                    for gene in results.get('potential_genes', [])
                ],
                "functional_predictions": [
                    gene.get('gene_prediction', {}) 
                    for gene in results.get('potential_genes', [])
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error in gene discovery: {e}")
        raise HTTPException(status_code=500, detail=f"Gene discovery failed: {str(e)}")


@router.post("/identify-mutations")
async def identify_mutations(
    request: MutationAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Identify disease-causing mutations including SNVs, indels, and oncogenic patterns
    """
    try:
        logger.info(f"Starting mutation analysis for {len(request.sequences)} sequences")
        
        results = dna_discovery_service.identify_disease_mutations(
            sequences=request.sequences,
            reference_seq=request.reference_sequence
        )
        
        return {
            "analysis_type": "mutation_analysis",
            "input_sequences": len(request.sequences),
            "results": results,
            "clinical_significance": {
                "total_variants": results['statistics']['total_snvs'],
                "indel_count": results['statistics']['total_indels'],
                "oncogenic_sites": results['statistics']['oncogenic_sites'],
                "mutation_burden": results['statistics']['mutation_rate'],
                "pathogenic_potential": _calculate_pathogenic_potential(results)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in mutation analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Mutation analysis failed: {str(e)}")


@router.post("/detect-pathogens")
async def detect_pathogens(
    request: PathogenDetectionRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Detect pathogens and classify microorganisms from DNA sequences
    """
    try:
        logger.info(f"Starting pathogen detection for {len(request.sequences)} sequences")
        
        results = dna_discovery_service.detect_pathogens(request.sequences)
        
        return {
            "analysis_type": "pathogen_detection",
            "input_sequences": len(request.sequences),
            "results": results,
            "infectious_disease_insights": {
                "bacterial_pathogens": len(results.get('bacterial_signatures', [])),
                "viral_pathogens": len(results.get('viral_signatures', [])),
                "antibiotic_resistance": len(results.get('resistance_genes', [])),
                "virulence_factors": len(results.get('pathogenicity_factors', [])),
                "outbreak_potential": _assess_outbreak_potential(results)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in pathogen detection: {e}")
        raise HTTPException(status_code=500, detail=f"Pathogen detection failed: {str(e)}")


@router.post("/find-drug-targets")
async def find_drug_targets(
    request: DrugTargetRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Identify potential drug targets and protein binding sites
    """
    try:
        logger.info(f"Starting drug target identification for {len(request.sequences)} sequences")
        
        results = dna_discovery_service.find_drug_targets(request.sequences)
        
        return {
            "analysis_type": "drug_target_identification",
            "input_sequences": len(request.sequences),
            "results": results,
            "drug_development_insights": {
                "druggable_targets": len(results.get('druggable_proteins', [])),
                "enzyme_active_sites": len(results.get('enzyme_sites', [])),
                "binding_pockets": len(results.get('binding_pockets', [])),
                "therapeutic_potential": _assess_therapeutic_potential(results),
                "development_priority": _prioritize_drug_targets(results)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in drug target identification: {e}")
        raise HTTPException(status_code=500, detail=f"Drug target identification failed: {str(e)}")


@router.post("/identify-motifs")
async def identify_functional_motifs(
    sequences: List[str],
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Detect functional DNA motifs including promoters, enhancers, and binding sites
    """
    try:
        logger.info(f"Starting motif analysis for {len(sequences)} sequences")
        
        results = dna_discovery_service.identify_functional_motifs(sequences)
        
        return {
            "analysis_type": "functional_motif_analysis",
            "input_sequences": len(sequences),
            "results": results,
            "regulatory_insights": {
                "promoter_regions": len(results.get('promoters', [])),
                "enhancer_elements": len(results.get('enhancers', [])),
                "tf_binding_sites": len(results.get('tf_binding_sites', [])),
                "cpg_islands": len(results.get('cpg_islands', [])),
                "splice_sites": len(results.get('splice_sites', [])),
                "gene_regulation_potential": _assess_regulatory_potential(results)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in motif analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Motif analysis failed: {str(e)}")


@router.post("/generate-biomarkers")
async def generate_biomarkers(
    request: BiomarkerRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Generate sequence-based biomarkers for diagnostics
    """
    try:
        logger.info(f"Starting biomarker generation for {len(request.sequences)} sequences")
        
        results = dna_discovery_service.generate_biomarkers(
            sequences=request.sequences,
            labels=request.labels
        )
        
        return {
            "analysis_type": "biomarker_generation",
            "input_sequences": len(request.sequences),
            "results": results,
            "diagnostic_potential": {
                "total_biomarkers": _count_total_biomarkers(results),
                "discriminative_power": _assess_discriminative_power(results),
                "clinical_applicability": _assess_clinical_applicability(results),
                "validation_recommendations": _generate_validation_recommendations(results)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in biomarker generation: {e}")
        raise HTTPException(status_code=500, detail=f"Biomarker generation failed: {str(e)}")


@router.post("/train-ml-model")
async def train_dna_ml_model(
    request: MLModelTrainingRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Train specialized machine learning models for DNA sequence analysis
    """
    try:
        logger.info(f"Training {request.model_type} model with {len(request.sequences)} sequences")
        
        # Create and train model
        model = create_dna_model(request.model_type, **(request.training_config or {}))
        
        if request.model_type == 'biomarker_discoverer':
            # Special handling for biomarker discoverer
            results = model.discover_biomarkers(request.sequences, request.labels)
        else:
            # Standard classifier training
            model.fit(request.sequences, request.labels)
            
            # Evaluate model
            predictions = model.predict(request.sequences)
            probabilities = model.predict_proba(request.sequences)
            
            results = {
                "model_type": request.model_type,
                "training_samples": len(request.sequences),
                "predictions": predictions.tolist(),
                "prediction_probabilities": probabilities.tolist()
            }
            
            # Add feature importance if available
            if hasattr(model, 'get_feature_importance'):
                results["feature_importance"] = model.get_feature_importance()
        
        return {
            "status": "success",
            "model_type": request.model_type,
            "training_results": results,
            "model_performance": _evaluate_model_performance(results)
        }
        
    except Exception as e:
        logger.error(f"Error in model training: {e}")
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")


@router.post("/upload-fasta")
async def upload_fasta_for_analysis(
    file: UploadFile = File(...),
    analysis_type: str = "comprehensive",
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Upload FASTA file and perform DNA discovery analysis
    """
    try:
        logger.info(f"Processing uploaded FASTA file: {file.filename}")
        
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Validate FASTA format
        validation = validate_fasta_format(tmp_file_path)
        if not validation['is_valid']:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid FASTA format: {validation['errors']}"
            )
        
        # Parse sequences from FASTA
        from Bio import SeqIO
        sequences = []
        sequence_ids = []
        
        with open(tmp_file_path, 'r') as handle:
            for record in SeqIO.parse(handle, "fasta"):
                sequences.append(str(record.seq))
                sequence_ids.append(record.id)
        
        # Clean up temporary file
        Path(tmp_file_path).unlink()
        
        if not sequences:
            raise HTTPException(status_code=400, detail="No valid sequences found in FASTA file")
        
        # Perform analysis based on type
        if analysis_type == "comprehensive":
            results = dna_discovery_service.comprehensive_sequence_analysis(
                sequences=sequences,
                sequence_ids=sequence_ids
            )
        elif analysis_type == "genes":
            results = dna_discovery_service.discover_new_genes(sequences)
        elif analysis_type == "pathogens":
            results = dna_discovery_service.detect_pathogens(sequences)
        elif analysis_type == "drug_targets":
            results = dna_discovery_service.find_drug_targets(sequences)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported analysis type: {analysis_type}")
        
        return SequenceUploadResponse(
            message=f"Successfully analyzed {len(sequences)} sequences from {file.filename}",
            sequence_count=len(sequences),
            sequences_processed=[
                {"id": seq_id, "length": len(seq), "type": detect_sequence_type(seq)}
                for seq_id, seq in zip(sequence_ids, sequences)
            ],
            analysis_id=f"upload_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing FASTA upload: {e}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


@router.post("/ensemble-analysis")
async def ensemble_analysis(
    sequences: List[str],
    training_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Run ensemble analysis using multiple specialized models
    """
    try:
        logger.info(f"Starting ensemble analysis for {len(sequences)} sequences")
        
        # Initialize ensemble analyzer
        analyzer = ComprehensiveDNAAnalyzer()
        
        # Train models if training data provided
        if training_data:
            analyzer.fit(
                sequences=training_data.get('sequences', []),
                gene_labels=training_data.get('gene_labels'),
                pathogen_labels=training_data.get('pathogen_labels'),
                drug_target_labels=training_data.get('drug_target_labels'),
                biomarker_labels=training_data.get('biomarker_labels')
            )
        
        # Analyze sequences
        results = analyzer.analyze_sequences(sequences)
        
        return {
            "analysis_type": "ensemble_ml_analysis",
            "input_sequences": len(sequences),
            "model_results": results,
            "ensemble_insights": {
                "consensus_predictions": _generate_consensus_predictions(results),
                "confidence_scores": _calculate_confidence_scores(results),
                "biological_significance": _assess_biological_significance(results)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in ensemble analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Ensemble analysis failed: {str(e)}")


# Helper functions for biological insights
def _calculate_pathogenic_potential(mutation_results: Dict[str, Any]) -> float:
    """Calculate pathogenic potential score"""
    oncogenic_count = len(mutation_results.get('oncogenic_patterns', []))
    total_mutations = mutation_results['statistics']['total_snvs']
    
    if total_mutations == 0:
        return 0.0
    
    pathogenic_score = (oncogenic_count / total_mutations) * 100
    return min(pathogenic_score, 100.0)


def _assess_outbreak_potential(pathogen_results: Dict[str, Any]) -> str:
    """Assess outbreak potential based on pathogen detection"""
    virulence_count = len(pathogen_results.get('pathogenicity_factors', []))
    resistance_count = len(pathogen_results.get('resistance_genes', []))
    
    if virulence_count > 5 and resistance_count > 3:
        return "HIGH"
    elif virulence_count > 2 or resistance_count > 1:
        return "MODERATE"
    else:
        return "LOW"


def _assess_therapeutic_potential(drug_target_results: Dict[str, Any]) -> str:
    """Assess therapeutic development potential"""
    druggable_count = len(drug_target_results.get('druggable_proteins', []))
    enzyme_sites = len(drug_target_results.get('enzyme_sites', []))
    
    if druggable_count > 3 and enzyme_sites > 2:
        return "HIGH"
    elif druggable_count > 1 or enzyme_sites > 0:
        return "MODERATE"
    else:
        return "LOW"


def _prioritize_drug_targets(drug_target_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Prioritize drug targets for development"""
    druggable_proteins = drug_target_results.get('druggable_proteins', [])
    
    # Sort by druggability score
    prioritized = sorted(
        druggable_proteins, 
        key=lambda x: x.get('druggability_score', 0), 
        reverse=True
    )
    
    return prioritized[:5]  # Top 5 targets


def _assess_regulatory_potential(motif_results: Dict[str, Any]) -> float:
    """Assess gene regulation potential"""
    promoter_count = len(motif_results.get('promoters', []))
    enhancer_count = len(motif_results.get('enhancers', []))
    tf_sites = len(motif_results.get('tf_binding_sites', []))
    
    # Simple scoring based on regulatory element density
    regulatory_score = (promoter_count * 3 + enhancer_count * 2 + tf_sites) / 10
    return min(regulatory_score, 10.0)


def _count_total_biomarkers(biomarker_results: Dict[str, Any]) -> int:
    """Count total biomarkers identified"""
    total = 0
    for key, value in biomarker_results.items():
        if isinstance(value, list):
            total += len(value)
    return total


def _assess_discriminative_power(biomarker_results: Dict[str, Any]) -> str:
    """Assess discriminative power of biomarkers"""
    # Simple assessment based on number of discriminative features
    discriminative_kmers = biomarker_results.get('discriminative_kmers', [])
    
    if len(discriminative_kmers) > 20:
        return "HIGH"
    elif len(discriminative_kmers) > 10:
        return "MODERATE"
    else:
        return "LOW"


def _assess_clinical_applicability(biomarker_results: Dict[str, Any]) -> str:
    """Assess clinical applicability of discovered biomarkers"""
    # Based on conservation and frequency of biomarkers
    conserved_motifs = biomarker_results.get('conserved_motifs', [])
    high_freq_motifs = [m for m in conserved_motifs if m.get('frequency', 0) > 0.5]
    
    if len(high_freq_motifs) > 5:
        return "HIGH"
    elif len(high_freq_motifs) > 2:
        return "MODERATE"
    else:
        return "LOW"


def _generate_validation_recommendations(biomarker_results: Dict[str, Any]) -> List[str]:
    """Generate recommendations for biomarker validation"""
    recommendations = []
    
    discriminative_kmers = biomarker_results.get('discriminative_kmers', [])
    if len(discriminative_kmers) > 10:
        recommendations.append("Perform independent validation on larger cohort")
        recommendations.append("Conduct cross-population validation studies")
    
    conserved_motifs = biomarker_results.get('conserved_motifs', [])
    if len(conserved_motifs) > 5:
        recommendations.append("Validate motif conservation across species")
        recommendations.append("Test functional significance of conserved motifs")
    
    recommendations.append("Implement qPCR validation for top biomarkers")
    recommendations.append("Consider longitudinal studies for temporal validation")
    
    return recommendations


def _evaluate_model_performance(results: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate ML model performance"""
    performance = {
        "status": "evaluated",
        "metrics_available": bool(results.get('model_performance')),
        "feature_importance_available": bool(results.get('feature_importance')),
        "recommendation": "Model trained successfully"
    }
    
    if results.get('model_performance'):
        model_perf = results['model_performance']
        val_accuracy = model_perf.get('validation_accuracy', 0)
        
        if val_accuracy > 0.9:
            performance["quality"] = "EXCELLENT"
        elif val_accuracy > 0.8:
            performance["quality"] = "GOOD"
        elif val_accuracy > 0.7:
            performance["quality"] = "FAIR"
        else:
            performance["quality"] = "POOR"
            performance["recommendation"] = "Consider model optimization or more training data"
    
    return performance


def _generate_consensus_predictions(ensemble_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate consensus predictions from ensemble models"""
    consensus = {}
    
    # Simple majority voting for binary predictions
    for model_name, results in ensemble_results.items():
        if 'predictions' in results:
            predictions = results['predictions']
            if predictions:
                consensus[model_name] = {
                    "most_common_prediction": max(set(predictions), key=predictions.count),
                    "prediction_distribution": dict(Counter(predictions))
                }
    
    return consensus


def _calculate_confidence_scores(ensemble_results: Dict[str, Any]) -> Dict[str, float]:
    """Calculate confidence scores for ensemble predictions"""
    confidence_scores = {}
    
    for model_name, results in ensemble_results.items():
        if 'probabilities' in results:
            probabilities = results['probabilities']
            if probabilities and len(probabilities[0]) > 0:
                # Average maximum probability as confidence
                max_probs = [max(prob_list) for prob_list in probabilities]
                avg_confidence = sum(max_probs) / len(max_probs)
                confidence_scores[model_name] = avg_confidence
    
    return confidence_scores


def _assess_biological_significance(ensemble_results: Dict[str, Any]) -> Dict[str, str]:
    """Assess biological significance of ensemble predictions"""
    significance = {}
    
    for model_name, results in ensemble_results.items():
        if 'error' in results:
            significance[model_name] = "ANALYSIS_FAILED"
        elif 'predictions' in results:
            predictions = results['predictions']
            unique_predictions = len(set(predictions)) if predictions else 0
            
            if unique_predictions > 1:
                significance[model_name] = "BIOLOGICALLY_DIVERSE"
            elif unique_predictions == 1:
                significance[model_name] = "HOMOGENEOUS_PATTERN"
            else:
                significance[model_name] = "NO_CLEAR_PATTERN"
    
    return significance