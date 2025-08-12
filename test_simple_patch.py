#!/usr/bin/env python3
"""
Simple test to verify PATCH request format
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:5000/api"
CANDIDATE_ID = 1

def test_simple_patch():
    """Test a simple PATCH request with proper headers"""
    print("🔍 Testing simple PATCH request...")
    
    # Simple payload
    payload = {
        "remarks": "Simple test"
    }
    
    print(f"📤 Sending PATCH request to: {API_BASE_URL}/candidates/{CANDIDATE_ID}")
    print(f"📄 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Method 1: Using json parameter (recommended)
        response = requests.patch(
            f"{API_BASE_URL}/candidates/{CANDIDATE_ID}?generate_ai_summary=false",
            json=payload  # This automatically sets Content-Type: application/json
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ PATCH request successful!")
            return True
        else:
            print(f"❌ PATCH request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_manual_headers():
    """Test PATCH request with manually set headers"""
    print("\n🔍 Testing PATCH with manual headers...")
    
    payload = {
        "remarks": "Manual headers test"
    }
    
    try:
        # Method 2: Manual headers
        response = requests.patch(
            f"{API_BASE_URL}/candidates/{CANDIDATE_ID}?generate_ai_summary=false",
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Manual headers PATCH successful!")
            return True
        else:
            print(f"❌ Manual headers PATCH failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_get_candidate():
    """Test GET request to verify candidate exists"""
    print("\n🔍 Testing GET candidate...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/{CANDIDATE_ID}")
        
        if response.status_code == 200:
            print("✅ Candidate exists")
            candidate = response.json()
            print(f"   Name: {candidate.get('first_name')} {candidate.get('last_name')}")
            return True
        else:
            print(f"❌ Candidate not found: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ GET request failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Simple PATCH Request Test")
    print("=" * 40)
    
    # Test candidate exists first
    if test_get_candidate():
        print("\n" + "-" * 40)
        test_simple_patch()
        
        print("\n" + "-" * 40)
        test_manual_headers()
    
    print("\n💡 Tips:")
    print("1. Use requests.patch(url, json=data) for automatic JSON handling")
    print("2. Or use requests.patch(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})")
    print("3. Make sure your Flask app is running on http://localhost:5000") 