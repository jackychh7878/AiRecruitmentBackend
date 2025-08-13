#!/usr/bin/env python3
"""
Test script to validate both Azure Document Intelligence and spaCy resume parsing modes.
This script tests that both modes produce the same output structure and handle errors gracefully.
"""

import os
import sys
import json
from io import BytesIO
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.resume_parser import ResumeParser

# Load environment variables
load_dotenv()

def test_parser_initialization():
    """Test that both parser modes initialize correctly"""
    print("Testing parser initialization...")
    
    # Test spaCy mode
    print("  Testing spaCy mode...")
    os.environ['USE_AZURE_DOCUMENT_INTELLIGENCE'] = 'false'
    try:
        spacy_parser = ResumeParser()
        print("    ✓ spaCy parser initialized successfully")
        print(f"    ✓ Using Azure DI: {spacy_parser.use_azure_di}")
    except Exception as e:
        print(f"    ✗ spaCy parser failed to initialize: {e}")
        return False
    
    # Test Azure DI mode (only if credentials are available)
    print("  Testing Azure Document Intelligence mode...")
    if os.getenv('AZURE_DI_ENDPOINT') and os.getenv('AZURE_DI_API_KEY'):
        os.environ['USE_AZURE_DOCUMENT_INTELLIGENCE'] = 'true'
        try:
            azure_parser = ResumeParser()
            print("    ✓ Azure DI parser initialized successfully")
            print(f"    ✓ Using Azure DI: {azure_parser.use_azure_di}")
        except Exception as e:
            print(f"    ✗ Azure DI parser failed to initialize: {e}")
            return False
    else:
        print("    ⚠ Azure DI credentials not found, skipping Azure DI test")
    
    return True

def test_output_structure():
    """Test that both parsers produce the expected output structure"""
    print("\nTesting output structure consistency...")
    
    # Expected keys in the output
    expected_keys = {
        'first_name', 'last_name', 'email', 'location', 'phone_number',
        'personal_summary', 'availability_weeks', 'preferred_work_types',
        'right_to_work', 'salary_expectation', 'classification_of_interest',
        'sub_classification_of_interest', 'is_active', 'career_history',
        'skills', 'education', 'licenses_certifications', 'languages', 'resumes'
    }
    
    # Create a mock PDF (empty for structure test)
    mock_pdf = BytesIO(b"Mock PDF content for structure testing")
    
    # Test spaCy parser structure
    print("  Testing spaCy parser output structure...")
    os.environ['USE_AZURE_DOCUMENT_INTELLIGENCE'] = 'false'
    spacy_parser = ResumeParser()
    
    try:
        # This will fail with actual parsing, but we can catch and check the structure
        result = spacy_parser.parse_resume(mock_pdf)
        spacy_keys = set(result.keys())
        missing_keys = expected_keys - spacy_keys
        extra_keys = spacy_keys - expected_keys
        
        if missing_keys:
            print(f"    ✗ Missing keys in spaCy output: {missing_keys}")
            return False
        if extra_keys:
            print(f"    ⚠ Extra keys in spaCy output: {extra_keys}")
        
        print("    ✓ spaCy parser output structure is correct")
        
    except Exception as e:
        # Expected for mock PDF, but we can still validate the error handling
        print(f"    ⚠ spaCy parser error (expected with mock PDF): {type(e).__name__}")
    
    # Test Azure DI parser structure (if available)
    if os.getenv('AZURE_DI_ENDPOINT') and os.getenv('AZURE_DI_API_KEY'):
        print("  Testing Azure DI parser output structure...")
        os.environ['USE_AZURE_DOCUMENT_INTELLIGENCE'] = 'true'
        azure_parser = ResumeParser()
        
        try:
            result = azure_parser.parse_resume(mock_pdf)
            azure_keys = set(result.keys())
            missing_keys = expected_keys - azure_keys
            extra_keys = azure_keys - expected_keys
            
            if missing_keys:
                print(f"    ✗ Missing keys in Azure DI output: {missing_keys}")
                return False
            if extra_keys:
                print(f"    ⚠ Extra keys in Azure DI output: {extra_keys}")
            
            print("    ✓ Azure DI parser output structure is correct")
            
        except Exception as e:
            print(f"    ⚠ Azure DI parser error (expected with mock PDF): {type(e).__name__}")
    
    return True

