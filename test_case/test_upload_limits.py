#!/usr/bin/env python3
"""
Quick test to verify upload limit configuration
"""

import requests
import os

def test_upload_config():
    """Test the upload configuration endpoint"""
    
    BASE_URL = "http://localhost:5000/api"
    
    print("🔧 Testing Upload Configuration")
    print("=" * 40)
    
    try:
        # Check current configuration
        response = requests.get(f"{BASE_URL}/candidates/batch-parse-resumes/config")
        
        if response.status_code == 200:
            config = response.json()
            
            print("✅ Current Configuration:")
            print(f"   Individual file limit: {config['limits']['individual_file_limit_mb']}MB")
            print(f"   Batch upload limit: {config['limits']['batch_upload_limit_mb']}MB")
            print(f"   Flask effective limit: {config['limits']['flask_max_content_length_mb']}MB")
            print(f"   Max files per batch: {config['limits']['max_files_per_batch']}")
            
            print("\n📋 Environment Variables:")
            print(f"   MAX_CONTENT_LENGTH: {config['environment_variables']['MAX_CONTENT_LENGTH']}")
            print(f"   BATCH_UPLOAD_LIMIT: {config['environment_variables']['BATCH_UPLOAD_LIMIT']}")
            
            print(f"\n💡 {config['recommendations']['message']}")
            print(f"   Current effective limit: {config['recommendations']['current_effective_limit_mb']}MB")
            
            # Recommendations
            effective_limit = config['limits']['flask_max_content_length_mb']
            if effective_limit < 100:
                print(f"\n⚠️  Your effective limit ({effective_limit}MB) is less than 100MB")
                print("   Consider setting BATCH_UPLOAD_LIMIT=104857600 (100MB) in your .env file")
            else:
                print(f"\n✅ Your configuration looks good for batch uploads up to {effective_limit}MB")
                
        else:
            print(f"❌ Failed to get configuration: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")

if __name__ == "__main__":
    test_upload_config() 