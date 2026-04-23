"""Test script to verify dataset analysis returns correct stats"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.dataset_service import DatasetService


async def test_fasta_analysis():
    """Test FASTA file analysis"""
    service = DatasetService()
    
    # Test file path
    test_file = Path(__file__).parent.parent / "test_dna_sequences.fasta"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"Testing FASTA analysis: {test_file.name}")
    print("-" * 60)
    
    try:
        # Analyze the dataset
        stats = await service.analyze_dataset(test_file, "dna")
        
        print(f"✅ Analysis completed successfully!")
        print(f"\nStats returned:")
        for key, value in stats.items():
            if key != "nucleotide_composition":
                print(f"  {key}: {value}")
        
        # Check for required keys
        required_keys = ["total_rows", "sequence_count", "format"]
        missing_keys = [key for key in required_keys if key not in stats]
        
        if missing_keys:
            print(f"\n❌ Missing required keys: {missing_keys}")
            return False
        
        # Verify total_rows matches sequence_count
        if stats["total_rows"] != stats["sequence_count"]:
            print(f"\n❌ Mismatch: total_rows={stats['total_rows']}, sequence_count={stats['sequence_count']}")
            return False
        
        # Verify we found sequences
        if stats["total_rows"] == 0:
            print(f"\n❌ No sequences found (total_rows=0)")
            return False
        
        print(f"\n✅ All checks passed!")
        print(f"   - Found {stats['total_rows']} sequences")
        print(f"   - Format: {stats['format']}")
        print(f"   - Avg length: {stats.get('avg_sequence_length', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_preview():
    """Test dataset preview"""
    service = DatasetService()
    
    test_file = Path(__file__).parent.parent / "test_dna_sequences.fasta"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"\n\nTesting dataset preview")
    print("-" * 60)
    
    try:
        preview_data = await service.preview_dataset(str(test_file), "dna", rows=5)
        
        print(f"✅ Preview generated successfully!")
        print(f"   - Preview rows: {len(preview_data)}")
        
        if preview_data:
            print(f"   - Columns: {list(preview_data[0].keys())}")
            print(f"\nFirst row preview:")
            for key, value in list(preview_data[0].items())[:5]:
                print(f"     {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during preview: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("Dataset Service Test Suite")
    print("=" * 60)
    
    analysis_passed = await test_fasta_analysis()
    preview_passed = await test_preview()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Analysis: {'✅ PASSED' if analysis_passed else '❌ FAILED'}")
    print(f"  Preview:  {'✅ PASSED' if preview_passed else '❌ FAILED'}")
    print("=" * 60)
    
    return analysis_passed and preview_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
