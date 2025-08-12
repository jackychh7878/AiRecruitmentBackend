#!/usr/bin/env python3
"""
Simple test to verify database updates work
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_simple_database_update():
    """Test a simple database update"""
    print("🧪 Testing simple database update...")
    
    try:
        # 1. Get a candidate
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
        
        # 2. Check current state
        print(f"\n📊 Current state:")
        print(f"   ai_short_summary: {'Present' if candidate.get('ai_short_summary') else 'None'}")
        print(f"   embedding_vector: {'Present' if candidate.get('embedding_vector') else 'None'}")
        
        # 3. Test simple PATCH update (without AI generation)
        print(f"\n🔧 Testing simple PATCH update...")
        
        patch_data = {
            "remarks": "Testing database update functionality"
        }
        
        patch_response = requests.patch(
            f"{API_BASE_URL}/candidates/{candidate_id}",
            json=patch_data,
            headers={"Content-Type": "application/json"}
        )
        
        if patch_response.status_code == 200:
            print("✅ Simple PATCH update successful")
            
            # 4. Verify the update
            verify_response = requests.get(f"{API_BASE_URL}/candidates/{candidate_id}")
            
            if verify_response.status_code == 200:
                updated_candidate = verify_response.json()
                new_remarks = updated_candidate.get('remarks')
                
                if new_remarks == "Testing database update functionality":
                    print("✅ Database update verified successfully!")
                    return True
                else:
                    print(f"❌ Database update not persisted. Expected: 'Testing database update functionality', Got: '{new_remarks}'")
                    return False
            else:
                print(f"❌ Failed to verify update: {verify_response.status_code}")
                return False
        else:
            print(f"❌ Simple PATCH update failed: {patch_response.status_code}")
            print(f"   Response: {patch_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Simple Database Update Test")
    print("=" * 35)
    
    success = test_simple_database_update()
    
    print("\n" + "=" * 35)
    if success:
        print("✅ Database updates are working!")
        print("💡 The issue might be in the AI processing or bulk regeneration logic")
    else:
        print("❌ Basic database updates are not working")
        print("💡 This suggests a fundamental database issue")
    
    print("\n🔍 Next steps:")
    print("1. If this test passes, run the debug test:")
    print("   python test_database_update_debug.py")
    print("2. If this test fails, check database connection and models") 