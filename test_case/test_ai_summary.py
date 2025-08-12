#!/usr/bin/env python3
"""
Test script for AI Summary and Embedding functionality
This script demonstrates how to use the new AI-powered candidate profile finalization
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:5000"
CANDIDATE_ID = 1  # Replace with actual candidate ID

def test_get_current_prompt_template():
    """Test getting the current AI prompt template"""
    print("Testing: Get current AI prompt template")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/prompt-template")
        
        if response.status_code == 200:
            print("✅ Current prompt template retrieved successfully")
            data = response.json()
            print(f"Template: {data.get('template', '')[:200]}...")
            return data
        else:
            print(f"❌ Failed to get prompt template: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
    
    return None

def test_update_prompt_template():
    """Test updating the AI prompt template"""
    print("Testing: Update AI prompt template")
    
    # Custom prompt template
    custom_template = """
You are a professional recruitment AI assistant specializing in candidate profile summaries.

Analyze the candidate profile data below and create a concise, professional summary in exactly 200 words or less.

Format your response as follows:
"[X] years of experience in [position] in [domain field].
Graduated from [university/education details].
Strengths: [key skills and technical competencies]
Looking for: [salary expectations and role preferences]
Open to work status: [availability timeline and notice period]
Other remarks: [certifications, languages, and additional qualifications]"

Candidate Profile Data:
{candidate_data}

Requirements:
- Professional and concise tone
- Highlight quantifiable achievements where possible
- Include education background and key certifications
- Mention salary expectations and work preferences if available
- Note availability status and notice period
- Keep under 200 words total
- Focus on most relevant and recent experience

Professional Summary:"""
    
    payload = {
        "template": custom_template,
        "description": "Custom recruitment-focused template with emphasis on quantifiable achievements"
    }
    
    try:
        response = requests.put(
            f"{API_BASE_URL}/candidates/ai-summary/prompt-template",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Prompt template updated successfully")
            print(f"Response: {response.json()}")
            return response.json()
        else:
            print(f"❌ Failed to update prompt template: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
    
    return None

def test_finalize_candidate_profile(candidate_id, include_updates=True):
    """Test finalizing a candidate profile with AI summary generation"""
    print(f"Testing: Finalize candidate profile ID {candidate_id}")
    
    # Optional profile updates to include with finalization
    profile_updates = {
        "personal_summary": "Updated personal summary for testing AI generation",
        "classification_of_interest": "Software Development",
        "sub_classification_of_interest": "Full Stack Development",
        "preferred_work_types": "Full-time, Remote",
        "availability_weeks": 2,
        "salary_expectation": 95000.00
    } if include_updates else {}
    
    try:
        response = requests.patch(
            f"{API_BASE_URL}/candidates/{candidate_id}?generate_ai_summary=true",
            json=profile_updates,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Candidate profile finalized successfully")
            data = response.json()
            
            print(f"Message: {data.get('message')}")
            print(f"AI Processing Enabled: {data.get('ai_processing', {}).get('enabled')}")
            print(f"AI Processing Success: {data.get('ai_processing', {}).get('success')}")
            
            if data.get('ai_processing', {}).get('success'):
                ai_summary = data.get('ai_processing', {}).get('ai_summary', '')
                print(f"Generated AI Summary: {ai_summary[:300]}...")
                print("✅ Embedding vector created successfully")
            else:
                error_msg = data.get('ai_processing', {}).get('error', 'Unknown error')
                print(f"❌ AI Processing failed: {error_msg}")
            
            return data
        else:
            print(f"❌ Failed to finalize profile: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
    
    return None

def test_get_updated_candidate(candidate_id):
    """Test getting the updated candidate profile to verify AI summary"""
    print(f"Testing: Get updated candidate profile ID {candidate_id}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/{candidate_id}")
        
        if response.status_code == 200:
            print("✅ Updated candidate profile retrieved successfully")
            data = response.json()
            
            ai_summary = data.get('ai_short_summary', '')
            if ai_summary:
                print(f"AI Summary: {ai_summary}")
                print("✅ AI summary is present in the profile")
            else:
                print("⚠️  No AI summary found in the profile")
            
            # Check if embedding vector exists (won't display the actual vector)
            embedding_vector = data.get('embedding_vector')
            if embedding_vector:
                print(f"✅ Embedding vector present (dimension: {len(embedding_vector)})")
            else:
                print("⚠️  No embedding vector found")
            
            return data
        else:
            print(f"❌ Failed to get candidate: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
    
    return None

def test_finalize_without_ai(candidate_id):
    """Test finalizing profile without AI generation"""
    print(f"Testing: Finalize profile without AI (candidate ID {candidate_id})")
    
    profile_updates = {
        "remarks": "Updated via finalization test without AI processing"
    }
    
    try:
        response = requests.patch(
            f"{API_BASE_URL}/candidates/{candidate_id}?generate_ai_summary=false",
            json=profile_updates,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Profile finalized without AI processing")
            data = response.json()
            print(f"AI Processing Enabled: {data.get('ai_processing', {}).get('enabled')}")
            return data
        else:
            print(f"❌ Failed to finalize profile: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
    
    return None

def main():
    """Run all AI summary tests"""
    print("🤖 Testing AI Summary and Embedding Functionality")
    print("=" * 60)
    
    # Test 1: Get current prompt template
    print("1️⃣ Getting current prompt template...")
    current_template = test_get_current_prompt_template()
    print("\n" + "-" * 60 + "\n")
    
    # Test 2: Update prompt template
    print("2️⃣ Updating prompt template...")
    template_update = test_update_prompt_template()
    print("\n" + "-" * 60 + "\n")
    
    # Test 3: Finalize candidate profile with AI processing
    print("3️⃣ Finalizing candidate profile with AI...")
    finalization_result = test_finalize_candidate_profile(CANDIDATE_ID, include_updates=True)
    print("\n" + "-" * 60 + "\n")
    
    # Test 4: Get updated candidate to verify AI summary
    print("4️⃣ Verifying AI summary in candidate profile...")
    updated_candidate = test_get_updated_candidate(CANDIDATE_ID)
    print("\n" + "-" * 60 + "\n")
    
    # Test 5: Test finalization without AI processing
    print("5️⃣ Testing finalization without AI processing...")
    no_ai_result = test_finalize_without_ai(CANDIDATE_ID)
    print("\n" + "-" * 60 + "\n")
    
    print("🏁 AI Summary testing completed!")
    
    # Summary
    print("\n📊 SUMMARY:")
    if current_template:
        print("✅ Prompt template retrieval: SUCCESS")
    if template_update:
        print("✅ Prompt template update: SUCCESS")
    if finalization_result and finalization_result.get('ai_processing', {}).get('success'):
        print("✅ AI summary generation: SUCCESS")
        print("✅ Embedding creation: SUCCESS")
    elif finalization_result:
        print("⚠️  AI summary generation: ATTEMPTED (check errors)")
    if updated_candidate and updated_candidate.get('ai_short_summary'):
        print("✅ AI summary persistence: SUCCESS")

if __name__ == "__main__":
    main() 