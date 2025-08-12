#!/usr/bin/env python3
"""
Test script for AI Recruitment Prompt Template Management APIs
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_list_templates():
    """Test listing all prompt templates"""
    print("🔍 Testing GET /ai-summary/prompt-templates (all templates)")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/prompt-templates")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data.get('templates', []))} templates")
            
            for template in data.get('templates', []):
                print(f"   - ID: {template['id']}, Name: {template['name']}, Active: {template['is_active']}")
            
            return data
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_list_active_templates():
    """Test listing only active templates"""
    print("\n🔍 Testing GET /ai-summary/prompt-templates?active_only=true")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/prompt-templates?active_only=true")
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get('templates', [])
            print(f"✅ Found {len(templates)} active templates")
            
            # Verify all returned templates are active
            all_active = all(template['is_active'] for template in templates)
            if all_active:
                print("✅ All returned templates are active")
            else:
                print("❌ Some returned templates are not active")
            
            return data
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_list_inactive_templates():
    """Test listing only inactive templates"""
    print("\n🔍 Testing GET /ai-summary/prompt-templates?active_only=false")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/prompt-templates?active_only=false")
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get('templates', [])
            print(f"✅ Found {len(templates)} inactive templates")
            
            # Verify all returned templates are inactive
            all_inactive = all(not template['is_active'] for template in templates)
            if all_inactive:
                print("✅ All returned templates are inactive")
            else:
                print("❌ Some returned templates are active")
            
            return data
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_get_active_template():
    """Test getting the active prompt template"""
    print("\n🔍 Testing GET /ai-summary/prompt-template (active)")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/ai-summary/prompt-template")
        
        if response.status_code == 200:
            data = response.json()
            template = data.get('template', {})
            print(f"✅ Active template: {template.get('name')} (ID: {template.get('id')})")
            print(f"   Version: {template.get('version_number')}")
            return data
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_create_template():
    """Test creating a new prompt template"""
    print("\n🔍 Testing POST /ai-summary/prompt-templates")
    
    new_template = {
        "name": "Test Template",
        "description": "A test template for validation",
        "template_content": """Test prompt template:

Please analyze this candidate data and create a summary:

{candidate_profile_data}

Focus on experience and skills.""",
        "created_by": "test_user"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/candidates/ai-summary/prompt-templates",
            json=new_template
        )
        
        if response.status_code == 201:
            data = response.json()
            template = data.get('template', {})
            print(f"✅ Created template: {template.get('name')} (ID: {template.get('id')})")
            return template
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_update_template(template_id):
    """Test updating a prompt template"""
    print(f"\n🔍 Testing PUT /ai-summary/prompt-templates/{template_id}")
    
    updates = {
        "name": "Updated Test Template",
        "description": "Updated description for testing",
        "created_by": "test_user_updated"
    }
    
    try:
        response = requests.put(
            f"{API_BASE_URL}/candidates/ai-summary/prompt-templates/{template_id}",
            json=updates
        )
        
        if response.status_code == 200:
            data = response.json()
            template = data.get('template', {})
            print(f"✅ Updated template: {template.get('name')}")
            return template
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_activate_template(template_id):
    """Test activating a prompt template"""
    print(f"\n🔍 Testing POST /ai-summary/prompt-templates/{template_id}/activate")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/candidates/ai-summary/prompt-templates/{template_id}/activate"
        )
        
        if response.status_code == 200:
            data = response.json()
            template = data.get('template', {})
            print(f"✅ Activated template: {template.get('name')}")
            return template
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_get_specific_template(template_id):
    """Test getting a specific template by ID"""
    print(f"\n🔍 Testing GET /ai-summary/prompt-templates/{template_id}")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/candidates/ai-summary/prompt-templates/{template_id}"
        )
        
        if response.status_code == 200:
            template = response.json()
            print(f"✅ Retrieved template: {template.get('name')}")
            return template
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_delete_template(template_id):
    """Test deleting a prompt template"""
    print(f"\n🔍 Testing DELETE /ai-summary/prompt-templates/{template_id}")
    
    try:
        response = requests.delete(
            f"{API_BASE_URL}/candidates/ai-summary/prompt-templates/{template_id}"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Deleted template successfully")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_create_invalid_template():
    """Test creating template with invalid data"""
    print("\n🔍 Testing POST with invalid template (missing placeholder)")
    
    invalid_template = {
        "name": "Invalid Template",
        "description": "Missing required placeholder",
        "template_content": "This template has no placeholder for candidate data",
        "created_by": "test_user"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/candidates/ai-summary/prompt-templates",
            json=invalid_template
        )
        
        if response.status_code == 400:
            print("✅ Correctly rejected invalid template")
            return True
        else:
            print(f"❌ Should have failed but got: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 AI Recruitment Prompt Template Management API Test")
    print("=" * 50)
    
    # List initial templates (all)
    initial_templates = test_list_templates()
    
    # Test filtering
    test_list_active_templates()
    test_list_inactive_templates()
    
    # Get active template
    active_template = test_get_active_template()
    
    # Test creating new template
    created_template = test_create_template()
    
    if created_template:
        template_id = created_template['id']
        
        # Test getting specific template
        test_get_specific_template(template_id)
        
        # Test updating template
        test_update_template(template_id)
        
        # Test activating template
        test_activate_template(template_id)
        
        # Verify it's now active
        test_get_active_template()
        
        # Test trying to delete active template (should fail)
        print(f"\n🔍 Testing DELETE active template (should fail)")
        test_delete_template(template_id)
        
        # Reactivate original template if it exists
        if active_template and active_template.get('template', {}).get('id'):
            original_id = active_template['template']['id']
            test_activate_template(original_id)
        
        # Now delete the test template
        test_delete_template(template_id)
    
    # Test invalid template creation
    test_create_invalid_template()
    
    # Final list
    print("\n" + "=" * 50)
    print("Final template list:")
    test_list_templates()
    
    print("\n💡 All tests completed!")
    print("📖 Available endpoints:")
    print("   GET    /api/candidates/ai-summary/prompt-templates")
    print("   POST   /api/candidates/ai-summary/prompt-templates")
    print("   GET    /api/candidates/ai-summary/prompt-templates/{id}")
    print("   PUT    /api/candidates/ai-summary/prompt-templates/{id}")
    print("   DELETE /api/candidates/ai-summary/prompt-templates/{id}")
    print("   POST   /api/candidates/ai-summary/prompt-templates/{id}/activate")
    print("   GET    /api/candidates/ai-summary/prompt-template (active)") 