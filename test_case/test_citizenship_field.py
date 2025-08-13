#!/usr/bin/env python3
"""
Test script to verify citizenship field integration in candidate profiles
"""

import json

def test_candidate_profile_model():
    """Test that the citizenship field is properly integrated"""
    
    # Test 1: Check if models.py includes citizenship field
    try:
        from models import CandidateMasterProfile
        
        # Check if citizenship field exists in the model
        if hasattr(CandidateMasterProfile, 'citizenship'):
            print("✓ Citizenship field exists in CandidateMasterProfile model")
        else:
            print("✗ Citizenship field NOT found in CandidateMasterProfile model")
            
        # Create a sample candidate instance (without saving to DB)
        sample_candidate = CandidateMasterProfile(
            first_name="John",
            last_name="Doe", 
            email="john.doe@example.com",
            citizenship="Hong Kong SARS Permanent Resident"
        )
        
        # Test the to_dict method includes citizenship
        candidate_dict = sample_candidate.to_dict()
        if 'citizenship' in candidate_dict:
            print("✓ Citizenship field included in to_dict() method")
            print(f"  Sample citizenship value: {candidate_dict.get('citizenship')}")
        else:
            print("✗ Citizenship field NOT included in to_dict() method")
            
    except ImportError as e:
        print(f"✗ Error importing models: {e}")
    except Exception as e:
        print(f"✗ Error testing model: {e}")

def test_api_models():
    """Test that API models include citizenship field"""
    try:
        from routes.candidate_profile_routes import candidate_profile_ns
        
        # Get all registered models
        models = candidate_profile_ns.models
        
        # Check key models for citizenship field
        models_to_check = [
            'Candidate',
            'CandidateBulkCreate', 
            'CandidateInput',
            'SemanticSearchResult'
        ]
        
        for model_name in models_to_check:
            if model_name in models:
                model = models[model_name]
                if 'citizenship' in model:
                    print(f"✓ Citizenship field found in {model_name} API model")
                else:
                    print(f"✗ Citizenship field NOT found in {model_name} API model")
            else:
                print(f"✗ {model_name} model not found in API namespace")
                
    except ImportError as e:
        print(f"✗ Error importing routes: {e}")
    except Exception as e:
        print(f"✗ Error testing API models: {e}")

def test_citizenship_options():
    """Test the available citizenship options from sample data"""
    
    citizenship_options = [
        "Hong Kong SARS Permanent Resident",
        "Hong Kong SARS Citizen", 
        "Hong Kong SARS temporary visa with restrictions on industry (e.g. TeachTAS)",
        "Hong Kong SARS temporary visa (e.g. QMAS, TTPS, IANG)",
        "Require sponsorship to work for a new employer in Hong Kong SARS"
    ]
    
    print("✓ Available citizenship options:")
    for i, option in enumerate(citizenship_options, 1):
        print(f"  {i}. {option}")

def print_sample_api_request():
    """Print sample API request with citizenship field"""
    
    sample_request = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "location": "Hong Kong",
        "phone_number": "+852-12345678",
        "personal_summary": "Experienced software engineer",
        "citizenship": "Hong Kong SARS Permanent Resident",
        "classification_of_interest": "Information Technology",
        "right_to_work": True
    }
    
    print("✓ Sample API request payload with citizenship field:")
    print(json.dumps(sample_request, indent=2))

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("TESTING CITIZENSHIP FIELD INTEGRATION")
    print("=" * 60)
    
    print("\n1. Testing Model Integration:")
    print("-" * 30)
    test_candidate_profile_model()
    
    print("\n2. Testing API Models:")
    print("-" * 30)
    test_api_models()
    
    print("\n3. Citizenship Options:")
    print("-" * 30)
    test_citizenship_options()
    
    print("\n4. Sample API Request:")
    print("-" * 30)
    print_sample_api_request()
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests() 