"""
Test script for DNA Discovery Service
Demonstrates the biological analysis capabilities
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.dna_discovery_service import dna_discovery_service
from app.services.dna_ml_models import (
    DNAFeatureExtractor, GeneClassifier, PathogenDetector, 
    DrugTargetPredictor, BiomarkerDiscoverer, ComprehensiveDNAAnalyzer
)
from Bio import SeqIO
import json

def load_test_sequences(fasta_file):
    """Load test sequences from FASTA file"""
    sequences = []
    sequence_ids = []
    
    with open(fasta_file, 'r') as handle:
        for record in SeqIO.parse(handle, "fasta"):
            sequences.append(str(record.seq))
            sequence_ids.append(record.id)
    
    return sequences, sequence_ids

def test_gene_discovery():
    """Test gene discovery functionality"""
    print("🧬 Testing Gene Discovery...")
    
    sequences = [
        "ATGAAACGTAGCAAGATCGTAGCTAGCTAGCTAGCTATGCGATCGTAGCTAGCTAGGCTAGCTGATCGTAGCTAGCTAGCTGATCGTAGCTAGCTGATCGTAGCTAGCTGATCGTAGCTAGCTGATCGTAGCTAGCTGATCGTAGCTAGCTGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG",
        "ATGGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACTAG"
    ]
    
    results = dna_discovery_service.discover_new_genes(sequences, min_length=100)
    
    print(f"  ✅ Found {len(results['potential_genes'])} potential genes")
    print(f"  📊 Total ORFs: {results['statistics']['total_orfs_found']}")
    print(f"  📏 Average ORF length: {results['statistics'].get('average_orf_length', 0):.1f} bp")
    
    return results

def test_mutation_analysis():
    """Test mutation analysis functionality"""
    print("\n⚠️ Testing Mutation Analysis...")
    
    sequences = [
        "ATCGTAGCTAGCTAGCTAGCRRRCWWGYYYTAGCTAGCTAGCTAGCTAGCTAGGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGGGTGGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCACGTGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG",
        "GCTAGCTAGCTGACTCAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCGGGACTTTCCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCGGGCGGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"
    ]
    
    reference = "ATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"
    
    results = dna_discovery_service.identify_disease_mutations(sequences, reference)
    
    print(f"  🧬 SNVs detected: {results['statistics']['total_snvs']}")
    print(f"  ➕ Insertions: {len(results['insertions'])}")
    print(f"  ➖ Deletions: {len(results['deletions'])}")
    print(f"  ☢️ Oncogenic sites: {results['statistics']['oncogenic_sites']}")
    
    return results

def test_drug_target_identification():
    """Test drug target identification"""
    print("\n🎯 Testing Drug Target Identification...")
    
    sequences = [
        "ATGAAACGTAGCAAGATCGTAGCTAGCTAGCTAGCTATGCGATCGTAGCTAGCTAGGCTAGCTGATCGTAGCTAGCTAGCTGATCGTAGCTAGCTGATCGTAGCTAGCTGATCGTAGCTAGCTGATCGTAGCTAGCTGATCGTAGCTAGCTGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG",
        "ATGGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACGGCAAGATCGTGGCCATCGACTAG"
    ]
    
    results = dna_discovery_service.find_drug_targets(sequences)
    
    print(f"  💊 Druggable proteins: {len(results['druggable_proteins'])}")
    print(f"  🔬 Enzyme sites: {len(results['enzyme_sites'])}")
    print(f"  🎪 Binding pockets: {len(results['binding_pockets'])}")
    print(f"  🏛️ Conserved domains: {len(results['conserved_domains'])}")
    
    return results

def test_pathogen_detection():
    """Test pathogen detection"""
    print("\n🦠 Testing Pathogen Detection...")
    
    sequences = [
        "ACCTGGTTGATCCTGCCAGTAGCGATGCGACACTGGTTGATCCTGCCAGTAGCGATGCGACACTGGTTGATCCTGCCAGTAGCGATGCGACACTGGTTGATCCTGCCAGTAGCGATGCGACACTGGTTGATCCTGCCAGTAGCGATGCGACACTGGTTGATCCTGCCAGTAGCGATGCGACACTGGTTGATCCTGCCAGTAGCGATGCGACA",
        "ATCGTAGCTAGCTAGCTAGCYGDDTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCGPNGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"
    ]
    
    results = dna_discovery_service.detect_pathogens(sequences)
    
    print(f"  🦠 Bacterial signatures: {len(results['bacterial_signatures'])}")
    print(f"  🦠 Viral signatures: {len(results['viral_signatures'])}")
    print(f"  💊 Resistance genes: {len(results['resistance_genes'])}")
    print(f"  ⚔️ Virulence factors: {len(results['pathogenicity_factors'])}")
    
    return results

def test_motif_analysis():
    """Test functional motif analysis"""
    print("\n🔍 Testing Motif Analysis...")
    
    sequences = [
        "GCTAGCTAGCTAGCTATAAAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCCCAATGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCGGGCGGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG",
        "GCTAGCTAGCTGACTCAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCGGGACTTTCCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCGGGCGGTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"
    ]
    
    results = dna_discovery_service.identify_functional_motifs(sequences)
    
    print(f"  🎭 Promoters: {len(results['promoters'])}")
    print(f"  🎪 Enhancers: {len(results['enhancers'])}")
    print(f"  🎯 TF binding sites: {len(results['tf_binding_sites'])}")
    print(f"  🏝️ CpG islands: {len(results['cpg_islands'])}")
    print(f"  ✂️ Splice sites: {len(results['splice_sites'])}")
    
    return results

def test_biomarker_generation():
    """Test biomarker generation"""
    print("\n📊 Testing Biomarker Generation...")
    
    sequences = [
        "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGC",
        "ATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATAT"
    ]
    
    labels = ["cancer", "normal"]
    
    results = dna_discovery_service.generate_biomarkers(sequences, labels)
    
    print(f"  🧬 Sequence signatures: {len(results.get('sequence_signatures', []))}")
    print(f"  🔬 Diagnostic kmers: {len(results.get('diagnostic_kmers', []))}")
    print(f"  📈 Conserved motifs: {len(results.get('conserved_motifs', []))}")
    
    return results

def test_comprehensive_analysis():
    """Test comprehensive analysis with real FASTA file"""
    print("\n🔬 Testing Comprehensive Analysis...")
    
    try:
        sequences, sequence_ids = load_test_sequences("test_dna_discovery.fasta")
        print(f"  📂 Loaded {len(sequences)} test sequences")
        
        results = dna_discovery_service.comprehensive_sequence_analysis(
            sequences=sequences[:5],  # Use first 5 sequences for testing
            sequence_ids=sequence_ids[:5]
        )
        
        print("  ✅ Comprehensive analysis completed!")
        print(f"  📊 Analysis ID: {results['summary']['analysis_timestamp']}")
        
        # Print summary of each analysis
        for analysis_type, data in results.items():
            if analysis_type != 'summary' and data:
                print(f"  🧬 {analysis_type}: Analysis completed")
        
        return results
        
    except FileNotFoundError:
        print("  ⚠️ Test FASTA file not found, using sample sequences")
        
        sample_sequences = [
            "ATGAAACGTAGCAAGATCGTAGCTAGCTAGCTAGCTATGCGATCGTAGCTAGCTAG",
            "ACCTGGTTGATCCTGCCAGTAGCGATGCGACACTGGTTGATCCTGCCAGTAGC",
            "GCTAGCTAGCTATAAAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAG"
        ]
        
        results = dna_discovery_service.comprehensive_sequence_analysis(
            sequences=sample_sequences,
            sequence_ids=["sample_1", "sample_2", "sample_3"]
        )
        
        return results

def test_ml_models():
    """Test ML models for DNA analysis"""
    print("\n🤖 Testing ML Models...")
    
    # Test feature extraction
    extractor = DNAFeatureExtractor(kmer_sizes=[3, 4], max_features_per_kmer=20)
    
    test_sequences = [
        "ATGCGTACGTAGCTAGCTAGCTAG",
        "GCTAGCTAGCTAGCTAGCTAGCTA",
        "CGATCGATCGATCGATCGATCGAT"
    ]
    
    # Fit and transform
    features = extractor.fit_transform(test_sequences)
    print(f"  🧬 Extracted {features.shape[1]} features from {features.shape[0]} sequences")
    print(f"  📊 Feature names: {len(extractor.feature_names_)} total")
    
    # Test with labels for supervised learning
    labels = ["gene", "non_gene", "gene"]
    
    try:
        # Test gene classifier
        gene_classifier = GeneClassifier()
        gene_classifier.fit(test_sequences, labels)
        predictions = gene_classifier.predict(test_sequences)
        print(f"  🎯 Gene classifier predictions: {predictions}")
        
        # Test biomarker discoverer
        biomarker_discoverer = BiomarkerDiscoverer()
        biomarker_results = biomarker_discoverer.discover_biomarkers(test_sequences, labels)
        print(f"  📈 Biomarker discovery completed")
        print(f"  🔬 Model accuracy: {biomarker_results['model_performance']['validation_accuracy']:.3f}")
        
    except Exception as e:
        print(f"  ⚠️ ML model testing encountered issue: {e}")

def main():
    """Run all DNA discovery tests"""
    print("🧬 DNA Discovery Service Test Suite")
    print("=" * 50)
    
    # Individual component tests
    gene_results = test_gene_discovery()
    mutation_results = test_mutation_analysis()
    drug_results = test_drug_target_identification()
    pathogen_results = test_pathogen_detection()
    motif_results = test_motif_analysis()
    biomarker_results = test_biomarker_generation()
    
    # Comprehensive analysis test
    comprehensive_results = test_comprehensive_analysis()
    
    # ML models test
    test_ml_models()
    
    print("\n🎉 All tests completed!")
    print("\n📋 Summary:")
    print(f"  🧬 Genes discovered: {len(gene_results['potential_genes'])}")
    print(f"  ⚠️ Mutations found: {mutation_results['statistics']['total_snvs']}")
    print(f"  🎯 Drug targets: {len(drug_results['druggable_proteins'])}")
    print(f"  🦠 Pathogen signatures: {len(pathogen_results['bacterial_signatures']) + len(pathogen_results['viral_signatures'])}")
    print(f"  🔍 Functional motifs: {len(motif_results['promoters']) + len(motif_results['enhancers'])}")
    
    # Save comprehensive results
    with open('dna_discovery_test_results.json', 'w') as f:
        json.dump(comprehensive_results, f, indent=2, default=str)
    
    print("  💾 Results saved to 'dna_discovery_test_results.json'")

if __name__ == "__main__":
    main()