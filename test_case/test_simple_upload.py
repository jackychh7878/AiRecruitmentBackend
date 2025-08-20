#!/usr/bin/env python3
"""
Simple test to isolate 413 error issue
"""

import requests
import io

def test_simple_upload():
    """Test with a very small file to isolate the issue"""
    
    BASE_URL = "http://localhost:5000/api"
    
    print("🔧 Testing Simple Upload")
    print("=" * 40)
    
    # Create a tiny mock PDF (about 250 bytes)
    mock_pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 22>>stream
BT/F1 12 Tf 72 720 Td(Test)Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000201 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref
245
%%EOF"""
    
    print(f"📄 Mock PDF size: {len(mock_pdf_content)} bytes ({len(mock_pdf_content)/1024:.2f} KB)")
    
    try:
        # Test 1: Single file
        print("\n1️⃣ Testing single file upload...")
        files = {
            'resume_files': ('test.pdf', mock_pdf_content, 'application/pdf')
        }
        
        response = requests.post(f"{BASE_URL}/candidates/batch-parse-resumes", files=files)
        print(f"   Status: {response.status_code}")
        if response.status_code != 202:
            print(f"   Response: {response.text}")
        else:
            result = response.json()
            print(f"   ✅ Success! Job ID: {result.get('job_id', 'N/A')}")
        
        # Test 2: Multiple files (still very small)
        print("\n2️⃣ Testing multiple file upload...")
        files = [
            ('resume_files', ('file1.pdf', mock_pdf_content, 'application/pdf')),
            ('resume_files', ('file2.pdf', mock_pdf_content, 'application/pdf')),
        ]
        
        total_size = len(mock_pdf_content) * 2
        print(f"   Total size: {total_size} bytes ({total_size/1024:.2f} KB)")
        
        response = requests.post(f"{BASE_URL}/candidates/batch-parse-resumes", files=files)
        print(f"   Status: {response.status_code}")
        if response.status_code != 202:
            print(f"   Response: {response.text}")
        else:
            result = response.json()
            print(f"   ✅ Success! Job ID: {result.get('job_id', 'N/A')}")
            
        # Test 3: Empty request
        print("\n3️⃣ Testing empty request...")
        response = requests.post(f"{BASE_URL}/candidates/batch-parse-resumes")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        # Test 4: Non-PDF file
        print("\n4️⃣ Testing non-PDF file...")
        files = {
            'resume_files': ('test.txt', b'This is not a PDF', 'text/plain')
        }
        
        response = requests.post(f"{BASE_URL}/candidates/batch-parse-resumes", files=files)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_upload() 