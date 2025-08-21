#!/usr/bin/env python3
"""
Test script to debug classification service issues
"""
import asyncio
import json
from database import db
from models import AiRecruitmentComCode, CandidateMasterProfile
from services.candidate_classification_service import candidate_classification_service
from app import app

def test_sample_candidate_data():
    """Test classification with sample candidate data"""
    
    # Sample candidate data similar to what would come from resume parsing
    sample_candidate = {
        'first_name': 'John',
        'last_name': 'Doe',
        'personal_summary': 'Experienced software engineer with 5 years in web development and database management.',
        'career_history': [
            {
                'job_title': 'Senior Software Engineer',
                'company_name': 'Tech Corp',
                'description': 'Developed web applications using Python, React, and PostgreSQL. Led a team of 3 developers.'
            },
            {
                'job_title': 'Software Developer',
                'company_name': 'StartupXYZ',
                'description': 'Built REST APIs and implemented database schemas. Worked with Django and MySQL.'
            }
        ],
        'skills': [
            {'skill_name': 'Python'},
            {'skill_name': 'JavaScript'},
            {'skill_name': 'React'},
            {'skill_name': 'PostgreSQL'},
            {'skill_name': 'Django'}
        ],
        'education': [
            {
                'degree': 'Bachelor of Computer Science',
                'school': 'University of Technology',
                'field_of_study': 'Computer Science'
            }
        ]
    }
    
    return sample_candidate

async def test_classification():
    """Test the classification service"""
    print("=== Testing Classification Service ===")
    
    # Test getting available classifications
    try:
        print("\n1. Testing classification statistics...")
        stats = candidate_classification_service.get_classification_statistics()
        print(f"✅ Stats retrieved: {stats}")
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")
        return
    
    # Test actual classification
    try:
        print("\n2. Testing actual classification...")
        sample_data = test_sample_candidate_data()
        print(f"Sample candidate data: {json.dumps(sample_data, indent=2)}")
        
        result = await candidate_classification_service.classify_candidate(sample_data)
        print(f"\n✅ Classification result:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error during classification: {str(e)}")
        import traceback
        traceback.print_exc()

def test_lookup_data():
    """Test that lookup data is accessible"""
    print("\n=== Testing Lookup Data Access ===")
    
    try:
        classifications = AiRecruitmentComCode.query.filter_by(
            category='Classification of interest',
            is_active=True
        ).all()
        
        sub_classifications = AiRecruitmentComCode.query.filter_by(
            category='Sub classification of interest',
            is_active=True
        ).all()
        
        print(f"✅ Found {len(classifications)} classifications")
        print(f"✅ Found {len(sub_classifications)} sub-classifications")
        
        print("\nFirst 5 classifications:")
        for c in classifications[:5]:
            print(f"  - {c.com_code}: {c.description}")
            
        print("\nFirst 5 sub-classifications:")
        for c in sub_classifications[:5]:
            print(f"  - {c.com_code}: {c.description}")
            
    except Exception as e:
        print(f"❌ Error accessing lookup data: {str(e)}")

def main():
    """Main test function"""
    with app.app_context():
        print("🔍 Starting Classification Debug Test")
        print("====================================")
        
        # Test lookup data access
        test_lookup_data()
        
        # Test classification service
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(test_classification())
            finally:
                loop.close()
                asyncio.set_event_loop(None)
        except Exception as e:
            print(f"❌ Error running async test: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 