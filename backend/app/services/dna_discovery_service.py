"""
DNA Discovery Service - Advanced bioinformatics analysis for biological insights
Extracts meaningful patterns from DNA sequences for drug discovery, pathogen detection,
disease prediction, and genetic classification.
"""

import logging
import re
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter, defaultdict
from pathlib import Path
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction, molecular_weight
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from Bio.Seq import Seq
from Bio.SeqUtils.CodonUsage import CodonAdaptationIndex
import joblib

logger = logging.getLogger(__name__)


class DNADiscoveryService:
    """Advanced DNA sequence analysis for biological discoveries"""
    
    def __init__(self):
        self.genetic_code = {
            'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
            'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
            'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
            'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
            'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
            'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
            'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
            'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
            'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
            'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
            'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
            'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
            'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
            'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
            'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
            'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G'
        }
        
    def discover_new_genes(self, sequences: List[str], min_length: int = 300) -> Dict[str, Any]:
        """
        Discover potential new genes by identifying Open Reading Frames (ORFs)
        and analyzing their coding potential
        """
        # Adaptive minimum length based on dataset size
        total_bp = sum(len(seq) for seq in sequences)
        avg_seq_length = total_bp / len(sequences) if sequences else 0
        
        # Use smaller minimum length for small datasets
        adaptive_min_length = min_length
        if total_bp < 50000:  # Small dataset
            adaptive_min_length = max(60, int(avg_seq_length * 0.3))  # At least 60bp or 30% of avg sequence
            logger.info(f"📊 Small dataset detected. Using adaptive min_length: {adaptive_min_length} bp")
        
        results = {
            'potential_genes': [],
            'statistics': {
                'total_orfs_found': 0,
                'protein_coding_orfs': 0,
                'long_orfs': 0,
                'average_orf_length': 0,
                'adaptive_min_length': adaptive_min_length
            }
        }
        
        all_orfs = []
        
        for seq_idx, sequence in enumerate(sequences):
            sequence = sequence.upper().replace('U', 'T')
            
            # Find ORFs in all 6 reading frames
            for frame in range(3):
                # Forward strand
                orfs = self._find_orfs(sequence[frame:], frame + 1, seq_idx)
                all_orfs.extend(orfs)
                
                # Reverse strand
                rev_seq = str(Seq(sequence).reverse_complement())
                orfs = self._find_orfs(rev_seq[frame:], -(frame + 1), seq_idx)
                all_orfs.extend(orfs)
        
        # Filter and analyze ORFs with adaptive threshold
        for orf in all_orfs:
            if orf['length'] >= adaptive_min_length:
                orf['coding_potential'] = self._calculate_coding_potential(orf['sequence'])
                orf['gene_prediction'] = self._predict_gene_function(orf['protein_seq'])
                results['potential_genes'].append(orf)
        
        # Calculate statistics with adaptive thresholds
        results['statistics']['total_orfs_found'] = len(all_orfs)
        results['statistics']['protein_coding_orfs'] = len([o for o in all_orfs if o['length'] >= adaptive_min_length])
        results['statistics']['long_orfs'] = len([o for o in all_orfs if o['length'] >= max(adaptive_min_length * 2, 200)])
        if all_orfs:
            results['statistics']['average_orf_length'] = np.mean([o['length'] for o in all_orfs])
        
        return results
    
    def identify_disease_mutations(self, sequences: List[str], reference_seq: str = None) -> Dict[str, Any]:
        """
        Identify potential disease-causing mutations including SNVs and indels
        """
        mutations = {
            'snvs': [],
            'insertions': [],
            'deletions': [],
            'oncogenic_patterns': [],
            'statistics': {}
        }
        
        for seq_idx, sequence in enumerate(sequences):
            if reference_seq:
                # Compare with reference to find mutations
                seq_mutations = self._identify_mutations_vs_reference(sequence, reference_seq, seq_idx)
                mutations['snvs'].extend(seq_mutations['snvs'])
                mutations['insertions'].extend(seq_mutations['insertions'])
                mutations['deletions'].extend(seq_mutations['deletions'])
            
            # Look for known oncogenic patterns
            oncogenic = self._detect_oncogenic_patterns(sequence, seq_idx)
            mutations['oncogenic_patterns'].extend(oncogenic)
        
        # Calculate mutation statistics
        mutations['statistics'] = {
            'total_snvs': len(mutations['snvs']),
            'total_indels': len(mutations['insertions']) + len(mutations['deletions']),
            'oncogenic_sites': len(mutations['oncogenic_patterns']),
            'mutation_rate': len(mutations['snvs']) / sum(len(s) for s in sequences) if sequences else 0
        }
        
        return mutations
    
    def find_drug_targets(self, sequences: List[str]) -> Dict[str, Any]:
        """
        Identify potential drug targets and protein binding sites
        """
        targets = {
            'enzyme_sites': [],
            'binding_pockets': [],
            'conserved_domains': [],
            'druggable_proteins': []
        }
        
        for seq_idx, sequence in enumerate(sequences):
            # Translate to protein sequences for drug target analysis
            proteins = self._translate_all_frames(sequence)
            
            for frame, protein in proteins.items():
                # Adaptive minimum protein length for small datasets
                min_length = 20 if len(sequence) < 500 else 50
                
                if len(protein) > min_length:
                    # Analyze for druggable features
                    drug_analysis = self._analyze_druggability(protein, seq_idx, frame, len(sequence) < 500)
                    
                    if drug_analysis['enzyme_sites']:
                        targets['enzyme_sites'].extend(drug_analysis['enzyme_sites'])
                    if drug_analysis['binding_pockets']:
                        targets['binding_pockets'].extend(drug_analysis['binding_pockets'])
                    if drug_analysis['conserved_domains']:
                        targets['conserved_domains'].extend(drug_analysis['conserved_domains'])
                    
                    # Lower threshold for small datasets
                    threshold = 0.4 if len(sequence) < 500 else 0.7
                    if drug_analysis['druggability_score'] > threshold:
                        targets['druggable_proteins'].append({
                            'sequence_id': seq_idx,
                            'frame': frame,
                            'protein': protein[:50] + '...' if len(protein) > 50 else protein,  # Truncate for display
                            'druggability_score': drug_analysis['druggability_score'],
                            'length': len(protein)
                        })
        
        return targets
    
    def detect_pathogens(self, sequences: List[str]) -> Dict[str, Any]:
        """
        Detect potential pathogens and classify microorganisms
        """
        pathogen_results = {
            'bacterial_signatures': [],
            'viral_signatures': [],
            'resistance_genes': [],
            'pathogenicity_factors': []
        }
        
        for seq_idx, sequence in enumerate(sequences):
            # Look for bacterial signatures
            bacterial = self._detect_bacterial_signatures(sequence, seq_idx)
            pathogen_results['bacterial_signatures'].extend(bacterial)
            
            # Look for viral signatures
            viral = self._detect_viral_signatures(sequence, seq_idx)
            pathogen_results['viral_signatures'].extend(viral)
            
            # Detect antibiotic resistance genes
            resistance = self._detect_resistance_genes(sequence, seq_idx)
            pathogen_results['resistance_genes'].extend(resistance)
            
            # Identify pathogenicity factors
            pathogenicity = self._detect_pathogenicity_factors(sequence, seq_idx)
            pathogen_results['pathogenicity_factors'].extend(pathogenicity)
        
        return pathogen_results
    
    def identify_functional_motifs(self, sequences: List[str]) -> Dict[str, Any]:
        """
        Detect functional DNA motifs including promoters, enhancers, and binding sites
        """
        motifs = {
            'promoters': [],
            'enhancers': [],
            'tf_binding_sites': [],
            'cpg_islands': [],
            'splice_sites': []
        }
        
        for seq_idx, sequence in enumerate(sequences):
            sequence = sequence.upper()
            
            # Detect promoter regions
            promoters = self._detect_promoters(sequence, seq_idx)
            motifs['promoters'].extend(promoters)
            
            # Detect enhancer elements
            enhancers = self._detect_enhancers(sequence, seq_idx)
            motifs['enhancers'].extend(enhancers)
            
            # Transcription factor binding sites
            tf_sites = self._detect_tf_binding_sites(sequence, seq_idx)
            motifs['tf_binding_sites'].extend(tf_sites)
            
            # CpG islands
            cpg_islands = self._detect_cpg_islands(sequence, seq_idx)
            motifs['cpg_islands'].extend(cpg_islands)
            
            # Splice sites
            splice_sites = self._detect_splice_sites(sequence, seq_idx)
            motifs['splice_sites'].extend(splice_sites)
        
        return motifs
    
    def generate_biomarkers(self, sequences: List[str], labels: List[str] = None) -> Dict[str, Any]:
        """
        Generate sequence-based biomarkers for diagnostics
        """
        biomarkers = {
            'sequence_signatures': [],
            'diagnostic_kmers': [],
            'gc_patterns': [],
            'length_distributions': []
        }
        
        if labels:
            # Supervised biomarker discovery
            biomarkers.update(self._supervised_biomarker_discovery(sequences, labels))
        else:
            # Unsupervised pattern discovery
            biomarkers.update(self._unsupervised_biomarker_discovery(sequences))
        
        return biomarkers
    
    def extract_evolutionary_features(self, sequences: List[str]) -> Dict[str, Any]:
        """
        Extract evolutionary and phylogenetic features
        """
        features = {
            'codon_usage': [],
            'substitution_patterns': [],
            'selection_pressure': [],
            'phylogenetic_signals': []
        }
        
        for seq_idx, sequence in enumerate(sequences):
            # Analyze codon usage bias
            codon_analysis = self._analyze_codon_usage(sequence, seq_idx)
            features['codon_usage'].append(codon_analysis)
            
            # Detect substitution patterns
            substitutions = self._analyze_substitution_patterns(sequence, seq_idx)
            features['substitution_patterns'].append(substitutions)
            
            # Calculate selection pressure indicators
            selection = self._calculate_selection_pressure(sequence, seq_idx)
            features['selection_pressure'].append(selection)
        
        return features
    
    def comprehensive_sequence_analysis(self, sequences: List[str], 
                                     sequence_ids: List[str] = None,
                                     analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform comprehensive analysis combining all discovery methods
        Optimized for performance with large datasets
        """
        if not analysis_config:
            analysis_config = {
                'gene_discovery': True,
                'mutation_analysis': True,
                'drug_targets': True,
                'pathogen_detection': True,
                'motif_analysis': True,
                'biomarker_generation': True,
                'evolutionary_analysis': True
            }
        
        # Batch processing configuration for massive datasets
        BATCH_SIZE_SEQUENCES = 100  # Process in batches of 100 sequences
        BATCH_SIZE_BP = 500000      # Process in batches of 500k bp
        MAX_TOTAL_SEQUENCES = 1000  # Maximum sequences per analysis (can be increased)
        MAX_TOTAL_BP = 10000000     # Maximum 10M bp per analysis (can be increased)
        
        original_count = len(sequences)
        total_bp = sum(len(seq) for seq in sequences)
        
        # Check if we need batch processing
        use_batch_processing = (len(sequences) > BATCH_SIZE_SEQUENCES or 
                               total_bp > BATCH_SIZE_BP or
                               analysis_config.get('force_batch_processing', False))
        
        if use_batch_processing:
            logger.info(f"🔄 Large dataset detected ({len(sequences)} sequences, {total_bp:,} bp). Using batch processing.")
            return self._batch_comprehensive_analysis(
                sequences, sequence_ids, analysis_config, 
                BATCH_SIZE_SEQUENCES, BATCH_SIZE_BP
            )
        
        # For smaller datasets, use original logic with higher limits
        if len(sequences) > MAX_TOTAL_SEQUENCES:
            logger.warning(f"Dataset too large ({len(sequences)} sequences). Processing first {MAX_TOTAL_SEQUENCES} sequences.")
            sequences = sequences[:MAX_TOTAL_SEQUENCES]
            if sequence_ids:
                sequence_ids = sequence_ids[:MAX_TOTAL_SEQUENCES]
        
        if total_bp > MAX_TOTAL_BP:
            logger.warning(f"Dataset too large ({total_bp:,} bp). Truncating sequences to fit {MAX_TOTAL_BP:,} bp limit.")
            truncated_sequences = []
            current_bp = 0
            for seq in sequences:
                if current_bp + len(seq) <= MAX_TOTAL_BP:
                    truncated_sequences.append(seq)
                    current_bp += len(seq)
                else:
                    remaining_bp = MAX_TOTAL_BP - current_bp
                    if remaining_bp > 100:  # Only add if at least 100bp remaining
                        truncated_sequences.append(seq[:remaining_bp])
                    break
            sequences = truncated_sequences
        
        results = {
            'summary': {
                'total_sequences': len(sequences),
                'original_sequence_count': original_count,
                'total_base_pairs': sum(len(seq) for seq in sequences),
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'sequence_ids': sequence_ids or [f'seq_{i}' for i in range(len(sequences))],
                'performance_note': 'Dataset was limited for optimal performance' if (len(sequences) < original_count or total_bp > MAX_TOTAL_BP) else 'Full dataset processed'
            }
        }
        
        try:
            # Gene Discovery - Fast ORF detection
            if analysis_config.get('gene_discovery', True):
                logger.info("Performing gene discovery analysis...")
                results['gene_discovery'] = self.discover_new_genes(sequences)
            
            # Mutation Analysis - Pattern matching
            if analysis_config.get('mutation_analysis', True):
                logger.info("Analyzing mutations...")
                results['mutation_analysis'] = self.identify_disease_mutations(sequences)
            
            # Drug Target Identification - Protein analysis (most intensive)
            if analysis_config.get('drug_targets', True):
                logger.info("Identifying drug targets...")
                # Limit to first 20 sequences for drug target analysis (most compute-intensive)
                drug_sequences = sequences[:20] if len(sequences) > 20 else sequences
                results['drug_targets'] = self.find_drug_targets(drug_sequences)
            
            # Pathogen Detection - Signature matching
            if analysis_config.get('pathogen_detection', True):
                logger.info("Detecting pathogens...")
                results['pathogen_detection'] = self.detect_pathogens(sequences)
            
            # Motif Analysis - Fast pattern detection
            if analysis_config.get('motif_analysis', True):
                logger.info("Analyzing functional motifs...")
                results['motif_analysis'] = self.identify_functional_motifs(sequences)
            
            # Biomarker Generation - K-mer analysis
            if analysis_config.get('biomarker_generation', True):
                logger.info("Generating biomarkers...")
                results['biomarker_generation'] = self.generate_biomarkers(sequences)
            
            # Evolutionary Analysis - Statistical analysis
            if analysis_config.get('evolutionary_analysis', True):
                logger.info("Performing evolutionary analysis...")
                results['evolutionary_analysis'] = self.extract_evolutionary_features(sequences)
            
            logger.info(f"Comprehensive analysis completed for {len(sequences)} sequences ({sum(len(seq) for seq in sequences)} bp total)")
            
        except Exception as e:
            logger.error(f"Error during comprehensive analysis: {e}")
            results['error'] = f"Analysis partially failed: {str(e)}"
            
        return results
    
    def _batch_comprehensive_analysis(self, sequences: List[str], 
                                    sequence_ids: List[str] = None,
                                    analysis_config: Dict[str, Any] = None,
                                    batch_size_seqs: int = 100,
                                    batch_size_bp: int = 500000) -> Dict[str, Any]:
        """
        Process massive datasets in batches to handle millions of sequences
        """
        logger.info(f"📊 Starting batch processing for {len(sequences)} sequences ({sum(len(s) for s in sequences):,} bp)")
        
        # Initialize aggregated results
        aggregated_results = {
            'summary': {
                'total_sequences': len(sequences),
                'total_base_pairs': sum(len(seq) for seq in sequences),
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'sequence_ids': sequence_ids or [f'seq_{i}' for i in range(len(sequences))],
                'processing_mode': 'batch_processing',
                'batch_count': 0
            },
            'batch_summaries': []
        }
        
        # Create batches
        batches = self._create_batches(sequences, sequence_ids, batch_size_seqs, batch_size_bp)
        aggregated_results['summary']['batch_count'] = len(batches)
        
        logger.info(f"🔢 Created {len(batches)} batches for processing")
        
        # Initialize analysis result containers
        for analysis_type in ['gene_discovery', 'mutation_analysis', 'drug_targets', 
                             'pathogen_detection', 'motif_analysis', 'biomarker_generation', 
                             'evolutionary_analysis']:
            if analysis_config.get(analysis_type, True):
                aggregated_results[analysis_type] = {
                    'batch_results': [],
                    'aggregated_stats': {}
                }
        
        # Process each batch
        for batch_idx, (batch_seqs, batch_ids) in enumerate(batches):
            logger.info(f"⚙️  Processing batch {batch_idx + 1}/{len(batches)} ({len(batch_seqs)} sequences, {sum(len(s) for s in batch_seqs):,} bp)")
            
            try:
                # Process batch with original method (but smaller dataset)
                batch_results = self._process_single_batch(
                    batch_seqs, batch_ids, analysis_config
                )
                
                # Aggregate results
                batch_summary = {
                    'batch_id': batch_idx + 1,
                    'sequence_count': len(batch_seqs),
                    'base_pair_count': sum(len(s) for s in batch_seqs),
                    'processing_time': batch_results.get('processing_time', 'unknown')
                }
                aggregated_results['batch_summaries'].append(batch_summary)
                
                # Merge batch results into aggregated results
                self._merge_batch_results(aggregated_results, batch_results, batch_idx)
                
                # Log batch results for debugging
                logger.debug(f"📋 Batch {batch_idx + 1} results: {list(batch_results.keys())}")
                if 'gene_discovery' in batch_results:
                    gene_count = len(batch_results['gene_discovery'].get('potential_genes', []))
                    logger.debug(f"  🧬 Genes found in batch: {gene_count}")
                
            except Exception as e:
                logger.error(f"❌ Error processing batch {batch_idx + 1}: {e}")
                aggregated_results['batch_summaries'].append({
                    'batch_id': batch_idx + 1,
                    'error': str(e)
                })
        
        # Calculate final aggregated statistics
        self._calculate_aggregated_statistics(aggregated_results)
        
        # Create simplified results structure for frontend compatibility
        simplified_results = self._create_simplified_results(aggregated_results)
        
        logger.info(f"✅ Batch processing completed. Processed {len(sequences)} sequences in {len(batches)} batches")
        logger.info(f"📊 Final aggregated stats: {simplified_results.get('summary', {})}")
        
        return simplified_results
    
    def _create_batches(self, sequences: List[str], sequence_ids: List[str] = None, 
                       batch_size_seqs: int = 100, batch_size_bp: int = 500000) -> List[Tuple[List[str], List[str]]]:
        """Create batches of sequences based on count and base pair limits"""
        batches = []
        current_batch_seqs = []
        current_batch_ids = []
        current_bp = 0
        
        for i, seq in enumerate(sequences):
            seq_id = sequence_ids[i] if sequence_ids else f'seq_{i}'
            
            # Handle massive individual sequences by splitting them
            if len(seq) > batch_size_bp:
                logger.info(f"🔪 Splitting large sequence {seq_id} ({len(seq):,} bp) into chunks")
                
                # Save current batch if not empty
                if current_batch_seqs:
                    batches.append((current_batch_seqs.copy(), current_batch_ids.copy()))
                    current_batch_seqs = []
                    current_batch_ids = []
                    current_bp = 0
                
                # Split the large sequence into chunks
                chunk_size = batch_size_bp
                for chunk_start in range(0, len(seq), chunk_size):
                    chunk_end = min(chunk_start + chunk_size, len(seq))
                    chunk_seq = seq[chunk_start:chunk_end]
                    chunk_id = f"{seq_id}_chunk_{chunk_start//chunk_size + 1}"
                    
                    batches.append(([chunk_seq], [chunk_id]))
                    logger.debug(f"  Created chunk {chunk_id}: {len(chunk_seq):,} bp")
                
                continue  # Skip normal batching for this sequence
            
            # Normal batching logic for smaller sequences
            # Check if adding this sequence would exceed limits
            if (len(current_batch_seqs) >= batch_size_seqs or 
                current_bp + len(seq) > batch_size_bp) and current_batch_seqs:
                
                # Save current batch and start new one
                batches.append((current_batch_seqs.copy(), current_batch_ids.copy()))
                current_batch_seqs = []
                current_batch_ids = []
                current_bp = 0
            
            current_batch_seqs.append(seq)
            current_batch_ids.append(seq_id)
            current_bp += len(seq)
        
        # Add final batch if not empty
        if current_batch_seqs:
            batches.append((current_batch_seqs, current_batch_ids))
        
        return batches
    
    def _process_single_batch(self, sequences: List[str], sequence_ids: List[str], 
                            analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single batch using the original comprehensive analysis"""
        start_time = pd.Timestamp.now()
        
        # Use the original analysis logic but without batch processing
        config_copy = analysis_config.copy()
        config_copy['force_batch_processing'] = False  # Prevent recursive batching
        
        results = {
            'summary': {
                'total_sequences': len(sequences),
                'total_base_pairs': sum(len(seq) for seq in sequences),
                'analysis_timestamp': start_time.isoformat(),
                'sequence_ids': sequence_ids
            }
        }
        
        # Run individual analyses
        try:
            if config_copy.get('gene_discovery', True):
                results['gene_discovery'] = self.discover_new_genes(sequences)
            if config_copy.get('mutation_analysis', True):
                results['mutation_analysis'] = self.identify_disease_mutations(sequences)
            if config_copy.get('drug_targets', True):
                results['drug_targets'] = self.find_drug_targets(sequences[:20])  # Limit for performance
            if config_copy.get('pathogen_detection', True):
                results['pathogen_detection'] = self.detect_pathogens(sequences)
            if config_copy.get('motif_analysis', True):
                results['motif_analysis'] = self.identify_functional_motifs(sequences)
            if config_copy.get('biomarker_generation', True):
                results['biomarker_generation'] = self.generate_biomarkers(sequences)
            if config_copy.get('evolutionary_analysis', True):
                results['evolutionary_analysis'] = self.extract_evolutionary_features(sequences)
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            results['error'] = str(e)
        
        end_time = pd.Timestamp.now()
        results['processing_time'] = str(end_time - start_time)
        
        return results
    
    def _merge_batch_results(self, aggregated_results: Dict[str, Any], 
                           batch_results: Dict[str, Any], batch_idx: int):
        """Merge individual batch results into aggregated results"""
        for analysis_type in ['gene_discovery', 'mutation_analysis', 'drug_targets', 
                             'pathogen_detection', 'motif_analysis', 'biomarker_generation', 
                             'evolutionary_analysis']:
            if analysis_type in batch_results and analysis_type in aggregated_results:
                # Merge results with chunk handling
                batch_data = {
                    'batch_id': batch_idx + 1,
                    'results': batch_results[analysis_type],
                    'sequence_ids': batch_results.get('summary', {}).get('sequence_ids', [])
                }
                
                aggregated_results[analysis_type]['batch_results'].append(batch_data)
    
    def _calculate_aggregated_statistics(self, aggregated_results: Dict[str, Any]):
        """Calculate final statistics across all batches"""
        for analysis_type in ['gene_discovery', 'mutation_analysis', 'drug_targets', 
                             'pathogen_detection', 'motif_analysis', 'biomarker_generation', 
                             'evolutionary_analysis']:
            if analysis_type in aggregated_results:
                batch_results = aggregated_results[analysis_type]['batch_results']
                
                # Aggregate statistics based on analysis type
                if analysis_type == 'gene_discovery':
                    total_genes = sum(len(br['results'].get('potential_genes', [])) 
                                    for br in batch_results)
                    total_orfs = sum(br['results'].get('statistics', {}).get('total_orfs_found', 0)
                                   for br in batch_results)
                    
                    aggregated_results[analysis_type]['aggregated_stats'] = {
                        'total_potential_genes': total_genes,
                        'total_orfs_found': total_orfs,
                        'batches_processed': len(batch_results),
                        'chunks_processed': len([br for br in batch_results if 'chunk' in str(br.get('sequence_ids', []))])
                    }
                
                elif analysis_type == 'pathogen_detection':
                    total_bacterial = sum(len(br['results'].get('bacterial_signatures', [])) 
                                        for br in batch_results)
                    total_viral = sum(len(br['results'].get('viral_signatures', [])) 
                                    for br in batch_results)
                    total_resistance = sum(len(br['results'].get('resistance_genes', [])) 
                                         for br in batch_results)
                    
                    aggregated_results[analysis_type]['aggregated_stats'] = {
                        'total_bacterial_signatures': total_bacterial,
                        'total_viral_signatures': total_viral,
                        'total_resistance_genes': total_resistance,
                        'total_pathogen_signatures': total_bacterial + total_viral + total_resistance,
                        'batches_processed': len(batch_results)
                    }
                
                elif analysis_type == 'mutation_analysis':
                    total_snvs = sum(br['results'].get('statistics', {}).get('total_snvs', 0)
                                   for br in batch_results)
                    total_indels = sum(br['results'].get('statistics', {}).get('total_indels', 0)
                                     for br in batch_results)
                    
                    aggregated_results[analysis_type]['aggregated_stats'] = {
                        'total_snvs': total_snvs,
                        'total_indels': total_indels,
                        'total_mutations': total_snvs + total_indels,
                        'batches_processed': len(batch_results)
                    }
                
                elif analysis_type == 'drug_targets':
                    total_enzyme_sites = sum(len(br['results'].get('enzyme_sites', [])) 
                                           for br in batch_results)
                    total_binding_pockets = sum(len(br['results'].get('binding_pockets', [])) 
                                              for br in batch_results)
                    
                    aggregated_results[analysis_type]['aggregated_stats'] = {
                        'total_enzyme_sites': total_enzyme_sites,
                        'total_binding_pockets': total_binding_pockets,
                        'total_drug_targets': total_enzyme_sites + total_binding_pockets,
                        'batches_processed': len(batch_results)
                    }
                
                elif analysis_type == 'motif_analysis':
                    total_promoters = sum(len(br['results'].get('promoters', [])) 
                                        for br in batch_results)
                    total_enhancers = sum(len(br['results'].get('enhancers', [])) 
                                        for br in batch_results)
                    total_tf_sites = sum(len(br['results'].get('tf_binding_sites', [])) 
                                       for br in batch_results)
                    
                    aggregated_results[analysis_type]['aggregated_stats'] = {
                        'total_promoters': total_promoters,
                        'total_enhancers': total_enhancers,
                        'total_tf_binding_sites': total_tf_sites,
                        'total_regulatory_elements': total_promoters + total_enhancers + total_tf_sites,
                        'batches_processed': len(batch_results)
                    }
                
                # Add generic aggregation for other analysis types
                else:
                    aggregated_results[analysis_type]['aggregated_stats'] = {
                        'batches_processed': len(batch_results),
                        'note': f'Results available in {len(batch_results)} batches'
                    }
    
    def _create_simplified_results(self, aggregated_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create simplified results structure that matches frontend expectations"""
        simplified = {
            'summary': aggregated_results.get('summary', {}),
            'batch_info': {
                'batch_count': aggregated_results['summary'].get('batch_count', 0),
                'processing_mode': 'batch_processing'
            }
        }
        
        # Convert batch results to simplified format for each analysis type
        for analysis_type in ['gene_discovery', 'mutation_analysis', 'drug_targets', 
                             'pathogen_detection', 'motif_analysis', 'biomarker_generation', 
                             'evolutionary_analysis']:
            
            if analysis_type in aggregated_results:
                batch_data = aggregated_results[analysis_type]
                aggregated_stats = batch_data.get('aggregated_stats', {})
                
                # Create simplified structure matching original format
                if analysis_type == 'gene_discovery':
                    # Combine all potential genes from all batches
                    all_genes = []
                    total_orfs = 0
                    
                    for batch_result in batch_data.get('batch_results', []):
                        genes = batch_result.get('results', {}).get('potential_genes', [])
                        all_genes.extend(genes)
                        
                        stats = batch_result.get('results', {}).get('statistics', {})
                        total_orfs += stats.get('total_orfs_found', 0)
                    
                    simplified[analysis_type] = {
                        'potential_genes': all_genes,
                        'statistics': {
                            'total_orfs_found': total_orfs,
                            'protein_coding_orfs': len(all_genes),
                            'long_orfs': len([g for g in all_genes if g.get('length', 0) >= 1000]),
                            'average_orf_length': np.mean([g.get('length', 0) for g in all_genes]) if all_genes else 0,
                            'batches_processed': aggregated_stats.get('batches_processed', 0)
                        }
                    }
                
                elif analysis_type == 'pathogen_detection':
                    # Combine all pathogen signatures
                    all_bacterial = []
                    all_viral = []
                    all_resistance = []
                    
                    for batch_result in batch_data.get('batch_results', []):
                        results = batch_result.get('results', {})
                        all_bacterial.extend(results.get('bacterial_signatures', []))
                        all_viral.extend(results.get('viral_signatures', []))
                        all_resistance.extend(results.get('resistance_genes', []))
                    
                    simplified[analysis_type] = {
                        'bacterial_signatures': all_bacterial,
                        'viral_signatures': all_viral,
                        'resistance_genes': all_resistance,
                        'pathogenicity_factors': [],
                        'statistics': {
                            'total_bacterial': len(all_bacterial),
                            'total_viral': len(all_viral),
                            'total_resistance': len(all_resistance),
                            'batches_processed': aggregated_stats.get('batches_processed', 0)
                        }
                    }
                
                elif analysis_type == 'mutation_analysis':
                    # Combine all mutations
                    all_snvs = []
                    all_insertions = []
                    all_deletions = []
                    all_oncogenic = []
                    
                    for batch_result in batch_data.get('batch_results', []):
                        results = batch_result.get('results', {})
                        all_snvs.extend(results.get('snvs', []))
                        all_insertions.extend(results.get('insertions', []))
                        all_deletions.extend(results.get('deletions', []))
                        all_oncogenic.extend(results.get('oncogenic_patterns', []))
                    
                    simplified[analysis_type] = {
                        'snvs': all_snvs,
                        'insertions': all_insertions,
                        'deletions': all_deletions,
                        'oncogenic_patterns': all_oncogenic,
                        'statistics': {
                            'total_snvs': len(all_snvs),
                            'total_indels': len(all_insertions) + len(all_deletions),
                            'oncogenic_sites': len(all_oncogenic),
                            'batches_processed': aggregated_stats.get('batches_processed', 0)
                        }
                    }
                
                elif analysis_type == 'drug_targets':
                    # Combine all drug targets
                    all_enzyme_sites = []
                    all_binding_pockets = []
                    all_conserved_domains = []
                    all_druggable_proteins = []
                    
                    for batch_result in batch_data.get('batch_results', []):
                        results = batch_result.get('results', {})
                        all_enzyme_sites.extend(results.get('enzyme_sites', []))
                        all_binding_pockets.extend(results.get('binding_pockets', []))
                        all_conserved_domains.extend(results.get('conserved_domains', []))
                        all_druggable_proteins.extend(results.get('druggable_proteins', []))
                    
                    simplified[analysis_type] = {
                        'enzyme_sites': all_enzyme_sites,
                        'binding_pockets': all_binding_pockets,
                        'conserved_domains': all_conserved_domains,
                        'druggable_proteins': all_druggable_proteins,
                        'statistics': {
                            'total_enzyme_sites': len(all_enzyme_sites),
                            'total_binding_pockets': len(all_binding_pockets),
                            'total_drug_targets': len(all_enzyme_sites) + len(all_binding_pockets),
                            'batches_processed': aggregated_stats.get('batches_processed', 0)
                        }
                    }
                
                elif analysis_type == 'motif_analysis':
                    # Combine all motifs
                    all_promoters = []
                    all_enhancers = []
                    all_tf_sites = []
                    all_cpg_islands = []
                    all_splice_sites = []
                    
                    for batch_result in batch_data.get('batch_results', []):
                        results = batch_result.get('results', {})
                        all_promoters.extend(results.get('promoters', []))
                        all_enhancers.extend(results.get('enhancers', []))
                        all_tf_sites.extend(results.get('tf_binding_sites', []))
                        all_cpg_islands.extend(results.get('cpg_islands', []))
                        all_splice_sites.extend(results.get('splice_sites', []))
                    
                    simplified[analysis_type] = {
                        'promoters': all_promoters,
                        'enhancers': all_enhancers,
                        'tf_binding_sites': all_tf_sites,
                        'cpg_islands': all_cpg_islands,
                        'splice_sites': all_splice_sites,
                        'statistics': {
                            'total_promoters': len(all_promoters),
                            'total_enhancers': len(all_enhancers),
                            'total_tf_sites': len(all_tf_sites),
                            'batches_processed': aggregated_stats.get('batches_processed', 0)
                        }
                    }
                
                else:
                    # For other analysis types, use aggregated stats
                    simplified[analysis_type] = {
                        'batch_results': batch_data.get('batch_results', []),
                        'aggregated_stats': aggregated_stats
                    }
        
        return simplified
    
    # Helper methods for specific analyses
    
    def _find_orfs(self, sequence: str, frame: int, seq_idx: int) -> List[Dict[str, Any]]:
        """Find Open Reading Frames in a sequence"""
        orfs = []
        start_codons = ['ATG']
        stop_codons = ['TAA', 'TAG', 'TGA']
        
        for start_codon in start_codons:
            start_pos = 0
            while True:
                start_pos = sequence.find(start_codon, start_pos)
                if start_pos == -1:
                    break
                
                # Find the next stop codon
                for i in range(start_pos + 3, len(sequence) - 2, 3):
                    codon = sequence[i:i+3]
                    if len(codon) == 3 and codon in stop_codons:
                        orf_seq = sequence[start_pos:i+3]
                        protein_seq = self._translate_sequence(orf_seq)
                        
                        orfs.append({
                            'sequence_id': seq_idx,
                            'frame': frame,
                            'start': start_pos,
                            'end': i + 3,
                            'length': len(orf_seq),
                            'sequence': orf_seq,
                            'protein_seq': protein_seq,
                            'start_codon': start_codon,
                            'stop_codon': codon
                        })
                        break
                
                start_pos += 1
        
        return orfs
    
    def _translate_sequence(self, dna_seq: str) -> str:
        """Translate DNA sequence to protein"""
        protein = ""
        for i in range(0, len(dna_seq) - 2, 3):
            codon = dna_seq[i:i+3]
            if len(codon) == 3:
                protein += self.genetic_code.get(codon, 'X')
        return protein
    
    def _calculate_coding_potential(self, sequence: str) -> float:
        """Calculate the coding potential of a sequence"""
        # Simple coding potential based on codon usage bias and composition
        codons = [sequence[i:i+3] for i in range(0, len(sequence) - 2, 3)]
        valid_codons = [c for c in codons if len(c) == 3 and c in self.genetic_code]
        
        if not valid_codons:
            return 0.0
        
        # Calculate codon adaptation index (simplified)
        codon_freq = Counter(valid_codons)
        total_codons = len(valid_codons)
        
        # Bias towards preferred codons
        preferred_codons = ['ATG', 'TGG', 'TTT', 'AAA', 'GAA']  # Simplified set
        preferred_count = sum(codon_freq.get(c, 0) for c in preferred_codons)
        
        coding_score = preferred_count / total_codons if total_codons > 0 else 0
        return min(coding_score * 2, 1.0)  # Normalize to 0-1
    
    def _predict_gene_function(self, protein_seq: str) -> Dict[str, Any]:
        """Predict gene function from protein sequence"""
        function_prediction = {
            'enzyme_type': 'unknown',
            'domain_family': 'unknown',
            'cellular_location': 'unknown',
            'confidence': 0.0
        }
        
        # Simple pattern-based function prediction
        if 'CATALYTIC' in protein_seq or 'KINASE' in protein_seq:
            function_prediction['enzyme_type'] = 'kinase'
            function_prediction['confidence'] = 0.8
        elif 'BINDING' in protein_seq or 'RECEPTOR' in protein_seq:
            function_prediction['enzyme_type'] = 'receptor'
            function_prediction['confidence'] = 0.7
        elif protein_seq.count('C') > len(protein_seq) * 0.1:  # Cysteine-rich
            function_prediction['domain_family'] = 'zinc_finger'
            function_prediction['confidence'] = 0.6
        
        return function_prediction
    
    def _identify_mutations_vs_reference(self, sequence: str, reference: str, seq_idx: int) -> Dict[str, List]:
        """Identify mutations compared to reference sequence"""
        mutations = {'snvs': [], 'insertions': [], 'deletions': []}
        
        # Align sequences (simplified alignment)
        min_len = min(len(sequence), len(reference))
        
        for i in range(min_len):
            if sequence[i] != reference[i]:
                mutations['snvs'].append({
                    'sequence_id': seq_idx,
                    'position': i,
                    'reference_base': reference[i],
                    'variant_base': sequence[i],
                    'mutation_type': 'SNV'
                })
        
        # Simple indel detection
        if len(sequence) > len(reference):
            mutations['insertions'].append({
                'sequence_id': seq_idx,
                'position': len(reference),
                'inserted_bases': sequence[len(reference):],
                'length': len(sequence) - len(reference)
            })
        elif len(sequence) < len(reference):
            mutations['deletions'].append({
                'sequence_id': seq_idx,
                'position': len(sequence),
                'deleted_bases': reference[len(sequence):],
                'length': len(reference) - len(sequence)
            })
        
        return mutations
    
    def _detect_oncogenic_patterns(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect known oncogenic patterns in sequence"""
        oncogenic_patterns = []
        
        # Known oncogenic motifs (simplified)
        cancer_motifs = {
            'TP53_BINDING': 'RRRCWWGYYY',
            'MYC_BINDING': 'CACGTG',
            'RAS_MUTATION': 'GGTGGC'  # Simplified RAS codon
        }
        
        for motif_name, pattern in cancer_motifs.items():
            # Convert IUPAC codes to regex (simplified)
            regex_pattern = pattern.replace('R', '[AG]').replace('Y', '[CT]').replace('W', '[AT]')
            
            for match in re.finditer(regex_pattern, sequence):
                oncogenic_patterns.append({
                    'sequence_id': seq_idx,
                    'motif_name': motif_name,
                    'position': match.start(),
                    'sequence': match.group(),
                    'oncogenic_risk': 0.8 if 'TP53' in motif_name else 0.6
                })
        
        return oncogenic_patterns
    
    def _translate_all_frames(self, sequence: str) -> Dict[str, str]:
        """Translate sequence in all reading frames"""
        proteins = {}
        
        for frame in range(3):
            # Forward frames
            proteins[f'frame_{frame+1}'] = self._translate_sequence(sequence[frame:])
            
            # Reverse frames
            rev_seq = str(Seq(sequence).reverse_complement())
            proteins[f'frame_-{frame+1}'] = self._translate_sequence(rev_seq[frame:])
        
        return proteins
    
    def _analyze_druggability(self, protein: str, seq_idx: int, frame: str, is_small_dataset: bool = False) -> Dict[str, Any]:
        """Analyze protein druggability with adaptive thresholds"""
        analysis = {
            'enzyme_sites': [],
            'binding_pockets': [],
            'conserved_domains': [],
            'druggability_score': 0.0
        }
        
        # Primary enzyme active sites
        enzyme_motifs = {
            'SERINE_PROTEASE': 'HDS',
            'KINASE_DOMAIN': 'DFG',
            'ZINC_FINGER': 'CxxC'
        }
        
        # Secondary patterns for small datasets
        if is_small_dataset:
            flexible_motifs = {
                'CATALYTIC_TRIAD': ['HD', 'DS', 'HG'],
                'METAL_BINDING': ['CC', 'HH', 'CG'],
                'ATP_BINDING': ['GK', 'MG', 'DG']
            }
        
        # Check primary motifs
        for motif_name, pattern in enzyme_motifs.items():
            if pattern in protein:
                analysis['enzyme_sites'].append({
                    'sequence_id': seq_idx,
                    'frame': frame,
                    'motif_type': motif_name,
                    'position': protein.find(pattern),
                    'druggability': 0.9
                })
        
        # Check flexible motifs for small datasets
        if is_small_dataset and not analysis['enzyme_sites']:
            for motif_class, patterns in flexible_motifs.items():
                for pattern in patterns:
                    if pattern in protein:
                        analysis['enzyme_sites'].append({
                            'sequence_id': seq_idx,
                            'frame': frame,
                            'motif_type': f'{motif_class}_PARTIAL',
                            'position': protein.find(pattern),
                            'druggability': 0.6
                        })
                        break
        
        # Calculate overall druggability score
        hydrophobic_aa = 'AILMFWYV'
        charged_aa = 'DEKR'
        polar_aa = 'STNQ'
        
        if len(protein) > 0:
            hydrophobic_ratio = sum(1 for aa in protein if aa in hydrophobic_aa) / len(protein)
            charged_ratio = sum(1 for aa in protein if aa in charged_aa) / len(protein)
            polar_ratio = sum(1 for aa in protein if aa in polar_aa) / len(protein)
            
            # Enhanced druggability calculation
            diversity_score = len(set(protein)) / 20.0  # Amino acid diversity
            
            # Balanced composition indicates druggability
            composition_score = min(hydrophobic_ratio * 1.5, 1.0) * min(charged_ratio * 2, 1.0) * min(polar_ratio * 2, 1.0)
            
            analysis['druggability_score'] = (composition_score + diversity_score) / 2
            
            # Bonus for enzyme sites
            if analysis['enzyme_sites']:
                analysis['druggability_score'] = min(analysis['druggability_score'] + 0.2, 1.0)
        
        return analysis
    
    def _detect_bacterial_signatures(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect bacterial signature sequences with flexible matching"""
        signatures = []
        
        # Primary bacterial motifs (strict matching)
        bacterial_motifs = {
            'RIBOSOMAL_16S': 'ACCTGGTTGATCCTGCCAG',
            'BACTERIAL_PROMOTER': 'TTGACA',
            'SHINE_DALGARNO': 'AGGAGG'
        }
        
        # Secondary patterns for small datasets (more flexible)
        flexible_motifs = {
            'RIBOSOMAL_PARTIAL': ['ACCTGG', 'GATCCT', 'TGCCAG'],
            'PROMOTER_LIKE': ['TTGAC', 'TGACA', 'GACAA'],
            'RBS_LIKE': ['AGGAG', 'GGAGG', 'GAGG']
        }
        
        # Check strict patterns first
        for motif_name, pattern in bacterial_motifs.items():
            if pattern in sequence:
                signatures.append({
                    'sequence_id': seq_idx,
                    'signature_type': motif_name,
                    'position': sequence.find(pattern),
                    'confidence': 0.8,
                    'organism_type': 'bacteria'
                })
        
        # If no strict matches, try flexible patterns for small datasets
        if not signatures and len(sequence) < 500:
            for motif_class, patterns in flexible_motifs.items():
                for pattern in patterns:
                    if pattern in sequence:
                        signatures.append({
                            'sequence_id': seq_idx,
                            'signature_type': f'{motif_class}_PARTIAL',
                            'position': sequence.find(pattern),
                            'confidence': 0.6,
                            'organism_type': 'bacteria_potential'
                        })
                        break  # Only add one per class
        
        return signatures
    
    def _detect_viral_signatures(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect viral signature sequences"""
        signatures = []
        
        # Viral motifs (simplified)
        viral_motifs = {
            'VIRAL_POLYMERASE': 'YGDD',
            'VIRAL_CAPSID': 'GPNG',
            'PACKAGING_SIGNAL': 'AAUAAA'
        }
        
        for motif_name, pattern in viral_motifs.items():
            # Convert RNA to DNA if needed
            dna_pattern = pattern.replace('U', 'T')
            if dna_pattern in sequence:
                signatures.append({
                    'sequence_id': seq_idx,
                    'signature_type': motif_name,
                    'position': sequence.find(dna_pattern),
                    'confidence': 0.7,
                    'organism_type': 'virus'
                })
        
        return signatures
    
    def _detect_resistance_genes(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect antibiotic resistance genes with flexible matching"""
        resistance_genes = []
        
        # Primary resistance gene patterns (strict)
        resistance_motifs = {
            'BETA_LACTAMASE': 'SXXK',
            'AMINOGLYCOSIDE': 'APH',
            'TETRACYCLINE': 'TETM'
        }
        
        # DNA-level patterns for small datasets
        dna_resistance_patterns = {
            'BETA_LACTAM_DNA': ['TCGAAANNNAAG', 'SERINE_ACTIVE'],  # Serine-based motifs
            'AMINOGLYCOSIDE_DNA': ['GCCCAC', 'PHOSPHOTRANS'],
            'EFFLUX_PUMP': ['ATGAAA', 'EFFLUX_PROTEIN']
        }
        
        # Translate sequence to look for protein patterns
        try:
            proteins = self._translate_all_frames(sequence)
            
            for frame, protein in proteins.items():
                # Check strict protein patterns
                for gene_name, pattern in resistance_motifs.items():
                    if pattern.replace('X', '[A-Z]') in protein or pattern in protein:
                        resistance_genes.append({
                            'sequence_id': seq_idx,
                            'resistance_type': gene_name,
                            'frame': frame,
                            'position': protein.find(pattern) if pattern in protein else 0,
                            'antibiotic_class': self._get_antibiotic_class(gene_name),
                            'confidence': 0.8
                        })
                
                # For small sequences, look for resistance-like patterns
                if len(sequence) < 1000:
                    # Look for conserved amino acid patterns
                    if 'S' in protein and 'K' in protein:  # Basic serine-lysine pattern
                        if abs(protein.find('S') - protein.find('K')) < 10:
                            resistance_genes.append({
                                'sequence_id': seq_idx,
                                'resistance_type': 'POTENTIAL_BETA_LACTAMASE',
                                'frame': frame,
                                'position': min(protein.find('S'), protein.find('K')),
                                'antibiotic_class': 'beta_lactams',
                                'confidence': 0.5
                            })
        except:
            pass  # Skip if translation fails
        
        return resistance_genes
    
    def _get_antibiotic_class(self, gene_name: str) -> str:
        """Map resistance gene to antibiotic class"""
        mapping = {
            'BETA_LACTAMASE': 'beta_lactams',
            'AMINOGLYCOSIDE': 'aminoglycosides',
            'TETRACYCLINE': 'tetracyclines'
        }
        return mapping.get(gene_name, 'unknown')
    
    def _detect_pathogenicity_factors(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect pathogenicity factors"""
        factors = []
        
        # Virulence factor patterns
        virulence_motifs = {
            'ADHESIN': 'RGDS',
            'TOXIN': 'ADPRT',
            'INVASION': 'INVASIN'
        }
        
        proteins = self._translate_all_frames(sequence)
        
        for frame, protein in proteins.items():
            for factor_name, pattern in virulence_motifs.items():
                if pattern in protein:
                    factors.append({
                        'sequence_id': seq_idx,
                        'virulence_factor': factor_name,
                        'frame': frame,
                        'position': protein.find(pattern),
                        'pathogenicity_score': 0.8
                    })
        
        return factors
    
    def _detect_promoters(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect promoter regions"""
        promoters = []
        
        # TATA box and other promoter elements
        promoter_motifs = {
            'TATA_BOX': 'TATAAA',
            'CAAT_BOX': 'CCAAT',
            'GC_BOX': 'GGGCGG'
        }
        
        for motif_name, pattern in promoter_motifs.items():
            for match in re.finditer(pattern, sequence):
                promoters.append({
                    'sequence_id': seq_idx,
                    'promoter_type': motif_name,
                    'position': match.start(),
                    'sequence': match.group(),
                    'strength': self._calculate_promoter_strength(sequence, match.start())
                })
        
        return promoters
    
    def _calculate_promoter_strength(self, sequence: str, position: int) -> float:
        """Calculate promoter strength based on surrounding context"""
        # Look at GC content in surrounding region
        window_size = 100
        start = max(0, position - window_size)
        end = min(len(sequence), position + window_size)
        region = sequence[start:end]
        
        gc_content = gc_fraction(region)
        # Moderate GC content often indicates strong promoters
        if 0.4 <= gc_content <= 0.6:
            return 0.8
        elif 0.3 <= gc_content <= 0.7:
            return 0.6
        else:
            return 0.4
    
    def _detect_enhancers(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect enhancer elements"""
        enhancers = []
        
        # Enhancer motifs
        enhancer_motifs = {
            'AP1_SITE': 'TGACTCA',
            'NF_KB_SITE': 'GGGACTTTCC',
            'SP1_SITE': 'GGGCGG'
        }
        
        for motif_name, pattern in enhancer_motifs.items():
            for match in re.finditer(pattern, sequence):
                enhancers.append({
                    'sequence_id': seq_idx,
                    'enhancer_type': motif_name,
                    'position': match.start(),
                    'sequence': match.group(),
                    'activity_score': 0.7
                })
        
        return enhancers
    
    def _detect_tf_binding_sites(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect transcription factor binding sites"""
        tf_sites = []
        
        # Common TF binding motifs
        tf_motifs = {
            'P53_SITE': 'RRRCWWGYYY',
            'MYC_SITE': 'CACGTG',
            'ETS_SITE': 'GGAA'
        }
        
        for tf_name, pattern in tf_motifs.items():
            # Convert IUPAC to regex
            regex_pattern = pattern.replace('R', '[AG]').replace('Y', '[CT]').replace('W', '[AT]')
            
            for match in re.finditer(regex_pattern, sequence):
                tf_sites.append({
                    'sequence_id': seq_idx,
                    'tf_name': tf_name,
                    'position': match.start(),
                    'sequence': match.group(),
                    'binding_affinity': 0.6
                })
        
        return tf_sites
    
    def _detect_cpg_islands(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect CpG islands"""
        cpg_islands = []
        window_size = 200
        
        for i in range(0, len(sequence) - window_size, 50):
            window = sequence[i:i + window_size]
            
            # Calculate CpG ratio
            cpg_count = window.count('CG')
            c_count = window.count('C')
            g_count = window.count('G')
            
            if c_count + g_count > 0:
                gc_content = (c_count + g_count) / len(window)
                cpg_ratio = cpg_count / len(window) * 100
                
                # CpG island criteria: GC > 50%, CpG ratio > 0.6%
                if gc_content > 0.5 and cpg_ratio > 0.6:
                    cpg_islands.append({
                        'sequence_id': seq_idx,
                        'start': i,
                        'end': i + window_size,
                        'gc_content': gc_content,
                        'cpg_ratio': cpg_ratio,
                        'methylation_potential': min(cpg_ratio / 2, 1.0)
                    })
        
        return cpg_islands
    
    def _detect_splice_sites(self, sequence: str, seq_idx: int) -> List[Dict[str, Any]]:
        """Detect splice sites"""
        splice_sites = []
        
        # Canonical splice site sequences
        donor_sites = ['GT', 'GC']  # 5' splice site
        acceptor_sites = ['AG']     # 3' splice site
        
        for donor in donor_sites:
            for match in re.finditer(donor, sequence):
                splice_sites.append({
                    'sequence_id': seq_idx,
                    'splice_type': 'donor',
                    'position': match.start(),
                    'sequence': match.group(),
                    'canonical': donor == 'GT'
                })
        
        for acceptor in acceptor_sites:
            for match in re.finditer(acceptor, sequence):
                splice_sites.append({
                    'sequence_id': seq_idx,
                    'splice_type': 'acceptor',
                    'position': match.start(),
                    'sequence': match.group(),
                    'canonical': True
                })
        
        return splice_sites
    
    def _supervised_biomarker_discovery(self, sequences: List[str], labels: List[str]) -> Dict[str, Any]:
        """Discover biomarkers using supervised learning"""
        biomarkers = {}
        
        # Group sequences by label
        label_groups = defaultdict(list)
        for seq, label in zip(sequences, labels):
            label_groups[label].append(seq)
        
        # Find discriminative k-mers
        discriminative_kmers = []
        for k in [3, 4, 5]:
            for label, group_seqs in label_groups.items():
                other_seqs = [s for s, l in zip(sequences, labels) if l != label]
                
                # Calculate k-mer frequencies
                group_kmers = self._extract_kmer_frequencies(group_seqs, k)
                other_kmers = self._extract_kmer_frequencies(other_seqs, k)
                
                # Find discriminative k-mers
                for kmer in group_kmers:
                    if kmer in group_kmers and kmer in other_kmers:
                        fold_change = group_kmers[kmer] / (other_kmers[kmer] + 0.001)
                        if fold_change > 2.0:  # At least 2-fold enrichment
                            discriminative_kmers.append({
                                'kmer': kmer,
                                'associated_label': label,
                                'fold_change': fold_change,
                                'frequency_in_group': group_kmers[kmer],
                                'frequency_in_others': other_kmers[kmer]
                            })
        
        biomarkers['discriminative_kmers'] = discriminative_kmers
        return biomarkers
    
    def _unsupervised_biomarker_discovery(self, sequences: List[str]) -> Dict[str, Any]:
        """Discover biomarkers without labels using unsupervised methods"""
        biomarkers = {}
        
        # Find conserved motifs
        conserved_motifs = []
        for k in [6, 7, 8]:  # Look for longer conserved sequences
            kmer_counts = Counter()
            for seq in sequences:
                for i in range(len(seq) - k + 1):
                    kmer = seq[i:i+k]
                    if re.match(r'^[ATCG]+$', kmer):  # Only valid DNA k-mers
                        kmer_counts[kmer] += 1
            
            # Find highly conserved k-mers
            total_possible = sum(max(0, len(seq) - k + 1) for seq in sequences)
            for kmer, count in kmer_counts.most_common(20):
                frequency = count / total_possible
                if frequency > 0.1:  # Present in >10% of possible positions
                    conserved_motifs.append({
                        'motif': kmer,
                        'count': count,
                        'frequency': frequency,
                        'conservation_score': frequency * len(kmer)
                    })
        
        biomarkers['conserved_motifs'] = conserved_motifs
        return biomarkers
    
    def _extract_kmer_frequencies(self, sequences: List[str], k: int) -> Dict[str, float]:
        """Extract k-mer frequencies from sequences"""
        kmer_counts = Counter()
        total_kmers = 0
        
        for seq in sequences:
            for i in range(len(seq) - k + 1):
                kmer = seq[i:i+k]
                if re.match(r'^[ATCG]+$', kmer):
                    kmer_counts[kmer] += 1
                    total_kmers += 1
        
        # Convert to frequencies
        return {kmer: count / total_kmers for kmer, count in kmer_counts.items()}
    
    def _analyze_codon_usage(self, sequence: str, seq_idx: int) -> Dict[str, Any]:
        """Analyze codon usage bias"""
        analysis = {
            'sequence_id': seq_idx,
            'codon_frequencies': {},
            'bias_score': 0.0,
            'preferred_codons': []
        }
        
        # Extract codons
        codons = []
        for i in range(0, len(sequence) - 2, 3):
            codon = sequence[i:i+3]
            if len(codon) == 3 and codon in self.genetic_code:
                codons.append(codon)
        
        if not codons:
            return analysis
        
        # Calculate codon frequencies
        codon_counts = Counter(codons)
        total_codons = len(codons)
        
        analysis['codon_frequencies'] = {
            codon: count / total_codons 
            for codon, count in codon_counts.items()
        }
        
        # Calculate codon adaptation index (simplified)
        # Preferred codons for major amino acids
        preferred_codons = {
            'F': 'TTT', 'L': 'CTG', 'S': 'TCT', 'Y': 'TAT',
            'C': 'TGT', 'W': 'TGG', 'P': 'CCT', 'H': 'CAT',
            'Q': 'CAG', 'R': 'CGT', 'I': 'ATT', 'M': 'ATG',
            'T': 'ACT', 'N': 'AAT', 'K': 'AAG', 'V': 'GTT',
            'A': 'GCT', 'D': 'GAT', 'E': 'GAG', 'G': 'GGT'
        }
        
        preferred_count = 0
        for codon in codons:
            aa = self.genetic_code[codon]
            if aa in preferred_codons and codon == preferred_codons[aa]:
                preferred_count += 1
        
        analysis['bias_score'] = preferred_count / total_codons if total_codons > 0 else 0
        analysis['preferred_codons'] = list(preferred_codons.values())
        
        return analysis
    
    def _analyze_substitution_patterns(self, sequence: str, seq_idx: int) -> Dict[str, Any]:
        """Analyze substitution patterns in sequence"""
        analysis = {
            'sequence_id': seq_idx,
            'transition_ratio': 0.0,
            'transversion_ratio': 0.0,
            'cpg_transitions': 0,
            'mutation_hotspots': []
        }
        
        # Look for potential mutation signatures
        transitions = ['AG', 'GA', 'CT', 'TC']  # A<->G, C<->T
        transversions = ['AC', 'CA', 'AT', 'TA', 'GC', 'CG', 'GT', 'TG']
        
        transition_count = sum(sequence.count(dinuc) for dinuc in transitions)
        transversion_count = sum(sequence.count(dinuc) for dinuc in transversions)
        
        total_dinucs = len(sequence) - 1
        if total_dinucs > 0:
            analysis['transition_ratio'] = transition_count / total_dinucs
            analysis['transversion_ratio'] = transversion_count / total_dinucs
        
        # Count CpG dinucleotides (methylation hotspots)
        analysis['cpg_transitions'] = sequence.count('CG')
        
        return analysis
    
    def _calculate_selection_pressure(self, sequence: str, seq_idx: int) -> Dict[str, Any]:
        """Calculate indicators of selection pressure"""
        analysis = {
            'sequence_id': seq_idx,
            'gc_content': 0.0,
            'codon_bias': 0.0,
            'conservation_score': 0.0
        }
        
        # GC content as indicator of selection
        analysis['gc_content'] = gc_fraction(sequence)
        
        # Simple conservation score based on repetitive elements
        kmer_diversity = len(set(sequence[i:i+6] for i in range(len(sequence) - 5)))
        max_possible_kmers = min(4**6, len(sequence) - 5)
        analysis['conservation_score'] = kmer_diversity / max_possible_kmers if max_possible_kmers > 0 else 0
        
        return analysis


# Service instance
dna_discovery_service = DNADiscoveryService()