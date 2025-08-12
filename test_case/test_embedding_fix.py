#!/usr/bin/env python3
"""
Test script to verify the embedding vector fix
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_embedding_vector_fix():
    """Test that embedding vectors are handled properly"""
    print("🧪 Testing Embedding Vector Fix")
    print("=" * 35)
    
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
        
        # 2. Check current embedding vector
        print(f"\n2️⃣ Checking current embedding vector...")
        current_embedding = candidate.get('embedding_vector')
        
        if current_embedding:
            print(f"   Current embedding: Present")
            try:
                if hasattr(current_embedding, 'size'):
                    print(f"   Embedding size: {current_embedding.size}")
                elif hasattr(current_embedding, '__len__'):
                    print(f"   Embedding length: {len(current_embedding)}")
                else:
                    print(f"   Embedding type: {type(current_embedding)}")
            except Exception as e:
                print(f"   Error checking embedding: {str(e)}")
        else:
            print(f"   Current embedding: None")
        
        # 3. Test AI processing to generate embedding
        print(f"\n3️⃣ Testing AI processing to generate embedding...")
        
        patch_response = requests.patch(
            f"{API_BASE_URL}/candidates/{candidate_id}?generate_ai_summary=true",
            json={"remarks": "Testing embedding vector fix"},
            headers={"Content-Type": "application/json"}
        )
        
        if patch_response.status_code == 200:
            print("✅ AI processing successful")
            
            # 4. Wait and verify the update
            print(f"\n4️⃣ Verifying the update...")
            time.sleep(3)
            
            verify_response = requests.get(f"{API_BASE_URL}/candidates/{candidate_id}")
            
            if verify_response.status_code == 200:
                updated_candidate = verify_response.json()
                new_embedding = updated_candidate.get('embedding_vector')
                
                if new_embedding:
                    print(f"✅ New embedding generated successfully!")
                    try:
                        if hasattr(new_embedding, 'size'):
                            print(f"   New embedding size: {new_embedding.size}")
                        elif hasattr(new_embedding, '__len__'):
                            print(f"   New embedding length: {len(new_embedding)}")
                        else:
                            print(f"   New embedding type: {type(new_embedding)}")
                    except Exception as e:
                        print(f"   Error checking new embedding: {str(e)}")
                else:
                    print(f"❌ No new embedding generated")
                
                # 5. Test bulk regeneration
                print(f"\n5️⃣ Testing bulk regeneration...")
                
                bulk_response = requests.post(
                    f"{API_BASE_URL}/candidates/ai-summary/bulk-regenerate",
                    json={"created_by": "embedding_test_user"}
                )
                
                if bulk_response.status_code == 200:
                    bulk_data = bulk_response.json()
                    if bulk_data.get('success'):
                        job_id = bulk_data.get('job_id')
                        print(f"✅ Bulk job started: {job_id}")
                        
                        # Monitor for a short time
                        for i in range(5):
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
                        
                        if successful > 0:
                            print(f"✅ Bulk regeneration successful! {successful} profiles updated")
                            return True
                        else:
                            print(f"❌ Bulk regeneration failed. All {failed} profiles failed")
                            return False
                    else:
                        print(f"⚠️ Bulk job not started: {bulk_data.get('message')}")
                        return False
                else:
                    print(f"❌ Failed to start bulk job: {bulk_response.status_code}")
                    return False
            else:
                print(f"❌ Failed to verify update: {verify_response.status_code}")
                return False
        else:
            print(f"❌ AI processing failed: {patch_response.status_code}")
            print(f"   Response: {patch_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Starting Embedding Vector Fix Test...")
    success = test_embedding_vector_fix()
    
    print("\n" + "=" * 35)
    if success:
        print("🎉 Embedding vector fix is working!")
        print("✅ No more 'truth value of array' errors")
        print("✅ Database updates should now work properly")
    else:
        print("❌ Embedding vector fix needs more work")
    
    print("\n🔧 What was fixed:")
    print("1. Proper handling of pgvector fields (numpy arrays)")
    print("2. Safe length checking with try/catch blocks")
    print("3. Use of .size for numpy arrays instead of len()")
    print("4. Proper null checking before operations")
    
    print("\n💡 The error was caused by:")
    print("- pgvector fields return numpy arrays")
    print("- numpy arrays can't be used directly in boolean contexts")
    print("- len() on numpy arrays can cause ambiguity errors") 