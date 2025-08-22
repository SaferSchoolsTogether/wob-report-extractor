"""
Test script to verify enhanced error logging for empty cells and missing fields
"""

import os
import sys
from datetime import datetime
from config_manager import ConfigManager
from extractor_engine import SmartExtractor
import json

def create_test_scenarios():
    """Create test scenarios to simulate different extraction issues"""
    
    test_scenarios = [
        {
            "name": "Complete Record",
            "text": """Subject of Concern: John Doe
Location: Vancouver
School: Test High School
☒ Mental Health Concerns
☒ Bullying/Cyberbullying
Instagram Information Activity
Username: johndoe123
URL: https://instagram.com/johndoe123
""",
            "expected": {
                "name": True,
                "location": True,
                "school": True,
                "concerns": True,
                "social_media": True
            }
        },
        {
            "name": "Missing Location",
            "text": """Subject of Concern: Jane Smith
School: Another School
☒ Firearms
☒ Physical Violence
""",
            "expected": {
                "name": True,
                "location": False,
                "school": True,
                "concerns": True,
                "social_media": False
            }
        },
        {
            "name": "Missing School",
            "text": """Subject of Concern: Bob Johnson
Location: Seattle
☒ Substance Use Concerns
TikTok Information Activity
Username: bobjohn
""",
            "expected": {
                "name": True,
                "location": True,
                "school": False,
                "concerns": True,
                "social_media": True
            }
        },
        {
            "name": "No Concerns Marked",
            "text": """Subject of Concern: Alice Brown
Location: Portland
School: Test Elementary
Instagram Information Activity
URL: https://instagram.com/alice
""",
            "expected": {
                "name": True,
                "location": True,
                "school": True,
                "concerns": False,
                "social_media": True
            }
        },
        {
            "name": "Empty Name Field",
            "text": """Subject of Concern: 
Location: San Francisco
School: Middle School
☒ Gang-Associated Behavior
""",
            "expected": {
                "name": False,
                "location": True,
                "school": True,
                "concerns": True,
                "social_media": False
            }
        },
        {
            "name": "Alternative Field Names",
            "text": """Subject of Concern: Charlie Davis
City/Town: Los Angeles
Institution: Private Academy
☒ Threat-Related Behavior
☒ Weapons
""",
            "expected": {
                "name": True,
                "location": True,  # Should match City/Town
                "school": True,     # Should match Institution
                "concerns": True,
                "social_media": False
            }
        }
    ]
    
    return test_scenarios

