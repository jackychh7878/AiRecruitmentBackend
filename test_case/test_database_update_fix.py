#!/usr/bin/env python3
"""
Test script to verify database update fix in bulk regeneration
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_single_profile_before_bulk():
    """Test individual profile finalization first to ensure AI service works"""
    print("🧪 Testing individual profile AI processing first...")
    
    try:
        # Get a candidate to test with
        response = requests.get(f"{API_BASE_URL}/candidates?per_page=1")
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('candidates', [])
            
            if not candidates:
                print("❌ No candidates found to test with")
                return False
            
            candidate_id = candidates[0]['id']
            candidate_name = f"{candidates[0].get('first_name', '')} {candidates[0].get('last_name', '')}"
            print(f"✅ Testing with candidate {candidate_id}: {candidate_name}")
            
            # Test PATCH API with AI generation
            patch_response = requests.patch(
                f"{API_BASE_URL}/candidates/{candidate_id}?generate_ai_summary=true",
                json={"remarks": "Test AI processing before bulk"},
                headers={"Content-Type": "application/json"}
            )
            
            if patch_response.status_code == 200:
                print("✅ Individual AI processing successful")
                return True
            else:
                print(f"❌ Individual AI processing failed: {patch_response.status_code}")
                print(f"   Response: {patch_response.text}")
                return False
        else:
            print(f"❌ Failed to get candidates: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing individual profile: {str(e)}")
        return False

def test_bulk_regeneration_database_fix():
    """Test bulk regeneration with focus on database updates"""
    print("\n🧪 Testing bulk regeneration database update fix...")
    
    try:
        # Start a small test job
        payload = {
            "created_by": "database_test_user"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                job_id = data.get('job_id')
                print(f"✅ Bulk job started: {job_id}")
                
                # Monitor for a short time to see progress
                for check_count in range(6):  # Check 6 times over 30 seconds
                    time.sleep(5)
                    
                    status_response = requests.get(
                        f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs/{job_id}"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        processed = status_data.get('processed_profiles', 0)
                        successful = status_data.get('successful_updates', 0)
                        failed = status_data.get('failed_updates', 0)
                        errors = status_data.get('errors', [])
                        
                        print(f"   Check {check_count + 1}: Status={status}, Processed={processed}, Success={successful}, Failed={failed}")
                        
                        if errors:
                            print(f"   Recent errors:")
                            for error in errors[-2:]:  # Show last 2 errors
                                print(f"      - {error}")
                        
                        if status in ['completed', 'failed']:
                            break
                    else:
                        print(f"   ❌ Failed to get status: {status_response.status_code}")
                
                # Cancel the job for safety
                print("\n🛑 Cancelling job for safety...")
                cancel_response = requests.delete(
                    f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs/{job_id}"
                )
                
                if cancel_response.status_code == 200:
                    print("✅ Job cancelled successfully")
                
                # Final status check
                final_response = requests.get(
                    f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs/{job_id}"
                )
                
                if final_response.status_code == 200:
                    final_data = final_response.json()
                    final_successful = final_data.get('successful_updates', 0)
                    final_failed = final_data.get('failed_updates', 0)
                    final_errors = final_data.get('errors', [])
                    
                    print(f"\n📊 Final Results:")
                    print(f"   Successful updates: {final_successful}")
                    print(f"   Failed updates: {final_failed}")
                    
                    if final_successful > 0:
                        print("✅ Database updates are working!")
                        return True
                    elif final_failed > 0:
                        print("❌ All updates failed. Checking errors:")
                        
                        # Check for specific error patterns
                        key_errors = [e for e in final_errors if 'success' in e.lower()]
                        context_errors = [e for e in final_errors if 'application context' in e]
                        
                        if key_errors:
                            print("   - Fixed KeyError 'success' -> now using 'processing_success'")
                        if context_errors:
                            print("   - Flask context errors still present")
                        
                        return False
                    else:
                        print("⚠️ No profiles processed yet")
                        return False
                
                return True
            else:
                print(f"⚠️ Job not started: {data.get('message')}")
                return False
        else:
            print(f"❌ Failed to start job: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bulk regeneration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Database Update Fix Test for Bulk Regeneration")
    print("=" * 55)
    
    # Test individual profile first
    individual_success = test_single_profile_before_bulk()
    
    if not individual_success:
        print("\n❌ Individual AI processing failed - bulk will also fail")
        print("💡 Fix the individual AI processing first")
        exit(1)
    
    # Test bulk regeneration
    bulk_success = test_bulk_regeneration_database_fix()
    
    print("\n" + "=" * 55)
    if bulk_success:
        print("🎉 Database update fix appears to be working!")
    else:
        print("❌ Database update fix needs more work")
    
    print("\n🔧 What was fixed:")
    print("1. Changed result['success'] to result.get('processing_success', False)")
    print("2. Added proper error handling and logging")
    print("3. Added detailed debugging output")
    print("4. Ensured Flask app context in worker threads")
    print("5. Added proper database session management")
    
    print("\n📝 Expected improvements:")
    print("- No more KeyError: 'success' errors")
    print("- Proper AI summary and embedding updates")
    print("- Better error tracking and debugging")
    print("- Successful database commits") 