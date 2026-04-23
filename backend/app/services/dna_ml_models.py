"""
Advanced ML Models for DNA Sequence Analysis and Biological Discovery
Specialized models for genomics, drug discovery, pathogen detection, and disease prediction
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import logging
import joblib
from collections import Counter
import re

logger = logging.getLogger(__name__)


class DNAFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract comprehensive features from DNA sequences for ML models"""
    
    def __init__(self, 
                 kmer_sizes: List[int] = [3, 4, 5, 6],
                 include_composition: bool = True,
                 include_physicochemical: bool = True,
                 include_structural: bool = True,
                 max_features_per_kmer: int = 100):
        self.kmer_sizes = kmer_sizes
        self.include_composition = include_composition
        self.include_physicochemical = include_physicochemical
        self.include_structural = include_structural
        self.max_features_per_kmer = max_features_per_kmer
        self.feature_names_ = []
        self.kmer_vocabularies_ = {}
        
    def fit(self, X, y=None):
        """Learn feature vocabularies from training data"""
        sequences = [seq if isinstance(seq, str) else seq[0] for seq in X]
        
        # Build k-mer vocabularies
        for k in self.kmer_sizes:
            kmer_counts = Counter()
            for seq in sequences:
                seq = seq.upper()
                for i in range(len(seq) - k + 1):
                    kmer = seq[i:i+k]
                    if re.match(r'^[ATCG]+$', kmer):
                        kmer_counts[kmer] += 1
            
            # Keep top k-mers
            top_kmers = [kmer for kmer, _ in kmer_counts.most_common(self.max_features_per_kmer)]
            self.kmer_vocabularies_[k] = top_kmers
        
        # Build feature names
        self._build_feature_names()
        
        return self
    
    def transform(self, X):
        """Extract features from sequences"""
        sequences = [seq if isinstance(seq, str) else seq[0] for seq in X]
        features = []
        
        for seq in sequences:
            seq_features = self._extract_sequence_features(seq.upper())
            features.append(seq_features)
        
        return np.array(features)
    
    def _extract_sequence_features(self, sequence: str) -> List[float]:
        """Extract all features for a single sequence"""
        features = []
        
        # Basic composition features
        if self.include_composition:
            features.extend(self._get_composition_features(sequence))
        
        # K-mer features
        for k in self.kmer_sizes:
            features.extend(self._get_kmer_features(sequence, k))
        
        # Physicochemical properties
        if self.include_physicochemical:
            features.extend(self._get_physicochemical_features(sequence))
        
        # Structural features
        if self.include_structural:
            features.extend(self._get_structural_features(sequence))
        
        return features
    
    def _get_composition_features(self, sequence: str) -> List[float]:
        """Extract nucleotide composition features"""
        length = len(sequence)
        if length == 0:
            return [0.0] * 8
        
        features = []
        
        # Single nucleotide frequencies
        for nucleotide in 'ATCG':
            features.append(sequence.count(nucleotide) / length)
        
        # Dinucleotide frequencies (selected important ones)
        important_dinucs = ['AT', 'TA', 'CG', 'GC']
        for dinuc in important_dinucs:
            count = sum(1 for i in range(len(sequence) - 1) if sequence[i:i+2] == dinuc)
            features.append(count / max(1, length - 1))
        
        return features
    
    def _get_kmer_features(self, sequence: str, k: int) -> List[float]:
        """Extract k-mer frequency features"""
        if k not in self.kmer_vocabularies_:
            return [0.0] * self.max_features_per_kmer
        
        kmer_counts = Counter()
        total_kmers = 0
        
        for i in range(len(sequence) - k + 1):
            kmer = sequence[i:i+k]
            if re.match(r'^[ATCG]+$', kmer):
                kmer_counts[kmer] += 1
                total_kmers += 1
        
        features = []
        for kmer in self.kmer_vocabularies_[k]:
            frequency = kmer_counts.get(kmer, 0) / max(1, total_kmers)
            features.append(frequency)
        
        # Pad with zeros if necessary
        while len(features) < self.max_features_per_kmer:
            features.append(0.0)
        
        return features[:self.max_features_per_kmer]
    
    def _get_physicochemical_features(self, sequence: str) -> List[float]:
        """Extract physicochemical properties"""
        if len(sequence) == 0:
            return [0.0] * 6
        
        features = []
        
        # GC content
        gc_count = sequence.count('G') + sequence.count('C')
        features.append(gc_count / len(sequence))
        
        # Purine/Pyrimidine ratio
        purines = sequence.count('A') + sequence.count('G')
        pyrimidines = sequence.count('C') + sequence.count('T')
        ratio = purines / max(1, pyrimidines)
        features.append(min(ratio, 10.0))  # Cap extreme values
        
        # Melting temperature (simplified approximation)
        tm_simple = (gc_count * 4 + (len(sequence) - gc_count) * 2) / len(sequence)
        features.append(tm_simple / 100.0)  # Normalize
        
        # Complexity (Shannon entropy)
        entropy = self._calculate_entropy(sequence)
        features.append(entropy / 2.0)  # Normalize by log2(4)
        
        # Repeat content
        repeat_score = self._calculate_repeat_score(sequence)
        features.append(repeat_score)
        
        # CpG islands indicator
        cpg_score = self._calculate_cpg_score(sequence)
        features.append(cpg_score)
        
        return features
    
    def _get_structural_features(self, sequence: str) -> List[float]:
        """Extract structural features"""
        features = []
        
        # Length (log-transformed and normalized)
        log_length = np.log10(max(1, len(sequence))) / 6.0  # Normalize by log10(10^6)
        features.append(log_length)
        
        # ORF features
        max_orf_length, num_orfs = self._analyze_orfs(sequence)
        features.append(max_orf_length / max(1, len(sequence)))  # Relative max ORF length
        features.append(min(num_orfs / 10.0, 1.0))  # Normalized ORF count
        
        # Codon bias (if sequence length is multiple of 3)
        if len(sequence) % 3 == 0:
            codon_bias = self._calculate_codon_bias(sequence)
            features.append(codon_bias)
        else:
            features.append(0.0)
        
        # Periodicity (3-mer periodicity for coding sequences)
        periodicity = self._calculate_periodicity(sequence, period=3)
        features.append(periodicity)
        
        return features
    
    def _calculate_entropy(self, sequence: str) -> float:
        """Calculate Shannon entropy of sequence"""
        if len(sequence) == 0:
            return 0.0
        
        counts = Counter(sequence)
        probs = [count / len(sequence) for count in counts.values()]
        entropy = -sum(p * np.log2(p) for p in probs if p > 0)
        return entropy
    
    def _calculate_repeat_score(self, sequence: str) -> float:
        """Calculate repeat content score"""
        if len(sequence) < 6:
            return 0.0
        
        # Look for simple repeats (di- and tri-nucleotide)
        repeat_bases = 0
        
        # Check dinucleotide repeats
        for i in range(len(sequence) - 3):
            if sequence[i:i+2] == sequence[i+2:i+4]:
                repeat_bases += 2
        
        return min(repeat_bases / len(sequence), 1.0)
    
    def _calculate_cpg_score(self, sequence: str) -> float:
        """Calculate CpG island score"""
        if len(sequence) < 20:
            return 0.0
        
        # Count CpG dinucleotides
        cpg_count = sequence.count('CG')
        c_count = sequence.count('C')
        g_count = sequence.count('G')
        
        if c_count == 0 or g_count == 0:
            return 0.0
        
        # CpG ratio calculation
        expected_cpg = (c_count * g_count) / len(sequence)
        observed_cpg = cpg_count
        
        cpg_ratio = observed_cpg / max(1, expected_cpg)
        return min(cpg_ratio, 2.0) / 2.0  # Normalize
    
    def _analyze_orfs(self, sequence: str) -> Tuple[int, int]:
        """Analyze Open Reading Frames"""
        start_codons = ['ATG']
        stop_codons = ['TAA', 'TAG', 'TGA']
        
        max_orf_length = 0
        num_orfs = 0
        
        for frame in range(3):
            frame_seq = sequence[frame:]
            
            i = 0
            while i < len(frame_seq) - 2:
                codon = frame_seq[i:i+3]
                if len(codon) == 3 and codon in start_codons:
                    # Look for stop codon
                    j = i + 3
                    while j < len(frame_seq) - 2:
                        stop_codon = frame_seq[j:j+3]
                        if len(stop_codon) == 3 and stop_codon in stop_codons:
                            orf_length = j - i + 3
                            max_orf_length = max(max_orf_length, orf_length)
                            num_orfs += 1
                            i = j + 3
                            break
                        j += 3
                    else:
                        i += 3
                else:
                    i += 3
        
        return max_orf_length, num_orfs
    
    def _calculate_codon_bias(self, sequence: str) -> float:
        """Calculate codon usage bias"""
        if len(sequence) % 3 != 0:
            return 0.0
        
        # Extract codons
        codons = [sequence[i:i+3] for i in range(0, len(sequence), 3)]
        valid_codons = [c for c in codons if re.match(r'^[ATCG]{3}$', c)]
        
        if len(valid_codons) == 0:
            return 0.0
        
        # Calculate codon frequencies
        codon_counts = Counter(valid_codons)
        
        # Simple bias measure: how uneven is the distribution?
        max_freq = max(codon_counts.values())
        total_codons = len(valid_codons)
        
        bias_score = max_freq / total_codons
        return min(bias_score * 2, 1.0)  # Normalize
    
    def _calculate_periodicity(self, sequence: str, period: int = 3) -> float:
        """Calculate sequence periodicity"""
        if len(sequence) < period * 2:
            return 0.0
        
        correlations = []
        for shift in range(1, min(period + 1, len(sequence) // 2)):
            correlation = 0
            valid_comparisons = 0
            
            for i in range(len(sequence) - shift):
                if sequence[i] == sequence[i + shift]:
                    correlation += 1
                valid_comparisons += 1
            
            if valid_comparisons > 0:
                correlations.append(correlation / valid_comparisons)
        
        return max(correlations) if correlations else 0.0
    
    def _build_feature_names(self):
        """Build feature names for interpretability"""
        self.feature_names_ = []
        
        if self.include_composition:
            # Composition features
            for nucleotide in 'ATCG':
                self.feature_names_.append(f'{nucleotide}_freq')
            
            for dinuc in ['AT', 'TA', 'CG', 'GC']:
                self.feature_names_.append(f'{dinuc}_freq')
        
        # K-mer features
        for k in self.kmer_sizes:
            for i, kmer in enumerate(self.kmer_vocabularies_.get(k, [])):
                self.feature_names_.append(f'kmer_{k}_{kmer}')
            # Add padding names if needed
            while len([n for n in self.feature_names_ if f'kmer_{k}_' in n]) < self.max_features_per_kmer:
                idx = len([n for n in self.feature_names_ if f'kmer_{k}_' in n])
                self.feature_names_.append(f'kmer_{k}_feature_{idx}')
        
        if self.include_physicochemical:
            phys_features = ['gc_content', 'purine_pyrimidine_ratio', 'melting_temp', 
                           'entropy', 'repeat_content', 'cpg_score']
            self.feature_names_.extend(phys_features)
        
        if self.include_structural:
            struct_features = ['log_length', 'max_orf_ratio', 'orf_count', 
                             'codon_bias', 'periodicity']
            self.feature_names_.extend(struct_features)


class GeneClassifier(BaseEstimator, ClassifierMixin):
    """Specialized classifier for gene discovery and classification"""
    
    def __init__(self, 
                 feature_extractor: DNAFeatureExtractor = None,
                 base_classifier: str = 'random_forest',
                 **classifier_params):
        
        self.feature_extractor = feature_extractor or DNAFeatureExtractor()
        self.base_classifier = base_classifier
        self.classifier_params = classifier_params
        self.classifier_ = None
        self.scaler_ = StandardScaler()
        self.label_encoder_ = LabelEncoder()
        
    def fit(self, X, y):
        """Train the gene classifier"""
        # Extract features
        X_features = self.feature_extractor.fit_transform(X)
        
        # Scale features
        X_scaled = self.scaler_.fit_transform(X_features)
        
        # Encode labels
        y_encoded = self.label_encoder_.fit_transform(y)
        
        # Initialize classifier
        if self.base_classifier == 'random_forest':
            self.classifier_ = RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                **self.classifier_params
            )
        elif self.base_classifier == 'gradient_boosting':
            self.classifier_ = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                **self.classifier_params
            )
        elif self.base_classifier == 'svm':
            self.classifier_ = SVC(
                kernel='rbf',
                probability=True,
                **self.classifier_params
            )
        else:
            raise ValueError(f"Unsupported classifier: {self.base_classifier}")
        
        # Train classifier
        self.classifier_.fit(X_scaled, y_encoded)
        
        return self
    
    def predict(self, X):
        """Predict gene classes"""
        X_features = self.feature_extractor.transform(X)
        X_scaled = self.scaler_.transform(X_features)
        y_pred_encoded = self.classifier_.predict(X_scaled)
        return self.label_encoder_.inverse_transform(y_pred_encoded)
    
    def predict_proba(self, X):
        """Predict class probabilities"""
        X_features = self.feature_extractor.transform(X)
        X_scaled = self.scaler_.transform(X_features)
        return self.classifier_.predict_proba(X_scaled)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores"""
        if hasattr(self.classifier_, 'feature_importances_'):
            importance_scores = self.classifier_.feature_importances_
            feature_names = self.feature_extractor.feature_names_
            
            return dict(zip(feature_names, importance_scores))
        else:
            return {}


class PathogenDetector(BaseEstimator, ClassifierMixin):
    """Specialized detector for pathogenic sequences"""
    
    def __init__(self):
        self.feature_extractor = DNAFeatureExtractor(
            kmer_sizes=[4, 5, 6],  # Longer k-mers for pathogen signatures
            max_features_per_kmer=50
        )
        self.classifier = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=3,
            class_weight='balanced'
        )
        self.scaler = StandardScaler()
        
    def fit(self, X, y):
        """Train pathogen detector"""
        # Extract pathogen-specific features
        X_features = self._extract_pathogen_features(X)
        X_scaled = self.scaler.fit_transform(X_features)
        
        self.classifier.fit(X_scaled, y)
        return self
    
    def predict(self, X):
        """Predict pathogen presence"""
        X_features = self._extract_pathogen_features(X)
        X_scaled = self.scaler.transform(X_features)
        return self.classifier.predict(X_scaled)
    
    def predict_proba(self, X):
        """Predict pathogen probability"""
        X_features = self._extract_pathogen_features(X)
        X_scaled = self.scaler.transform(X_features)
        return self.classifier.predict_proba(X_scaled)
    
    def _extract_pathogen_features(self, X):
        """Extract features specific to pathogen detection"""
        sequences = [seq if isinstance(seq, str) else seq[0] for seq in X]
        
        # Use base feature extractor
        base_features = self.feature_extractor.fit_transform(sequences)
        
        # Add pathogen-specific features
        pathogen_features = []
        for seq in sequences:
            seq = seq.upper()
            
            # Virulence factor signatures
            virulence_score = self._calculate_virulence_score(seq)
            
            # Antibiotic resistance signatures
            resistance_score = self._calculate_resistance_score(seq)
            
            # Phylogenetic markers
            phylo_score = self._calculate_phylogenetic_markers(seq)
            
            # Host interaction patterns
            host_interaction = self._calculate_host_interaction_score(seq)
            
            pathogen_features.append([
                virulence_score, resistance_score, 
                phylo_score, host_interaction
            ])
        
        # Combine features
        pathogen_features = np.array(pathogen_features)
        combined_features = np.hstack([base_features, pathogen_features])
        
        return combined_features
    
    def _calculate_virulence_score(self, sequence: str) -> float:
        """Calculate virulence factor score"""
        virulence_motifs = [
            'TTSS',    # Type III secretion system
            'INVASIN', # Invasion proteins
            'TOXIN',   # Toxin signatures
            'ADHESIN'  # Adhesion factors
        ]
        
        score = 0
        for motif in virulence_motifs:
            if motif in sequence:
                score += 1
        
        return score / len(virulence_motifs)
    
    def _calculate_resistance_score(self, sequence: str) -> float:
        """Calculate antibiotic resistance score"""
        resistance_patterns = [
            'BLACTAM',    # Beta-lactamase
            'AMINOGLY',   # Aminoglycoside resistance
            'TETRACYC',   # Tetracycline resistance
            'VANCOMYC'    # Vancomycin resistance
        ]
        
        score = 0
        for pattern in resistance_patterns:
            if pattern in sequence:
                score += 1
        
        return score / len(resistance_patterns)
    
    def _calculate_phylogenetic_markers(self, sequence: str) -> float:
        """Calculate phylogenetic marker score"""
        # 16S rRNA signatures for bacterial identification
        ribosomal_motifs = [
            'ACCTGGTTGATCCTGCCAG',  # 16S signature
            'TTGACA',               # -35 promoter
            'TATAAT'                # -10 promoter (Pribnow box)
        ]
        
        score = 0
        for motif in ribosomal_motifs:
            if motif in sequence:
                score += sequence.count(motif)
        
        return min(score / 10.0, 1.0)  # Normalize
    
    def _calculate_host_interaction_score(self, sequence: str) -> float:
        """Calculate host interaction potential"""
        # Patterns associated with host cell interaction
        host_motifs = [
            'RGD',     # Cell adhesion motif
            'NPXY',    # Endocytosis signal
            'YXXL'     # Tyrosine-based motif
        ]
        
        score = 0
        for motif in host_motifs:
            score += sequence.count(motif)
        
        return min(score / 5.0, 1.0)  # Normalize


class DrugTargetPredictor(BaseEstimator, ClassifierMixin):
    """Predict druggable targets from protein sequences"""
    
    def __init__(self):
        self.feature_extractor = DNAFeatureExtractor(
            kmer_sizes=[3, 4, 5],
            include_physicochemical=True,
            include_structural=True
        )
        self.classifier = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.05,
            max_depth=8
        )
        self.scaler = StandardScaler()
        
    def fit(self, X, y):
        """Train drug target predictor"""
        # Convert DNA to protein sequences
        protein_sequences = [self._translate_to_protein(seq) for seq in X]
        
        # Extract drug target features
        X_features = self._extract_drug_target_features(protein_sequences)
        X_scaled = self.scaler.fit_transform(X_features)
        
        self.classifier.fit(X_scaled, y)
        return self
    
    def predict(self, X):
        """Predict drug target potential"""
        protein_sequences = [self._translate_to_protein(seq) for seq in X]
        X_features = self._extract_drug_target_features(protein_sequences)
        X_scaled = self.scaler.transform(X_features)
        return self.classifier.predict(X_scaled)
    
    def predict_proba(self, X):
        """Predict drug target probability"""
        protein_sequences = [self._translate_to_protein(seq) for seq in X]
        X_features = self._extract_drug_target_features(protein_sequences)
        X_scaled = self.scaler.transform(X_features)
        return self.classifier.predict_proba(X_scaled)
    
    def _translate_to_protein(self, dna_sequence: str) -> str:
        """Translate DNA to protein sequence"""
        genetic_code = {
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
        
        protein = ""
        dna_sequence = dna_sequence.upper().replace('U', 'T')
        
        for i in range(0, len(dna_sequence) - 2, 3):
            codon = dna_sequence[i:i+3]
            if len(codon) == 3 and codon in genetic_code:
                aa = genetic_code[codon]
                if aa != '*':  # Stop codon
                    protein += aa
                else:
                    break
        
        return protein
    
    def _extract_drug_target_features(self, protein_sequences: List[str]) -> np.ndarray:
        """Extract drug target specific features"""
        features = []
        
        for protein in protein_sequences:
            if not protein:
                # Handle empty proteins
                features.append([0.0] * 15)
                continue
            
            protein_features = []
            
            # Amino acid composition features
            aa_composition = self._calculate_aa_composition(protein)
            protein_features.extend(aa_composition)
            
            # Drug target specific features
            hydrophobicity = self._calculate_hydrophobicity(protein)
            charge_distribution = self._calculate_charge_distribution(protein)
            secondary_structure = self._predict_secondary_structure(protein)
            binding_potential = self._calculate_binding_potential(protein)
            
            protein_features.extend([
                hydrophobicity, charge_distribution, 
                secondary_structure, binding_potential
            ])
            
            features.append(protein_features)
        
        return np.array(features)
    
    def _calculate_aa_composition(self, protein: str) -> List[float]:
        """Calculate amino acid composition"""
        if not protein:
            return [0.0] * 20
        
        # 20 standard amino acids
        amino_acids = 'ACDEFGHIKLMNPQRSTVWY'
        composition = []
        
        for aa in amino_acids:
            frequency = protein.count(aa) / len(protein)
            composition.append(frequency)
        
        return composition
    
    def _calculate_hydrophobicity(self, protein: str) -> float:
        """Calculate average hydrophobicity"""
        if not protein:
            return 0.0
        
        # Hydrophobicity scale (Kyte-Doolittle)
        hydrophobicity_scale = {
            'A': 1.8, 'C': 2.5, 'D': -3.5, 'E': -3.5, 'F': 2.8,
            'G': -0.4, 'H': -3.2, 'I': 4.5, 'K': -3.9, 'L': 3.8,
            'M': 1.9, 'N': -3.5, 'P': -1.6, 'Q': -3.5, 'R': -4.5,
            'S': -0.8, 'T': -0.7, 'V': 4.2, 'W': -0.9, 'Y': -1.3
        }
        
        total_hydrophobicity = sum(hydrophobicity_scale.get(aa, 0) for aa in protein)
        return total_hydrophobicity / len(protein)
    
    def _calculate_charge_distribution(self, protein: str) -> float:
        """Calculate charge distribution"""
        if not protein:
            return 0.0
        
        positive_charges = protein.count('K') + protein.count('R') + protein.count('H')
        negative_charges = protein.count('D') + protein.count('E')
        
        net_charge = positive_charges - negative_charges
        return net_charge / len(protein)
    
    def _predict_secondary_structure(self, protein: str) -> float:
        """Predict secondary structure propensity"""
        if not protein:
            return 0.0
        
        # Simple secondary structure propensities
        helix_formers = 'AEHKQR'
        sheet_formers = 'FILVWY'
        
        helix_propensity = sum(1 for aa in protein if aa in helix_formers) / len(protein)
        sheet_propensity = sum(1 for aa in protein if aa in sheet_formers) / len(protein)
        
        return helix_propensity + sheet_propensity  # Combined structural propensity
    
    def _calculate_binding_potential(self, protein: str) -> float:
        """Calculate drug binding potential"""
        if not protein:
            return 0.0
        
        # Look for potential binding motifs
        binding_motifs = ['ATP', 'GTP', 'NAD', 'FAD', 'KINASE', 'DOMAIN']
        binding_score = 0
        
        for motif in binding_motifs:
            if motif in protein:
                binding_score += 1
        
        # Also consider aromatic and hydrophobic residues for binding pockets
        aromatic_residues = protein.count('F') + protein.count('W') + protein.count('Y')
        hydrophobic_residues = protein.count('I') + protein.count('L') + protein.count('V')
        
        pocket_potential = (aromatic_residues + hydrophobic_residues) / len(protein)
        
        return (binding_score / len(binding_motifs)) + pocket_potential


class BiomarkerDiscoverer:
    """Discover biomarkers from DNA sequences using machine learning"""
    
    def __init__(self):
        self.feature_extractor = DNAFeatureExtractor(
            kmer_sizes=[4, 5, 6, 7],
            max_features_per_kmer=200
        )
        self.classifier = RandomForestClassifier(
            n_estimators=500,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            bootstrap=True,
            oob_score=True
        )
        self.scaler = StandardScaler()
        
    def discover_biomarkers(self, 
                          sequences: List[str], 
                          labels: List[str],
                          validation_split: float = 0.2) -> Dict[str, Any]:
        """Discover discriminative biomarkers"""
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            sequences, labels, test_size=validation_split, 
            random_state=42, stratify=labels
        )
        
        # Extract features
        X_train_features = self.feature_extractor.fit_transform(X_train)
        X_val_features = self.feature_extractor.transform(X_val)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train_features)
        X_val_scaled = self.scaler.transform(X_val_features)
        
        # Train classifier
        self.classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.classifier.score(X_train_scaled, y_train)
        val_score = self.classifier.score(X_val_scaled, y_val)
        
        # Get feature importance
        feature_importance = self.classifier.feature_importances_
        feature_names = self.feature_extractor.feature_names_
        
        # Identify top biomarkers
        importance_pairs = list(zip(feature_names, feature_importance))
        importance_pairs.sort(key=lambda x: x[1], reverse=True)
        
        top_biomarkers = importance_pairs[:50]  # Top 50 features
        
        # Cross-validation
        cv_scores = cross_val_score(self.classifier, X_train_scaled, y_train, cv=5)
        
        results = {
            'biomarkers': [
                {'feature': name, 'importance': importance} 
                for name, importance in top_biomarkers
            ],
            'model_performance': {
                'training_accuracy': train_score,
                'validation_accuracy': val_score,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'oob_score': self.classifier.oob_score_ if hasattr(self.classifier, 'oob_score_') else None
            },
            'feature_statistics': {
                'total_features': len(feature_names),
                'selected_features': len(top_biomarkers),
                'mean_importance': np.mean(feature_importance),
                'std_importance': np.std(feature_importance)
            }
        }
        
        return results
    
    def predict_biomarker_class(self, sequences: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """Predict class and probabilities for new sequences"""
        X_features = self.feature_extractor.transform(sequences)
        X_scaled = self.scaler.transform(X_features)
        
        predictions = self.classifier.predict(X_scaled)
        probabilities = self.classifier.predict_proba(X_scaled)
        
        return predictions, probabilities


# Factory function to create specialized models
def create_dna_model(model_type: str, **kwargs):
    """Factory function to create specialized DNA analysis models"""
    
    if model_type == 'gene_classifier':
        return GeneClassifier(**kwargs)
    elif model_type == 'pathogen_detector':
        return PathogenDetector()
    elif model_type == 'drug_target_predictor':
        return DrugTargetPredictor()
    elif model_type == 'biomarker_discoverer':
        return BiomarkerDiscoverer()
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


# Ensemble model for comprehensive analysis
class ComprehensiveDNAAnalyzer:
    """Ensemble model combining multiple specialized DNA analysis models"""
    
    def __init__(self):
        self.models = {
            'gene_classifier': GeneClassifier(),
            'pathogen_detector': PathogenDetector(),
            'drug_target_predictor': DrugTargetPredictor(),
            'biomarker_discoverer': BiomarkerDiscoverer()
        }
        self.trained_models = {}
    
    def fit(self, sequences: List[str], 
            gene_labels: List[str] = None,
            pathogen_labels: List[str] = None,
            drug_target_labels: List[str] = None,
            biomarker_labels: List[str] = None):
        """Train all specialized models"""
        
        if gene_labels:
            logger.info("Training gene classifier...")
            self.trained_models['gene_classifier'] = self.models['gene_classifier'].fit(
                sequences, gene_labels
            )
        
        if pathogen_labels:
            logger.info("Training pathogen detector...")
            self.trained_models['pathogen_detector'] = self.models['pathogen_detector'].fit(
                sequences, pathogen_labels
            )
        
        if drug_target_labels:
            logger.info("Training drug target predictor...")
            self.trained_models['drug_target_predictor'] = self.models['drug_target_predictor'].fit(
                sequences, drug_target_labels
            )
        
        if biomarker_labels:
            logger.info("Training biomarker discoverer...")
            biomarker_results = self.models['biomarker_discoverer'].discover_biomarkers(
                sequences, biomarker_labels
            )
            self.trained_models['biomarker_discoverer'] = biomarker_results
        
        return self
    
    def analyze_sequences(self, sequences: List[str]) -> Dict[str, Any]:
        """Perform comprehensive analysis on sequences"""
        results = {}
        
        for model_name, model in self.trained_models.items():
            logger.info(f"Running {model_name} analysis...")
            
            try:
                if model_name == 'biomarker_discoverer':
                    # Special handling for biomarker results
                    predictions, probabilities = self.models[model_name].predict_biomarker_class(sequences)
                    results[model_name] = {
                        'predictions': predictions.tolist(),
                        'probabilities': probabilities.tolist()
                    }
                else:
                    predictions = model.predict(sequences)
                    probabilities = model.predict_proba(sequences)
                    results[model_name] = {
                        'predictions': predictions.tolist(),
                        'probabilities': probabilities.tolist()
                    }
            except Exception as e:
                logger.error(f"Error in {model_name}: {e}")
                results[model_name] = {'error': str(e)}
        
        return results
    
    def save_models(self, directory_path: str):
        """Save all trained models"""
        import os
        os.makedirs(directory_path, exist_ok=True)
        
        for model_name, model in self.trained_models.items():
            model_path = os.path.join(directory_path, f"{model_name}.joblib")
            joblib.dump(model, model_path)
            logger.info(f"Saved {model_name} to {model_path}")
    
    def load_models(self, directory_path: str):
        """Load pre-trained models"""
        import os
        
        for model_name in self.models.keys():
            model_path = os.path.join(directory_path, f"{model_name}.joblib")
            if os.path.exists(model_path):
                self.trained_models[model_name] = joblib.load(model_path)
                logger.info(f"Loaded {model_name} from {model_path}")