def test_empty_cells_logging():
    """Test the enhanced error logging for empty cells"""
    
    print("=" * 70)
    print("WOB Report Extractor - Empty Cells Error Logging Test")
    print("=" * 70)
    
    # Initialize the extractor with debug mode
    config_manager = ConfigManager()
    extractor = SmartExtractor(config_manager, debug_mode=True)
    
    print("\n✅ Extractor initialized with debug mode enabled")
    print(f"📝 Log file: logs/wob_extractor_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Get test scenarios
    scenarios = create_test_scenarios()
    
    print("\n🧪 Running extraction tests for various scenarios...")
    print("-" * 60)
    
    results = []
    
    for scenario in scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        print("-" * 40)
        
        # Extract record from the test text
        record = extractor.extract_record_from_section(scenario['text'])
        
        # Check extraction results
        extraction_results = {
            "scenario": scenario['name'],
            "fields": {}
        }
        
        # Check name field
        has_name = bool(record.get('name'))
        extraction_results['fields']['name'] = {
            "extracted": has_name,
            "expected": scenario['expected']['name'],
            "value": record.get('name', 'MISSING')
        }
        print(f"  Name: {'✓' if has_name == scenario['expected']['name'] else '✗'} - {record.get('name', 'MISSING')}")
        
        # Check location field
        has_location = bool(record.get('location'))
        extraction_results['fields']['location'] = {
            "extracted": has_location,
            "expected": scenario['expected']['location'],
            "value": record.get('location', 'MISSING')
        }
        print(f"  Location: {'✓' if has_location == scenario['expected']['location'] else '✗'} - {record.get('location', 'MISSING')}")
        
        # Check school field
        has_school = bool(record.get('school'))
        extraction_results['fields']['school'] = {
            "extracted": has_school,
            "expected": scenario['expected']['school'],
            "value": record.get('school', 'MISSING')
        }
        print(f"  School: {'✓' if has_school == scenario['expected']['school'] else '✗'} - {record.get('school', 'MISSING')}")
        
        # Check concerns
        has_concerns = bool(record.get('concerns') and any(record['concerns'].values()))
        extraction_results['fields']['concerns'] = {
            "extracted": has_concerns,
            "expected": scenario['expected']['concerns'],
            "count": sum(1 for v in record.get('concerns', {}).values() if v)
        }
        print(f"  Concerns: {'✓' if has_concerns == scenario['expected']['concerns'] else '✗'} - {sum(1 for v in record.get('concerns', {}).values() if v)} marked")
        
        # Check social media
        has_social = bool(record.get('social_media'))
        extraction_results['fields']['social_media'] = {
            "extracted": has_social,
            "expected": scenario['expected']['social_media'],
            "count": len(record.get('social_media', []))
        }
        print(f"  Social Media: {'✓' if has_social == scenario['expected']['social_media'] else '✗'} - {len(record.get('social_media', []))} platforms")
        
        results.append(extraction_results)
    
    print("\n" + "=" * 70)
    print("📊 EXTRACTION STATISTICS SUMMARY")
    print("=" * 70)
    
    # Get extraction quality report
    quality_report = extractor.get_extraction_quality_report()
    
    print(f"\n📈 Total Records Processed: {quality_report['total_records_processed']}")
    
    if quality_report['field_success_rates']:
        print("\n📊 Field Success Rates:")
        for field, stats in quality_report['field_success_rates'].items():
            print(f"  • {field:15} : {stats['success_rate']:>6} ({stats['successful']}/{stats['total']})")
            if stats['missing'] > 0:
                print(f"    ⚠️ Missing in {stats['missing']} records")
    
    if quality_report['missing_data_summary']:
        print("\n⚠️ Missing Data Summary:")
        for field, stats in quality_report['missing_data_summary'].items():
            print(f"  • {field:15} : {stats['missing_count']} missing ({stats['percentage']})")
    
    if quality_report['extraction_warnings']:
        print(f"\n⚠️ Extraction Warnings ({len(quality_report['extraction_warnings'])} total):")
        for warning in quality_report['extraction_warnings'][:5]:  # Show first 5
            print(f"  • {warning}")
    
    if quality_report['recommendations']:
        print("\n💡 Recommendations:")
        for rec in quality_report['recommendations']:
            print(f"  • {rec}")
    
    # Test result summary
    print("\n" + "=" * 70)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    total_tests = len(scenarios)
    passed_tests = 0
    
    for result in results:
        all_correct = all(
            field_data['extracted'] == field_data['expected'] 
            for field_data in result['fields'].values()
        )
        if all_correct:
            passed_tests += 1
            print(f"✅ {result['scenario']}: PASSED")
        else:
            print(f"❌ {result['scenario']}: FAILED")
            for field, data in result['fields'].items():
                if data['extracted'] != data['expected']:
                    print(f"   - {field}: Expected {data['expected']}, got {data['extracted']}")
    
    print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
    
    # Check log file
    print("\n" + "=" * 70)
    print("📝 LOG FILE CHECK")
    print("=" * 70)
    
    log_file = f"logs/wob_extractor_{datetime.now().strftime('%Y%m%d')}.log"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log_content = f.read()
            
        # Count different log levels
        warning_count = log_content.count('WARNING')
        error_count = log_content.count('ERROR')
        debug_count = log_content.count('DEBUG')
        
        print(f"✅ Log file exists: {log_file}")
        print(f"  • Warnings logged: {warning_count}")
        print(f"  • Errors logged: {error_count}")
        print(f"  • Debug entries: {debug_count}")
        
        # Show sample of warnings about missing fields
        print("\n📋 Sample of missing field warnings:")
        lines = log_content.split('\n')
        missing_field_warnings = [line for line in lines if 'missing fields' in line.lower()]
        for warning in missing_field_warnings[:3]:
            if warning:
                print(f"  • {warning[warning.find('WARNING'):] if 'WARNING' in warning else warning}")
    else:
        print(f"⚠️ Log file not found: {log_file}")
    
    print("\n" + "=" * 70)
    print("✅ Empty cells error logging test completed!")
    print("=" * 70)

if __name__ == "__main__":
    test_empty_cells_logging()
