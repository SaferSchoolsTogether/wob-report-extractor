"""
Test script to verify the text cleaning functionality for removing PDF formatting characters
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extractor_engine import SmartExtractor
from config_manager import ConfigManager

def test_text_cleaning():
    """Test the clean_extracted_text method with various formatting scenarios"""
    
    # Initialize the extractor
    config = ConfigManager()
    extractor = SmartExtractor(config, debug_mode=True)
    
    # Test cases with different formatting patterns
    test_cases = [
        # (input, expected_output, description)
        ("Kiera Triplett ....................", "Kiera Triplett", "Name with dots"),
        ("Central High School ...............", "Central High School", "School with dots"),
        ("Vancouver .........................", "Vancouver", "Location with dots"),
        ("Gang ABC ..........................", "Gang ABC", "SOC affiliation with dots"),
        
        # Test with middle dots (unicode)
        ("John Smith ···················", "John Smith", "Name with middle dots"),
        
        # Test with underscores
        ("Jane Doe ____________________", "Jane Doe", "Name with underscores"),
        
        # Test with dashes
        ("Oak Ridge School -------------", "Oak Ridge School", "School with dashes"),
        
        # Test with mixed formatting
        ("Test Name ....___....", "Test Name", "Mixed dots and underscores"),
        
        # Test with sequences in the middle
        ("Part1.......Part2", "Part1Part2", "Dots in the middle"),
        ("Part1_______Part2", "Part1Part2", "Underscores in the middle"),
        ("Part1-------Part2", "Part1Part2", "Dashes in the middle"),
        
        # Test with normal text (shouldn't change)
        ("Normal Name", "Normal Name", "Normal text without formatting"),
        ("Dr. John Smith", "Dr. John Smith", "Name with period (should keep)"),
        ("St. Mary's School", "St. Mary's School", "School with apostrophe and period"),
        
        # Test with multiple spaces
        ("Name    with    spaces", "Name with spaces", "Multiple spaces"),
        
        # Test edge cases
        ("", "", "Empty string"),
        ("...", "", "Only dots"),
        ("___", "", "Only underscores"),
        ("---", "", "Only dashes"),
        ("   ", "", "Only spaces"),
        
        # Real-world examples from PDFs
        ("Kiera Triplett .................................................................................. 5", 
         "Kiera Triplett 5", "Name with dots and page number"),
        ("Central High School ................................................ Vancouver", 
         "Central High School Vancouver", "School and location with dots"),
    ]
    
    print("Testing Text Cleaning Functionality")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for input_text, expected, description in test_cases:
        result = extractor.clean_extracted_text(input_text)
        
        if result == expected:
            print(f"✓ PASS: {description}")
            print(f"  Input:    '{input_text}'")
            print(f"  Output:   '{result}'")
            passed += 1
        else:
            print(f"✗ FAIL: {description}")
            print(f"  Input:    '{input_text}'")
            print(f"  Expected: '{expected}'")
            print(f"  Got:      '{result}'")
            failed += 1
        print()
    
    print("=" * 80)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✓ All tests passed successfully!")
    else:
        print(f"✗ {failed} test(s) failed. Please review the cleaning logic.")
    
    return failed == 0

def test_extraction_with_cleaning():
    """Test actual extraction with sample text containing formatting"""
    
    config = ConfigManager()
    extractor = SmartExtractor(config, debug_mode=True)
    
    # Sample section text that mimics PDF format
    sample_section = """Kiera Triplett ....................................................................................
Location: Vancouver .............................................................................
School: Central High School .....................................................................
SOC Affiliation: Gang ABC .......................................................................

☒ Mental Health Concerns
☒ Weapons
☐ Firearms
"""
    
    print("\n" + "=" * 80)
    print("Testing Extraction with Cleaning")
    print("=" * 80)
    
    record = extractor.extract_record_from_section(sample_section)
    
    print("\nExtracted Record:")
    print(f"  Name: '{record.get('name', 'N/A')}'")
    print(f"  Location: '{record.get('location', 'N/A')}'")
    print(f"  School: '{record.get('school', 'N/A')}'")
    print(f"  SOC Affiliation: '{record.get('soc_affiliation', 'N/A')}'")
    print(f"  Concerns: {record.get('concerns', {})}")
    
    # Verify the cleaning worked
    assert record.get('name') == 'Kiera Triplett', f"Name not cleaned properly: {record.get('name')}"
    assert record.get('location') == 'Vancouver', f"Location not cleaned properly: {record.get('location')}"
    assert record.get('school') == 'Central High School', f"School not cleaned properly: {record.get('school')}"
    assert record.get('soc_affiliation') == 'Gang ABC', f"SOC Affiliation not cleaned properly: {record.get('soc_affiliation')}"
    
    print("\n✓ Extraction with cleaning successful!")

if __name__ == "__main__":
    # Run the tests
    success = test_text_cleaning()
    
    if success:
        test_extraction_with_cleaning()
    
    print("\n" + "=" * 80)
    print("Testing complete!")
