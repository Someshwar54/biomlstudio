#!/usr/bin/env python3
"""
Quick test to verify FASTA conversion works correctly
Run this from the backend directory: python test_fasta_conversion.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.bioinformatics import convert_fasta_to_csv
import tempfile
import pandas as pd

def test_fasta_conversion():
    print("Testing FASTA to CSV conversion...")
    
    # Path to test FASTA file
    fasta_path = "../test_dna_sequences.fasta"
    
    if not Path(fasta_path).exists():
        print(f"❌ Test file not found: {fasta_path}")
        return False
    
    # Create temp CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_csv:
        temp_csv_path = temp_csv.name
    
    try:
        # Convert FASTA
        config = {
            'add_composition': True,
            'add_kmers': True,
            'kmer_size': 3,
            'max_sequences': 100
        }
        
        print(f"\nConverting {fasta_path}...")
        result = convert_fasta_to_csv(fasta_path, temp_csv_path, config)
        
        if not result['success']:
            print(f"❌ Conversion failed: {result.get('error')}")
            return False
        
        print(f"✅ Conversion successful!")
        print(f"   Sequences converted: {result['sequences_converted']}")
        print(f"   Output columns: {len(result['columns'])}")
        
        # Load and verify CSV
        df = pd.read_csv(temp_csv_path)
        print(f"\nCSV loaded successfully:")
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)[:10]}...")
        
        # Check for required columns
        required_cols = ['label', 'length', 'gc_content']
        kmer_cols = [col for col in df.columns if col.startswith('kmer_')]
        
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            print(f"❌ Missing required columns: {missing}")
            return False
        
        print(f"\n✅ All required columns present:")
        print(f"   - label: {df['label'].nunique()} unique values")
        print(f"   - length: {df['length'].min()}-{df['length'].max()} bp")
        print(f"   - gc_content: {df['gc_content'].min():.1f}-{df['gc_content'].max():.1f}%")
        print(f"   - k-mer features: {len(kmer_cols)} features")
        print(f"   - Example k-mers: {kmer_cols[:5]}")
        
        # Check for bad columns (FASTA headers)
        bad_cols = [col for col in df.columns if col.startswith('>')]
        if bad_cols:
            print(f"❌ Found FASTA headers in columns: {bad_cols}")
            return False
        
        print(f"\n✅ No FASTA headers in columns")
        
        # Preview first row
        print(f"\nFirst row preview:")
        print(df.head(1).to_dict('records')[0])
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if Path(temp_csv_path).exists():
            Path(temp_csv_path).unlink()

if __name__ == '__main__':
    success = test_fasta_conversion()
    
    if success:
        print("\n" + "="*60)
        print("✅ FASTA CONVERSION TEST PASSED")
        print("="*60)
        print("\nYour FASTA conversion is working correctly!")
        print("The demo should work properly now.")
    else:
        print("\n" + "="*60)
        print("❌ FASTA CONVERSION TEST FAILED")
        print("="*60)
        print("\nCheck the errors above and fix before demo.")
    
    sys.exit(0 if success else 1)
