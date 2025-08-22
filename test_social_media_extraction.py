"""
Test script to verify social media extraction with User IDs and Other concerns
"""

import os
import sys
from config_manager import ConfigManager
from extractor_engine import SmartExtractor
from output_generator import OutputGenerator
import pprint

def test_extraction():
    """Test the extraction with a sample PDF"""
    
    # Initialize components
    config_manager = ConfigManager()
    extractor = SmartExtractor(config_manager, debug_mode=True)
    output_gen = OutputGenerator()
    
    # Test PDF path - update this to your test PDF location
    test_pdf = "c:/Users/sstan/OneDrive/Documents/01 PDF/Palm Springs USD WOB Report - August 2025.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ Test PDF not found at: {test_pdf}")
        print("Please update the test_pdf path in this script to point to your sample PDF")
        return
    
    print(f"📄 Testing extraction on: {os.path.basename(test_pdf)}")
    print("=" * 60)
    
    # Extract data from PDF
    result = extractor.extract_from_pdf(test_pdf)
    
    if 'error' in result:
        print(f"❌ Error extracting PDF: {result['error']}")
        return
    
    # Display extracted records
    records = result.get('records', [])
    print(f"\n✅ Found {len(records)} records")
    
    for i, record in enumerate(records, 1):
        print(f"\n{'='*60}")
        print(f"RECORD {i}: {record.get('name', 'Unknown')}")
        print(f"{'='*60}")
        
        # Basic info
        print(f"📍 School: {record.get('school', 'N/A')}")
        print(f"📍 Location: {record.get('location', 'N/A')}")
        print(f"📍 SOC Affiliation: {record.get('soc_affiliation', 'N/A')}")
        
        # Concerns
        concerns = record.get('concerns', {})
        checked_concerns = [k for k, v in concerns.items() if v]
        if checked_concerns:
            print(f"\n⚠️ Concerns Checked:")
            for concern in checked_concerns:
                print(f"  • {concern}")
        
        # Check for "Other" concern
        if record.get('other_concern'):
            print(f"\n⚠️ Other Concern: {record.get('other_concern_text', '')}")
        
        # Social Media
        social_media = record.get('social_media', [])
        if social_media:
            print(f"\n📱 Social Media Accounts ({len(social_media)}):")
            for sm in social_media:
                print(f"\n  Platform: {sm.get('platform', 'N/A')}")
                print(f"  Display Name: {sm.get('display_name', 'N/A')}")
                print(f"  Username: {sm.get('username', 'N/A')}")
                print(f"  User ID: {sm.get('user_id', 'N/A')}")  # This should now be captured
                print(f"  URL: {sm.get('url', 'N/A')}")
        else:
            print(f"\n📱 No social media accounts found")
    
    # Test output generation
    print(f"\n{'='*60}")
    print("TESTING OUTPUT GENERATION")
    print(f"{'='*60}")
    
    # Create test output folder
    output_folder = "./test_output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Generate reports
    month_year = "August 2025"
    files_created, platform_stats = output_gen.generate_reports(
        [result], output_folder, month_year
    )
    
    print(f"\n📁 Files Created:")
    for file_type, count, filepath in files_created:
        filename = os.path.basename(filepath) if isinstance(filepath, str) else 'Generated'
        print(f"  • {file_type}: {count} records → {filename}")
    
    if platform_stats:
        print(f"\n📊 Platform Statistics:")
        for platform, count in sorted(platform_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {platform}: {count} accounts")
    
    print(f"\n✅ Test complete! Check the '{output_folder}' folder for generated files.")
    
    # Display extraction quality
    quality_report = extractor.get_extraction_quality_report()
    if quality_report['field_success_rates']:
        print(f"\n📈 Field Extraction Success Rates:")
        for field, stats in quality_report['field_success_rates'].items():
            print(f"  • {field}: {stats['success_rate']}")

def test_specific_text():
    """Test extraction on specific text snippets"""
    
    print("\n" + "="*60)
    print("TESTING SPECIFIC TEXT EXTRACTION")
    print("="*60)
    
    config_manager = ConfigManager()
    extractor = SmartExtractor(config_manager, debug_mode=False)
    
    # Test social media extraction with ID
    test_section = """
Instagram Information & Activity
Instagram Display Name: yahirel
Instagram Username: flaco7sixtyy
Instagram ID: 53068315237
Instagram URL: https://www.instagram.com/flaco7sixtyy/
    """
    
    print("\nTest: Instagram with ID")
    print("-" * 30)
    sm_data = extractor.extract_platform_data(test_section, "Instagram")
    if sm_data:
        print(f"✅ Extracted:")
        for key, value in sm_data.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Failed to extract Instagram data")
    
    # Test Other concern extraction
    test_concern_section = """
☒ Firearms
☐ Weapons
☒ Other: Student making threats on Discord
    """
    
    print("\nTest: Other Concern with Text")
    print("-" * 30)
    
    # Check for Other concern
    other_patterns = [
        r'☒\s*Other:\s*(.+?)(?:\n|$)',
        r'\[X\]\s*Other:\s*(.+?)(?:\n|$)',
    ]
    
    for pattern in other_patterns:
        import re
        other_match = re.search(pattern, test_concern_section, re.IGNORECASE)
        if other_match:
            other_text = other_match.group(1).strip()
            print(f"✅ Found 'Other' concern: {other_text}")
            break
    else:
        print("❌ Failed to extract Other concern")

if __name__ == "__main__":
    print("WOB Report Extractor - Social Media & Other Concerns Test")
    print("="*60)
    
    # Run tests
    test_extraction()
    test_specific_text()
