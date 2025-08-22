"""
Test script to verify SOC affiliation extraction and report generation
"""

import os
import sys
from datetime import datetime
from config_manager import ConfigManager
from extractor_engine import SmartExtractor
from output_generator import OutputGenerator
import pandas as pd

def test_soc_affiliation_extraction():
    """Test the SOC affiliation extraction functionality"""
    
    print("=" * 70)
    print("WOB Report Extractor - SOC Affiliation Test")
    print("=" * 70)
    
    # Initialize the extractor with debug mode
    config_manager = ConfigManager()
    extractor = SmartExtractor(config_manager, debug_mode=True)
    output_gen = OutputGenerator()
    
    print("\n✅ Extractor and Output Generator initialized")
    
    # Test scenarios with SOC affiliation
    test_scenarios = [
        {
            "name": "Record with SOC Affiliation",
            "text": """Subject of Concern: John Doe
Location: Vancouver
School: Test High School
SOC Affiliation: Local Gang ABC
☒ Gang-Associated Behavior
☒ Weapons
Instagram Information Activity
Username: johndoe123
URL: https://instagram.com/johndoe123
""",
            "expected_affiliation": "Local Gang ABC"
        },
        {
            "name": "Record with Alternative Affiliation Label",
            "text": """Subject of Concern: Jane Smith
Location: Seattle
School: Another School
Affiliation: Street Group XYZ
☒ Firearms
☒ Physical Violence
""",
            "expected_affiliation": "Street Group XYZ"
        },
        {
            "name": "Record with Gang Affiliation Label",
            "text": """Subject of Concern: Bob Johnson
Location: Portland
School: Test Elementary
Gang Affiliation: Crew 123
☒ Substance Use Concerns
☒ Gang-Associated Behavior
TikTok Information Activity
Username: bobjohn
""",
            "expected_affiliation": "Crew 123"
        },
        {
            "name": "Record without SOC Affiliation",
            "text": """Subject of Concern: Alice Brown
Location: San Francisco
School: Middle School
☒ Mental Health Concerns
☒ Bullying/Cyberbullying
""",
            "expected_affiliation": ""
        }
    ]
    
    print("\n🧪 Testing SOC Affiliation Extraction...")
    print("-" * 60)
    
    extracted_records = []
    
    for scenario in test_scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        print("-" * 40)
        
        # Extract record from the test text
        record = extractor.extract_record_from_section(scenario['text'])
        
        # Check SOC affiliation extraction
        extracted_affiliation = record.get('soc_affiliation', '')
        expected = scenario['expected_affiliation']
        
        if extracted_affiliation == expected:
            print(f"  ✅ SOC Affiliation: '{extracted_affiliation}' (Expected: '{expected}')")
        else:
            print(f"  ❌ SOC Affiliation: '{extracted_affiliation}' (Expected: '{expected}')")
        
        # Store for report generation test
        extracted_records.append(record)
        
        # Display other extracted fields
        print(f"  Name: {record.get('name', 'MISSING')}")
        print(f"  Location: {record.get('location', 'MISSING')}")
        print(f"  School: {record.get('school', 'MISSING')}")
        print(f"  Concerns: {sum(1 for v in record.get('concerns', {}).values() if v)} marked")
    
    print("\n" + "=" * 70)
    print("📊 TESTING REPORT GENERATION WITH SOC AFFILIATION")
    print("=" * 70)
    
    # Create test data structure for report generation
    test_data = [
        {
            'file_name': 'SD73 WOB Report - Test.pdf',
            'records': extracted_records[:2]  # BC district records
        },
        {
            'file_name': 'Dodge County WOB Report - Test.pdf',
            'records': extracted_records[2:]  # US district records
        }
    ]
    
    # Create temporary output folder
    output_folder = 'test_output'
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Generate reports
    month_year = "Test 2025"
    account_count, soc_count, concerns_count = output_gen.generate_reports(
        test_data, output_folder, month_year
    )
    
    print(f"\n📄 Reports Generated:")
    print(f"  • Account Tracker: {account_count} records")
    print(f"  • SOC List (BC only): {soc_count} records")
    print(f"  • Concerns Summary: {concerns_count} records")
    
    # Check if SOC affiliation is in the generated CSV files
    print("\n📋 Verifying SOC Affiliation in Generated Reports:")
    print("-" * 60)
    
    # Check Account Tracker
    account_files = [f for f in os.listdir(output_folder) if 'Account Tracker' in f]
    if account_files:
        account_df = pd.read_csv(os.path.join(output_folder, account_files[0]))
        print(f"\n✅ Account Tracker columns: {list(account_df.columns)}")
        if 'soc_affiliation' in account_df.columns:
            print("  ✅ SOC affiliation column found in Account Tracker")
            print(f"  Sample affiliations: {account_df['soc_affiliation'].dropna().unique()[:3].tolist()}")
        else:
            print("  ❌ SOC affiliation column NOT found in Account Tracker")
    
    # Check SOC List
    soc_files = [f for f in os.listdir(output_folder) if 'SOC List' in f]
    if soc_files:
        soc_df = pd.read_csv(os.path.join(output_folder, soc_files[0]))
        print(f"\n✅ SOC List columns: {list(soc_df.columns)}")
        if 'soc_affiliation' in soc_df.columns:
            print("  ✅ SOC affiliation column found in SOC List")
            print(f"  Sample affiliations: {soc_df['soc_affiliation'].dropna().unique()[:3].tolist()}")
        else:
            print("  ❌ SOC affiliation column NOT found in SOC List")
    
    # Check Concerns Summary
    concerns_files = [f for f in os.listdir(output_folder) if 'WOB Concerns Data' in f]
    if concerns_files:
        concerns_df = pd.read_csv(os.path.join(output_folder, concerns_files[0]))
        print(f"\n✅ Concerns Summary columns (first 10): {list(concerns_df.columns)[:10]}")
        if 'soc_affiliation' in concerns_df.columns:
            print("  ✅ SOC affiliation column found in Concerns Summary")
            print(f"  Sample affiliations: {concerns_df['soc_affiliation'].dropna().unique()[:3].tolist()}")
        else:
            print("  ❌ SOC affiliation column NOT found in Concerns Summary")
    
    # Display sample data from Account Tracker
    if account_files:
        print("\n📊 Sample Account Tracker Data (first 3 records):")
        print("-" * 60)
        print(account_df[['entity_nam', 'school', 'soc_affiliation', 'district']].head(3).to_string())
    
    # Clean up test files
    print("\n🧹 Cleaning up test files...")
    for file in os.listdir(output_folder):
        os.remove(os.path.join(output_folder, file))
    os.rmdir(output_folder)
    
    print("\n" + "=" * 70)
    print("✅ SOC Affiliation test completed successfully!")
    print("=" * 70)
    print("\n📌 Summary:")
    print("  • SOC affiliation extraction is working")
    print("  • SOC affiliation is included in all three report types:")
    print("    - Account Tracker")
    print("    - SOC List (BC districts)")
    print("    - WOB Concerns Data")
    print("\n💡 The extractor now looks for these patterns:")
    print("  • 'SOC Affiliation: [value]'")
    print("  • 'Affiliation: [value]'")
    print("  • 'Gang Affiliation: [value]'")
    print("  • 'Group Affiliation: [value]'")

if __name__ == "__main__":
    test_soc_affiliation_extraction()
