#!/usr/bin/env python3
"""
Debug script for the finalize candidate profile API
This script helps identify exactly where the error occurs
"""

import requests
import json
import sys

# Configuration
API_BASE_URL = "http://localhost:5000/api"  # Note: added /api prefix
CANDIDATE_ID = 1

def test_candidate_exists():
    """Test if the candidate exists"""
    print("🔍 Testing if candidate exists...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/{CANDIDATE_ID}")
        
        if response.status_code == 200:
            print("✅ Candidate exists")
            candidate = response.json()
            print(f"   Name: {candidate.get('first_name')} {candidate.get('last_name')}")
            print(f"   Email: {candidate.get('email')}")
            return True
        else:
            print(f"❌ Candidate not found: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_finalize_without_ai():
    """Test finalization without AI processing"""
    print("\n🔍 Testing finalization without AI processing...")
    
    try:
        payload = {
            "remarks": "Debug test without AI processing"
        }
        
        response = requests.patch(
            f"{API_BASE_URL}/candidates/{CANDIDATE_ID}?generate_ai_summary=false",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        if response.status_code == 200:
            print("✅ Finalization without AI successful")
            return True
        else:
            print(f"❌ Finalization without AI failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_finalize_with_ai():
    """Test finalization with AI processing"""
    print("\n🔍 Testing finalization with AI processing...")
    
    try:
        payload = {
            "personal_summary": "Debug test with AI processing",
            "classification_of_interest": "Software Development"
        }
        
        response = requests.patch(
            f"{API_BASE_URL}/candidates/{CANDIDATE_ID}?generate_ai_summary=true",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Finalization with AI successful")
            data = response.json()
            
            ai_processing = data.get('ai_processing', {})
            print(f"   AI Processing Enabled: {ai_processing.get('enabled')}")
            print(f"   AI Processing Success: {ai_processing.get('success')}")
            
            if ai_processing.get('success'):
                print(f"   AI Summary Generated: ✅")
                ai_summary = ai_processing.get('ai_summary', '')
                print(f"   Summary Preview: {ai_summary[:100]}...")
            else:
                print(f"   AI Processing Error: {ai_processing.get('error')}")
            
            return True
        else:
            print(f"❌ Finalization with AI failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Message: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   Raw Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_prompt_template():
    """Test prompt template endpoints"""
    print("\n🔍 Testing prompt template endpoints...")
    
    try:
        # Get current template
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/prompt-template")
        
        if response.status_code == 200:
            print("✅ Prompt template retrieved successfully")
            data = response.json()
            template = data.get('template', '')
            print(f"   Template length: {len(template)} characters")
            return True
        else:
            print(f"❌ Failed to get prompt template: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_server_health():
    """Test if the server is running"""
    print("🔍 Testing server health...")
    
    try:
        # Try to get the API root or candidates list
        response = requests.get(f"{API_BASE_URL}/candidates/")
        
        if response.status_code in [200, 404]:  # 404 is ok, means server is running
            print("✅ Server is responding")
            return True
        else:
            print(f"⚠️  Server responded with status: {response.status_code}")
            return True  # Still consider it as running
            
    except requests.ConnectionError:
        print("❌ Cannot connect to server")
        print("   Make sure the Flask app is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Server health check failed: {str(e)}")
        return False

def main():
    """Run debug tests in sequence"""
    print("🐛 Debug: Finalize Candidate Profile API")
    print("=" * 50)
    
    tests = [
        ("Server Health", test_server_health),
        ("Candidate Exists", test_candidate_exists),
        ("Prompt Template", test_prompt_template),
        ("Finalize Without AI", test_finalize_without_ai),
        ("Finalize With AI", test_finalize_with_ai)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
        
        # Stop if server is not reachable
        if test_name == "Server Health" and not success:
            print("\n⚠️  Stopping tests - server is not reachable")
            break
    
    print("\n" + "=" * 50)
    print("📊 DEBUG RESULTS:")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n🔧 TROUBLESHOOTING STEPS:")
    print("1. Run the initialization test: python test_ai_service_init.py")
    print("2. Check server logs for detailed error messages")
    print("3. Verify Azure OpenAI environment variables are set")
    print("4. Check if all dependencies are installed: pip install -r requirements.txt")
    print("5. Test the API manually with smaller payloads")

if __name__ == "__main__":
    main() 