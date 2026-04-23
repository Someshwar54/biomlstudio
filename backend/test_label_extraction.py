"""Test label extraction from FASTA headers"""
from app.utils.bioinformatics import extract_label_from_header

# Test cases
test_headers = [
    ("seq1 Cancer_sample", "affected"),
    ("seq2 Normal_sample", "normal"),
    ("seq3 tumor", "affected"),
    ("seq4 healthy", "normal"),
    ("seq5|cancer", "affected"),
    ("seq6|control", "normal"),
    ("seq7_diseased", "affected"),
    ("seq8_wildtype", "normal"),
    ("seq9 custom_label", "custom_label"),
    ("seq10", "unknown")
]

print("Testing label extraction from FASTA headers:")
print("=" * 60)

passed = 0
failed = 0

for header, expected in test_headers:
    result = extract_label_from_header(header)
    status = "✅" if result == expected else "❌"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} '{header}' → '{result}' (expected: '{expected}')")

print("=" * 60)
print(f"Results: {passed} passed, {failed} failed")