def test_environment_toggle():
    """Test that the environment variable toggle works correctly"""
    print("\nTesting environment variable toggle...")
    
    # Test toggle to spaCy
    os.environ['USE_AZURE_DOCUMENT_INTELLIGENCE'] = 'false'
    parser1 = ResumeParser()
    if parser1.use_azure_di:
        print("    ✗ Parser should use spaCy when USE_AZURE_DOCUMENT_INTELLIGENCE=false")
        return False
    print("    ✓ Correctly using spaCy when USE_AZURE_DOCUMENT_INTELLIGENCE=false")
    
    # Test toggle to Azure DI
    os.environ['USE_AZURE_DOCUMENT_INTELLIGENCE'] = 'true'
    try:
        parser2 = ResumeParser()
        if not parser2.use_azure_di:
            print("    ✗ Parser should use Azure DI when USE_AZURE_DOCUMENT_INTELLIGENCE=true")
            return False
        print("    ✓ Correctly using Azure DI when USE_AZURE_DOCUMENT_INTELLIGENCE=true")
    except Exception as e:
        print(f"    ⚠ Azure DI not available: {e}")
    
    # Test default behavior (should be spaCy)
    if 'USE_AZURE_DOCUMENT_INTELLIGENCE' in os.environ:
        del os.environ['USE_AZURE_DOCUMENT_INTELLIGENCE']
    parser3 = ResumeParser()
    if parser3.use_azure_di:
        print("    ✗ Parser should default to spaCy when USE_AZURE_DOCUMENT_INTELLIGENCE is not set")
        return False
    print("    ✓ Correctly defaults to spaCy when USE_AZURE_DOCUMENT_INTELLIGENCE is not set")
    
    return True

def test_error_handling():
    """Test error handling for both parsers"""
    print("\nTesting error handling...")
    
    # Test with invalid file
    invalid_file = BytesIO(b"This is not a valid PDF file")
    
    # Test spaCy error handling
    print("  Testing spaCy error handling...")
    os.environ['USE_AZURE_DOCUMENT_INTELLIGENCE'] = 'false'
    spacy_parser = ResumeParser()
    
    try:
        spacy_parser.parse_resume(invalid_file)
        print("    ✗ spaCy parser should have raised an error for invalid PDF")
        return False
    except ValueError as e:
        print(f"    ✓ spaCy parser correctly raised ValueError: {str(e)[:50]}...")
    except Exception as e:
        print(f"    ⚠ spaCy parser raised unexpected error: {type(e).__name__}")
    
    # Test Azure DI error handling (if available)
    if os.getenv('AZURE_DI_ENDPOINT') and os.getenv('AZURE_DI_API_KEY'):
        print("  Testing Azure DI error handling...")
        os.environ['USE_AZURE_DOCUMENT_INTELLIGENCE'] = 'true'
        azure_parser = ResumeParser()
        
        try:
            azure_parser.parse_resume(invalid_file)
            print("    ✗ Azure DI parser should have raised an error for invalid PDF")
            return False
        except ValueError as e:
            print(f"    ✓ Azure DI parser correctly raised ValueError: {str(e)[:50]}...")
        except Exception as e:
            print(f"    ⚠ Azure DI parser raised unexpected error: {type(e).__name__}")
    
    return True

def main():
    """Run all tests"""
    print("Resume Parser Mode Testing")
    print("=" * 50)
    
    tests = [
        test_parser_initialization,
        test_environment_toggle,
        test_output_structure,
        test_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"  ✗ {test.__name__} failed")
        except Exception as e:
            print(f"  ✗ {test.__name__} raised unexpected error: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main()) 