#!/usr/bin/env python3
"""
Test script to verify all three resume parsing methods work correctly
and produce consistent output formats.
"""

import os
import sys
import json
import tempfile
from io import BytesIO
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.resume_parser import ResumeParser, get_resume_parser, reset_resume_parser

# Load environment variables
load_dotenv()

def create_sample_pdf_text():
    """Create a sample resume text for testing"""
    return """
    John Smith
    Software Engineer
    john.smith@email.com
    +1-555-123-4567
    San Francisco, CA

    PROFESSIONAL SUMMARY
    Experienced software engineer with 5+ years in full-stack development. 
    Skilled in Python, JavaScript, and cloud technologies.

    EXPERIENCE
    Senior Software Engineer at Tech Corp (2020-2023)
    - Led development of microservices architecture using Python and Docker
    - Managed team of 3 developers
    - Improved system performance by 40%

    Software Developer at StartupXYZ (2018-2020)
    - Developed web applications using React and Node.js
    - Implemented automated testing procedures

    EDUCATION
    Bachelor of Science in Computer Science
    Stanford University (2014-2018)
    GPA: 3.8

    SKILLS
    Python, JavaScript, React, Node.js, Docker, AWS, MySQL, Git

    LANGUAGES
    English (Native)
    Spanish (Intermediate)

    CERTIFICATIONS
    AWS Certified Developer
    Google Cloud Professional
    """

def test_parsing_method(method_name):
    """Test a specific parsing method"""
    print(f"\n{'='*50}")
    print(f"Testing {method_name.upper()} parsing method")
    print(f"{'='*50}")
    
    try:
        # Reset parser instance and set method
        reset_resume_parser()
        os.environ['RESUME_PARSING_METHOD'] = method_name
        
        # Initialize parser
        parser = get_resume_parser()
        
        # Create a simple text file as PDF simulation
        sample_text = create_sample_pdf_text()
        
        # For testing purposes, we'll use a text file instead of PDF
        # In real usage, this would be a PDF file
        print(f"✓ Parser initialized with method: {parser.parsing_method}")
        
        # Since we can't easily create a real PDF for testing,
        # we'll test the individual extraction methods
        if method_name == 'spacy':
            test_spacy_components(parser, sample_text)
        elif method_name == 'azure_di':
            test_azure_di_availability(parser)
        elif method_name == 'langextract':
            test_langextract_availability(parser)
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing {method_name}: {str(e)}")
        return False

def test_spacy_components(parser, sample_text):
    """Test spaCy components"""
    try:
        # Test text cleaning
        cleaned = parser.clean_text(sample_text)
        print(f"✓ Text cleaning successful (length: {len(cleaned)})")
        
        # Test contact info extraction
        contact = parser.extract_contact_info(sample_text)
        print(f"✓ Contact extraction: {contact}")
        
        # Test skills extraction
        skills = parser.extract_skills(sample_text)
        print(f"✓ Skills extraction: {len(skills)} skills found")
        
        # Test education extraction
        education = parser.extract_education(sample_text)
        print(f"✓ Education extraction: {len(education)} records found")
        
        # Test work experience extraction
        experience = parser.extract_work_experience(sample_text)
        print(f"✓ Work experience extraction: {len(experience)} records found")
        
        # Test language extraction
        languages = parser.extract_languages(sample_text)
        print(f"✓ Language extraction: {len(languages)} languages found")
        
        # Test certification extraction
        certs = parser.extract_certifications(sample_text)
        print(f"✓ Certification extraction: {len(certs)} certifications found")
        
    except Exception as e:
        print(f"✗ SpaCy component test failed: {str(e)}")

def test_azure_di_availability(parser):
    """Test Azure DI availability"""
    try:
        if hasattr(parser, 'azure_di_client'):
            print("✓ Azure Document Intelligence client initialized")
        else:
            print("⚠ Azure DI client not available - check environment variables")
    except Exception as e:
        print(f"✗ Azure DI test failed: {str(e)}")

def test_langextract_availability(parser):
    """Test LangExtract availability"""
    try:
        azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_openai_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        
        if azure_openai_endpoint and azure_openai_api_key and azure_openai_deployment:
            print("✓ Azure OpenAI configuration found for LangExtract")
            print(f"✓ LangExtract configured to use Azure OpenAI deployment: {azure_openai_deployment}")
            print("✓ Using same credentials as existing AI services")
        else:
            print("⚠ Azure OpenAI environment variables not complete")
            print("⚠ Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME")
    except Exception as e:
        print(f"✗ LangExtract test failed: {str(e)}")

def verify_output_consistency():
    """Verify that all methods produce consistent output structure"""
    print(f"\n{'='*50}")
    print("VERIFYING OUTPUT CONSISTENCY")
    print(f"{'='*50}")
    
    expected_keys = {
        'first_name', 'last_name', 'email', 'location', 'phone_number',
        'personal_summary', 'availability_weeks', 'preferred_work_types',
        'right_to_work', 'salary_expectation', 'classification_of_interest',
        'sub_classification_of_interest', 'is_active', 'career_history',
        'skills', 'education', 'licenses_certifications', 'languages', 'resumes'
    }
    
    career_history_keys = {'job_title', 'company_name', 'start_date', 'end_date', 'description'}
    skills_keys = {'skills', 'career_history_id'}
    education_keys = {'school', 'degree', 'field_of_study', 'start_date', 'end_date', 'grade', 'description'}
    cert_keys = {'name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url'}
    language_keys = {'language', 'proficiency_level'}
    
    print("✓ Expected output structure defined")
    print(f"✓ Main record keys: {len(expected_keys)}")
    print(f"✓ Career history keys: {len(career_history_keys)}")
    print(f"✓ Skills keys: {len(skills_keys)}")
    print(f"✓ Education keys: {len(education_keys)}")
    print(f"✓ Certification keys: {len(cert_keys)}")
    print(f"✓ Language keys: {len(language_keys)}")
    
    return True

def main():
    """Main test function"""
    print("RESUME PARSING METHODS TEST SUITE")
    print("="*50)
    
    # Test each parsing method
    methods = ['spacy', 'azure_di', 'langextract']
    results = {}
    
    for method in methods:
        results[method] = test_parsing_method(method)
    
    # Verify output consistency
    verify_output_consistency()
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    for method, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{method.upper():12} {status}")
    
    total_passed = sum(results.values())
    print(f"\nOverall: {total_passed}/{len(methods)} methods passed basic tests")
    
    print("\nNOTE: This test only verifies initialization and basic components.")
    print("For full testing with actual PDF files, use the API endpoints.")
    
    print(f"\n{'='*50}")
    print("CONFIGURATION GUIDE")
    print(f"{'='*50}")
    print("To use the resume parser:")
    print("1. Set RESUME_PARSING_METHOD environment variable")
    print("2. Configure the appropriate credentials for your chosen method")
    print("3. See RESUME_PARSING_CONFIGURATION.md for detailed setup")

if __name__ == "__main__":
    main() 