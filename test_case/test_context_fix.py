#!/usr/bin/env python3
"""
Simple test to verify Flask context fix for bulk regeneration
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_quick_bulk_regeneration():
    """Test starting and quickly cancelling a bulk regeneration job"""
    print("🧪 Testing Flask context fix for bulk regeneration")
    print("=" * 50)
    
    # Step 1: Get statistics first
    print("📊 Getting statistics...")
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/stats")
        
        if response.status_code == 200:
            data = response.json()
            active_profiles = data.get('profile_statistics', {}).get('active_profiles', 0)
            print(f"✅ Found {active_profiles} active profiles")
            
            if active_profiles == 0:
                print("⚠️ No active profiles to test with")
                return False
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")
        return False
    
    # Step 2: Start a test job
    print("\n🚀 Starting test bulk regeneration job...")
    try:
        payload = {
            "created_by": "context_test_user"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                job_id = data.get('job_id')
                print(f"✅ Job started successfully!")
                print(f"   Job ID: {job_id}")
                
                # Step 3: Check job status immediately
                print("\n📋 Checking job status...")
                time.sleep(2)  # Give it a moment to start
                
                status_response = requests.get(
                    f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs/{job_id}"
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    errors = status_data.get('errors', [])
                    
                    print(f"   Status: {status}")
                    
                    if errors:
                        print(f"   ❌ Errors found:")
                        for error in errors:
                            print(f"      - {error}")
                        
                        # Check if Flask context errors are present
                        context_errors = [e for e in errors if 'application context' in e]
                        if context_errors:
                            print("\n❌ Flask context errors still present - fix not working")
                            return False
                        else:
                            print("\n✅ No Flask context errors - but other errors present")
                    else:
                        print("   ✅ No errors detected")
                    
                    # Step 4: Cancel the job for safety
                    print("\n🛑 Cancelling test job...")
                    cancel_response = requests.delete(
                        f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs/{job_id}"
                    )
                    
                    if cancel_response.status_code == 200:
                        cancel_data = cancel_response.json()
                        print(f"   Cancel result: {cancel_data.get('message')}")
                    
                    return True
                else:
                    print(f"   ❌ Failed to get job status: {status_response.status_code}")
                    return False
                    
            else:
                print(f"⚠️ Job not started: {data.get('message')}")
                return False
        else:
            print(f"❌ Failed to start job: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting job: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_quick_bulk_regeneration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Context fix test completed!")
        print("💡 If no Flask context errors were shown, the fix is working")
    else:
        print("❌ Context fix test failed")
        print("💡 Check that the Flask app is running and accessible")
    
    print("\n🔧 What was fixed:")
    print("- Added Flask app context management to background threads")
    print("- Each worker thread now runs within app.app_context()")
    print("- Database operations now have proper Flask context")
    
    print("\n📝 Key changes:")
    print("1. Added app.app_context() wrapper in _run_bulk_regeneration()")
    print("2. Added app.app_context() wrapper in _process_single_profile()")
    print("3. Set Flask app reference in bulk_ai_regeneration_service")
    print("4. Initialize service with app context in app.py") 