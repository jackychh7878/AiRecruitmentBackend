#!/usr/bin/env python3
"""
Test script for the updated Resume API endpoints
This script demonstrates how to use the new PDF storage APIs
"""

import requests
import base64
import json

# Configuration
API_BASE_URL = "http://localhost:5000"
CANDIDATE_ID = 1  # Replace with actual candidate ID

def test_create_resume_with_base64():
    """Test creating a resume with base64 encoded PDF data"""
    print("Testing: Create resume with base64 PDF data")
    
    # Sample base64 PDF data (this is just a placeholder - use real PDF data)
    sample_pdf_base64 = "JVBERi0xLjQKJcfs..."  # This would be actual base64 PDF data
    
    payload = {
        "candidate_id": CANDIDATE_ID,
        "file_name": "test_resume.pdf",
        "file_size": 1024,  # Size in bytes
        "content_type": "application/pdf",
        "pdf_data_base64": sample_pdf_base64
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/resumes/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            print("✅ Resume created successfully")
            print(f"Response: {response.json()}")
            return response.json()
        else:
            print(f"❌ Failed to create resume: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
    
    return None

def test_upload_resume_file():
    """Test uploading a resume file directly"""
    print("Testing: Upload resume file (multipart)")
    
    # Note: This requires an actual PDF file
    try:
        files = {
            'pdf_file': ('test_resume.pdf', open('test_resume.pdf', 'rb'), 'application/pdf')
        }
        data = {
            'candidate_id': CANDIDATE_ID
        }
        
        response = requests.post(
            f"{API_BASE_URL}/resumes/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 201:
            print("✅ Resume uploaded successfully")
            print(f"Response: {response.json()}")
            return response.json()
        else:
            print(f"❌ Failed to upload resume: {response.status_code}")
            print(f"Error: {response.text}")
            
    except FileNotFoundError:
        print("❌ test_resume.pdf file not found. Create a test PDF file first.")
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
    
    return None

def test_get_resume_info(resume_id):
    """Test getting resume information"""
    print(f"Testing: Get resume info for ID {resume_id}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/resumes/{resume_id}/info")
        
        if response.status_code == 200:
            print("✅ Resume info retrieved successfully")
            print(f"Response: {response.json()}")
            return response.json()
        else:
            print(f"❌ Failed to get resume info: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
    
    return None

def test_download_resume(resume_id):
    """Test downloading a resume file"""
    print(f"Testing: Download resume ID {resume_id}")
    
    try:
        response = requests.get(f"{API_BASE_URL}/resumes/{resume_id}/download")
        
        if response.status_code == 200:
            print("✅ Resume downloaded successfully")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {response.headers.get('Content-Length')}")
            print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
            
            # Save the downloaded file
            with open(f"downloaded_resume_{resume_id}.pdf", "wb") as f:
                f.write(response.content)
            print(f"📁 Saved as downloaded_resume_{resume_id}.pdf")
            
        else:
            print(f"❌ Failed to download resume: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")

def test_list_resumes():
    """Test listing all resumes"""
    print("Testing: List all resumes")
    
    try:
        response = requests.get(f"{API_BASE_URL}/resumes/")
        
        if response.status_code == 200:
            print("✅ Resumes listed successfully")
            data = response.json()
            print(f"Total resumes: {data.get('total', 0)}")
            print(f"Current page: {data.get('current_page', 1)}")
            return data
        else:
            print(f"❌ Failed to list resumes: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
    
    return None

def main():
    """Run all tests"""
    print("🧪 Testing Resume API Endpoints")
    print("=" * 50)
    
    # Test 1: List existing resumes
    resume_list = test_list_resumes()
    print("\n" + "-" * 50 + "\n")
    
    # Test 2: Upload a resume file (if test file exists)
    uploaded_resume = test_upload_resume_file()
    print("\n" + "-" * 50 + "\n")
    
    # Test 3: Create resume with base64 data
    created_resume = test_create_resume_with_base64()
    print("\n" + "-" * 50 + "\n")
    
    # Test 4: Get resume info (use existing resume or newly created one)
    resume_id_to_test = None
    if created_resume and 'id' in created_resume:
        resume_id_to_test = created_resume['id']
    elif uploaded_resume and 'id' in uploaded_resume:
        resume_id_to_test = uploaded_resume['id']
    elif resume_list and resume_list.get('resumes') and len(resume_list['resumes']) > 0:
        resume_id_to_test = resume_list['resumes'][0]['id']
    
    if resume_id_to_test:
        test_get_resume_info(resume_id_to_test)
        print("\n" + "-" * 50 + "\n")
        
        # Test 5: Download resume
        test_download_resume(resume_id_to_test)
    else:
        print("⚠️  No resume ID available for testing info/download endpoints")
    
    print("\n🏁 Testing completed!")

if __name__ == "__main__":
    main() 