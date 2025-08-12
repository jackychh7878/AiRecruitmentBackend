#!/usr/bin/env python3
"""
Debug script to test database updates step by step
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_database_update_debug():
    """Test database updates with detailed debugging"""
    print("🔍 Database Update Debug Test")
    print("=" * 40)
    
    try:
        # 1. Get a candidate to test with
        print("1️⃣ Getting a candidate to test with...")
        response = requests.get(f"{API_BASE_URL}/candidates?per_page=1")
        
        if response.status_code != 200:
            print(f"❌ Failed to get candidates: {response.status_code}")
            return False
        
        data = response.json()
        candidates = data.get('candidates', [])
        
        if not candidates:
            print("❌ No candidates found")
            return False
        
        candidate = candidates[0]
        candidate_id = candidate['id']
        candidate_name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}"
        
        print(f"✅ Testing with candidate {candidate_id}: {candidate_name}")
        
        # 2. Check current AI summary and embedding
        print(f"\n2️⃣ Checking current AI summary and embedding...")
        print(f"   Current ai_short_summary: {candidate.get('ai_short_summary', 'None')[:100] if candidate.get('ai_short_summary') else 'None'}...")
        print(f"   Current embedding_vector: {'Present' if candidate.get('embedding_vector') else 'None'}")
        
        # 3. Test individual AI processing
        print(f"\n3️⃣ Testing individual AI processing...")
        patch_response = requests.patch(
            f"{API_BASE_URL}/candidates/{candidate_id}?generate_ai_summary=true",
            json={"remarks": "Debug test for database update"},
            headers={"Content-Type": "application/json"}
        )
        
        if patch_response.status_code != 200:
            print(f"❌ Individual AI processing failed: {patch_response.status_code}")
            print(f"   Response: {patch_response.text}")
            return False
        
        print("✅ Individual AI processing successful")
        
        # 4. Verify the update
        print(f"\n4️⃣ Verifying the update...")
        time.sleep(2)  # Wait for processing
        
        verify_response = requests.get(f"{API_BASE_URL}/candidates/{candidate_id}")
        
        if verify_response.status_code == 200:
            updated_candidate = verify_response.json()
            new_summary = updated_candidate.get('ai_short_summary')
            new_embedding = updated_candidate.get('embedding_vector')
            
            print(f"   Updated ai_short_summary: {new_summary[:100] if new_summary else 'None'}...")
            print(f"   Updated embedding_vector: {'Present' if new_embedding else 'None'}")
            
            if new_summary and new_summary != candidate.get('ai_short_summary'):
                print("✅ AI summary was updated successfully!")
            else:
                print("❌ AI summary was not updated")
            
            if new_embedding:
                print("✅ Embedding vector was updated successfully!")
            else:
                print("❌ Embedding vector was not updated")
        else:
            print(f"❌ Failed to verify update: {verify_response.status_code}")
        
        # 5. Test bulk regeneration on this single profile
        print(f"\n5️⃣ Testing bulk regeneration on single profile...")
        
        bulk_response = requests.post(
            f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate",
            json={"created_by": "debug_test_user"}
        )
        
        if bulk_response.status_code == 200:
            bulk_data = bulk_response.json()
            if bulk_data.get('success'):
                job_id = bulk_data.get('job_id')
                print(f"✅ Bulk job started: {job_id}")
                
                # Monitor for completion
                for i in range(10):
                    time.sleep(3)
                    
                    status_response = requests.get(
                        f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs/{job_id}"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        processed = status_data.get('processed_profiles', 0)
                        successful = status_data.get('successful_updates', 0)
                        failed = status_data.get('failed_updates', 0)
                        
                        print(f"   Check {i+1}: Status={status}, Processed={processed}, Success={successful}, Failed={failed}")
                        
                        if status in ['completed', 'failed']:
                            break
                
                # Cancel job
                requests.delete(f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate/jobs/{job_id}")
                
                # Final verification
                final_response = requests.get(f"{API_BASE_URL}/candidates/{candidate_id}")
                if final_response.status_code == 200:
                    final_candidate = final_response.json()
                    final_summary = final_candidate.get('ai_short_summary')
                    final_embedding = final_candidate.get('embedding_vector')
                    
                    print(f"\n6️⃣ Final verification after bulk job:")
                    print(f"   Final ai_short_summary: {final_summary[:100] if final_summary else 'None'}...")
                    print(f"   Final embedding_vector: {'Present' if final_embedding else 'None'}")
                    
                    if final_summary and final_summary != candidate.get('ai_short_summary'):
                        print("✅ AI summary persisted after bulk job!")
                    else:
                        print("❌ AI summary not persisted after bulk job")
                    
                    if final_embedding:
                        print("✅ Embedding vector persisted after bulk job!")
                    else:
                        print("❌ Embedding vector not persisted after bulk job")
            else:
                print(f"⚠️ Bulk job not started: {bulk_data.get('message')}")
        else:
            print(f"❌ Failed to start bulk job: {bulk_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during debug test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Starting Database Update Debug Test...")
    success = test_database_update_debug()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Debug test completed successfully")
    else:
        print("❌ Debug test failed")
    
    print("\n💡 This test will help identify:")
    print("   - Whether individual AI processing works")
    print("   - Whether database updates are committed")
    print("   - Whether bulk regeneration can update existing profiles")
    print("   - Where in the process the failure occurs") 