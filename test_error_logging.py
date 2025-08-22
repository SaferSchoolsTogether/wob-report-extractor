"""
Test script to verify error logging functionality for locked PDFs
"""

import os
import sys
from datetime import datetime
from config_manager import ConfigManager
from extractor_engine import SmartExtractor

def test_error_logging():
    """Test the error logging functionality"""
    
    print("=" * 60)
    print("WOB Report Extractor - Error Logging Test")
    print("=" * 60)
    
    # Initialize the extractor
    config_manager = ConfigManager()
    extractor = SmartExtractor(config_manager)
    
    print("\n✅ Extractor initialized with logging enabled")
    print(f"📝 Log file will be saved to: logs/wob_extractor_{datetime.now().strftime('%Y%m%d')}.log")
    
    # Test scenarios
    test_files = [
        ("test_files/normal.pdf", "Normal PDF file"),
        ("test_files/locked.pdf", "Password-protected PDF"),
        ("test_files/nonexistent.pdf", "Non-existent file"),
    ]
    
    print("\n🧪 Running test scenarios...")
    print("-" * 40)
    
    for file_path, description in test_files:
        print(f"\nTesting: {description}")
        print(f"File: {file_path}")
        
        # Create a mock locked PDF for testing (if needed)
        if "locked" in file_path and not os.path.exists(file_path):
            print("  ⚠️ Note: Locked PDF test file not found")
            print("  → To test locked PDF handling, place a password-protected PDF in test_files/locked.pdf")
        
        # Process the file
        result = extractor.extract_from_pdf(file_path)
        
        # Check results
        if 'error' in result:
            error_type = result.get('error_type', 'unknown')
            print(f"  ❌ Error detected: {error_type}")
            print(f"  Message: {result['error']}")
        else:
            num_records = len(result.get('records', []))
            print(f"  ✅ Success: Found {num_records} records")
    
    print("\n" + "-" * 40)
    
    # Check if log file was created
    log_file = f"logs/wob_extractor_{datetime.now().strftime('%Y%m%d')}.log"
    if os.path.exists(log_file):
        print(f"\n✅ Log file created successfully: {log_file}")
        
        # Display log file contents
        print("\n📋 Log file contents:")
        print("-" * 40)
        with open(log_file, 'r') as f:
            contents = f.read()
            if contents:
                # Show last 10 lines or all if less
                lines = contents.strip().split('\n')
                display_lines = lines[-10:] if len(lines) > 10 else lines
                for line in display_lines:
                    print(f"  {line}")
                if len(lines) > 10:
                    print(f"\n  ... (showing last 10 of {len(lines)} lines)")
            else:
                print("  (Log file is empty)")
    else:
        print(f"\n⚠️ Log file not found: {log_file}")
    
    # Get error summary
    print("\n📊 Error Summary:")
    print("-" * 40)
    summary = extractor.get_error_summary()
    
    if summary['locked_pdfs']:
        print(f"🔒 Locked PDFs: {len(summary['locked_pdfs'])}")
        for entry in summary['locked_pdfs'][:3]:  # Show first 3
            print(f"  - {entry[:100]}...")  # Truncate long lines
    
    if summary['permission_errors']:
        print(f"⛔ Permission Errors: {len(summary['permission_errors'])}")
        for entry in summary['permission_errors'][:3]:
            print(f"  - {entry[:100]}...")
    
    if summary['other_errors']:
        print(f"⚠️ Other Errors: {len(summary['other_errors'])}")
        for entry in summary['other_errors'][:3]:
            print(f"  - {entry[:100]}...")
    
    if not any([summary['locked_pdfs'], summary['permission_errors'], summary['other_errors']]):
        print("  No errors found in the log file")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_error_logging()
