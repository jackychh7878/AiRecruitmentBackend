#!/usr/bin/env python3

"""
Test script to validate that all parsing methods return the exact required JSON format.
"""

import json
from typing import Dict, Any, List

def validate_format(parsed_data: Dict[str, Any]) -> List[str]:
    """
    Validate that the parsed data matches the exact required format.
    Returns a list of validation errors (empty if valid).
    """
    errors = []
    
    # Required top-level fields with their expected types
    required_fields = {
        'first_name': (str, type(None)),
        'last_name': (str, type(None)),
        'email': (str, type(None)),
        'location': (str, type(None)),
        'phone_number': (str, type(None)),
        'personal_summary': (str, type(None)),
        'availability_weeks': int,
        'preferred_work_types': (str, type(None)),
        'right_to_work': bool,
        'salary_expectation': int,
        'classification_of_interest': (str, type(None)),
        'sub_classification_of_interest': (str, type(None)),
        'citizenship': (str, type(None)),
        'is_active': bool,
        'career_history': list,
        'skills': list,
        'education': list,
        'licenses_certifications': list,
        'languages': list,
        'resumes': list,
        'resume_file': dict
    }
    
    # Check top-level fields
    for field, expected_type in required_fields.items():
        if field not in parsed_data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(parsed_data[field], expected_type):
            errors.append(f"Field '{field}' has wrong type. Expected {expected_type}, got {type(parsed_data[field])}")
    
    # Validate career_history structure
    if 'career_history' in parsed_data and isinstance(parsed_data['career_history'], list):
        for i, career in enumerate(parsed_data['career_history']):
            career_fields = {
                'candidate_id': int,
                'job_title': (str, type(None)),
                'company_name': (str, type(None)),
                'start_date': (str, type(None)),
                'end_date': (str, type(None)),
                'description': (str, type(None)),
                'is_active': bool
            }
            for field, expected_type in career_fields.items():
                if field not in career:
                    errors.append(f"career_history[{i}] missing field: {field}")
                elif not isinstance(career[field], expected_type):
                    errors.append(f"career_history[{i}].{field} has wrong type. Expected {expected_type}, got {type(career[field])}")
    
    # Validate skills structure
    if 'skills' in parsed_data and isinstance(parsed_data['skills'], list):
        for i, skill in enumerate(parsed_data['skills']):
            skill_fields = {
                'candidate_id': int,
                'career_history_id': int,
                'skills': (str, type(None)),
                'is_active': bool
            }
            for field, expected_type in skill_fields.items():
                if field not in skill:
                    errors.append(f"skills[{i}] missing field: {field}")
                elif not isinstance(skill[field], expected_type):
                    errors.append(f"skills[{i}].{field} has wrong type. Expected {expected_type}, got {type(skill[field])}")
    
    # Validate education structure
    if 'education' in parsed_data and isinstance(parsed_data['education'], list):
        for i, edu in enumerate(parsed_data['education']):
            edu_fields = {
                'candidate_id': int,
                'school': (str, type(None)),
                'degree': (str, type(None)),
                'field_of_study': (str, type(None)),
                'start_date': (str, type(None)),
                'end_date': (str, type(None)),
                'grade': (str, type(None)),
                'description': (str, type(None)),
                'is_active': bool
            }
            for field, expected_type in edu_fields.items():
                if field not in edu:
                    errors.append(f"education[{i}] missing field: {field}")
                elif not isinstance(edu[field], expected_type):
                    errors.append(f"education[{i}].{field} has wrong type. Expected {expected_type}, got {type(edu[field])}")
    
    # Validate licenses_certifications structure
    if 'licenses_certifications' in parsed_data and isinstance(parsed_data['licenses_certifications'], list):
        for i, cert in enumerate(parsed_data['licenses_certifications']):
            cert_fields = {
                'candidate_id': int,
                'name': (str, type(None)),
                'issuing_organization': (str, type(None)),
                'issue_date': (str, type(None)),
                'expiration_date': (str, type(None)),
                'credential_id': (str, type(None)),
                'credential_url': (str, type(None)),
                'is_active': bool
            }
            for field, expected_type in cert_fields.items():
                if field not in cert:
                    errors.append(f"licenses_certifications[{i}] missing field: {field}")
                elif not isinstance(cert[field], expected_type):
                    errors.append(f"licenses_certifications[{i}].{field} has wrong type. Expected {expected_type}, got {type(cert[field])}")
    
    # Validate languages structure
    if 'languages' in parsed_data and isinstance(parsed_data['languages'], list):
        for i, lang in enumerate(parsed_data['languages']):
            lang_fields = {
                'candidate_id': int,
                'language': (str, type(None)),
                'proficiency_level': (str, type(None)),
                'is_active': bool
            }
            for field, expected_type in lang_fields.items():
                if field not in lang:
                    errors.append(f"languages[{i}] missing field: {field}")
                elif not isinstance(lang[field], expected_type):
                    errors.append(f"languages[{i}].{field} has wrong type. Expected {expected_type}, got {type(lang[field])}")
    
    return errors

def print_sample_format():
    """Print the expected JSON format for reference."""
    sample_format = {
        "first_name": "string",
        "last_name": "string", 
        "email": "string",
        "location": "string",
        "phone_number": "string",
        "personal_summary": "string",
        "availability_weeks": 0,
        "preferred_work_types": "string",
        "right_to_work": True,
        "salary_expectation": 0,
        "classification_of_interest": "string",
        "sub_classification_of_interest": "string",
        "citizenship": "string",
        "is_active": True,
        "career_history": [
            {
                "candidate_id": 0,
                "job_title": "string",
                "company_name": "string",
                "start_date": "2025-08-15",
                "end_date": "2025-08-15",
                "description": "string",
                "is_active": True
            }
        ],
        "skills": [
            {
                "candidate_id": 0,
                "career_history_id": 0,
                "skills": "string",
                "is_active": True
            }
        ],
        "education": [
            {
                "candidate_id": 0,
                "school": "string",
                "degree": "string",
                "field_of_study": "string",
                "start_date": "string",
                "end_date": "string",
                "grade": "string",
                "description": "string",
                "is_active": True
            }
        ],
        "licenses_certifications": [
            {
                "candidate_id": 0,
                "name": "string",
                "issuing_organization": "string",
                "issue_date": "string",
                "expiration_date": "string",
                "credential_id": "string",
                "credential_url": "string",
                "is_active": True
            }
        ],
        "languages": [
            {
                "candidate_id": 0,
                "language": "string",
                "proficiency_level": "string",
                "is_active": True
            }
        ],
        "resumes": [
            {
                "candidate_id": 0,
                "file_name": "string",
                "file_size": 0,
                "content_type": "string",
                "upload_date": "2025-08-15T04:31:47.088Z",
                "is_active": True
            }
        ],
        "resume_file": {}
    }
    
    print("Expected JSON Format:")
    print(json.dumps(sample_format, indent=2))

if __name__ == "__main__":
    print("Resume Parser Format Validation Tool")
    print("=" * 50)
    print_sample_format()
    print("\nUse validate_format(parsed_data) to validate your parsed resume data.") 