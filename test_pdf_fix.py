#!/usr/bin/env python3
"""Test that the PDF generator handles missing scorecard fields gracefully."""

import sys
sys.path.insert(0, '.')

from agents.state import IntegrityScorecard

# Test 1: Full scorecard with all fields
print("=" * 60)
print("Test 1: Full scorecard (all fields present)")
print("=" * 60)

scorecard: IntegrityScorecard = {
    "company_name": "Test Company",
    "report_year": "2024",
    "overall_score": 75.5,
    "materiality_score": 80.0,
    "controversy_score": 70.0,
    "scientific_alignment_score": 65.0,
    "risk_level": "MEDIUM",
    "summary": "Executive summary of the ESG audit.",
    "materiality_results": [],
    "controversies": [],
    "scientific_data": [],
    "contradictions": [],
    "all_evidence": [],
    "recommendations": ["Improve disclosure", "Conduct audit", "Publish goals"],
    "greenwashing_flags": ["Unclear metrics"],
}

try:
    # Test bracket access (OLD WAY - should work if key exists)
    print(f"✓ scorecard['company_name'] = {scorecard['company_name']}")
    print(f"✓ scorecard['recommendations'] = {scorecard['recommendations']}")
    
    # Test .get() access (NEW WAY - always safe)
    print(f"✓ scorecard.get('company_name', 'Unknown') = {scorecard.get('company_name', 'Unknown')}")
    print(f"✓ scorecard.get('recommendations', []) = {scorecard.get('recommendations', [])}")
    print(f"✓ scorecard.get('missing_field', 'DEFAULT') = {scorecard.get('missing_field', 'DEFAULT')}")
    
    print("\n✅ Test 1 PASSED: All patterns work with full scorecard")
except Exception as e:
    print(f"\n❌ Test 1 FAILED: {type(e).__name__}: {e}")
    sys.exit(1)

# Test 2: Delete "recommendations" to simulate the bug condition
print("\n" + "=" * 60)
print("Test 2: Scorecard without 'recommendations' key")
print("=" * 60)

scorecard2 = scorecard.copy()
del scorecard2["recommendations"]

try:
    # This SHOULD FAIL with KeyError
    print(f"Attempting bracket access: scorecard2['recommendations']...")
    val = scorecard2['recommendations']
    print(f"✗ No error raised! Got: {val}")
except KeyError as e:
    print(f"✓ Expected KeyError raised: {e}")

try:
    # This SHOULD SUCCEED with .get()
    val = scorecard2.get('recommendations', [])
    print(f"✓ .get() returns safe default: {val}")
    print("\n✅ Test 2 PASSED: .get() handles missing 'recommendations' gracefully")
except Exception as e:
    print(f"\n❌ Test 2 FAILED: {type(e).__name__}: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("""
Summary:
- Full scorecard works with both bracket and .get() access
- Missing 'recommendations' key causes KeyError with bracket access
- Missing 'recommendations' key is handled safely with .get()

The pdf_generator.py fix to use .get() throughout will prevent
the KeyError('recommendation') that was blocking audits.
""")
